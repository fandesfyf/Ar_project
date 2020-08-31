import socket
import sys

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication


class AndroidGpsThread(QThread):#从app中获取gps信息返回给导航系统和界面进行导航规划
    get_gps_from_mobile_signal = pyqtSignal(tuple, str)

    def __init__(self, host="", port=8888):
        super().__init__()
        self.host = host
        self.port = port

    def run(self):
        while True:
            try:
                print("host:{} port:{};waiting for connection...".format(self.host, self.port))
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind((self.host, self.port))
                server_socket.listen(5)
                client_socket, client_address = server_socket.accept()
                host_name = socket.gethostname()
                host_ip = socket.gethostbyname(host_name)
                print("Host: ", host_name + ' ' + host_ip)
                print("Connection from: ", client_address)
                print("Streaming...")
                stream_bytes = b' '
                while True:
                    stream_bytes += client_socket.recv(9999)
                    print(stream_bytes.decode())
                    end = stream_bytes.find(b"\n")
                    if end != -1:
                        address_str = stream_bytes.decode().replace("\n","").replace("\r","")
                        y, x, address = address_str.split(",")
                        pos = (float(x), float(y))
                        self.get_gps_from_mobile_signal.emit(pos, address)
                        print("receive and break", pos)
                        client_socket.close()
                        server_socket.close()
                        break
            except:
                print(sys.exc_info())


if __name__ == '__main__':
    app = QApplication(sys.argv)

    h, p = "", 8888
    st = AndroidGpsThread(h, p)
    st.start()

    sys.exit(app.exec_())
