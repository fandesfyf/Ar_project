import datetime
import json
import os
import random
import socket
import sys
import time

import cv2
import numpy
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication


class CommendThread(QThread):
    def __init__(self, action, *arges):
        super(CommendThread, self).__init__()
        self.action = action
        self.arges = arges

    def run(self):
        if len(self.arges) == 0:
            self.action()
        elif len(self.arges) == 1:
            self.action(self.arges[0])
        elif len(self.arges) == 2:
            self.action(self.arges[0], self.arges[1])
        self.quit()


class PicSender(QThread):  # 把违章信息发送给服务器
    def __init__(self, IP='192.168.137.76', port=2222):  # 服务器
        super(PicSender, self).__init__()
        self.ip = IP
        self.port = port
        self.sending = True
        self.datas = []

    def run(self):
        while True:
            le = len(self.datas)
            if le:
                try:
                    print("created a new frame_send thread,waiting for server")
                    self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.client_socket.settimeout(1)
                    self.client_socket.connect((self.ip, self.port))
                    self.writer = self.client_socket.makefile('wb')
                    print("connect to server")
                    self.send_frame(i=le)
                    self.writer.close()
                    self.client_socket.close()
                    print("sended!")
                except:
                    print("time out to connect, retry")
            else:
                time.sleep(0.1)

    def send_frame(self, i=1):
        for n in range(i):
            data = self.datas.pop()
            infodict = data[0]
            imdata = data[1]
            if type(imdata) == bytes:
                stringData = imdata
            else:
                result, imgencode = cv2.imencode('.jpg', imdata, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
                stringData = imgencode.tobytes()
            info = json.dumps(infodict, indent=4).encode()
            self.writer.write(info + stringData)
            self.writer.flush()

    # def send_frame2(self):
    #     self.sending = True
    #     pngs = os.listdir(r"D:/python_work/Ar_project/PaddleDetection/dataset/d222/val")
    #     for png in pngs[0:1]:
    #         infodict = {}
    #         print("sending {}".format(png))
    #         imdata = cv2.imread(r"D:/python_work/Ar_project/PaddleDetection/dataset/d222/val/" + png)
    #         result, imgencode = cv2.imencode('.jpg', imdata, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
    #         data = numpy.array(imgencode)
    #         infodict["name"] = png
    #         infodict["time"] = str(datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f"))
    #         infodict["type"] = "限外"  # 限号,违规变道
    #         infodict["carplate"] = "粤A{}".format(random.randrange(11111, 99999))
    #         infodict["pos"] = "{},{}".format(random.randrange(1000000,999999)/10000,random.randrange(1000000,599999)/100000)
    #         info = json.dumps(infodict, indent=4).encode()
    #         stringData = data.tobytes()
    #         self.writer.write(info + stringData)
    #         self.writer.flush()
    #
    #     self.sending = False

    def send(self, data, type: str, carplate: str, pos: str, box: list):
        """"data为图像数据,可以为encode的也可以为没有encoding的,box为矩形框列表[[box0],[box1]]"""
        info = {}
        info["time"] = str(datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f"))
        info["type"] = type  # 限号,违规变道
        info["carplate"] = carplate
        info["pos"] = pos
        info["box"] = box
        self.datas.append([info, data])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    h, p = "172.30.84.184", 2222
    client = PicSender("192.168.137.1")
    client.start()
    pngs = os.listdir(r"D:/python_work/Ar_project/PaddleDetection/dataset/d222/val")
    for png in pngs[0:5]:
        infodict = {}
        print("add a pic {}".format(png))
        imdata = cv2.imread(r"D:/python_work/Ar_project/PaddleDetection/dataset/d222/val/" + png)

        dtype = "限外"  # 限号,违规变道
        carplate = "粤A{}".format(random.randrange(11200, 11205))
        # pos = "{},{}".format(random.randrange(1000000, 1209999) / 10000, random.randrange(2000000, 3999999) / 100000)
        pos = "{},{}".format(113.937617, 22.52734)
        client.send(imdata, dtype, carplate, pos, box=[(20, 30, 100, 50)])
    sys.exit(app.exec_())
