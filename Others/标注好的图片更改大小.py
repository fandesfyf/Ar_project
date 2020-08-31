import base64
import json
import os
from PIL import Image

"""用于更改已经标注好的labelme文件，需要更改图片大小的，
先把图片文件分辨率更改，然后运行该脚本即可改变标注文件（json）的分辨率，免去重新标注麻烦"""


def get_jsshape(shapes, scale):
    newshape = []
    for shape in shapes:
        points = []
        for x, y in shape["points"]:
            points.append([x * scale, y * scale])
        shape["points"] = points
        newshape.append(shape)
    return newshape


rp = r"F:\目标检测数据\d222\d333"  # 已经更改好分辨率的图片和json文件在同一个文件夹
lis = os.listdir(rp)
for i in lis:
    p1, p2 = os.path.splitext(i)
    # print(i)
    if p2 == ".json":
        # 打开图片获取尺寸
        png = Image.open(rp + '/' + p1 + '.jpg')
        w, h = png.size
        # 打开json更改
        with open(rp + '/' + i, "r")as f:
            js = json.load(f)
            shapes = js["shapes"]
            imgheight = js['imageHeight']
            scale = h / imgheight
            with open(rp + '/' + p1 + '.jpg', 'rb') as f:
                image_data = f.read()
                base64_data = base64.b64encode(image_data)  # base64编码
            js['imageData'] = base64_data.decode()
            js["shapes"] = get_jsshape(shapes, scale)
            js['imageHeight'] = h
            js['imageWidth'] = w
            print(js["shapes"])

            # with open('testpp.png', 'wb') as file:
            #     jiema = base64.b64decode(data)  # 解码
            #     file.write(jiema)
        with open(rp + '/' + i, "w")as f:
            json.dump(js, f,indent=4)
        # break
