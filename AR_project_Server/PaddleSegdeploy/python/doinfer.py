# coding: utf8
# Copyright (c) 2019 PaddlePaddle Authors. All Rights Reserve.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ast
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import Process, Queue

import cv2
import gflags
import numpy as np
import paddle.fluid as fluid
import yaml

# gflags.DEFINE_string("conf", default="", help="Configuration File Path")
# gflags.DEFINE_string("input_dir", default="", help="Directory of Input Images")
gflags.DEFINE_string("trt_mode", default="", help="Use optimized model")


# gflags.DEFINE_string(
#     "ext", default=".jpeg|.jpg", help="Input Image File Extensions")
# gflags.FLAGS = gflags.FLAGS


# Generate ColorMap for visualization生成用于可视化的颜色映射
def generate_colormap(num_classes):
    color_map = num_classes * [0, 0, 0]
    for i in range(0, num_classes):
        j = 0
        lab = i
        while lab:
            color_map[i * 3] |= (((lab >> 0) & 1) << (7 - j))
            color_map[i * 3 + 1] |= (((lab >> 1) & 1) << (7 - j))
            color_map[i * 3 + 2] |= (((lab >> 2) & 1) << (7 - j))
            j += 1
            lab >>= 3
    color_map = [color_map[i:i + 3] for i in range(0, len(color_map), 3)]
    return color_map


# Paddle-TRT Precision Map
trt_precision_map = {
    "int8": fluid.core.AnalysisConfig.Precision.Int8,
    "fp32": fluid.core.AnalysisConfig.Precision.Float32,
    "fp16": fluid.core.AnalysisConfig.Precision.Half
}


# scan a directory and get all images with support extensions
def get_images_from_dir(img_dir, support_ext=".jpg|.jpeg"):
    if (not os.path.exists(img_dir) or not os.path.isdir(img_dir)):
        raise Exception("Image Directory [%s] invalid" % img_dir)
    imgs = []
    for item in os.listdir(img_dir):
        ext = os.path.splitext(item)[1][1:].strip().lower()
        if (len(ext) > 0 and ext in support_ext):
            item_path = os.path.join(img_dir, item)
            imgs.append(item_path)
    return imgs


# Deploy Configuration File Parser
# 部署配置文件分析器
class DeployConfig:
    def __init__(self, conf_file):
        if not os.path.exists(conf_file):
            raise Exception('Config file path [%s] invalid!' % conf_file)

        with open(conf_file) as fp:
            configs = yaml.load(fp, Loader=yaml.FullLoader)
            deploy_conf = configs["DEPLOY"]
            # 1. get eval_crop_size
            self.eval_crop_size = ast.literal_eval(
                deploy_conf["EVAL_CROP_SIZE"])
            # 2. get mean
            self.mean = deploy_conf["MEAN"]
            # 3. get std
            self.std = deploy_conf["STD"]
            # 4. get class_num
            self.class_num = deploy_conf["NUM_CLASSES"]
            # 5. get paddle model and params file path
            self.model_file = os.path.join(deploy_conf["MODEL_PATH"],
                                           deploy_conf["MODEL_FILENAME"])
            self.param_file = os.path.join(deploy_conf["MODEL_PATH"],
                                           deploy_conf["PARAMS_FILENAME"])
            # 6. use_gpu
            self.use_gpu = deploy_conf["USE_GPU"]
            # 7. predictor_mode
            self.predictor_mode = deploy_conf["PREDICTOR_MODE"]
            # 8. batch_size
            self.batch_size = deploy_conf["BATCH_SIZE"]
            # 9. channels
            self.channels = deploy_conf["CHANNELS"]
            # 10. use_pr
            self.use_pr = deploy_conf["USE_PR"]


class ImageReader:
    def __init__(self, configs):
        self.config = configs
        self.threads_pool = ThreadPoolExecutor(configs.batch_size)

    # image processing thread worker
    #
    def a_process_worker(self, imgs, idx, use_pr=False):
        t1 = time.process_time()
        image_path = imgs[idx]
        # cv2_imread_flag = cv2.IMREAD_COLOR
        # if self.config.channels == 4:
        #     cv2_imread_flag = cv2.IMREAD_UNCHANGED

        im = imgs
        channels = im.shape[2]
        if channels != 3 and channels != 4:
            print("Only support rgb(gray) or rgba image.")
            return -1
        ori_h = im.shape[0]
        ori_w = im.shape[1]

        # resize to eval_crop_size
        eval_crop_size = self.config.eval_crop_size
        if ori_h != eval_crop_size[1] or ori_w != eval_crop_size[0]:
            im = cv2.resize(
                im, eval_crop_size, fx=0, fy=0, interpolation=cv2.INTER_LINEAR)

        # if use models with no pre-processing/post-processing op optimizations
        if not use_pr:
            im_mean = np.array(self.config.mean).reshape((self.config.channels,
                                                          1, 1))
            im_std = np.array(self.config.std).reshape((self.config.channels, 1,
                                                        1))
            # HWC -> CHW, don't use transpose((2, 0, 1))
            im = im.swapaxes(1, 2)
            im = im.swapaxes(0, 1)
            im = im[:, :, :].astype('float32') / 255.0
            im -= im_mean
            im /= im_std
        im = im[np.newaxis, :, :, :]
        info = [image_path, im, (ori_w, ori_h)]
        # print("a图片读取时间:", time.process_time() - t1)
        return info

    def process_worker(self, imgs, idx, use_pr=False):
        t1 = time.process_time()
        image_path = imgs[idx]
        cv2_imread_flag = cv2.IMREAD_COLOR
        if self.config.channels == 4:
            cv2_imread_flag = cv2.IMREAD_UNCHANGED

        im = cv2.imread(image_path, cv2_imread_flag)
        channels = im.shape[2]
        if channels != 3 and channels != 4:
            print("Only support rgb(gray) or rgba image.")
            return -1
        ori_h = im.shape[0]
        ori_w = im.shape[1]

        # resize to eval_crop_size
        eval_crop_size = self.config.eval_crop_size
        if ori_h != eval_crop_size[1] or ori_w != eval_crop_size[0]:
            im = cv2.resize(
                im, eval_crop_size, fx=0, fy=0, interpolation=cv2.INTER_LINEAR)

        # if use models with no pre-processing/post-processing op optimizations
        if not use_pr:
            im_mean = np.array(self.config.mean).reshape((self.config.channels,
                                                          1, 1))
            im_std = np.array(self.config.std).reshape((self.config.channels, 1,
                                                        1))
            # HWC -> CHW, don't use transpose((2, 0, 1))
            im = im.swapaxes(1, 2)
            im = im.swapaxes(0, 1)
            im = im[:, :, :].astype('float32') / 255.0
            im -= im_mean
            im /= im_std
        im = im[np.newaxis, :, :, :]
        info = [image_path, im, (ori_w, ori_h)]
        print("图片读取时间:", time.process_time() - t1)
        return info

    # process multiple images with multithreading
    # 用多线程处理多个图像
    def process(self, imgs, use_pr=False):
        imgs_data = []
        with ThreadPoolExecutor(max_workers=self.config.batch_size) as exe_pool:
            tasks = [
                exe_pool.submit(self.process_worker, imgs, idx, use_pr)
                for idx in range(len(imgs))
            ]
        for task in as_completed(tasks):
            imgs_data.append(task.result())
        return imgs_data

    def a_process(self, imgs, use_pr=False):
        imgs_data = []
        with ThreadPoolExecutor(max_workers=self.config.batch_size) as exe_pool:
            tasks = [exe_pool.submit(self.a_process_worker, imgs, 0, use_pr)]
        for task in as_completed(tasks):
            imgs_data.append(task.result())
        return imgs_data


class Predictor:
    def __init__(self, model_conf_file):
        self.config = DeployConfig(model_conf_file)
        self.image_reader = ImageReader(self.config)
        self.forward_arrow = cv2.imread(r'D:/python_work/Ar_project/arrow/forward.png')
        self.left_arrow = cv2.imread(r'D:/python_work/Ar_project/arrow/left.png')
        self.right_arrow = cv2.imread(r"D:/python_work/Ar_project/arrow/right.png")
        # self.videoWriter = cv2.VideoWriter('segout{}.mp4'.format(time.time()),
        #                                    cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), 10, (640, 360))
        # self.pre_x = 0
        self.changing = True
        if self.config.predictor_mode == "NATIVE":
            predictor_config = fluid.core.NativeConfig()
            predictor_config.prog_file = self.config.model_file
            predictor_config.param_file = self.config.param_file
            predictor_config.use_gpu = self.config.use_gpu
            predictor_config.device = 0
            predictor_config.fraction_of_gpu_memory = 0
        elif self.config.predictor_mode == "ANALYSIS":
            predictor_config = fluid.core.AnalysisConfig(
                self.config.model_file, self.config.param_file)
            if self.config.use_gpu:
                predictor_config.enable_use_gpu(100, 0)
                predictor_config.switch_ir_optim(True)
                # if gflags.FLAGS.trt_mode != "":
                #     precision_type = trt_precision_map[gflags.FLAGS.trt_mode]
                #     use_calib = (gflags.FLAGS.trt_mode == "int8")
                #     predictor_config.enable_tensorrt_engine(
                #         workspace_size=1 << 30,
                #         max_batch_size=self.config.batch_size,
                #         min_subgraph_size=40,
                #         precision_mode=precision_type,
                #         use_static=False,
                #         use_calib_mode=use_calib)
            else:
                predictor_config.disable_gpu()
            predictor_config.switch_specify_input_names(True)
            predictor_config.enable_memory_optim()
        self.predictor = fluid.core.create_paddle_predictor(predictor_config)

    def create_tensor(self, inputs, batch_size, use_pr=False):
        im_tensor = fluid.core.PaddleTensor()
        im_tensor.name = "image"
        if not use_pr:
            im_tensor.shape = [
                batch_size, self.config.channels, self.config.eval_crop_size[1],
                self.config.eval_crop_size[0]
            ]
        else:
            im_tensor.shape = [
                batch_size, self.config.eval_crop_size[1],
                self.config.eval_crop_size[0], self.config.channels
            ]
        im_tensor.dtype = fluid.core.PaddleDType.FLOAT32
        im_tensor.data = fluid.core.PaddleBuf(inputs.ravel().astype("float32"))
        return [im_tensor]

    def find_center_mask(self, m, getmin=False):
        sum1 = np.sum(m)
        if sum1 > 200:
            if getmin:
                if sum1 != 0:
                    # if sum1 > 200:
                    s1y, s1x = np.where(m)
                    min1y = s1y[200:].min()
                    min1x = int(np.mean(s1x[s1y == min1y]))
                    print('min', min1y, min1x)
                    c1x, c1y = np.sum(s1x) // sum1, np.sum(s1y) // sum1
                    # else:
                    #     s1y, s1x = np.where(m)
                    #     min1y = s1y.min()
                    #     min1x = int(np.mean(s1x[s1y == min1y]))
                    #     print('min', min1y, min1x)
                    #     c1x, c1y = np.sum(s1x) // sum1, np.sum(s1y) // sum1
                else:
                    c1x = c1y = min1y = min1x = -1
                return c1x, c1y, min1x, min1y
            else:
                if sum1 != 0:
                    s1y, s1x = np.where(m)
                    c1x, c1y = np.sum(s1x) // sum1, np.sum(s1y) // sum1
                else:
                    c1x = c1y = -1
                return c1x, c1y
        else:
            if getmin:
                return -1, -1, -1, -1
            else:
                return -1, -1

    def an_output_result(self, imgs_data, output_mask, videowriter=None, use_pr=False):
        t1 = time.process_time()
        print(imgs_data.shape, output_mask.shape)
        # ori_shape = imgs_data[0][2]

        # print(imgs_data)
        mask = output_mask

        m1 = mask == 1
        c1x, c1y, min1x, min1y = self.find_center_mask(m1, True)
        # print(abs(self.pre_x - c1x))
        # changed = False
        # if abs(self.pre_x - c1x) > 200:
        #     print('change')
        #     changed = True
        #     self.changing = False

        # self.pre_x = c1x

        left_mask = mask[:, :c1x]
        right_mask = mask[:, c1x:]

        lm2 = left_mask == 2
        lc2x, lc2y = self.find_center_mask(lm2)

        rm2 = right_mask == 2
        rc2x, rc2y = self.find_center_mask(rm2)
        if rc2x != -1:
            rc2x += c1x
        print("各点坐标:", c1x, c1y, lc2x, lc2y, rc2x, rc2y)

        # mask_png = mask
        # score_png = mask_png[:, :, np.newaxis]
        # score_png = np.concatenate([score_png] * 3, axis=2)
        # im = Image.fromarray(mask)
        # im.save("your_file.png")
        # visualization score png
        # color_map = generate_colormap(self.config.class_num)
        showpng = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
        showpng[mask == 0] = [0, 0, 0]
        showpng[mask == 1] = [0, 200, 0]
        showpng[mask == 2] = [200, 0, 0]
        # cv2.circle(showpng, (c1x, c1y), 10, (0, 0, 255), -1, 0)
        # cv2.circle(showpng, (lc2x, lc2y), 10, (0, 255, 0), -1, 0)
        # cv2.circle(showpng, (rc2x, rc2y), 10, (0, 255, 0), -1, 0)
        # cv2.circle(showpng, (min1x, min1y), 10, (0, 255, 252), -1, 0)

        # w = imgs_data.shape[1]
        # posx = w // 2
        #
        # pos1 = [[200, 800], [300, 0], [400, 800]]
        # h = 8
        # pos2 = [[0, 800], [300, 0], [0, 800]]
        # if changed or not self.changing:
        #     if c1y != -1:
        #         h = imgs_data.shape[0] - c1y
        #         pos2 = [[posx - 50, h], [min1x + 90, 0], [posx + 50, h]]
        # else:
        #     if rc2y != -1:
        #         h = imgs_data.shape[0] - rc2y
        #         pos2 = [[posx - 50, h], [rc2x + 90, 0], [posx + 50, h]]
        # pts1 = np.float32(pos1)
        # pts2 = np.float32(pos2)
        # M = cv2.getAffineTransform(pts1, pts2)
        # res = cv2.warpAffine(self.forward_arrow, M, (w, h))
        # arrmask = np.zeros(imgs_data.shape, dtype=np.uint8)
        # print(h, w)
        # arrmask[-res.shape[0] - 80:-80, :] = res

        # print(type(imgs_data), type(showpng), imgs_data.dtype, showpng.dtype)
        aphalpng = cv2.addWeighted(imgs_data, 0.8, showpng, 0.2, 0)
        # aphalpng = cv2.addWeighted(imgs_data, 0.8, arrmask, 0.2, 0)
        # contours, image = cv2.findContours(mask* 100, cv2.RETR_LIST,
        #                                    cv2.CHAIN_APPROX_SIMPLE)
        # contours = sorted(contours, key=cv2.contourArea, reverse=True)
        # cv2.drawContours(aphalpng, contours[:2], -1, (0, 255, 0), 3)
        # self.videoWriter.write(aphalpng)
        cv2.imshow('mask', aphalpng)
        cv2.waitKey(1)
        videowriter.write(aphalpng)

        # cv2.imwrite('mask.png',showpng)
        # for i in range(score_png.shape[0]):
        #     for j in range(score_png.shape[1]):
        #         score_png[i, j] = color_map[score_png[i, j, 0]]
        # save the mask
        # mask of xxx.jpeg will be saved as xxx_jpeg_mask.png
        t11 = time.process_time()
        # ext_pos = img_name.rfind(".")
        # img_name_fix = img_name[:ext_pos] + "_" + img_name[ext_pos + 1:]
        # mask_save_name = img_name_fix + "_mask.png"
        # cv2.imwrite(mask_save_name, mask_png, [cv2.CV_8UC1])
        # save the visualized result
        # result of xxx.jpeg will be saved as xxx_jpeg_result.png
        # vis_result_name = img_name_fix + "_result.png"
        # result_png = score_png
        # if not use_pr:
        #     result_png = cv2.resize(
        #         result_png,
        #         ori_shape,
        #         fx=0,
        #         fy=0,
        #         interpolation=cv2.INTER_CUBIC)
        t2 = time.process_time()
        # cv2.imwrite(vis_result_name, result_png, [cv2.CV_8UC1])
        # print("save result of [" + img_name + "] done.")
        print("后处理时间:{} {}".format(time.process_time() - t1, time.process_time() - t2), t11 - t1)

    # save prediction results and visualization them
    def output_result(self, imgs_data, infer_out, use_pr=False):
        for idx in range(len(imgs_data)):
            t1 = time.process_time()
            print(infer_out.shape)
            # img_name = imgs_data[idx][0]
            # ori_shape = imgs_data[idx][2]
            # mask = infer_out[idx]
            # if not use_pr:
            #     mask = np.argmax(mask, axis=0)

            # mask = mask.astype('uint8')
            # mask_png = mask
            # score_png = mask_png[:, :, np.newaxis]
            # score_png = np.concatenate([score_png] * 3, axis=2)
            # print(score_png)
            # im = Image.fromarray(mask)
            # im.save("your_file.png")
            # visualization score png
            # color_map = generate_colormap(self.config.class_num)

            # for i in range(score_png.shape[0]):
            #     for j in range(score_png.shape[1]):
            #         score_png[i, j] = color_map[score_png[i, j, 0]]
            # save the mask
            # mask of xxx.jpeg will be saved as xxx_jpeg_mask.png
            t11 = time.process_time()
            # ext_pos = img_name.rfind(".")
            # img_name_fix = img_name[:ext_pos] + "_" + img_name[ext_pos + 1:]
            # mask_save_name = img_name_fix + "_mask.png"
            # cv2.imwrite(mask_save_name, mask_png, [cv2.CV_8UC1])
            # save the visualized result
            # result of xxx.jpeg will be saved as xxx_jpeg_result.png
            # vis_result_name = img_name_fix + "_result.png"
            # result_png = score_png
            # if not use_pr:
            # result_png = cv2.resize(
            #     result_png,
            #     ori_shape,
            #     fx=0,
            #     fy=0,
            #     interpolation=cv2.INTER_CUBIC)
            t2 = time.process_time()
            # cv2.imwrite(vis_result_name, result_png, [cv2.CV_8UC1])
            # print("save result of [" + img_name + "] done.")
            # print("保存时间:{} {}".format(time.process_time() - t1, time.process_time() - t2), t11 - t1)

    def predict_a_frame(self, frame):

        use_pr = self.config.use_pr

        img_datas = self.image_reader.a_process(frame, use_pr)
        input_data = np.concatenate([item[1] for item in img_datas])
        input_data = self.create_tensor(input_data, 1, use_pr=use_pr)
        output_data = self.predictor.run(input_data)[0]
        output_data = output_data.as_ndarray()
        mask = output_data[0]
        mask = np.argmax(mask, axis=0)
        mask = mask.astype('uint8')  # 分类像素数据
        return mask

    def predict(self, images):
        # image reader preprocessing time cost
        reader_time = 0
        # inference time cost
        infer_time = 0
        # post_processing: generate mask and visualize it
        post_time = 0
        # total time cost: preprocessing + inference + postprocessing
        total_runtime = 0

        # record starting time point
        total_start = time.time()
        batch_size = self.config.batch_size
        use_pr = self.config.use_pr
        for i in range(0, len(images), batch_size):  # batchsize作为步长
            real_batch_size = batch_size
            if i + batch_size >= len(images):
                real_batch_size = len(images) - i
            reader_start = time.time()
            img_datas = self.image_reader.process(images[i:i + real_batch_size],
                                                  use_pr)
            input_data = np.concatenate([item[1] for item in img_datas])
            input_data = self.create_tensor(
                input_data, real_batch_size, use_pr=use_pr)
            reader_end = time.time()
            infer_start = time.time()
            output_data = self.predictor.run(input_data)[0]
            output_data = output_data.as_ndarray()
            infer_end = time.time()
            # print(output_data)
            post_start = time.time()
            self.output_result(img_datas, output_data, use_pr)
            post_end = time.time()
            reader_time += (reader_end - reader_start)
            infer_time += (infer_end - infer_start)
            post_time += (post_end - post_start)
            print("readertime:{} infetime:{} posttime:{}".format(reader_end - reader_start, infer_end - infer_start,
                                                                 post_end - post_start))

        # finishing process all images
        total_end = time.time()
        # compute whole processing time
        total_runtime = (total_end - total_start)
        print(
            "images_num=[%d],preprocessing_time=[%f],infer_time=[%f],postprocessing_time=[%f],total_runtime=[%f]"
            % (len(images), reader_time, infer_time, post_time, total_runtime))


# def run(deploy_conf, imgs_dir, support_extensions=".jpg|.jpeg"):
#     # 1. scan and get all images with valid extensions in directory imgs_dir
#     imgs = get_images_from_dir(imgs_dir, support_extensions)
#     if len(imgs) == 0:
#         print("No Image (with extensions : %s) found in [%s]" %
#               (support_extensions, imgs_dir))
#         return -1
#     # 2. create a predictor#预测er
#     seg_predictor = Predictor(deploy_conf)
#     # 3. do a inference on images
#     seg_predictor.predict(imgs)
#     return 0
class BackgroundPredict(Process):
    def __init__(self, deploy_conf, sendq, recvq, frame=None):
        super().__init__()
        self.frame = frame
        try:
            if frame == None:
                self.predicterfree = True
            else:
                self.predicterfree = False
        except:
            self.predicterfree = False
        self.deploy_conf = deploy_conf
        self.isOpened = True
        self.sendq = sendq
        self.recvq = recvq

    def get_frame(self, frame):
        self.frame = frame
        print('getttt')

    def run(self):
        self.seg_predictor = Predictor(self.deploy_conf)

        while self.isOpened:
            if self.predicterfree:
                if not self.recvq.empty():
                    self.frame = self.recvq.get()
                    if type(self.frame) == int:
                        break
                    # cv2.imwrite(r'D:/python_work/Ar_project/PaddleSeg/dataset/test/{}.png'.format(time.time()),self.frame)
                    self.predicterfree = False
                    # a = self.sendq.recv()
                    print("child get a frame")
                else:
                    if self.sendq.empty():
                        self.sendq.put(0)
                        print("child is waiting a frame")
            else:
                print("predicting")
                output_mask = self.seg_predictor.predict_a_frame(self.frame)
                self.seg_predictor.an_output_result(self.frame, output_mask, self.seg_predictor.videoWriter,use_pr=self.seg_predictor.config.use_pr)
                self.predicterfree = True


def run(deploy_conf, videodir, support_extensions=".jpg|.jpeg"):
    # 1. scan and get all images with valid extensions in directory imgs_dir
    # 2. create a predictor#预测er

    # 视频来源，可以来自一段已存好的视频，也可以直接来自USB摄像头
    cap = cv2.VideoCapture(videodir)
    cv2.namedWindow('video', 0)
    cv2.resizeWindow('video', 640, 480)

    send_q = Queue()
    recv_q = Queue()
    predicter = BackgroundPredict(deploy_conf, recv_q, send_q)
    predicter.start()
    # VideoStreaming=VideoStreamingTest()
    while cap.isOpened():
        ok, frame = cap.read()
        # print('runing')
        if not ok:
            print("no frame,rereading")
            cap = cv2.VideoCapture(videodir)
            predicter.cap = cap
        else:
            if not recv_q.empty():
                g = recv_q.get()
                frame = cv2.resize(frame, (640, 360))
                send_q.put(frame)
            cv2.imshow('video', frame)
            c = cv2.waitKey(50)
            if c & 0xFF == ord('q'):
                send_q.put(0)
                break
    cap.release()
    cv2.destroyAllWindows()

    # # 3. do a inference on images
    # seg_predictor.predict(imgs)
    return 0


def pirun(deploy_conf, IP="192.168.43.174", port=8787):
    # 1. scan and get all images with valid extensions in directory imgs_dir
    # 2. create a predictor#预测er

    # 视频来源，可以来自一段已存好的视频，也可以直接来自USB摄像头
    # cap = cv2.VideoCapture(videodir)
    cv2.namedWindow('video', 0)
    cv2.resizeWindow('video', 640, 480)

    send_q = Queue()
    recv_q = Queue()
    predicter = BackgroundPredict(deploy_conf, recv_q, send_q)
    from pi_server import VideoStreamingTest
    videoStreaming = VideoStreamingTest(IP, port)
    predicter.start()
    stream_bytes = b' '
    n = 1
    while True:
        stream_bytes += videoStreaming.connection.read(1024)
        first = stream_bytes.find(b'\xff\xd8')
        last = stream_bytes.find(b'\xff\xd9')
        if first != -1 and last != -1:
            jpg = stream_bytes[first:last + 2]
            stream_bytes = stream_bytes[last + 2:]
            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            if n == 1:
                send_q.put(frame)
                n = 0
            # print('runing')
            if not recv_q.empty():
                # print("frame", frame)
                g = recv_q.get()
                send_q.put(frame)
            cv2.imshow('video', frame)

            c = cv2.waitKey(10)
            if c & 0xFF == ord('q'):
                send_q.put(0)
                break
    # cap.release()
    cv2.destroyAllWindows()

    # # 3. do a inference on images
    # seg_predictor.predict(imgs)
    return 0


if __name__ == "__main__":
    os.chdir('D:/python_work/Ar_project/PaddleSeg')
    run(r'freeze_model/cityscape_fast_scnnnds000/deploy.yaml',
        r'D:/python_work/Ar_project/video/nvideo1.mp4')
    # pirun(r'freeze_model/cityscape_fast_scnn555501/deploy.yaml',"192.168.43.174")
    # predicter=Predictor(model_conf_file=r'D:\python_work\Ar_project\PaddleSeg\freeze_model'
    #                                                    r'\cityscape_fast_scnnnds000\deploy.yaml')
    # predicter.predict_a_frame(cv2.imread(r"D:\python_work\Ar_project\0.png"))
