import hashlib
import threading
import urllib
import time
import requests
import random
import json
from voicecontrollermodel.voice_and_text import Voice2text, Text2voice
from PyQt5.QtCore import QThread, pyqtSignal, QObject


class Chat_Tread(QThread):  # 聊天线程
    chatting_signal = pyqtSignal(str, bool)

    def __init__(self, parent, voiceid=101001, sz=True):
        super(Chat_Tread, self).__init__()
        self.text2voice_player = Text2voice()
        self.voice2texter = Voice2text()
        self.parent = parent
        self.sz = sz
        self.voiceid = voiceid

    def run(self):
        voices = {"亲和女声": 0, "亲和男声": 1, "成熟男声": 2, "温暖女声": 4, "情感女声": 5, "情感男声": 6, "客服女声": 7,
                  "智侠|情感男声": 1000, "智瑜|情感女声": 1001, "智聆|通用女声": 1002, "智美|客服女声": 1003, "WeJack|英文男声": 1050,
                  "WeRose|英文女声": 1051,
                  "智侠|情感男声(精)": 101000, "智瑜|情感女声(精)": 101001, "智聆|通用女声(精)": 101002, "智美|客服女声(精)": 101003,
                  "智云|通用男声": 101004, "智莉|通用女声": 101005, "智言|助手女声": 101006, "智娜|客服女声": 101007, "智琪|客服女声": 101008,
                  "智芸|知性女声": 101009, "智华|通用男声": 101010, "WeJack|英文男声(精)": 101050, "WeRose|英文女声(精)": 101051,
                  "贝蕾|客服女声": 102000, "贝果|客服女声": 102001, "贝紫|粤语女声": 102002, "贝雪|新闻女声": 102003}
        while True:
            question = self.voice2texter.record2text(Bd=False)
            if '嗯' in question:
                print("嗯恩不识别")
                continue
            if question == "听不到任何声音":
                continue
            self.chatting_signal.emit(question, True)
            if "聊天" in question:
                if "退出" in question or "关闭" in question:
                    self.parent.chating = False
                    break
            elif "切换" in question:
                if "声音" in question:
                    self.voiceid = list(voices.values())[random.randint(0, len(voices) - 1)]
                    self.text2voice_player.get_voice_and_paly_it("已切换播报人id为{}".format(self.voiceid))
                    continue
            if self.sz:
                ans = self.parent.get_sizhibot_response(question)
            else:
                ans = self.parent.get_chatter_response(question)
            # self.chatting_signal.emit(ans, False)
            self.text2voice_player.get_voice_and_paly_it(ans, self.voiceid)
            if not self.parent.chating:
                break
        self.text2voice_player.play("voicecontrollermodel/inandoutchating_file/out{}.wav".format(self.voiceid))
        self.parent.chating = False


class CommenThread(threading.Thread):
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


class Chatter(QObject):
    chatter_response_singal = pyqtSignal(str, bool)

    def __init__(self):
        super(Chatter, self).__init__()
        self.url = r"https://api.ai.qq.com/fcgi-bin/nlp/nlp_textchat"
        self.chating = False

    def get_sizhibot_response(self, question):
        if len(question) == 0:
            question = "空文本"
        info = question.encode('utf-8')
        url = 'https://api.ownthink.com/bot'
        data = {u"appid": "db1b2a88a62c7650d74bee4d863f1853", "spoken": info, "userid": "test"}
        try:
            response = requests.post(url, data).content
        except:
            print('聊天出错')
            s = "聊天出错！请确保网络畅通！"
        else:
            res = json.loads(response)
            s = res['data']['info']['text']
        print("回答:", s)
        self.chatter_response_singal.emit(s, False)
        return s

    def __get_sign_code(self, params, app_key="TTkZvr74cJHQWQxR"):
        """ 生成签名CODE

        1. 计算步骤
        用于计算签名的参数在不同接口之间会有差异，但算法过程固定如下4个步骤。
        将<key, value>请求参数对按key进行字典升序排序，得到有序的参数对列表N
        将列表N中的参数对按URL键值对的格式拼接成字符串，得到字符串T（如：key1=value1&key2=value2），URL键值拼接过程value部分需要URL编码，URL编码算法用大写字母，例如%E8，而不是小写%e8
        将应用密钥以app_key为键名，组成URL键值拼接到字符串T末尾，得到字符串S（如：key1=value1&key2=value2&app_key=密钥)
        对字符串S进行MD5运算，将得到的MD5值所有字符转换成大写，得到接口请求签名
        2. 注意事项
        不同接口要求的参数对不一样，计算签名使用的参数对也不一样
        参数名区分大小写，参数值为空不参与签名
        URL键值拼接过程value部分需要URL编码
        签名有效期5分钟，需要请求接口时刻实时计算签名信息
        :param params: 参数字典
        :param app_key:
        :return:
        """
        if params is None or type(params) != dict or len(params) == 0: return
        try:
            params = sorted(params.items(), key=lambda x: x[0])
            _str = ''
            for item in params:
                key = item[0]
                value = item[1]
                if value == '': continue
                _str += urllib.parse.urlencode({key: value}) + '&'
            _str += 'app_key=' + app_key
            _str = hashlib.md5(_str.encode('utf-8')).hexdigest()
            return _str.upper()
        except Exception as e:
            print(e)

    def __get_random_str(self, n=17):
        s = "qwertyuiop7894561230asdfghjklzxcvbnm"
        rs = ''
        for i in range(n):
            rs += s[random.randint(0, 15)]
        return rs

    def get_chatter_response(self, question):
        params = {"app_id": 2154786206,
                  "time_stamp": int(time.time()),
                  "nonce_str": self.__get_random_str(),
                  "session": 10000,
                  "question": question,
                  }
        params["sign"] = self.__get_sign_code(params)
        response = requests.get(self.url, params=params)
        js = response.json()
        if js['msg'] == 'chat answer not found':
            answer = '蜂鸟不能理解你的意思'
        else:
            print(js, "get_chatter_response")
            answer = js["data"]["answer"]
        print("回答：", answer)
        return answer

    def open_chat(self, voiceid=101001, func=None):
        self.chating = True
        self.chatthread = Chat_Tread(self, voiceid)
        if func is not None:
            self.chatthread.chatting_signal.connect(func)
        self.chatthread.start()

    # def __auto_chat(self, voiceid, sz=True):
    #     voices = {"亲和女声": 0, "亲和男声": 1, "成熟男声": 2, "温暖女声": 4, "情感女声": 5, "情感男声": 6, "客服女声": 7,
    #               "智侠|情感男声": 1000, "智瑜|情感女声": 1001, "智聆|通用女声": 1002, "智美|客服女声": 1003, "WeJack|英文男声": 1050,
    #               "WeRose|英文女声": 1051,
    #               "智侠|情感男声(精)": 101000, "智瑜|情感女声(精)": 101001, "智聆|通用女声(精)": 101002, "智美|客服女声(精)": 101003,
    #               "智云|通用男声": 101004, "智莉|通用女声": 101005, "智言|助手女声": 101006, "智娜|客服女声": 101007, "智琪|客服女声": 101008,
    #               "智芸|知性女声": 101009, "智华|通用男声": 101010, "WeJack|英文男声(精)": 101050, "WeRose|英文女声(精)": 101051,
    #               "贝蕾|客服女声": 102000, "贝果|客服女声": 102001, "贝紫|粤语女声": 102002, "贝雪|新闻女声": 102003}
    #     self.text2voice_player = Text2voice()
    #     self.voice2texter = Voice2text()
    #     while True:
    #         question = self.voice2texter.record2text(Bd=False)
    #         if '嗯' in question:
    #             print("嗯恩不识别")
    #             continue
    #         if question == "听不到任何声音":
    #             continue
    #
    #         elif "聊天" in question:
    #             if "退出" in question or "关闭" in question:
    #                 self.chating = False
    #                 break
    #         elif "切换" in question:
    #             if "声音" in question:
    #                 voiceid = list(voices.values())[random.randint(0, len(voices) - 1)]
    #                 self.text2voice_player.get_voice_and_paly_it("已切换播报人id为{}".format(voiceid))
    #                 continue
    #         if sz:
    #             ans = self.get_sizhibot_response(question)
    #         else:
    #             ans = self.get_chatter_response(question)
    #         self.text2voice_player.get_voice_and_paly_it(ans, voiceid)
    #         if not self.chating:
    #             break
    #     self.text2voice_player.play("voicecontrollermodel/inandoutchating_file/out{}.wav".format(voiceid))

    def close_chat(self):
        # if self.chatthread.is_alive():
        self.chating = False


if __name__ == '__main__':
    # from text2voice import Text2voice

    #
    text2voicer = Text2voice()
    chatter = Chatter()
    # chatter.open_chat()
    chatter.get_sizhibot_response('年')
    # ans = chatter.get_chatter_response('你好')
    # text2voicer.get_voice_and_paly_it("好，那咱就说定了",True)
