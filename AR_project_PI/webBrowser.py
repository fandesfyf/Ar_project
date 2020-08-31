import sys
import time

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton


class ARBrowser(QWebEngineView):#内嵌浏览器界面
    def __init__(self, parent=None):
        if parent:
            super().__init__(parent)
            self.setGeometry(parent.width() - 100, 10, parent.width() - parent.width() // 4, parent.height() - 20)
        else:
            super().__init__()
            self.setGeometry(0, 0, 1280, 720)
        self.setWindowTitle("web")

        with open('Navigationhtml/pathplan.html', 'r', encoding='utf-8')as f:
            self.pathplanhtml = f.read()
        with open('Navigationhtml/navigating.html', 'r', encoding='utf-8')as f:
            self.navigatinghtml = f.read()
        with open('Navigationhtml/keywordsearch.html', 'r', encoding='utf-8')as f:
            self.searchhtml = f.read()
        with open('Navigationhtml/nowpos.html', 'r', encoding='utf-8')as f:
            self.nowposhtml = f.read()

    def showhtml(self, html, file=True):
        if file:
            with open(html, 'r', encoding="utf-8")as ht:
                html = ht.read()
        self.setHtml(html)
        QApplication.processEvents()
        # self.setCentraWidget(self.browser)

    def pathplanning(self, start_pos, end_pos):  # 显式路径规划
        start_str = str(start_pos[0]) + ',' + str(start_pos[1])
        end_str = str(end_pos[0]) + ',' + str(end_pos[1])
        self.setHtml(self.pathplanhtml.replace("start_pos", start_str).replace("end_pos", end_str))
        QApplication.processEvents()

    def navigating_show(self, start_pos, end_pos):  # 导航路径小地图显示
        start_str = str(start_pos[0]) + ',' + str(start_pos[1])
        end_str = str(end_pos[0]) + ',' + str(end_pos[1])
        self.setHtml(self.navigatinghtml.replace("start_pos", start_str).replace("end_pos", end_str))
        QApplication.processEvents()
        # self.set_center_pos(start_pos, 17)
        # QApplication.processEvents()

    def set_center_pos(self, pos, zoom=17):  # 更新一个pos
        self.page().runJavaScript('changecenter({},{},{});'.format(pos[0], pos[1], zoom))
        QApplication.processEvents()

    def show_initpage(self, pos, zoom=18):  # 初始化显示地图
        posstr = str(pos[0]) + ',' + str(pos[1])
        self.setHtml(self.nowposhtml.replace("nowpos", posstr).replace("zoom: 17", "zoom: {}".format(zoom)))
        QApplication.processEvents()

    def search(self, address):  # 显式搜索
        self.setHtml(self.searchhtml.replace("search_pos", address))

    def next_result_page(self):  # xyy
        self.page().runJavaScript("nextpage();")
        print("next page")

    def updatahtml(self):
        # self.n += 5
        # print("read", self.n)
        # html = self.pathplan_html.replace("100", str(self.n + 100))
        # self.setHtml(html)
        QApplication.processEvents()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_F5:
            print("刷新")
            self.reload()
        elif e.key() == Qt.Key_Q:
            print('quit')
            self.showNormal()
        elif e.key() == Qt.Key_Return:
            print("return")
            self.showFullScreen()
        elif e.key() == Qt.Key_Escape:
            self.close()


class controlthread(QThread):
    flashsignal = pyqtSignal()

    def __init__(self):
        super(controlthread, self).__init__()

    def run(self) -> None:
        n = 1
        while True:
            n += 1
            if n % 15 == 0:
                print(100 + n)
                self.flashsignal.emit()
            time.sleep(0.1)


class Text_win(QMainWindow):
    def __init__(self):
        super(Text_win, self).__init__()
        self.resize(1280, 720)
        self.browser = ARBrowser(self)
        self.browser.setGeometry(0, 0, 960, 640)
        self.bot = QPushButton("change", self)
        self.bot.setGeometry(5, self.height() - 40, 80, 30)
        self.bot.clicked.connect(self.change)
        self.pos = (113.930201, 22.526368)
        self.browser.navigating_show((113.930201, 22.526368), (116.427281, 39.903719))
        # self.browser.showpos((113.930201, 22.526368))

    def change(self):
        self.pos = (self.pos[0] + 0.001, self.pos[1] + 0.001)
        print(self.pos)
        self.browser.set_center_pos(self.pos, 18)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Text_win()
    win.show()
    # win.navigating_show((113.930591, 22.526802), ('113.972654', '22.59163'))
    # win.search("深圳大学")
    # win.set(QUrl.fromLocalFile("initbrowser.png"))
    # win.showinitpage((113.930201, 22.526368))

    # th = controlthread()
    # th.flashsignal.connect(win.updatahtml)
    # th.start()

    sys.exit(app.exec_())
