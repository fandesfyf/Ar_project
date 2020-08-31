import cv2


def set_dpi(cap, w, h, fps=18):
    cap.set(3, h)
    cap.set(4, w)
    cap.set(cv2.CAP_PROP_FPS, fps)


capture = cv2.VideoCapture(1, cv2.CAP_DSHOW)
# cv2.waitKey(2000)
while 1:
    re, frame = capture.read()
    if re:
        cv2.imshow("ds", frame)
        cv2.waitKey(1)
