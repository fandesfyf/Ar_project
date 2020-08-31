import base64
import hashlib
import random
import time
import urllib
import wave

import pyaudio
import requests


class Text2voice():
    def __init__(self):
        self.url = r"https://api.ai.qq.com/fcgi-bin/aai/aai_tts"
        self.palyer = pyaudio.PyAudio()

    def get_sign_code(self, params, app_key="TTkZvr74cJHQWQxR"):
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

    def get_random_str(self, n=17):
        s = "qwertyuiop7894561230asdfghjklzxcvbnm"
        rs = ''
        for i in range(n):
            rs += s[random.randint(0, 15)]
        return rs

    def get_voice_and_paly_it(self, text, speaker=1, format=2, volume=0, speed=95, aht=0, apc=58):
        params = {"app_id": 2154786206,
                  "time_stamp": int(time.time()),
                  "nonce_str": self.get_random_str(),
                  "speaker": speaker,
                  "format": format,
                  "volume": volume,
                  "speed": speed,
                  "text": text,
                  "aht": aht,
                  "apc": apc
                  }
        params["sign"] = self.get_sign_code(params)
        response = requests.get(self.url, params=params)
        js = response.json()
        audiobase64 = js["data"]["speech"]
        audio = base64.b64decode(audiobase64)
        with open("temp.wav", 'wb') as f:
            f.write(audio)
            f.close()
        self.play()

    def play(self):
        CHUNK = 1024
        wf = wave.open("temp.wav", "rb")

        stream = self.palyer.open(format=self.palyer.get_format_from_width(wf.getsampwidth()),
                                  channels=wf.getnchannels(),
                                  rate=wf.getframerate(),
                                  output=True)

        data = wf.readframes(CHUNK)

        while len(data):
            stream.write(data)
            data = wf.readframes(CHUNK)

        stream.stop_stream()
        stream.close()


if __name__ == '__main__':
    text = "你好啊 示例数据1000000001,redis"
    txt2vo = Text2voice()
    txt2vo.get_voice_and_paly_it(text)

"""参数名称	是否必选	数据类型	数据约束	示例数据	描述
app_id	是	int	正整数	1000001	应用标识（AppId）
time_stamp	是	int	正整数	1493468759	请求时间戳（秒级）
nonce_str	是	string	非空且长度上限32字节	fa577ce340859f9fe	随机字符串
sign	是	string	非空且长度固定32字节		签名信息，详见接口鉴权
speaker	是	int	正整数	1	语音发音人编码，定义见下文描述
format	是	int	正整数	2	合成语音格式编码，定义见下文描述
volume	是	int	[-10, 10]	0	合成语音音量，取值范围[-10, 10]，如-10表示音量相对默认值小10dB，0表示默认音量，10表示音量相对默认值大10dB
speed	是	int	[50, 200]	100	合成语音语速，默认100
text	是	string	UTF-8编码，非空且长度上限150字节	腾讯，你好！	待合成文本
aht	是	int	[-24, 24]	0	合成语音降低/升高半音个数，即改变音高，默认0
apc	是	int	[0, 100]	58	控制频谱翘曲的程度，改变说话人的音色，默认58"""

"""
base64编码
with open("D:\\redis.png", 'rb') as f:
    encode_img = base64.b64encode(f.read())
    file_ext = os.path.splitext("D:\\redis.png")[1]
    print('data:image/{};base64,{}'.format(file_ext[1:], encode_img.decode()))
    f.close()
解码
with open("D:\\redis2.png", 'wb') as f:
    f.write(base64.b64decode(encode_img))
    f.close()
"""
