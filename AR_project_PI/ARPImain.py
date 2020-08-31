import random
import sys
import time
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication
from ARui import ArMainwindow
from voicecontrollermodel.voicecontroller import Controller as VoiceController
from Navigation_system import Navigationsys
from voicecontrollermodel.voice_and_text import Text2voice
from voicecontrollermodel.voicecontroller import Choice_listening_Thread, Listening_start_thread
from pi_clientcv import Clientcvcap
from get_AndroidGps_server import AndroidGpsThread


class ArPiMain:  # 2F1D1D#FFFFFF
    def __init__(self, IP="192.168.137.1", port=8787, fps=15, dpi=(1280, 720)):
        self.ui_window = ArMainwindow()
        self.voicecontersys = VoiceController(self.ui_window.update_chatrecord, self.recording2textsignal_fuc)
        self.navigationsys = Navigationsys(self, mpuph=0.0720)
        self.voiceplayer = Text2voice()
        self.camera = Clientcvcap(IP, port, fps, dpi, self.navigationsys)
        self.navigating = False
        self.clicklistening = False
        self.voicecontersys.start()
        self.camera.start()

        self.choicedict = {}
        self.pathinfo = []

        self.ui_window.showPosMap(self.navigationsys.pos, zoom=16)
        self.get_Android_inputThread = AndroidGpsThread()
        self.get_Android_inputThread.get_gps_from_mobile_signal.connect(self.get_Android_input_func)
        self.get_Android_inputThread.start()

        self.camera.receive_info_signal.connect(self.receive_info_signal_func)
        self.voicecontersys.targetsignal.connect(self.targetsearch)
        self.ui_window.speechbot.clicked.connect(self.clicksignal_listening)
        self.ui_window.turnbot.clicked.connect(self.turn_test)

        self.choice_listen_thread = Choice_listening_Thread(parent=self)
        # self.choice_listen_thread.voice2texter.recording2textsignal.connect(self.recording2textsignal_fuc)
        self.choice_listen_thread.choiceresultsignal.connect(self.get_choice_result)
        self.listenstartthread = Listening_start_thread(self)
        # self.listenstartthread.voice2texter.recording2textsignal.connect(self.recording2textsignal_fuc)
        self.listenstartthread.startsignal.connect(self.startornot)
        # self.navigationsys.mputhread.yaw_angle_signal.connect(self.turn_around_func)  # 连接角度改变信号

    def turn_test(self):
        self.voiceplayer.get_voice_and_paly_it("前方路口左转")
        self.start_turn()
        self.ui_window.arrow_mask_viewer.show_arrow(self.ui_window.arrow_mask_viewer.leftarrow, anglez=0)

    def recording2textsignal_fuc(self, text: str):  # 处理录音状态改变时的ui界面
        if text == "recording":
            self.ui_window.listening()
            # self.voiceplayer.play("voicecontrollermodel/resources/ding0.wav")
            QApplication.processEvents()
        elif "endrecording" == text:
            self.ui_window.stop_listening()

        elif text == "endrecordinggettingtext":
            self.ui_window.stop_listening("正在处理...")
            self.voiceplayer.play("voicecontrollermodel/resources/dong.wav")
        elif "gettext" in text:
            self.ui_window.speechtext_editer.setText(text.replace("gettext", ""))

    def get_Android_input_func(self, pos, address):
        print("get a pos", pos)
        self.navigationsys.endpos = pos
        self.path_plan(address)

    def receive_info_signal_func(self, recbytes: bytes):
        if len(recbytes) == 1:
            result = recbytes.decode()
            if result == "r":
                self.ui_window.mask_viewer.show_red_mask()
            elif result == "g":
                self.ui_window.mask_viewer.show_green_mask()
            elif result == "c":
                self.ui_window.icon_viewer.show_construction_img()
            elif result == "h":
                self.ui_window.icon_viewer.show_height_limit_img()

    def clicksignal_listening(self):
        if self.clicklistening:
            self.ui_window.stop_listening()
            return
        else:
            self.clicklistening = True
            self.clicklisteningthread = CommendThread(self.voicecontersys.listening)
            self.clicklisteningthread.start()
            # self.voicecontersys.listening()
            self.clicklistening = False

    def targetsearch(self, commandans):
        print(commandans)
        self.ui_window.speechtext_editer.setText(commandans)
        if "目的地" in commandans:
            address = commandans.split("目的地")[-1]
            self.ui_window.search_address(address)
            self.navigationsys.searchresultpage = 1
            self.choicedict = self.navigationsys.search(address)
            self.choice_listening(address)
            # self.voiceplayer.get_voice_and_paly_it('请选择')
        else:
            if commandans == "退出":
                self.exit_navigation()
            else:
                self.voiceplayer.get_voice_and_paly_it(commandans)

    def choice_listening(self, address):
        address = address.replace(" ", "").replace("。", "")
        self.navigationsys.address = address
        self.choice_listen_thread.addresslist = tuple(self.choicedict.keys())
        self.choice_listen_thread.address = address
        self.choice_listen_thread.start()
        self.ui_window.listening()

    def get_choice_result(self, result):
        self.ui_window.stop_listening(result)
        print("选择结果", result)
        if result in self.choicedict.keys():
            self.navigationsys.endpos = (self.choicedict[result].split(",")[0], self.choicedict[result].split(",")[1])
            self.path_plan(result)
        elif result == "下一页":
            self.ui_window.browser_viewer.next_result_page()
            self.navigationsys.searchresultpage += 1
            self.choicedict = self.navigationsys.search(self.navigationsys.address, self.navigationsys.searchresultpage)
            self.choice_listening(self.navigationsys.address)
        else:
            self.exit_navigation(saygoodbye=False)
            self.voiceplayer.get_voice_and_paly_it("已退出")

    def path_plan(self, ad):
        self.ui_window.path_palning_view(self.navigationsys.pos, self.navigationsys.endpos)
        dt, self.pathinfo = self.navigationsys.path_planning(self.navigationsys.pos, self.navigationsys.endpos)
        distance = int(dt['totaldistance'])
        dtime = int(dt["time"])

        distancestr = "{:.2f}公里".format(distance / 1000) if distance > 1000 else str(distance) + "米"
        dtimestr = '{:.0f}分钟'.format(dtime / 60) if dtime > 60 else str(dtime) + "秒"

        self.listenstartthread.address = ad
        self.listenstartthread.d = distancestr
        self.listenstartthread.t = dtimestr
        self.listenstartthread.start()
        self.ui_window.listening()

    def startornot(self, signal):
        self.ui_window.stop_listening()
        if signal == "开始":
            print("开始")
            self.voiceplayer.get_voice_and_paly_it("开始导航,蜂鸟提醒您谨慎驾驶,行车不规范,亲人两航泪。 已进入导航模式")
            self.start_navigating()
        else:
            self.exit_navigation()

    def start_navigating(self):
        self.ui_window.resizeall()
        self.ui_window.browser_viewer.navigating_show(self.navigationsys.pos, self.navigationsys.endpos)

    def exit_navigation(self, saygoodbye=True):
        if saygoodbye:
            self.voiceplayer.get_voice_and_paly_it("已退出导航模式,欢迎再次使用蜂鸟")
        self.ui_window.resizeall()
        self.ui_window.showPosMap(self.navigationsys.pos)
        self.ui_window.stop_listening()

    def turn_around_func(self, ag):  # 角度改变信号
        if int(ag) == self.navigationsys.angle:
            return
        self.navigationsys.change_angle(ag)

        if abs(ag) > 85:
            print("turn done!")
            try:
                self.end_turn()
            except:
                print(sys.exc_info())
            return
        anglez = -ag * 0.7
        fov = 42 + ag * 1.1
        self.ui_window.arrow_mask_viewer.show_arrow(self.ui_window.arrow_mask_viewer.leftarrow, anglez=anglez, fov=fov)

    def start_turn(self):
        self.navigationsys.start_turn()

    def end_turn(self):
        try:
            self.navigationsys.end_turn()
        except:
            print(1)
        self.ui_window.arrow_mask_viewer.show_nothing()


class TestThread(QThread):
    def __init__(self, parent: ArPiMain):
        super(TestThread, self).__init__()
        self.parent = parent

    def run(self):
        # time.sleep(8)
        print("start turn")
        while True:
            for i in range(-90, 90, 2):
                self.parent.turn_around_func(i)
                time.sleep(0.2)


class CommendThread(QThread):
    def __init__(self, action, *arges):
        super(CommendThread, self).__init__()
        self.action = action
        self.arges = arges

    def run(self):
        if len(self.arges) == 0:
            self.action()
        elif len(self.arges) == 1:
            self.action(self.arges[0])
        elif len(self.arges) == 2:
            self.action(self.arges[0], self.arges[1])
        self.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pi = ArPiMain("192.168.134.1")  # 该文件为客户端主函数,默认启动几乎所有功能,需要你的硬件支持!没有的话应当注释掉相关代码
    # 注意先编译好snowboy语音唤醒把相应文件移动到voicecontrollermodel目录下才可运行,或者把语音系统部分代码注释掉..详情请看目录文件
    # tst = TestThread(pi)
    # tst.start()
    sys.exit(app.exec_())
