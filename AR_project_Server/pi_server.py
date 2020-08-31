import os
import socket
import sys

import cv2
import numpy as np

if not os.path.exists("pishot"):
    os.mkdir('pishot')


class VideoStreamingTest(object):
    def __init__(self, host="172.18.240.154", port=8787):
        self.host, self.port = host, port
        # if r:
        #     self.reset()

    def reset(self):
        print("host:{} port:{};waiting for connection...".format(self.host, self.port))
        self.server_socket = socket.socket()
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(0)
        self.client_socket, self.client_address = self.server_socket.accept()

        self.reader = self.client_socket.makefile('rb')
        self.writer = self.client_socket.makefile('wb')
        self.host_name = socket.gethostname()
        self.host_ip = socket.gethostbyname(self.host_name)
        print("Host: ", self.host_name + ' ' + self.host_ip)
        print("Connection from: ", self.client_address)
        print("Streaming...")
        # self.streaming()

    def streaming(self):
        while True:
            self.reset()
            # cv2.namedWindow('video', 0)
            # cv2.resizeWindow('video', 640, 360)
            print("connected")
            stream_bytes = b' '
            try:
                while True:
                    # print(stream_bytes[:20], len(stream_bytes))
                    # self.client_socket.settimeout(10)
                    stream_bytes += self.client_socket.recv(9999)
                    # self.client_socket.settimeout(None)
                    first = stream_bytes.find(b'\xff\xd8')
                    last = stream_bytes.find(b'\xff\xd9')
                    # print(len(stream_bytes[:5]))
                    if len(stream_bytes) == 0:
                        print("no frame data,exit!")
                        break
                    elif first != -1 and last != -1:
                        pos = stream_bytes[:first]
                        jpg_bytes = stream_bytes[first:last + 2]
                        stream_bytes = stream_bytes[last + 2:]
                        # self.writer.write("<| |>".encode())
                        # self.writer.flush()

                        frame = cv2.imdecode(np.frombuffer(jpg_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
                        cv2.imshow('video', frame)
                        c = cv2.waitKey(1)
                        if c & 0xFF == ord('q'):
                            break

                self.close()
                cv2.destroyAllWindows()
            except:
                self.close()
                cv2.destroyAllWindows()
                print(sys.exc_info())

    def close(self):
        # self.reader.close()
        # self.writer.close()
        self.server_socket.close()


if __name__ == '__main__':
    # host, port
    # szu_WLAM_172.26.107.243
    h, p = "192.168.137.1", 8787  # 172.18.240.154
    st = VideoStreamingTest(h, p)
    st.streaming()
