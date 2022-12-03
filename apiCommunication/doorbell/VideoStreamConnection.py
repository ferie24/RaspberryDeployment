import cv2
import time


class VideoStreamConnection:
    def __init__(self, cameraAvailable):
        self.inputVideoPath = "/Users/felixriemen/PycharmProjects/ServerDoorbellConnecton/Doorbell/videos/example_01.mp4"
        self.videoStream = None
        self.cameraAvailable = cameraAvailable

    def connectCamera(self):
        try:
            print("INFO - Trying to connect Camera Livestream")
            return cv2.VideoCapture("rtsp://6tFTmqw7:9dNQ8OlyAsSMDHeQ@192.168.178.77:554/live/ch0")

        except:
            print("[Error] No Video Stream Recognized")

    def connectVideo(self):
        return cv2.VideoCapture(self.inputVideoPath)

    def getVidStream(self):
        if self.cameraAvailable:
            vidstream = self.connectCamera()
        else:
            vidstream = self.connectVideo()
        ret, frame = vidstream.read()
        print(frame)
        # frame = frame[1] if args.get("input", False) else frame
        # guckt ob camera richtig verbunden ist nicht ganz sein job finde ich
        if frame is None:
            return False
        else:
            return frame
