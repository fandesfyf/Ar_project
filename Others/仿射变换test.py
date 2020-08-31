import cv2
import numpy as np
import matplotlib.pyplot as plt
#仿射变换测试
img = cv2.imread('0.png')
arr = cv2.imread('arrow/forward.png')
# rows, cols = arr.shape[:2]
w = img.shape[1]
posx = w // 2
n = 120
h = 400
pos1 = [[200, 800], [300, 0], [400, 800]]
pos2 = [[posx - 80, h], [800, 0], [posx + 80, h]]
pts1 = np.float32(pos1)
pts2 = np.float32(pos2)
M = cv2.getAffineTransform(pts1, pts2)
res = cv2.warpAffine(arr, M, (w, h))
arrmask = np.zeros(img.shape, dtype=np.uint8)
arrmask[-h:, :] = res

aphalpng = cv2.addWeighted(img, 0.8, arrmask, 0.2, 0)
plt.plot([i[0] for i in pos1], [i[1] for i in pos1])
plt.plot([i[0] for i in pos2], [i[1] for i in pos2])
plt.show()
print(M)
# 第三个参数：变换后的图像大小


# cv2.imshow('sdf', arr)
# cv2.imshow('fasdf', res)
cv2.imshow('dsf', aphalpng)
# cv2.waitKey(0)
plt.subplot(121)
plt.imshow(arr)
plt.subplot(122)
plt.imshow(res)
plt.show()
cv2.waitKey(0)
