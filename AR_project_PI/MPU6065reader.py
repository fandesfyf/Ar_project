import sys
import time
from time import sleep

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication

import MPU6050filter


class MPU6050Reader(QThread):
    yaw_angle_signal = pyqtSignal(float)

    def __init__(self, correcting_value: float = 0.0):
        super(MPU6050Reader, self).__init__()
        from mpu6050 import mpu6050
        self.running = True
        #self.sensor = mpu6050(0x68)
        self.sensor = mpu6050(address=0x68,bus=2)  # 设备地址
        self.sensor.set_accel_range(mpu6050.ACCEL_RANGE_16G)  # 设置加速度计的量程
        self.sensor.set_gyro_range(mpu6050.GYRO_RANGE_2000DEG)
        # self.yaw_angle_signal.connect(signal_handle_fuc)
        self.correcting_value = correcting_value

    def run(self):
        def getmpudata(sensor):
            try:
                accel_data = sensor.get_accel_data()
                gyro_data = sensor.get_gyro_data()
            except OSError:
                accel_data, gyro_data = getmpudata(sensor)
            return accel_data, gyro_data

        MPU6050filter.init_all()
        self.running = True
        dcount = 0
        while self.running:
            accel_data, gyro_data = getmpudata(self.sensor)
            # 四元素转欧拉角
            yaw_angle = MPU6050filter.IMUupdate(accel_data['x'], accel_data['y'], accel_data['z'],
                                                gyro_data['x'], gyro_data['y'], gyro_data['z'])
            yaw_angle -= self.correcting_value * dcount

            # print("偏航角", yaw_angle)
            self.yaw_angle_signal.emit(yaw_angle)
            sleep(0.1)
            dcount += 1

    def stop(self):
        self.running = False


class test():
    d = 1
    s = 0
    c = 0

    def pri(self, ph):
        print("ph", ph)
        self.c += 1
        self.s += (ph - self.d)
        print(ph - self.d, self.s / self.c)
        self.d = ph


if __name__ == '__main__':
    app = QApplication(sys.argv)
    a = test()
    mpu = MPU6050Reader(0.0720)
    mpu.yaw_angle_signal.connect(a.pri)
    mpu.start()
    sys.exit(app.exec_())
