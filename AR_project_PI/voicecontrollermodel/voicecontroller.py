import os
import random
import signal
import sys
import time
sys.path.append("..")
sys.path.append("voicecontrollermodel")
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication

from voicecontrollermodel import snowboydecoder
from voicecontrollermodel.chatbot import Chatter
from voicecontrollermodel.voice_and_text import Text2voice, Voice2text

interrupted = False


class Listening_start_thread(QThread):
    startsignal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(Listening_start_thread, self).__init__()
        self.d = 'distance'
        self.t = 'dtime'
        self.parent = parent
        self.voice2texter = Voice2text()
        self.address = "address"

    def run(self):
        starttime = time.time()
        self.parent.voiceplayer.get_voice_and_paly_it(
            "已为您规划好路线,从当前位置到{},全程{},预计耗时{},是否开始导航".format(self.address, self.d, self.t))
        self.choicing = True
        while self.choicing:
            text = self.voice2texter.record2text(timeout=60)
            if "是" in text or "开始" in text:
                self.startsignal.emit("开始")
                break
            elif "否" in text or "结束" in text or "退出" in text or "返回" in text or (time.time() - starttime) > 59:
                self.startsignal.emit("结束")
                break
        self.choicing = False

    def stop(self):
        self.choicing = False
        self.quit()


class Choice_listening_Thread(QThread):
    choiceresultsignal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(Choice_listening_Thread, self).__init__()
        self.choicing = True
        self.voice2texter = Voice2text()
        self.text2vocie = Text2voice()
        self.addresslist = {}
        self.parent = parent
        self.address = "address"

    def run(self):
        starttime = time.time()
        self.parent.voiceplayer.get_voice_and_paly_it("已为您搜索到{}相关地点如下,请选择".format(self.address))
        self.choicing = True
        while self.choicing:
            text = self.voice2texter.record2text(timeout=60)
            if text in self.addresslist:
                self.choiceresultsignal.emit(text)
                break
            elif "选择" in text:
                taddress = text.split("选择")[-1]
                print(taddress)
                if taddress in self.addresslist:
                    self.choiceresultsignal.emit(taddress)
                    break
                elif "一" in taddress:
                    self.choiceresultsignal.emit(self.addresslist[0])
                    break
                elif "二" in taddress:
                    self.choiceresultsignal.emit(self.addresslist[1])
                    break
                elif "三" in taddress:
                    self.choiceresultsignal.emit(self.addresslist[2])
                    break
                elif "退出" in text:
                    self.choiceresultsignal.emit("退出")
                    break
                else:
                    bbreak = False
                    for taddress in self.addresslist:
                        if taddress in text:
                            self.choiceresultsignal.emit(taddress)
                            bbreak = True
                            break
                    if bbreak:
                        break
                    self.text2vocie.get_voice_and_paly_it("选择有误, 请重新选择目的地")
            else:
                if "下一页" in text:
                    self.choiceresultsignal.emit("下一页")
                    break
                if "返回" in text or "退出" in text:
                    self.choiceresultsignal.emit("退出")
                    break
                bbreak = False
                for taddress in self.addresslist:
                    if taddress in text:
                        self.choiceresultsignal.emit(taddress)
                        bbreak = True
                        break
                if (time.time() - starttime) > 60:
                    self.text2vocie.get_voice_and_paly_it("已超时")
                    self.choiceresultsignal.emit("超时")
                    break
                elif bbreak:
                    break

        self.choicing = False

    def stop(self):
        self.choicing = False
        self.quit()


class CommenThread(QThread):
    def __init__(self, func, *args):
        super().__init__()
        self.func = func
        self.args = args

    def run(self):
        alen = len(self.args)
        if alen == 0:
            self.func()
        elif alen == 1:
            self.func(self.args[0])
        elif alen == 2:
            self.func(self.args[0], self.args[1])


class Controller(QThread):
    targetsignal = pyqtSignal(str)

    def __init__(self,updatachatrecordfuchandle=None,recording2textsignalfuchandle=None):
        super(Controller, self).__init__()
        if __name__ == '__main__':
            self.models = ["蜂鸟.pmdl"]
        else:
            self.models = ["voicecontrollermodel/蜂鸟.pmdl"]
        self.commands = ["打开投影", "关闭投影", "导航", "切换", "聊天", "语音系统", ]
        self.sensitivity = [0.52]
        self.callbacks = [self.call_fengniao]
        self.detector = snowboydecoder.HotwordDetector(self.models, sensitivity=self.sensitivity)
        self.signal = signal.signal(signal.SIGINT, self.signal_handler)
        self.interrupted = False
        self.joy = True
        self.listenning = False
        self.chatter = Chatter()


        self.text2voice_player = Text2voice()
        self.voice2texter = Voice2text()

        self.updatachatrecordfuchandle=updatachatrecordfuchandle
        self.recording2textsignalfuchandle=recording2textsignalfuchandle
        if None not in (recording2textsignalfuchandle,updatachatrecordfuchandle) :
            self.voice2texter.recording2textsignal.connect(recording2textsignalfuchandle)
            self.voice2texter.voice2text_signal.connect(updatachatrecordfuchandle)
            self.chatter.chatter_response_singal.connect(updatachatrecordfuchandle)
        self.voicetypes = {"亲和女声": 0, "亲和男声": 1, "成熟男声": 2, "温暖女声": 4, "情感女声": 5, "情感男声": 6, "客服女声": 7,
                           "智侠|情感男声": 1000, "智瑜|情感女声": 1001, "智聆|通用女声": 1002, "智美|客服女声": 1003, "WeJack|英文男声": 1050,
                           "WeRose|英文女声": 1051,
                           "智侠|情感男声(精)": 101000, "智瑜|情感女声(精)": 101001, "智聆|通用女声(精)": 101002, "智美|客服女声(精)": 101003,
                           "智云|通用男声": 101004, "智莉|通用女声": 101005, "智言|助手女声": 101006, "智娜|客服女声": 101007,
                           "智琪|客服女声": 101008,
                           "智芸|知性女声": 101009, "智华|通用男声": 101010, "WeJack|英文男声(精)": 101050, "WeRose|英文女声(精)": 101051,
                           "贝蕾|客服女声": 102000, "贝果|客服女声": 102001, "贝紫|粤语女声": 102002, "贝雪|新闻女声": 102003}
        self.voiceid = 101001

    def interrupt_callback(self):
        """检查是否退出"""
        # print("callback")
        return self.interrupted

    def signal_handler(self, signal, frame):
        self.interrupted = True

    def run(self):
        sleep_time = 0.03
        # try:
        print('语音控制系统已启动!')
        self.detector.start(detected_callback=self.callbacks,
                            interrupt_check=self.interrupt_callback,
                            sleep_time=sleep_time)
        print("语音控制系统已关闭!")
        # # except:
        #     print(sys.exc_info())
        #     self.text2voice_player.play("finderror.wav")
        #     print("出现错误，请稍后再试")
        #     self.start_listening()

    def command_close_AR(self):
        self.play_heard()
        print("hear 关闭投影")

    def command_open_AR(self):
        self.play_heard()
        print("hear 打开投影")

    def call_fengniao(self):
        if self.chatter.chating:
            print("正在聊天模式中")
            return
        self.play_heard("ihere_file/ihere{}.wav".format(self.voiceid))
        # return
        print('hear 蜂鸟')
        self.listening()

    def listening(self):
        if self.listenning:
            return
        else:
            self.listenning = True
        text = self.voice2texter.record2text(timeout=5)
        print(text)
        com = False
        for command in self.commands:
            if command in text:
                com = True
                print("识别到", command)
                # self.getvoicethread = CommenThread(self.text2voice_player.get_voice_and_paly_it, "识别到指令" + command)
                # self.getvoicethread.start()
                # self.text2voice_player.get_voice_and_paly_it("识别到指令" + command)
                break
        if com:
            if command == "切换":
                if "播报人" in text or "播音员" in text or "音色" in text or "声音" in text or "播报员" in text:
                    self.voiceid = list(self.voicetypes.values())[random.randint(0, len(self.voicetypes.values()) - 1)]
                    self.text2voice_player.get_voice_and_paly_it(
                        "已切换播报人id为" + str(self.voiceid),
                        self.voiceid)
                else:
                    self.text2voice_player.get_voice_and_paly_it("暂时没有这个指令", self.voiceid)
            elif command == "导航":
                if "导航到" in text and len(text.split('导航到')[1])>1:
                    target = text.split('导航到')[1]
                    print(target)
                    commandans = '正在为您搜索目的地 ' + target
                elif "退出" in text or "关闭" in text or "结束" in text:
                    commandans = "退出"
                else:
                    commandans = '暂时没有这个指令！'
                self.targetsignal.emit(commandans)
                # self.getvoicethread = CommenThread(self.text2voice_player.get_voice_and_paly_it, commandans, self.voiceid)
                # self.getvoicethread.start()

            elif command == "聊天":
                if "退出" in text or "关闭" in text:
                    if "模式" in text:
                        commandans = '退出聊天模式'
                        self.chatter.close_chat()
                    else:
                        commandans = "关闭聊天功能"
                        self.joy = False
                elif '进入' in text or '打开' in text or '开启' in text:
                    if "模式" in text:
                        self.chatter.open_chat(self.voiceid,self.updatachatrecordfuchandle)
                        self.text2voice_player.play(
                            "inandoutchating_file/in{}.wav".format(self.voiceid))
                        self.listenning=False
                        return
                    else:
                        commandans = "打开聊天功能"
                        self.joy = True

                else:
                    commandans = '暂时没有这个指令'
                # self.getvoicethread = CommenThread(self.text2voice_player.get_voice_and_paly_it, commandans, self.voiceid)
                # self.getvoicethread.start()
                self.text2voice_player.get_voice_and_paly_it(commandans, self.voiceid)
            elif command == "语音系统":
                if "退出" in text or "关闭" in text:
                    commandans = '退出语音系统'
                    self.close()
                else:
                    commandans = "暂时没有这个指令"
                self.text2voice_player.get_voice_and_paly_it(commandans, self.voiceid)
        else:
            print("非指令")
            # self.getvoicethread = CommenThread(self.__get_nocommendans, text)
            # self.getvoicethread.start()
            if text=="听不到任何声音":
                print("听不到任何声音")

            elif self.joy:
                self.__get_nocommendans(text)
        self.listenning=False

    def __get_nocommendans(self, text, sz=True):  # shizhi or txun
        if text == "听不到任何声音":
            result = '听不到任何声音'
        else:
            if sz:
                result = self.chatter.get_sizhibot_response(text)
            else:
                result = self.chatter.get_chatter_response(text)
        if len(result) != 0:
            self.text2voice_player.get_voice_and_paly_it(result, self.voiceid)
        else:
            result = '没有识别到任何声音'
            self.text2voice_player.get_voice_and_paly_it(result, self.voiceid)
            return
        print(result)

    def play_heard(self, file="voicecontrollermodel/heard.wav"):
        snowboydecoder.play_audio_file(file)

    def close(self):
        self.detector.terminate()
        print("已退出")


if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    vcontroler = Controller()
    vcontroler.start()
    sys.exit(app.exec_())
