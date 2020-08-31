import json
import os

rp = r"C:\Users\Fandes\Desktop\p333"  # 用于解决labelme标注后图片文件名更改时json文件里的文件名不对应的问题，
lis = os.listdir(rp)
# print(lis)
for i in lis:
    p1, p2 = os.path.splitext(i)
    # print(i)
    if p2 == ".json":
        with open(rp + '/' + i, "r")as f:
            js = json.load(f)
        name = js['imagePath']
        n1, n2 = os.path.splitext(name)
        print(p1, p2)
        os.rename(rp + '/{}.json'.format(p1), rp + '/{}.json'.format(n1))
        os.rename(rp + '/{}.png'.format(p1), rp + '/{}.png'.format(n1))
