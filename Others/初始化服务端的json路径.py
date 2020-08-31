import json
import os
import shutil

# 服务端初始化路径
if os.path.exists("limit_img"):  # 限号车抓拍文件夹
    shutil.rmtree("limit_img")
    print("已清空limit_img")

os.mkdir("limit_img")
if os.path.exists("illegal_img"):  # 违规车抓拍文件夹
    shutil.rmtree("illegal_img")

    print("已清空illegal_img")
os.mkdir("illegal_img")
with open("AllPaths.json", "w", encoding="utf-8")as f:  # 写入目录
    jsonstr = {
        "limit_img": {},
        "illegal_img": {}
    }
    json.dump(jsonstr, f, indent=4, ensure_ascii=False)
    print("已重写AllPaths.json")
