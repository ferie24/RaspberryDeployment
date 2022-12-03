import cv2
import imutils

from VideoStreamConnection import VideoStreamConnection


class VideoOutput:
    def __init__(self, cameraAvailable):
        self.rgb = None
        self.frame = None
        self.outputVideoPath = None
        self.writer = None
        self.cameraAvailable = cameraAvailable
        self.frameWidth = None
        self.frameHeight = None

    def setOutputVideoPath(self):
        if self.outputVideoPath is not None and self.writer is None:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.writer = cv2.VideoWriter(self.outputVideoPath, fourcc, 30,
                                          (self.frameWidth, self.frameHeight), True)

    def frameAdjustmentsforOutput(self):
        # resizing and colour adjustments
        self.frame = imutils.resize(VideoStreamConnection(self.cameraAvailable).getVidStream(), width=1000)
        self.rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        if self.frameWidth is None or self.frameHeight is None:
            (self.frameWidth, self.frameHeight) = self.frame.shape[:2]
            print(self.frameWidth, self.frameHeight)
