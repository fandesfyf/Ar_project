import sys
import time

import cv2
from PyQt5.QtCore import QRect, Qt, QThread, pyqtSignal, QStandardPaths, QTimer, QSettings, QFileInfo, \
    QSharedMemory, QPoint, QUrl, QMimeData, QRectF, QMutex, QMutexLocker
from PyQt5.QtGui import QPixmap, QPainter, QPen, QIcon, QFont, QImage, QTextCursor, QColor, QDesktopServices, QCursor, \
    QBrush, QPainterPath
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QToolTip, QAction, QTextEdit, QLineEdit, \
    QMessageBox, QFileDialog, QMenu, QSystemTrayIcon, QGroupBox, QComboBox, QCheckBox, QSpinBox, QTabWidget, \
    QDoubleSpinBox, QLCDNumber, QSlider, QScrollArea, QWidget, QToolBox, QRadioButton, QTimeEdit, QColorDialog, \
    QListWidget
from PyQt5.QtNetwork import QLocalSocket, QLocalServer
from webBrowser import ARBrowser
from Navigation_system import Navigationsys
from Arrowclass import Arrow
import resources_rc

class MaskViewerLabel(QLabel):#最底层绘图图层
    def __init__(self, parent):
        super(MaskViewerLabel, self).__init__(parent)
        self.palyingmask = False
        self.setScaledContents(True)
        self.VideoCapture = cv2.VideoCapture()
        self.VideoTimer = VideoTimer(frequent=15)
        self.VideoTimer.timeSignal.connect(self.paly_mask)
        self.show_mask = 0
        self.change_to_green = False
        self.red_nogreen_timer = QTimer(self)
        self.red_nogreen_timer.timeout.connect(self.stop_play)
        self.forwardarrow = Arrow("arrow/forward.png")
        self.leftarrow = Arrow("arrow/left.png")
        self.rightarrow = Arrow("arrow/right.png")

    def show_arrow(self, arrow: Arrow, anglex=None, angley=None, anglez=None, fov=None, w=None, h=None):
        frame = arrow.updata_angle(anglex, angley, anglez, fov, w, h)
        self.show_a_frame(frame)

    def paly_mask(self, s):
        if s:
            re, frame = self.VideoCapture.read()
            if re:
                # print("read a frame")
                self.show_a_frame(frame)
            else:
                if self.show_mask == 1:
                    self.show_mask = 0
                    self.VideoTimer.stop()
                elif self.show_mask == 2:
                    if self.change_to_green:
                        self.change_to_green = False
                        self.show_mask = 1
                        self.VideoCapture.open('foundgreen.mp4')
                    else:
                        self.VideoCapture.open('foundred.mp4')
        else:
            self.stop_play()

    def show_a_frame(self, frame):
        # st = time.time()
        height, width = frame.shape[:2]
        if frame.ndim == 3:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        elif frame.ndim == 2:
            rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        temp_image = QImage(rgb.flatten(), width, height, QImage.Format_RGB888)
        temp_pixmap = QPixmap.fromImage(temp_image)
        self.setPixmap(temp_pixmap)
        # print(time.time() - st)
        self.update()

    def show_red_mask(self):
        if not self.red_nogreen_timer.isActive():
            self.show_mask = 2
            self.red_nogreen_timer.start(30000)
            self.update()

    def show_green_mask(self):
        if self.show_mask == 2:
            self.change_to_green = True
        self.show_mask = 1
        self.update()

    def stop_play(self):
        self.VideoTimer.stop()
        self.red_nogreen_timer.stop()
        print("播放结束")
        self.show_nothing()
        self.palyingmask = False
        self.change_to_green = False
        self.show_mask = 0

    def show_nothing(self):
        blackpix = QPixmap()
        blackpix.fill(QColor(0, 0, 0))
        self.setPixmap(blackpix)
        self.update()

    def paintEvent(self, e):
        super(MaskViewerLabel, self).paintEvent(e)
        if self.show_mask:
            if not self.palyingmask:
                if self.show_mask == 1:
                    print("检测到绿灯,开始播放")
                    self.palyingmask = True
                    self.VideoTimer.start()
                    self.VideoCapture.open('foundgreen.mp4')
                else:
                    print("检测到红灯,开始播放")

                    self.palyingmask = True
                    self.VideoTimer.start()
                    self.VideoCapture.open('foundred.mp4')


class MaskArrowLabel(QLabel):#箭头图层
    def __init__(self, parent):
        super(MaskArrowLabel, self).__init__(parent)
        self.setScaledContents(True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.forwardarrow = Arrow("arrow/forward.png")
        self.leftarrow = Arrow("arrow/left.png")
        self.rightarrow = Arrow("arrow/right.png")

    def show_arrow(self, arrow: Arrow, anglex=None, angley=None, anglez=None, fov=None, w=None, h=None):
        frame = arrow.updata_angle(anglex, angley, anglez, fov, w, h)
        self.show_a_frame(frame)

    def show_a_frame(self, frame):
        height, width, ndim = frame.shape[:3]
        print(ndim)
        if ndim == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        elif ndim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        temp_image = QImage(frame.flatten(), width, height, QImage.Format_ARGB32)
        temp_pixmap = QPixmap.fromImage(temp_image)
        self.setPixmap(temp_pixmap)
        self.update()

    def show_nothing(self):
        blackpix = QPixmap()
        blackpix.fill(QColor(0, 0, 0))
        self.setPixmap(blackpix)
        self.update()


class IconLabel(QLabel):#图标图层
    def __init__(self, parent):
        super(IconLabel, self).__init__(parent)
        self.setScaledContents(True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.height_limit_img = cv2.imread("height_limit.png", cv2.IMREAD_UNCHANGED)
        self.construction_img = cv2.imread("construction.png", cv2.IMREAD_UNCHANGED)
        # self.setStyleSheet("border:2px solid rgb(4, 136, 220);border-radius: 10px;")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_nothing)
        self.show()
        # self.show_height_limit_img()

    def show_height_limit_img(self):
        self.show_a_frame(self.height_limit_img)

    def show_construction_img(self):
        self.show_a_frame(self.construction_img)

    def show_nothing(self):
        blackpix = QPixmap()
        blackpix.fill(QColor(0, 0, 0))
        self.setPixmap(blackpix)
        self.update()

    def show_a_frame(self, frame):
        self.timer.start(1500)
        height, width, ndim = frame.shape[:3]
        # print(ndim)
        if ndim == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        elif ndim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        temp_image = QImage(frame.flatten(), width, height, QImage.Format_ARGB32)
        temp_pixmap = QPixmap.fromImage(temp_image)
        self.setPixmap(temp_pixmap)
        self.update()


class VideoTimer(QThread):#视频播放控制线程
    timeSignal = pyqtSignal(int)

    def __init__(self, frequent=12):
        QThread.__init__(self)
        self.stopped = False
        self.frequent = frequent

    def run(self):
        self.stopped = False
        while True:
            if self.stopped:
                self.timeSignal.emit(0)
                return
            self.timeSignal.emit(1)
            time.sleep(1 / self.frequent)

    def stop(self):
        self.stopped = True

    def set_fps(self, fps):
        self.frequent = fps


class ArMainwindow(QMainWindow):#主界面主窗口
    def __init__(self):
        super().__init__()
        print("UI界面正在初始化")

        self.mask_viewer = MaskViewerLabel(self)
        self.arrow_mask_viewer = MaskArrowLabel(self)

        self.grubox = QGroupBox(self)
        self.icon_viewer = IconLabel(self)
        self.browser_viewer_box = QGroupBox(self)
        self.browser_viewer = ARBrowser(self)
        self.browser_viewer_box.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.controllboard = QGroupBox(self)
        self.exitfullscreenbot = QPushButton("退出全屏", self.controllboard)
        self.exitfullscreenbot.clicked.connect(self.showNormal)
        self.fullscreenbot = QPushButton("全屏", self.controllboard)
        self.fullscreenbot.clicked.connect(self.showFullScreen)
        self.exitbot = QPushButton("退出", self.controllboard)
        self.exitbot.clicked.connect(self.close)
        self.testbot = QPushButton("test", self.controllboard)
        self.testbot.clicked.connect(self.test)
        self.turnbot = QPushButton("转弯测试", self.controllboard)
        self.mask_viewer.setPixmap(QPixmap(':/black.png'))
        self.speechbot = QPushButton(self)
        self.speechtext_editer = QLineEdit(self)
        self.speechtext_editer.setPlaceholderText('请说"蜂鸟"以唤醒')
        self.chatrecord_editer = QTextEdit(self)
        self.chatrecord_editer.setPlaceholderText("......")
        self.chatrecord_editer.setFont(QFont('', 9))
        self.chatrecord_editer.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.navigationsystem = Navigationsys()

        # self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.controllboard.setStyleSheet(
            "QPushButton{background-color:rgba(20,20,20,10);color:rgba(200,0,0,20);border:none}"
            "QPushButton:hover { color: blue;background-color:rgba(200,200,200,200);}")
        self.setStyleSheet("""QMainWindow{background-color:rgb(0,0,0);}"""
                           """QGroupBox{border: None}"""
                           )
        self.browser_viewer_box.setStyleSheet("""border:4px solid rgb(4, 136, 220)""")
        self.speechbot.setStyleSheet("QPushButton{background-color:rgba(20,20,20,0);border-image: url(:/graymkf.png);}")
        self.speechtext_editer.setStyleSheet("""background-color:rgba(20,20,20,20);color: rgb(240,0,251);
        border: 2px solid rgb(128, 122, 253);border-radius: 15px;""")
        self.chatrecord_editer.setStyleSheet("""background-color:rgba(20,20,20,20);color: rgb(240,0,251);
        border: 1px solid rgb(70, 100, 150);border-radius: 5px;""")
        self.grubox.setStyleSheet("border:2px solid rgb(4, 136, 220);border-radius: 10px;")
        # self.icon_viewer.setStyleSheet("border:2px solid rgb(4, 136, 220);border-radius: 10px;")
        self.resizeall()
        self.resize(640, 360)
        self.setWindowTitle("AR车载导航")
        self.show()
        print("UI界面已初始化!")

    def test(self):
        self.mask_viewer.show_red_mask()
        self.icon_viewer.show_height_limit_img()
        self.arrow_mask_viewer.show_arrow(self.arrow_mask_viewer.leftarrow)
        self.listening()

    def resizeall(self):

        self.mask_viewer.setGeometry(0, 0, self.width(), self.height())
        self.arrow_mask_viewer.setGeometry(0, 0, self.width(), self.height())
        self.icon_viewer.setGeometry(self.width() - 90, self.height() - 90, 85, 85)
        self.grubox.setGeometry(0, 0, self.width(), self.height())
        self.controllboard.setGeometry(0, 0, self.width() // 3, self.height())
        self.speechbot.setGeometry(5, self.height() - 45, 40, 40)
        self.speechtext_editer.setGeometry(self.speechbot.x() + self.speechbot.width() + 5,
                                           self.speechbot.y() + 5, self.width() // 4, 30)
        self.chatrecord_editer.setGeometry(self.speechbot.x(), self.speechbot.y() - 100,
                                           self.speechtext_editer.x() + self.speechtext_editer.width() - self.speechbot.x() - 10,
                                           92)
        self.exitbot.setGeometry(5, 5, 80, 30)
        self.fullscreenbot.setGeometry(self.exitbot.x(),
                                       self.exitbot.y() + self.exitbot.height() + 5,
                                       self.exitbot.width(),
                                       self.exitbot.height())
        self.exitfullscreenbot.setGeometry(self.fullscreenbot.x(),
                                           self.fullscreenbot.y() + self.fullscreenbot.height() + 5,
                                           self.exitbot.width(),
                                           self.exitbot.height())
        self.testbot.setGeometry(self.exitfullscreenbot.x(),
                                 self.exitfullscreenbot.y() + self.exitfullscreenbot.height() + 5,
                                 self.exitbot.width(),
                                 self.exitbot.height())
        self.turnbot.setGeometry(self.testbot.x(),
                                 self.testbot.y() + self.testbot.height(),
                                 self.exitbot.width(),
                                 self.exitbot.height())
        self.browser_viewer.setGeometry(self.width() - self.width() // 3, 10,
                                        self.width() // 3 - 4, int(self.height() / 1.7))
        self.browser_viewer_box.setGeometry(self.browser_viewer.x() - 4, self.browser_viewer.y() - 4,
                                            self.browser_viewer.width() + 8, self.browser_viewer.height() + 8)

    def update_chatrecord(self, text, user=True):  # 更新聊天框
        self.chatrecord_editer.moveCursor(QTextCursor.End)
        if user:
            self.chatrecord_editer.setTextColor(QColor(10, 100, 222))
            self.chatrecord_editer.insertPlainText("user: ")
            self.chatrecord_editer.setTextColor(QColor(240, 0, 251))
            self.chatrecord_editer.insertPlainText(text + "\n")
        else:
            self.chatrecord_editer.setTextColor(QColor(10, 100, 222))
            self.chatrecord_editer.insertPlainText("蜂鸟: ")
            self.chatrecord_editer.setTextColor(QColor(240, 0, 251))
            self.chatrecord_editer.insertPlainText(text + "\n")
        self.chatrecord_editer.moveCursor(QTextCursor.End)

    def search_address(self, address):  # 显示目的地搜索界面
        self.browser_viewer.setGeometry(10, 10, self.width() - 20, self.height() - 20)
        self.browser_viewer_box.setGeometry(self.browser_viewer.x() - 4, self.browser_viewer.y() - 4,
                                            self.browser_viewer.width() + 8, self.browser_viewer.height() + 8)
        self.browser_viewer.search(address)

    def listening(self, text=None):
        if text:
            self.speechtext_editer.setText(text)
        else:
            self.speechtext_editer.clear()
        self.speechbot.setStyleSheet("QPushButton{background-color:rgba(20,20,20,0);border-image: url(:/mkf.png);}")
        self.speechtext_editer.setPlaceholderText("正在聆听...")

    def stop_listening(self, text=None):
        if text:
            self.speechtext_editer.setText(text)
        else:
            self.speechtext_editer.clear()
        self.speechbot.setStyleSheet("QPushButton{background-color:rgba(20,20,20,0);border-image: url(:/graymkf.png);}")
        self.speechtext_editer.setPlaceholderText('请说"蜂鸟"以唤醒...')

    def path_palning_view(self, start_pos=(113.931337, 22.527091), end_pos=(113.370555, 23.039919)):  # 显示路径规划界面
        self.browser_viewer.setGeometry(10, 10, self.width() - 20, self.height() - 20)
        print(start_pos, end_pos)
        self.browser_viewer_box.setGeometry(self.browser_viewer.x() - 4, self.browser_viewer.y() - 4,
                                            self.browser_viewer.width() + 8, self.browser_viewer.height() + 8)
        self.browser_viewer.pathplanning(start_pos, end_pos)
        QApplication.processEvents()

    def set_browser_viewer_box_smaller(self):
        self.browser_viewer.setGeometry(self.width() - self.width() // 3, 10, self.width() // 3, self.height() // 2)
        self.browser_viewer_box.setGeometry(self.browser_viewer.x() - 4, self.browser_viewer.y() - 4,
                                            self.browser_viewer.width() + 8, self.browser_viewer.height() + 8)

    def showPosMap(self, pos=(113.930201, 22.526368), zoom=17):
        self.browser_viewer.show_initpage(pos, zoom=zoom)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Q or e.key() == Qt.Key_Escape:
            print('quit')
            self.showNormal()
        elif e.key() == Qt.Key_Return:
            print("return")
            self.showFullScreen()
        # elif e.key()==Qt.Key_Space:
        #     print("space press")

    def resizeEvent(self, e):
        super(ArMainwindow, self).resizeEvent(e)
        self.resizeall()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    UI = ArMainwindow()

    # UI.setGeometry(100, 100, 400, 200)
    UI.show()
    UI.showPosMap(zoom=16)

    # UI.listening()
    # UI.stop_listening("你好")
    # UI.choose_address("深圳大学")
    # UI.path_palning_view()
    # UI.mask_viewer.show_mask = 2
    # UI.showFullScreen()
    # time.sleep(3)

    sys.exit(app.exec_())
