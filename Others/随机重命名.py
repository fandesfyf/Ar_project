import json
import os, sys, random

randstr = "qwert61ybnm72uio45dfgpas89hjklzxcv3"


def get_randstr(n=10):
    s = ''
    for i in range(n):
        s += randstr[random.randint(0, len(randstr) - 1)]
    return s


pt = r"C:\Users\Fandes\Desktop\路标"#更改这个路径，注意重命名为直接覆盖！不可逆，注意备份数据！
imgs = os.listdir(pt)
# 只重命名图片
for img in imgs:
    old = pt + '/' + img
    p1, p2 = os.path.splitext(img)
    new = pt + '/' + get_randstr() + p2
    if new not in os.listdir(pt):
        os.rename(old, new)
        print(new)
    else:
        new = pt + '/' + get_randstr() + p2
        os.rename(old, new)
        print("有重复名称")
#

# ##重命名图片和json文件
# for js in imgs:
#     p1, p2 = os.path.splitext(js)
#     if p2 == '.json':
#         randname = get_randstr()
#         newjson = pt+'/' + randname + p2
#         newimg = pt+'/' + randname + '.jpg'
#         if newimg not in os.listdir(pt):
#             js2=json.load(open(pt+'/'+js,'r'))
#             js2["imagePath"]=randname + '.jpg'
#             with open(pt + '/' + js, "w")as f:
#                 json.dump(js2, f)
#             print(randname + '.jpg')
#             os.rename(pt+'/'+js,newjson)
#             os.rename(pt+'/'+p1+'.jpg',newimg)
# ##
