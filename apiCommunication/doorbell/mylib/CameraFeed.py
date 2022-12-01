from VideoStreamConnection import VideoStreamConnection
import cv2


class CameraFeed:
    def __init__(self, cameraThere):
        self.cameraThere = cameraThere

    def showPicture(self):
        vidstream = VideoStreamConnection(False).connectVideo()

        while True:
            ret, frame = vidstream.read()
            cv2.imshow("aaa", frame)
            if cv2.waitKey(20) & 0xFF == ord('q'):
                break
            print("Test")
        vidstream.release()
        cv2.destroyAllWindows()


CameraFeed(False).showPicture()
