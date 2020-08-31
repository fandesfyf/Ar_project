# -*- coding:utf-8 -*-
import cv2
import numpy as np


class Arrow:#箭头类
    def __init__(self, imgpath=r"arrow/left.png", anglex=-70, angley=0, anglez=0, fov=42):
        self.img = cv2.imread(imgpath, cv2.IMREAD_UNCHANGED)
        self.anglex = anglex
        self.angley = angley
        self.anglez = anglez
        self.fov = fov
        self.h, self.w = self.img.shape[:2]

    def updata_angle(self, anglex=None, angley=None, anglez=None, fov=None, w=None, h=None):
        if w is None:
            w = self.w
        if h is None:
            h = self.h
        if anglez is None:
            anglez = self.anglez
        if angley is None:
            angley = self.angley
        if anglex is None:
            anglex = self.anglex
        if fov is None:
            fov = self.fov

        wr = self.get_warpR(anglex, angley, anglez, fov, w, h)
        result = cv2.warpPerspective(self.img, wr, (w, h),borderMode = cv2.BORDER_TRANSPARENT)
        return result

    def get_warpR(self, anglex=0, angley=0, anglez=0, fov=42, w=200, h=200):
        def rad(x):
            return x * np.pi / 180

        # 镜头与图像间的距离，21为半可视角，算z的距离是为了保证在此可视角度下恰好显示整幅图像
        z = np.sqrt(w ** 2 + h ** 2) / 2 / np.tan(rad(fov / 2))
        # 齐次变换矩阵
        rx = np.array([[1, 0, 0, 0],
                       [0, np.cos(rad(anglex)), -np.sin(rad(anglex)), 0],
                       [0, -np.sin(rad(anglex)), np.cos(rad(anglex)), 0, ],
                       [0, 0, 0, 1]], np.float32)

        ry = np.array([[np.cos(rad(angley)), 0, np.sin(rad(angley)), 0],
                       [0, 1, 0, 0],
                       [-np.sin(rad(angley)), 0, np.cos(rad(angley)), 0, ],
                       [0, 0, 0, 1]], np.float32)

        rz = np.array([[np.cos(rad(anglez)), np.sin(rad(anglez)), 0, 0],
                       [-np.sin(rad(anglez)), np.cos(rad(anglez)), 0, 0],
                       [0, 0, 1, 0],
                       [0, 0, 0, 1]], np.float32)

        r = rx.dot(ry).dot(rz)

        # 四对点的生成
        pcenter = np.array([h / 2, w / 2, 0, 0], np.float32)

        p1 = np.array([0, 0, 0, 0], np.float32) - pcenter
        p2 = np.array([w, 0, 0, 0], np.float32) - pcenter
        p3 = np.array([0, h, 0, 0], np.float32) - pcenter
        p4 = np.array([w, h, 0, 0], np.float32) - pcenter

        dst1 = r.dot(p1)
        dst2 = r.dot(p2)
        dst3 = r.dot(p3)
        dst4 = r.dot(p4)

        list_dst = [dst1, dst2, dst3, dst4]

        org = np.array([[0, 0],
                        [w, 0],
                        [0, h],
                        [w, h]], np.float32)

        dst = np.zeros((4, 2), np.float32)

        # 投影至成像平面
        for i in range(4):
            dst[i, 0] = list_dst[i][0] * z / (z - list_dst[i][2]) + pcenter[0]
            dst[i, 1] = list_dst[i][1] * z / (z - list_dst[i][2]) + pcenter[1]

        warpR = cv2.getPerspectiveTransform(org, dst)
        return warpR


if __name__ == '__main__':
    ar = Arrow()
    cv2.namedWindow("hj", 0)
    cv2.imshow("hj", ar.updata_angle(anglex=-70, w=1200, h=800))
    cv2.waitKey(0)
