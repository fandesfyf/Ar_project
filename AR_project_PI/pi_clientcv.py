import socket
import sys, time

import cv2
import numpy
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication

from Navigation_system import Navigationsys


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


class Clientcvcap(QThread):  # 获取摄像头数据并不断传输
    receive_info_signal = pyqtSignal(bytes)

    def __init__(self, IP='192.168.137.1', port=8787, fps=20, dpi=(1280, 720), navigationsys=None):
        super(Clientcvcap, self).__init__()
        self.ip = IP
        self.port = port
        self.fps = fps
        self.sending = True
        self.dpi = dpi
        self.navigatesys = navigationsys

        # self.send_frame()

    def run(self):
        while True:
            try:
                print("created a new frame_send thread,waiting for server")
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.settimeout(10)
                self.client_socket.connect((self.ip, self.port))
                self.client_socket.settimeout(None)

                self.writer = self.client_socket.makefile('wb')
                self.reader = self.client_socket.makefile('rb')
                print("connect to server")
                self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
                self.set_dpi(self.cap, self.dpi[0], self.dpi[1], self.fps)
                self.send_frame()
                # self.writer.close()
                self.reader.close()
                print("connection break!")
            except:
                print(sys.exc_info(), "l61")
                time.sleep(0.2)
                # self.cap.release()
                cv2.destroyAllWindows()
                print("time out to connect, retry l63")

            # self.writer.close()
            # self.reader.close()
            self.client_socket.close()

    def set_dpi(self, cap, w, h, fps=12):
        cap.set(3, w)
        cap.set(4, h)
        cap.set(cv2.CAP_PROP_FPS, fps)
        cap.set(10, 20)  # 20为亮度

    def send_frame(self):
        self.read_thread = CommendThread(self.receive_info)
        self.read_thread.start()
        self.sending = True
        print("已启动摄像头!")
        try:
            while self.cap.isOpened() and self.sending:
                s, frame = self.cap.read()
                if s:
                    print("read a frame")
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
                    result, imgencode = cv2.imencode('.jpg', frame, encode_param)
                    data = numpy.array(imgencode)
                    stringData = data.tobytes()
                    pos = "{},{}".format(self.navigatesys.pos[0], self.navigatesys.pos[1])
                    pos = pos.encode()
                    self.client_socket.settimeout(3)
                    self.client_socket.send(pos + stringData)
                    self.client_socket.settimeout(None)
                    print("send")
                    # self.writer.write(a)
                    # self.writer.flush()
                else:
                    print("read frame fail!")
                    break

        except ConnectionResetError:
            print("reset by server")
            print(sys.exc_info())
        except:
            time.sleep(0.2)
            print(sys.exc_info(), "l99")
            self.client_socket.close()

        self.sending = False
        self.cap.release()
        cv2.destroyAllWindows()

    def receive_info(self):  # 获取返回的信息,放在子线程的子线程中(CommendThread)
        stream_bytes = b' '
        print("start receiver")
        while self.sending:
            # print(stream_bytes)
            try:
                stream_bytes += self.client_socket.recv(5)
                # print(stream_bytes)
                first = stream_bytes.find(b'<|')
                last = stream_bytes.find(b'|>')
                if first != -1 and last != -1:
                    receive_obj = stream_bytes[first + 2:last]
                    stream_bytes = stream_bytes[last + 2:]
                    print("receive", receive_obj)
                    if len(receive_obj) == 1:
                        if receive_obj.decode() == "q":
                            self.sending = False
                            print("receive to quit")
                            break

                    else:
                        print("send to main")
                        self.receive_info_signal.emit(receive_obj)

            except:
                print(sys.exc_info(), 142)
                break


if __name__ == '__main__':
    app = QApplication(sys.argv)
    navigationsys = Navigationsys()
    client = Clientcvcap(IP="172.30.84.24", navigationsys=navigationsys)
    client.start()
    sys.exit(app.exec_())
