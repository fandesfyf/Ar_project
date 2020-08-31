from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 32
rawCapture = PiRGBArray(camera)
# allow the camera to warmup
time.sleep(0.1)
# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    image = frame.array
    # show the frame
    cv2.imshow("Frame", image)
    # prepare for net stream
    rawCapture.truncate(0)

    if(cv2.waitKey(1) == ord('q')):
        cv2.destroyAllWindows()
        break;