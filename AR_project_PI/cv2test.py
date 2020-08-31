import cv2

capture = cv2.VideoCapture(0)
# capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
while capture.isOpened():
    re, frame = capture.read()
    if re:
        cv2.imshow("cv2test", frame)
        c = cv2.waitKey(1)
        if c & 0xFF == ord('q'):
            break
    else:
        break
cv2.destroyAllWindows()
