# 分训练集和测试集
import os, random, shutil

rp = r"C:\Users\Fandes\Desktop\p555"  # 把该文件夹的数据集分类，用于paddle图像分割套件的数据准备

if not os.path.exists(rp + "/annotations/train"):
    os.mkdir(rp + "/annotations/train")
if not os.path.exists(rp + "/annotations/val"):
    os.mkdir(rp + "/annotations/val")
if not os.path.exists(rp + '/images'):
    os.mkdir(rp + '/images')
if not os.path.exists(rp + "/images/train"):
    os.mkdir(rp + "/images/train")
if not os.path.exists(rp + "/images/val"):
    os.mkdir(rp + "/images/val")

tpnglis = os.listdir(rp + "/annotations")
print(tpnglis)
pnglis = []
for i in tpnglis:
    if "png" in i:
        pnglis.append(i)
while len(pnglis):
    png = pnglis.pop(random.randint(0, len(pnglis) - 1))
    print(png)
    p1, p2 = os.path.splitext(png)
    if len(os.listdir(rp + "/annotations/train/")) < 110:  # 110为测试集大小
        shutil.copy(rp + "/annotations/" + png, rp + "/annotations/train/" + png)
        shutil.copy(rp + "/" + png.replace('png', 'png'), rp + '/images/train/' + png.replace('png', 'png'))
    else:
        shutil.copy(rp + "/annotations/" + png, rp + "/annotations/val/" + png)
        shutil.copy(rp + "/" + png.replace('png', 'png'), rp + '/images/val/' + png.replace('png', 'png'))
