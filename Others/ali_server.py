import sys
import time, os, json
from Navigation_system import Navigationsys  # 需要把树莓派客户端的Navigation_system.py文件移到该目录，用于根据gps获取地面
import numpy as np
import cv2
import socket

if not os.path.exists("limit_img"):
    os.mkdir('limit_img')
if not os.path.exists("illegal_img"):
    os.mkdir('illegal_img')
if not os.path.exists("AllPaths.json"):
    with open("AllPaths.json", "w", encoding="utf-8")as af:
        ddddict = {
            "limit_img": {},
            "illegal_img": {}
        }
        json.dump(ddddict, af, indent=4, ensure_ascii=False)


class PicReceiver(object):
    def __init__(self, host="172.18.240.154", port=2222):
        print("host:{} port:{};waiting for connection...".format(host, port))
        self.host = host
        self.port = port
        self.navisys = Navigationsys()

        # self.streaming()

    def streaming(self):
        while True:
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.bind((self.host, self.port))
                self.server_socket.listen(100)
                print('server waiting for new connection')
                self.server_socket.settimeout(5)
                try:
                    self.client_socket, self.client_address = self.server_socket.accept()
                except:
                    # print(sys.exc_info())
                    time.sleep(0.2)
                    continue
                self.host_name = socket.gethostname()
                self.host_ip = socket.gethostbyname(self.host_name)
                # print("Host: ", self.host_name + ' ' + self.host_ip)
                print("Connection from: ", self.client_address)
                print("receiveing...")

                stream_bytes = b' '
                while True:
                    try:
                        stream_bytes += self.client_socket.recv(99999)
                        first = stream_bytes.find(b'\xff\xd8')
                        last = stream_bytes.find(b'\xff\xd9')
                        print(len(stream_bytes))
                        print(stream_bytes)

                        if len(stream_bytes) == 0 or len(stream_bytes) == 1:
                            break
                        if first != -1 and last != -1:
                            jpg = stream_bytes[first:last + 2]
                            info_bytes = stream_bytes[:first]
                            info_str = info_bytes.decode()
                            info = json.loads(info_str)
                            info["pos"] = self.get_address(info['pos'])
                            stream_bytes = stream_bytes[last + 2:]
                            # image = np.frombuffer(jpg, dtype=np.uint8)
                            image = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                            for box in info["box"]:
                                cv2.rectangle(image, (int(box[0] - 2), int(box[1] - 2)),
                                              (int(box[2] + 2), int(box[3] + 2)),
                                              (0, 0, 255), thickness=2)
                            _, image = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
                            if info["type"] == "限外" or info["type"] == "限号":
                                p = "limit_img/" + info["carplate"]
                                if not os.path.exists(p):
                                    os.mkdir(p)
                                with open(p + "/{}_{}.json".format(info["carplate"], info["time"]), "w",
                                          encoding="utf-8")as f:
                                    json.dump(info, f, indent=4, ensure_ascii=False)
                                image.tofile(p + "/{}_{}.jpg".format(info["carplate"], info["time"]))

                                # 写入路径文件
                                with open("AllPaths.json", "r", encoding="utf-8")as allpathfiler:
                                    allpathjson = json.loads(allpathfiler.read())
                                if info["carplate"] not in allpathjson["limit_img"].keys():
                                    allpathjson["limit_img"][info["carplate"]] = [
                                        "{}_{}".format(info["carplate"], info["time"])]
                                else:
                                    allpathjson["limit_img"][info["carplate"]].insert(0,
                                                                                      "{}_{}".format(info["carplate"],
                                                                                                     info["time"]))
                                with open("AllPaths.json", "w", encoding="utf-8")as allpathfilew:
                                    json.dump(allpathjson, allpathfilew, indent=4, ensure_ascii=False)

                            elif info["type"] == "违规变道":
                                p = "illegal_img/" + info["carplate"]
                                if not os.path.exists(p):
                                    os.mkdir(p)
                                with open(p + "/{}_{}.json".format(info["carplate"], info["time"]), "w",
                                          encoding="utf-8")as f:
                                    json.dump(info, f, indent=4, ensure_ascii=False)
                                image.tofile(p + "/{}_{}.jpg".format(info["carplate"], info["time"]))

                                # 写入路径文件
                                with open("AllPaths.json", "r", encoding="utf-8")as allpathfiler:
                                    allpathjson = json.loads(allpathfiler.read())
                                if info["carplate"] not in allpathjson["illegal_img"].keys():
                                    allpathjson["illegal_img"][info["carplate"]] = [
                                        "{}_{}".format(info["carplate"], info["time"])]
                                else:
                                    allpathjson["illegal_img"][info["carplate"]].insert(0,
                                                                                        "{}_{}".format(info["carplate"],
                                                                                                       info["time"]))
                                with open("AllPaths.json", "w", encoding="utf-8")as allpathfilew:
                                    json.dump(allpathjson, allpathfilew, indent=4, ensure_ascii=False)
                            print('receive a pic', info["time"], info["carplate"], info["type"], "\n")
                    except:
                        print(sys.exc_info())
                        break
                self.client_socket.close()
            except:
                print(sys.exc_info())

    def get_address(self, posstr: str):

        p1, p2 = posstr.split(',')
        pos = (float(p1), float(p2))
        print("pos", pos)
        return self.navisys.get_address_from_location(pos)

    def close(self):
        self.client_socket.close()
        self.server_socket.close()


if __name__ == '__main__':
    h, p = "172.30.84.184", 2222
    st = PicReceiver("192.168.137.1")
    st.streaming()
