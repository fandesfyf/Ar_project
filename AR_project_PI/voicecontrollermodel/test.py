import snowboydecoder
import sys
import signal
from chatbot import Chatter
from voice_and_text import Text2voice, Voice2text

interrupted = False


class Controller:
    def __init__(self):
        self.models = ["蜂鸟.pmdl", "关闭投影.pmdl", "打开投影.pmdl"]
        self.commands = ["打开投影", "关闭投影", "开始导航", "导航到", "切换性别", "聊天"]
        self.sensitivity = [0.45, 0.6, 0.6]
        self.callbacks = [self.call_fengniao, self.command_close_AR, self.command_open_AR]
        self.detector = snowboydecoder.HotwordDetector(self.models, sensitivity=self.sensitivity)
        self.signal = signal.signal(signal.SIGINT, self.signal_handler)
        self.interrupted = False
        self.chatter = Chatter()
        self.text2voice_player = Text2voice()
        self.voice2texter = Voice2text()

    def interrupt_callback(self):
        "检查是否退出"
        # print("callback")
        return self.interrupted

    def signal_handler(self, signal, frame):
        print(11)
        self.interrupted = True

    def start_listening(self, sleep_time=0.03):
        self.detector.start(detected_callback=self.callbacks,
                            interrupt_check=self.interrupt_callback,
                            sleep_time=sleep_time)

    def command_close_AR(self):
        self.play_heard()
        print("hear 关闭投影")

    def command_open_AR(self):
        self.play_heard()
        print("hear 打开投影")

    def call_fengniao(self):
        self.play_heard()
        print('hear 蜂鸟')

    def play_heard(self):
        snowboydecoder.play_audio_file("heard.wav")

    def close(self):
        self.detector.terminate()


if __name__ == '__main__':
    controler = Controller()
    controler.start_listening()
