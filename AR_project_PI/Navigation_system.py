import time, sys

import requests
from PyQt5.QtCore import QThread, pyqtSignal
from MPU6065reader import MPU6050Reader
from PyQt5.QtWidgets import QApplication
from GPStransformer import wgs84togcj02


class GetPositionThread(QThread):  # GPS获取线程,需要树莓派gps模块
    gps_signal = pyqtSignal(float, float)

    def __init__(self, gps_signal_func):
        super(GetPositionThread, self).__init__()
        self.gps_signal.connect(gps_signal_func)  # 连接信号和槽函数

    def run(self) -> None:
        import serial
        import pynmea2
        a = serial.Serial("/dev/ttyUSB0", 9600)
        while True:
            try:
                line = a.readline()
                line = str(line, encoding='utf-8')
                if line[:6] == '$GPRMC':
                    rmc = pynmea2.parse(line)
                    dd1 = int(float(rmc.lat) / 100)
                    dd2 = int(float(rmc.lon) / 100)
                    b1, b2 = wgs84togcj02((float(rmc.lon) - dd2 * 100) / 60 + dd2,
                                          (float(rmc.lat) - dd1 * 100) / 60 + dd1)
                    b1 = round(b1, 6)
                    b2 = round(b2, 6)
                    self.gps_signal.emit(b1, b2)  # 发送信号
                    time.sleep(0.01)  # 避免过快(占用大)
            except:
                print(sys.exc_info())
                print("gps lack of signal")


class Navigationsys():  # 导航系统
    def __init__(self, parent=None, mpuph=0):
        self.web_key = "1915f73dc3c9fe7a41b44c8fe37aee77"
        self.webjs_key = "e8ba4956dd4f477c2e9206eeebf1da8d"
        self.pos = (113.937617, 22.52734)  # 当前位置(宿舍113.930201 22.526368)
        self.endpos = (113.930591, 22.526802)
        self.angle = 0  # 当前角度

        self.parent = parent
        self.address = ""
        self.searchresultpage = 1
        # self.get_gps_thread = GetPositionThread(self.change_pos)  # 获取gps信息线程,有该模块可开启
        # self.get_gps_thread.start()  # 启动线程不断更新当前位置,有该模块可开启
        # self.mputhread = MPU6050Reader(mpuph)  # 陀螺仪传感器,mpuph修正值,mpu6065陀螺仪线程,不用可关闭,注意要在mpu6065reader里面更改对应的bus号
        print("导航系统已启动!")

    def change_pos(self, p1, p2):
        print("更新当前位置为:", p1, p2)
        self.pos = (p1, p2)
        if self.parent.navigating:
            self.parent.ui_window.browser_viewer.set_center_pos((p1, p2), zoom=18)
        else:
            self.parent.ui_window.browser_viewer.set_center_pos((p1, p2), zoom=16)

    def change_angle(self, ag):
        print("当前角度", self.angle)
        self.angle = int(ag)

    def search(self, pos, page=1):  # 目的地搜索
        """目的地搜索,返回5个可能结果包含坐标"""
        url = "https://restapi.amap.com/v3/place/text?parameters"
        params = {"key": self.web_key,
                  "keywords": str(pos),
                  "offset": 3,
                  "page": page,
                  }

        response = requests.get(url, params=params)
        js = response.json()
        names = {}
        for id in js["pois"]:
            names[id["name"]] = id['location']
        print(names)
        return names  # 返回5个可能结果包含坐标

    def path_planning(self, origin, destination):  # 路径规划
        """路径规划
        输入：两个坐标或目的地；
        返回：规划信息(总长,用时等)、每一步的动作和位置坐标"""
        if type(origin) == str:  # 传入文字时获得坐标
            originstr, _ = self.get_location_from_address(origin)
            print("pos1", origin)
        else:
            originstr = str(origin[0]) + ',' + str(origin[1])
        if type(destination) == str:
            destinationstr, _ = self.get_location_from_address(destination)
            print("pos2", destination)
        else:
            destinationstr = str(destination[0]) + ',' + str(destination[1])

        def getactionpos(polyline: str):
            p1, p2 = polyline.split(";")[-1].split(",")
            return float(p1), float(p2)

        returninfo = {}
        returnsteps = []
        parameters = {
            'key': self.web_key,
            'origin': originstr,
            'destination': destinationstr,
            'output': 'json'
        }
        r = requests.get("https://restapi.amap.com/v3/direction/driving?parameters", params=parameters)
        # print(r.json())
        path0 = r.json()['route']['paths'][0]
        returninfo["totaldistance"] = path0["distance"]
        returninfo["time"] = int(path0["duration"])
        steps = path0['steps']
        for step in steps:
            stepinfo = {'distance': step["distance"], "nextaction": step["action"],
                        "actionpos": getactionpos(step["polyline"])}

            returnsteps.append(stepinfo)
            print(stepinfo)
        # print(returninfo)
        return returninfo, returnsteps

    def get_location_from_address(self, address, city=None, format: type = str):
        """"从文字地址中获取坐标和规范名"""
        parameters = {'key': self.web_key,
                      'city': city,
                      'citylimit': True,
                      'address': address
                      }
        r = requests.get("https://restapi.amap.com/v3/geocode/geo?parameters", params=parameters)
        # print(r.json())
        location = r.json()['geocodes'][0]['location']
        formatted_name = r.json()['geocodes'][0]['formatted_address']
        if format == float:  # 返回字符串还是坐标值
            location = (float(location.split(",")[0]), float(location.split(",")[1]))
        return location, formatted_name

    def start_turn(self):  # 开始转弯
        self.angle = 0
        self.mputhread.start()

    def end_turn(self):
        self.mputhread.stop()
        self.angle = 0

    def get_address_from_location(self, pos: tuple):
        """"从GPS坐标中获取文字地址"""
        parameters = {'key': self.web_key,
                      'location': str(pos[0]) + ',' + str(pos[1])
                      }
        r = requests.get("https://restapi.amap.com/v3/geocode/regeo?parameters", params=parameters)
        address = r.json()['regeocode']['formatted_address']
        print(address)
        return address


if __name__ == '__main__':
    app = QApplication(sys.argv)
    n = Navigationsys()
    # loaction, formatted_name = n.get_location_from_address("深圳大学")
    # print(loaction, formatted_name)
    # n.search("深圳大学")
    # n.path_planning((113.930591, 22.526802), (113.972654, 22.59163))
    # n.strat_turn()
    # print(n.get_distance("深圳大学西门", "深圳大学西南学生公寓"))

    sys.exit(app.exec_())
