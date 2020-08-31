# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import re
import sys

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)
sys.path.append(os.path.abspath(os.path.join(__dir__, '../..')))

import utility as utility
from ppocr.utils.utility import initial_logger

logger = initial_logger()
import cv2
import predict_det000 as predict_det
import predict_rec000 as predict_rec
import copy
import numpy as np
import math
import time
from ppocr.utils.utility import get_image_file_list, check_and_read_gif
from PIL import Image
from utility import draw_ocr
from utility import draw_ocr_box_txt


class TextSystem(object):
    def __init__(self, args):
        self.text_detector = predict_det.TextDetector(args)
        self.text_recognizer = predict_rec.TextRecognizer(args)

    def get_rotate_crop_image(self, img, points):
        '''
        img_height, img_width = img.shape[0:2]
        left = int(np.min(points[:, 0]))
        right = int(np.max(points[:, 0]))
        top = int(np.min(points[:, 1]))
        bottom = int(np.max(points[:, 1]))
        img_crop = img[top:bottom, left:right, :].copy()
        points[:, 0] = points[:, 0] - left
        points[:, 1] = points[:, 1] - top
        '''
        img_crop_width = int(
            max(
                np.linalg.norm(points[0] - points[1]),
                np.linalg.norm(points[2] - points[3])))
        img_crop_height = int(
            max(
                np.linalg.norm(points[0] - points[3]),
                np.linalg.norm(points[1] - points[2])))
        pts_std = np.float32([[0, 0], [img_crop_width, 0],
                              [img_crop_width, img_crop_height],
                              [0, img_crop_height]])
        M = cv2.getPerspectiveTransform(points, pts_std)
        dst_img = cv2.warpPerspective(
            img,
            M, (img_crop_width, img_crop_height),
            borderMode=cv2.BORDER_REPLICATE,
            flags=cv2.INTER_CUBIC)
        dst_img_height, dst_img_width = dst_img.shape[0:2]
        if dst_img_height * 1.0 / dst_img_width >= 1.5:
            dst_img = np.rot90(dst_img)
        return dst_img

    def print_draw_crop_rec_res(self, img_crop_list, rec_res):
        bbox_num = len(img_crop_list)
        for bno in range(bbox_num):
            cv2.imwrite("./output/img_crop_%d.jpg" % bno, img_crop_list[bno])
            print(bno, rec_res[bno])

    def rec_a_frame(self, img):
        ori_im = img.copy()
        dt_boxes, elapse = self.text_detector(img)
        # print("dt_boxes num : {}, elapse : {}".format(len(dt_boxes), elapse))
        if dt_boxes is None:
            return None, None
        img_crop_list = []

        dt_boxes = sorted_boxes(dt_boxes)

        for bno in range(len(dt_boxes)):
            tmp_box = copy.deepcopy(dt_boxes[bno])
            img_crop = self.get_rotate_crop_image(ori_im, tmp_box)
            img_crop_list.append(img_crop)
        rec_res, elapse = self.text_recognizer(img_crop_list)
        # print("rec_res num  : {}, elapse : {}".format(len(rec_res), elapse))
        # self.print_draw_crop_rec_res(img_crop_list, rec_res)
        return dt_boxes, rec_res

    def __call__(self, img):
        t0 = time.time()
        ori_im = img.copy()
        dt_boxes, elapse = self.text_detector(img)
        # print("dt_boxes num : {}, elapse : {}".format(len(dt_boxes), elapse))
        if dt_boxes is None:
            return None, None
        img_crop_list = []
        t1 = time.time()
        dt_boxes = sorted_boxes(dt_boxes)

        for bno in range(len(dt_boxes)):
            tmp_box = copy.deepcopy(dt_boxes[bno])
            img_crop = self.get_rotate_crop_image(ori_im, tmp_box)
            img_crop_list.append(img_crop)
        # t1 = time.time()
        rec_res, elapse = self.text_recognizer(img_crop_list)
        # print("rec_res num  : {}, elapse : {}".format(len(rec_res), elapse))
        # self.print_draw_crop_rec_res(img_crop_list, rec_res)
        # print(time.time() - t1, t1 - t0)
        return dt_boxes, rec_res


def sorted_boxes(dt_boxes):
    """
    Sort text boxes in order from top to bottom, left to right
    args:
        dt_boxes(array):detected text boxes with shape [4, 2]
    return:
        sorted boxes(array) with shape [4, 2]
    """
    num_boxes = dt_boxes.shape[0]
    sorted_boxes = sorted(dt_boxes, key=lambda x: (x[0][1], x[0][0]))
    _boxes = list(sorted_boxes)

    for i in range(num_boxes - 1):
        if abs(_boxes[i + 1][0][1] - _boxes[i][0][1]) < 10 and \
                (_boxes[i + 1][0][0] < _boxes[i][0][0]):
            tmp = _boxes[i]
            _boxes[i] = _boxes[i + 1]
            _boxes[i + 1] = tmp
    return _boxes


class OCRpredicter():
    def __init__(self, args=utility.parse_args(),
                 det_model_dir=r"D:\python_work\Ar_project\PaddleOCR\inference\ch_det_mv3_db",
                 rec_model_dir=r"D:\python_work\Ar_project\PaddleOCR\inference\ch_rec_mv3_crnn",
                 rec_char_dict_path=r"D:\python_work\Ar_project\PaddleOCR\ppocr\utils\ppocr_keys_v1.txt"):
        print("init ocrsystem")
        args.det_model_dir = det_model_dir
        args.rec_model_dir = rec_model_dir
        args.rec_char_dict_path = rec_char_dict_path
        # print(args,111)
        # image_file_list = get_image_file_list(args.image_dir)
        self.text_sys = TextSystem(args)
        print("ocrsystem ready!")
        # is_visualize = True
        # tackle_img_num = 0
        # for image_file in image_file_list:
        #     img, flag = check_and_read_gif(image_file)
        #     if not flag:
        # image_file = r"D:\python_work\Ar_project\PaddleOCR\0.png"
        # img = cv2.imread(image_file)
        # if img is None:
        #     logger.info("error in loading image:{}".format(image_file))
        # continue
        # starttime = time.time()
        # tackle_img_num += 1
        # if not args.use_gpu and args.enable_mkldnn and tackle_img_num % 30 == 0:
        #     self.text_sys = TextSystem(args)

    def predict_a_frame(self, frame):
        t0 = time.time()
        dt_boxes, rec_res = self.text_sys(frame)
        # print("Predict time:", time.time() - t0)
        # print("Predict time:", dt_boxes, rec_res)
        return dt_boxes, rec_res

    def visual_a_frame(self, frame, dt_boxes, rec_res):
        drop_score = 0.5
        dt_num = len(dt_boxes)
        for dno in range(dt_num):
            text, score = rec_res[dno]
            if score >= drop_score:
                text_str = "%s, %.3f" % (text, score)
                print(text_str)
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        boxes = dt_boxes
        txts = [rec_res[i][0] for i in range(len(rec_res))]
        scores = [rec_res[i][1] for i in range(len(rec_res))]

        draw_img = draw_ocr(
            image,
            boxes,
            txts,
            scores,
            draw_txt=True,
            drop_score=drop_score)
        draw_img_save = "./inference_results/"
        if not os.path.exists(draw_img_save):
            os.makedirs(draw_img_save)
        cv2.imwrite(
            os.path.join(draw_img_save, 'visul.png'),
            draw_img[:, :, ::-1])
        print("The visualized image saved in {}".format(
            os.path.join(draw_img_save, 'visul.png')))


def main(args):
    args.det_model_dir = r"D:\python_work\Ar_project\PaddleOCR\inference\ch_det_mv3_db"
    args.rec_model_dir = r"D:\python_work\Ar_project\PaddleOCR\inference\ch_rec_mv3_crnn"
    args.rec_char_dict_path = r"D:\python_work\Ar_project\PaddleOCR\ppocr\utils\ppocr_keys_v1.txt"
    # print(args)
    # image_file_list = get_image_file_list(args.image_dir)
    text_sys = TextSystem(args)
    # print(text_sys)
    is_visualize = True
    tackle_img_num = 0
    # for image_file in image_file_list:
    #     img, flag = check_and_read_gif(image_file)
    #     if not flag:
    image_file = r"D:\python_work\Ar_project\PaddleOCR\0.png"
    img = cv2.imread(image_file)
    if img is None:
        logger.info("error in loading image:{}".format(image_file))
        # continue
    starttime = time.time()
    tackle_img_num += 1
    if not args.use_gpu and args.enable_mkldnn and tackle_img_num % 30 == 0:
        text_sys = TextSystem(args)
    dt_boxes, rec_res = text_sys(img)
    elapse = time.time() - starttime
    # print("Predict time of %s: %.3fs" % (image_file, elapse))

    drop_score = 0.5
    dt_num = len(dt_boxes)
    for dno in range(dt_num):
        text, score = rec_res[dno]
        if score >= drop_score:
            text_str = "%s, %.3f" % (text, score)
            print(text_str)

    if is_visualize:
        image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        boxes = dt_boxes
        txts = [rec_res[i][0] for i in range(len(rec_res))]
        scores = [rec_res[i][1] for i in range(len(rec_res))]

        draw_img = draw_ocr(
            image,
            boxes,
            txts,
            scores,
            draw_txt=True,
            drop_score=drop_score)
        draw_img_save = "./inference_results/"
        if not os.path.exists(draw_img_save):
            os.makedirs(draw_img_save)
        cv2.imwrite(
            os.path.join(draw_img_save, os.path.basename(image_file)),
            draw_img[:, :, ::-1])
        print("The visualized image saved in {}".format(
            os.path.join(draw_img_save, os.path.basename(image_file))))


def replace_all_blank(value):
    """
  去除value中的所有非字母内容，包括标点符号、空格、换行、下划线等
  :param value: 需要处理的内容
  :return: 返回处理后的内容
  """
    # \W 表示匹配非数字字母下划线
    result = re.sub('\W+', '', value).replace("_", '')
    return result


def find_cartext(res):
    """找到正确的车牌号"""
    info = res[0]
    if info[1] > 0.85 and len(info[0]) >= 7:
        print("sure", info)
        cartext = info[0]
        cartext = replace_all_blank(cartext)
        if len(cartext) == 7 and cartext[0] in CARTEXT and cartext[1].isalpha():
            print("正确车牌:", cartext)
            return cartext
        else:
            return None
    else:
        return None


if __name__ == "__main__":
    # main(utility.parse_args())
    CARTEXT = "浙粤京津冀晋蒙辽黑沪吉苏皖赣鲁豫鄂湘桂琼渝川贵云藏陕甘青宁"
    predicter = OCRpredicter()
    img = cv2.imread(r"D:\python_work\Ar_project\PaddleDetection\te\2.png")
    # while 1:
    _, res = predicter.predict_a_frame(img)
    print(res)
    find_cartext(res)

    # predicter.predict_a_frame(img)
    # predicter.predict_a_frame(img)
    # text_sys = TextSystem(img)
    # print(text_sys)
