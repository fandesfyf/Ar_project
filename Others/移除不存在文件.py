import os, random

rp = r"C:\Users\Fandes\Desktop\目标检测数据"#移除不存在的图片文件的json文件，或移除没有对应json文件的图片文件
lis = os.listdir(rp)
print(lis)
for i in lis:
    p1, p2 = os.path.splitext(i)

    if p2 == ".jpg":
        if p1 + '.json' not in lis:
            print('not in ' + p1 + '.png')
            os.remove(rp + '/' + i)

    # if i.split()
