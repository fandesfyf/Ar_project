import asyncio
import datetime
import sys, time
import threading
from queue import Queue

import websockets
from PyQt5.QtWidgets import QApplication


class WebsocketThread(threading.Thread):#通过websocket与前端通信
    def __init__(self, recq: Queue, sendq: Queue):
        super(WebsocketThread, self).__init__()
        self.recq = recq
        self.sendq = sendq

    def run(self):
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        print("websocket waiting ")

        async def recandreturn(websocket, path):
            name = await websocket.recv()
            print("recv:", name)
            self.sendq.put(name)
            # with open("0.png", "rb")as f:
            #     b = f.read()
            # await websocket.send("车牌错误")
            # await websocket.send(b)
            # await websocket.send(str(datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")))
            while True:
                if not self.recq.empty():
                    result = self.recq.get()
                    await websocket.send(result)
                    print("已返回结果", result)
                    if result !="车牌号有误":
                        await websocket.send(str(datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")))
                    break
                else:
                    time.sleep(0.2)

            print("00000")

        start_server = websockets.serve(recandreturn, '192.168.137.1', 1234)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    sendq = Queue()
    recq = Queue()
    t = WebsocketThread(sendq, recq)
    t.start()
    sys.exit(app.exec_())
