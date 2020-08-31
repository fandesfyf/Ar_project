import datetime
import json
import os
import re
import sys
import time
import cv2
from multiprocessing import Process, Queue

import numpy as np

sys.path.append(os.getcwd() + "/PaddleDetectiondeploy/python")
sys.path.append(os.getcwd() + "/PaddleSegdeploy/python")
# print(os.getcwd())
from PaddleDetectiondeploy.python.doinfer import Detector as Detectionpredicter
from PaddleDetectiondeploy.python.doinfer import pi_visualize as detectionvisualize
from PaddleOCR.tools.infer.predict_system000 import OCRpredicter as OCRpredicter
from PaddleSegdeploy.python.doinfer import Predictor as PaddleSegpredicter
from ali_client import PicSender
from websocket import WebsocketThread


class Seg_predicter(Process):  # 道路分割进程,不是线程,所以初始化只能有基本类型
    def __init__(self, recvq, sendq):
        super(Seg_predicter, self).__init__()
        self.predicterfree = True
        self.sendq = recvq
        self.recvq = sendq
        self.visual = True

    def run(self):
        self.Segpredicter = PaddleSegpredicter(model_conf_file=r'model/SegModel/cityscape_fast_scnnnds111/deploy.yaml')
        print("seg predicter open successfully")
        while True:
            if self.predicterfree:
                # print("wait for a frame")
                if self.sendq.empty():
                    # print("wait signal put!")
                    self.sendq.put(0)
                else:
                    time.sleep(0.01)
            if not self.recvq.empty():
                # print("child get a frame")
                self.stream_bytes = self.recvq.get()
                t = type(self.stream_bytes)
                if t == int:
                    print("predicter exit")
                    break
                elif t == bytes:
                    self.predicterfree = False
                    frame = cv2.imdecode(np.frombuffer(self.stream_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
                    frame = cv2.resize(frame, (640, 360))
                    self.seg_predict(frame)
                    # cv2.imshow("a", frame)
                    # cv2.waitKey(1)
                    # self.detection_predict(self.frame)
                    # self.signal_active(self.detection_predict(frame))  # 预测并处理结果
                    self.predicterfree = True

    def seg_predict(self, frame):
        mask = self.Segpredicter.predict_a_frame(frame)
        self.sendq.put(mask)
        if self.visual:
            self.Segpredicter.an_output_result(frame, mask)
            # 写入视频
            # self.Segpredicter.an_output_result(frame, mask, videowriter=self.Segpredicter.videoWriter)
            # c = cv2.waitKey(1)
            # if c & 0xFF == ord('q'):
            #     self.Segpredicter.videoWriter.release()
            #     self.Segpredicter.videoWriter = cv2.VideoWriter('segout{}.mp4'.format(time.time()),
            #                                                     cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), 10,
            #                                                     (640, 360))


class Det_OCR_predicter(Process):  # 目标检测+车牌识别进程,不是线程!初始化只能有基本类型
    def __init__(self, recvq: Queue, sendq: Queue, searchrecq: Queue, threshold=0.5, run_mode='fluid',
                 output_dir='output/', use_gpu=True):
        super(Det_OCR_predicter, self).__init__()

        self.sendq = recvq
        self.recvq = sendq
        self.searchrecq = searchrecq
        self.threshold = threshold
        self.output_dir = output_dir
        self.predicterfree = True
        self.use_gpu = use_gpu
        self.run_mode = run_mode
        self.visual = True
        self.searching = False
        self.searchcarplate = None

        self.CARTEXT = "浙粤京津冀晋蒙辽黑沪吉苏皖赣鲁豫鄂湘桂琼渝川贵云藏陕甘青宁"

        self.redtime = time.time()
        self.redcount = 0
        self.greentime = time.time()
        self.greencount = 0
        self.yellowtime = time.time()
        self.yellowcount = 0
        self.stream_bytes = None
        self.limit_num = [6, 8, 0]  # 限制的尾号
        self.allow_area = "粤"  # 允许的车牌省号
        self.countjs = {}

    def run(self):
        self.OCRpredicter = OCRpredicter()
        print("ocr predicter open successfully")
        self.Detectionpredicter = Detectionpredicter(model_dir=r"model/DetectionModel/yolov3_mobilenet_v3ndd444blargep",
                                                     use_gpu=self.use_gpu)
        self.video_writer = None
        # 取消注释可以启用录制
        # self.video_writer = cv2.VideoWriter('decocrout{}.mp4'.format(time.time()),
        #                                     cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), 10,
        #                                     (1280, 720))
        print("Detectionpredicter open successfully")
        if self.visual:
            cv2.namedWindow("mask", 0)
            cv2.resizeWindow('mask', 640, 360)

        while True:
            if self.predicterfree:
                # print("wait for a frame")
                if self.sendq.empty():
                    # print("wait signal put!")
                    self.sendq.put(0)
                else:
                    time.sleep(0.01)
            if not self.searchrecq.empty():
                self.searchcarplate = self.searchrecq.get()
                print("get a searchcarplate", self.searchcarplate)
                self.searching = True
            if not self.recvq.empty():
                # print("child get a frame")
                self.stream_bytes = self.recvq.get()
                t = type(self.stream_bytes)
                if t == int:
                    print("predicter exit")
                    self.video_writer.release()
                    break
                elif t == bytes:
                    self.predicterfree = False
                    frame = cv2.imdecode(np.frombuffer(self.stream_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
                    # self.detection_predict(self.frame)
                    self.signal_active(self.detection_predict(frame))  # 预测并处理结果
                    self.predicterfree = True

    def signal_active(self, predicterinfos):  # 信号处理
        print(predicterinfos)
        if predicterinfos["red"]:
            if time.time() - self.redtime < 1:
                self.redcount += 1
            else:
                self.redcount = 1
            self.redtime = time.time()
            if self.redcount > 3:
                self.sendq.put('r')
                print('put a red signal')
        elif predicterinfos["green"]:
            if time.time() - self.greentime < 1:
                self.greencount += 1
            else:
                self.greencount = 1
            self.greentime = time.time()
            if self.greencount > 3:
                self.sendq.put('g')
                print("put a green signal")
        elif predicterinfos["yellow"]:
            if time.time() - self.yellowtime < 1:
                self.yellowcount += 1
            else:
                self.yellowcount = 1
            self.yellowtime = time.time()
            if self.yellowcount > 3:
                self.sendq.put('y')
                print("put a yellow signal")
        if predicterinfos["construction"]:
            self.sendq.put("c")
        if predicterinfos["height_limit"]:
            self.sendq.put("h")
        if len(predicterinfos["carplate"]) > 0:
            for carplateinfo in predicterinfos["carplate"]:
                carplate = carplateinfo[0]
                signaljs = {}
                if carplate[0] not in self.allow_area:
                    print("外地车")
                    if carplate + "xw" not in self.countjs.keys():
                        self.countjs[carplate + "xw"] = [1, time.time() - 0.7]
                    if self.countjs[carplate + "xw"][0] < 100 and (
                            time.time() - self.countjs[carplate + "xw"][1]) > 1:  # 间隔一秒取样,每个车牌100次
                        self.countjs[carplate + "xw"][1] = time.time()
                        self.countjs[carplate + "xw"][0] += 1
                        signaljs["type"] = "限外"
                        signaljs['carplate'] = carplate
                        signaljs['box'] = [carplateinfo[1].tolist()]
                        signaljs['image'] = self.stream_bytes
                        self.sendq.put(signaljs)
                elif int(carplate[-1]) in self.limit_num:
                    print("限号车")
                    if carplate + "xh" not in self.countjs.keys():
                        self.countjs[carplate + "xh"] = [1, time.time() - 0.7]
                    if self.countjs[carplate + "xh"][0] < 100 and (
                            time.time() - self.countjs[carplate + "xh"][1]) > 1:  # 间隔一秒取样,每个车牌100次
                        self.countjs[carplate + "xh"][1] = time.time()
                        self.countjs[carplate + "xh"][0] += 1
                        signaljs["type"] = "限号"
                        signaljs['carplate'] = carplate
                        signaljs['box'] = [carplateinfo[1].tolist()]
                        signaljs['image'] = self.stream_bytes
                        self.sendq.put(signaljs)
            if len(predicterinfos["badcar"]) > 0:
                signaljs = {}
                for badcar in predicterinfos['badcar']:
                    carplate = badcar[0][0]
                    if carplate + "changeline" not in self.countjs.keys():
                        self.countjs[carplate + "changeline"] = 1
                    else:
                        self.countjs[carplate + "changeline"] += 1
                    if self.countjs[carplate + "changeline"] < 100:
                        signaljs["carplate"] = carplate
                        signaljs["type"] = "违规变道"
                        signaljs["box"] = [badcar[0][1].tolist(), badcar[1].tolist()]
                        signaljs["image"] = self.stream_bytes
                        self.sendq.put(signaljs)
                        print("barcar emit")
            if predicterinfos["searchcarplateresult"] is not None:
                print("找到查询车!")
                self.searching = False
                searchcarplateresultjs = {"carplate": self.searchcarplate, "image": self.stream_bytes}
                self.sendq.put(searchcarplateresultjs)

    def detection_predict(self, frame):  # 预测
        result = self.Detectionpredicter.predict_a_frame(frame, self.threshold)
        returntext = {"red": 0, "yellow": 0, "green": 0, "construction": 0, "height_limit": 0, "carplate": [],
                      "badcar": [], "searchcarplateresult": None}
        # print(result)
        draw_carplate = []
        for box in result["boxes"]:
            detection_type = self.Detectionpredicter.config.labels[int(box[0])]
            if detection_type == "carplate":  # 车牌
                draw_carplate.append("notfound")
                if box[1] > 0.75:
                    # print(box)
                    if box[2] > 5 and box[4] < frame.shape[1]:
                        carplatebox = frame[int(box[3]):int(box[5]), int(box[2]) - 5:int(box[4]) + 2]
                    else:
                        carplatebox = frame[int(box[3]):int(box[5]), int(box[2]):int(box[4])]
                    info = self.get_carplate_info(carplatebox)  # 获取车牌信息
                    if info is not None:
                        # print("检测到车牌")
                        draw_carplate[-1] = info
                        if self.searching:
                            if self.searchcarplate == info:
                                returntext["searchcarplateresult"] = info
                        returntext["carplate"].append([info, box[2:]])
            elif detection_type == "red":  # 红灯
                if box[1] > 0.7:
                    print("检测到红灯")
                    returntext['red'] = 1
            elif detection_type == "green":  # 绿灯
                if box[1] > 0.6:
                    print("检测到绿灯")
                    returntext["green"] = 1
            elif detection_type == "yellow":  # 黄灯
                if box[1] > 0.7:
                    print("检测到黄灯")
                    returntext["yellow"] = 1
            elif detection_type == "badcar":
                if box[1] > 0.8:
                    print("检测到违规变道车")
                    returntext["badcar"].append([box[2:]])
            elif detection_type == "construction":
                if box[1] > 0.6:
                    print("检测到前方施工")
                    returntext["construction"] = 1
            elif detection_type == "height_limit":
                if box[1] > 0.6:
                    print("检测到限高")
                    returntext["height_limit"] = 1

        if len(returntext["badcar"]) > 0:
            carplates = returntext["carplate"]
            newbadcar = []
            for badcar in returntext["badcar"]:
                badcarpos = badcar[0]
                for carplate in carplates:
                    carplatepos = carplate[1]
                    carplatecenter = self.get_center_point(carplatepos)
                    badcarcenter = self.get_center_point(badcarpos)
                    if carplatepos[0] < badcarcenter[0] < carplatepos[2] and \
                            badcarpos[0] < carplatecenter[0] < badcarpos[2] and \
                            badcarpos[1] < carplatecenter[1] < badcarpos[3]:
                        print("找到违规车车牌", carplate[0])
                        badcar.insert(0, carplate)
                        newbadcar.append(badcar)
                        break

            returntext["badcar"] = newbadcar

        if self.visual:
            # cv2.namedWindow("mask", 0)
            # cv2.resizeWindow('mask', 640, 360)
            result["draw_carplate"] = draw_carplate
            # print(self.Detectionpredicter.config.labels)
            detectionvisualize(
                frame,
                result,
                self.Detectionpredicter.config.labels,
                mask_resolution=20, video_writer=self.video_writer
            )
            # 取消注释可以录制
            # c = cv2.waitKey(1)
            # if c & 0xFF == ord('q'):
            #     self.video_writer.release()
            #     self.video_writer = cv2.VideoWriter('decocrout{}.mp4'.format(time.time()),
            #                                         cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), 10,
            #                                         (1280, 720))

        return returntext

    def get_center_point(self, box):
        return np.array([(box[0] + box[2]) // 2, (box[1] + box[3]) // 2])

    def find_cartext(self, res):
        """找到正确的车牌号"""
        returncartext = None
        cartext = res
        cartext = re.sub('\W+', '', cartext).replace("_", '')
        if len(cartext) == 7 and cartext[0] in self.CARTEXT and cartext[1].isalpha():
            returncartext = cartext
        return returncartext

    def get_carplate_info(self, carplatebox):  # 获取车牌信息
        h, w = carplatebox.shape[0:2]
        scale = 110 / h
        h = int(h * scale)
        w = int(w * scale)
        print(h, w)
        carplatebox = cv2.resize(carplatebox, (w, h))
        _, ocr_text = self.OCRpredicter.predict_a_frame(carplatebox)
        # print("车牌识别结果:", ocr_text)
        returninfo = None

        if len(ocr_text) > 1:
            ocr_text = [["".join([ocr_text[0][0], ocr_text[1][0]]), max(ocr_text[0][1], ocr_text[1][1])]]
            print(ocr_text, "ocr_text")
        if len(ocr_text) == 1 and len(ocr_text[0][0]) > 6 and ocr_text[0][1] > 0.8:
            if ocr_text[0][0][0] in "喜夏店博鸟停电厚身潮惠窗要":
                ocr_text[0][0] = ocr_text[0][0].replace(ocr_text[0][0][0], "粤")  # 矫正粤的识别
            if ocr_text[0][0][0] in "男务游":
                ocr_text[0][0] = ocr_text[0][0].replace(ocr_text[0][0][0], "苏")  # 矫正粤的识别
            if ocr_text[0][0][1] == "8":
                ocr_text[0][0] = ocr_text[0][0].replace(ocr_text[0][0][1], "B")
            res = self.find_cartext(ocr_text[0][0])
            if res is not None:
                returninfo = res
                # print("正确车牌号:", res)
                # cv2.imwrite("pishot/{}.png".format(time.time()), carplatebox)  # 保存取样

        return returninfo


class Ar_Predicter():  # 主进程类主要负责数据传输
    def __init__(self, IP="192.168.137.1", port=8787, use_gpu=True):
        self.pos = ''
        self.det_ocr_send_q = Queue()
        self.det_ocr_recv_q = Queue()
        self.search_detocr_sendq = Queue()

        self.seg_send_q = Queue()
        self.seg_recv_q = Queue()

        self.search_sendq = Queue()
        self.search_recq = Queue()

        self.pic_sender = PicSender()
        self.pic_sender.start()
        self.Det_OCR_predicter = Det_OCR_predicter(self.det_ocr_recv_q, self.det_ocr_send_q, self.search_detocr_sendq,
                                                   use_gpu=use_gpu)
        self.Seg_predicter = Seg_predicter(self.seg_recv_q, self.seg_send_q)
        self.websocket_searcher = WebsocketThread(self.search_sendq, self.search_recq)
        # self.get_frame_start(IP=IP, port=port) # 远程连接
        self.get_frame_start(video=r"nvideo.mp4")  # 也可以传入视频

    def get_frame_start(self, IP='192.168.43.174', port=8787, video=None):
        self.Det_OCR_predicter.start()  # 目标检测进程启动
        # self.Seg_predicter.start()#道路分割进程启动
        self.websocket_searcher.start()  # 车牌搜索线程
        if video and type(video) == str:
            cap = cv2.VideoCapture(video)
            cv2.namedWindow('video', 0)
            cv2.resizeWindow('video', 640, 360)
            while cap.isOpened():
                r, frame = cap.read()
                if r:
                    try:

                        cv2.imshow("video", frame)
                        c = cv2.waitKey(30)
                        if c & 0xFF == ord('q'):
                            break
                        jpgbytes = self.frame2bytes(frame)
                        self.process_dispatch(jpgbytes, isvideo=True)
                    except:
                        cv2.destroyAllWindows()
                        print(sys.exc_info())
                        break
                else:
                    cap = cv2.VideoCapture(video)
                    print("fail and reread!")

            cap.release()
            cv2.destroyAllWindows()
        else:
            print("waiting server")
            from pi_server import VideoStreamingTest
            self.videoStreaming = VideoStreamingTest(IP, port)
            while True:
                self.videoStreaming.reset()
                # cv2.namedWindow('video', 0)
                # cv2.resizeWindow('video', 640, 360)
                print("connected")
                stream_bytes = b' '
                n = 1
                self.old_detocr_len = 1
                self.old_seg_len = 1
                try:
                    while True:
                        self.videoStreaming.client_socket.settimeout(10)
                        stream_bytes += self.videoStreaming.client_socket.recv(9999)
                        self.videoStreaming.client_socket.settimeout(None)
                        first = stream_bytes.find(b'\xff\xd8')
                        last = stream_bytes.find(b'\xff\xd9')
                        # print(len(stream_bytes[:5]))
                        if len(stream_bytes) == 0:
                            print("no frame data,exit!")
                            break
                        elif first != -1 and last != -1:
                            pos = stream_bytes[:first]
                            jpg_bytes = stream_bytes[first:last + 2]
                            self.pos = pos.decode()
                            stream_bytes = stream_bytes[last + 2:]

                            # if n == 1:#先发一帧
                            #     self.det_ocr_send_q.put(jpg_bytes)
                            #     n = 00
                            self.process_dispatch(jpg_bytes)
                            # 取消注释可预览传输的摄像头数据
                            # frame = cv2.imdecode(np.frombuffer(jpg_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
                            # cv2.imshow('video', frame)
                            # c = cv2.waitKey(1)
                            # if c & 0xFF == ord('q'):
                            # #     self.videoStreaming.writer.write("<|{}|>".format("q").encode())
                            # #     self.videoStreaming.writer.flush()
                            # #     print("write a signal")
                            # #     self.det_ocr_send_q.put(0)
                            #     break

                    self.videoStreaming.close()
                    cv2.destroyAllWindows()
                except:
                    self.videoStreaming.close()
                    cv2.destroyAllWindows()
                    print(sys.exc_info())
        print("退出")

    def process_dispatch(self, jpg_bytes, isvideo=False):
        if not self.search_recq.empty():
            searchcarplate = self.search_recq.get()
            print("正在寻找:", searchcarplate)
            if len(searchcarplate) == 7 and searchcarplate[0] in self.Det_OCR_predicter.CARTEXT:
                self.search_detocr_sendq.put(searchcarplate)
            else:
                self.search_sendq.put("车牌号有误")
        while not self.det_ocr_recv_q.empty():
            g = self.det_ocr_recv_q.get()
            print('parent receive a signal ', type(g))
            if isvideo:  # 如果是视频
                if type(g) == int:
                    print("parent get a int and put a frame", g)
                    self.det_ocr_send_q.put(jpg_bytes)
                    self.old_detocr_len = len(jpg_bytes)

            else:
                if type(g) == dict:
                    print("parent get a dict")
                    if len(g.keys()) == 2:
                        print("已找到")
                        # g["time"] = str(datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f"))
                        # g["address"] = "深圳大学粤海校区"
                        imgbytes = g["image"]
                        self.search_sendq.put(imgbytes)
                        with open("pishot/search{}.jpg".format(time.time()), "wb")as f:
                            f.write(imgbytes)
                        print("已发送 ")
                    else:
                        self.pic_sender.send(data=g["image"], type=g["type"], carplate=g["carplate"],
                                             pos=self.pos, box=g["box"])
                        print("已上报", g["carplate"], g["type"])
                elif type(g) == str:
                    print("parent get a str", g)
                    self.videoStreaming.writer.write("<|{}|>".format(g).encode())
                    self.videoStreaming.writer.flush()
                    print("write a signal'{}' to pi".format(g))
                elif type(g) == int:
                    if len(jpg_bytes) != self.old_detocr_len:
                        print("parent get a int and put a frame", g)
                        self.det_ocr_send_q.put(jpg_bytes)
                        self.old_detocr_len = len(jpg_bytes)
                    else:
                        print("重复帧d")

        while not self.seg_recv_q.empty():
            s = self.seg_recv_q.get()
            if isvideo:  # 如果是视频
                if type(s) == int:
                    print("seg require a frame")
                    self.seg_send_q.put(jpg_bytes)
                    self.old_seg_len = len(jpg_bytes)
                else:
                    print(type(s))
            else:
                if type(s) == int:
                    if len(jpg_bytes) != self.old_seg_len:
                        print("seg require a frame")
                        self.seg_send_q.put(jpg_bytes)
                        self.old_seg_len = len(jpg_bytes)
                    else:
                        print("重复帧")
                else:
                    print(type(s))

    def frame2bytes(self, frame):
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        result, imgencode = cv2.imencode('.jpg', frame, encode_param)
        data = np.array(imgencode)
        stringData = data.tobytes()
        return stringData


if __name__ == '__main__':
    IP = "172.30.84.24"
    port = 8787
    predicter = Ar_Predicter(IP)  # 需要先到Ar_Predicter初始化函数中设置为远程连接才能用socket连接远程客户端
