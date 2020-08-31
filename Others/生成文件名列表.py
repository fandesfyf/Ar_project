import os, random

rp = r"D:\python_work\Ar_project\PaddleSeg\dataset\d222\images\val"
while "\\" in rp:
    rp = rp.replace('\\', '/')
lis = os.listdir(rp)
print(lis)
with open('list.txt', 'w')as file:
    for i in lis:
        p1, p2 = os.path.splitext(i)
        if p2 == ".png":
            print(i)
            file.write(rp + '/' + i + '\n')
