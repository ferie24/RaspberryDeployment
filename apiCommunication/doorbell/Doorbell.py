import csv
import cv2
import datetime
import dlib
import time
from itertools import zip_longest

import imutils
import numpy as np
from imutils.video import FPS

from apiCommunication.doorbell.config import config
from apiCommunication.doorbell.centroidtracker import CentroidTracker
from apiCommunication.doorbell.notification import Notification
from apiCommunication.doorbell.trackableobject import TrackableObject
from apiCommunication.doorbell.VideoStreamConnection import VideoStreamConnection


# --prototxt mobilenet_ssd/MobileNetSSD_deploy.prototxt --model mobilenet_ssd/MobileNetSSD_deploy.caffemodel
class DoorBell:
    def __init__(self):
        self.cameraStreamAvailable = False
        self.t0 = time.time()
        self.rgb = None
        self.fps = None
        self.pathToCaffeProtoTxt = "apiCommunication/doorbell/mobilenet_ssd/MobileNetSSD_deploy.prototxt"
        self.pathToModel = "apiCommunication/doorbell/mobilenet_ssd/MobileNetSSD_deploy.caffemodel"
        self.confidence = 0.4  # default
        self.skipFrames = 15
        self.classes = ["background", "aeroplane", "bicycle", "bird", "boat",
                        "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
                        "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
                        "sofa", "train", "tvmonitor"]
        self.videoStream = None
        self.netModel = None
        self.frameWidth = None
        self.frameHeight = None
        self.ct = CentroidTracker(maxDisappeared=40, maxDistance=50)
        self.trackers = []
        self.trackableObjects = {}
        self.totalFrames = 0
        self.totalDown = 0
        self.totalUp = 0
        self.x = []
        self.empty = []
        self.empty1 = []
        self.writer = None

    def loadModel(self):
        self.netModel = cv2.dnn.readNetFromCaffe(self.pathToCaffeProtoTxt, self.pathToModel)

    def vidstream(self):
        return VideoStreamConnection(self.cameraStreamAvailable).getVidStream()

    def startFPS(self):
        self.fps = FPS().start()
        # if config.Thread:
        #    vs = thread.ThreadingClass(config.url)
        frameWidth = None
        frameHeight = None
        temp = VideoStreamConnection(self.cameraStreamAvailable).connectCamera()

        while True:
            # gets Vidstream
            ret, frame = temp.read()
            vidStreamFrame = imutils.resize(frame, width=1000)
            frame = vidStreamFrame
            rgb = cv2.cvtColor(vidStreamFrame, cv2.COLOR_BGR2RGB)
            if frameWidth is None or frameHeight is None:
                frameWidth, frameHeight = vidStreamFrame.shape[:2]
                (self.frameWidth, self.frameHeight) = vidStreamFrame.shape[:2]
            status = "Waiting"
            rects = []
            if self.totalFrames % self.skipFrames == 0:
                status = "Detecting"
                self.trackers = []
                blob = cv2.dnn.blobFromImage(image=vidStreamFrame, scalefactor=0.007843,
                                             size=(self.frameWidth, self.frameHeight), mean=127.5)
                self.netModel.setInput(blob)
                detections = self.netModel.forward()

                for i in np.arange(0, detections.shape[2]):
                    confidence = detections[0, 0, i, 2]
                    if confidence > self.confidence:

                        idx = int(detections[0, 0, i, 1])

                        if self.classes[idx] != "person" or self.classes[idx] != "car":
                            continue

                        box = detections[0, 0, i, 3:7] * np.array(
                            [self.frameWidth, self.frameHeight, self.frameWidth, self.frameHeight])
                        (startX, startY, endX, endY) = box.astype("int")
                        tracker = dlib.correlation_tracker()
                        rect = dlib.rectangle(startX, startY, endX, endY)
                        tracker.start_track(rgb, rect)
                        self.trackers.append(tracker)
            else:
                for tracker in self.trackers:
                    print("Tracking")
                    status = "Tracking"
                    tracker.update(rgb)
                    pos = tracker.get_position()
                    startX = int(pos.left())
                    startY = int(pos.top())
                    endX = int(pos.right())
                    endY = int(pos.bottom())
                    rects.append((startX, startY, endX, endY))

            cv2.line(frame, (0, frameHeight // 3), (frameWidth, frameHeight // 3), (0, 0, 0), 3)
            cv2.putText(frame, "-Prediction border - Entrance-", (10, frameHeight - ((i * 20) + 200)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            x = []
            objects = self.ct.update(rects)
            for (objectID, centroid) in objects.items():
                trackableObject = self.trackableObjects.get(objectID, None)
                if trackableObject is None:
                    trackableObject = TrackableObject(objectID, centroid)
                else:
                    y = [c[1] for c in trackableObject.centroids]
                    direction = centroid[1] - np.mean(y)
                    trackableObject.centroids.append(centroid)
                    if not trackableObject.counted:
                        if direction < 0 and centroid[1] < self.frameHeight // 2:
                            self.totalUp += 1
                            self.empty.append(self.totalUp)
                            trackableObject.counted = True
                            return True
                            Notification().notify("Kekse", "Kekse")

                        elif direction > 0 and centroid[1] > self.frameHeight // 2:
                            self.totalDown += 1
                            self.empty1.append(self.totalDown)
                            if sum(x) >= config.Threshold:
                                cv2.putText(vidStreamFrame, "-ALERT: People limit exceeded-",
                                            (10, vidStreamFrame.shape[0] - 80),
                                            cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 2)
                                if config.ALERT:
                                    Notification().notify("Kekse", "Kekse")
                                    print("[INFO] Alert sent")
                            trackableObject.counted = True

                        x.append(len(self.empty1) - len(self.empty))
                    # print("Total people inside:", x)
                self.trackableObjects[objectID] = trackableObject
                text = "ID {}".format(objectID)
                cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                cv2.circle(frame, (centroid[0], centroid[1]), 4, (255, 255, 255), -1)
            info = [
                ("Exit", self.totalUp),
                ("Enter", self.totalDown),
                ("Status", status),
            ]
            info2 = [
                ("Total people inside", x),
            ]
            for (i, (k, v)) in enumerate(info):
                text = "{}: {}".format(k, v)
                cv2.putText(frame, text, (10, frameHeight - ((i * 20) + 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0),
                            2)

            for (i, (k, v)) in enumerate(info2):
                text = "{}: {}".format(k, v)
                cv2.putText(frame, text, (265, frameHeight - ((i * 20) + 60)), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            (255, 255, 255), 2)
            if config.Log:
                datetimee = [datetime.datetime.now()]
                d = [datetimee, self.empty1, self.empty, x]
                export_data = zip_longest(*d, fillvalue='')
                with open('Log.csv', 'w', newline='') as myfile:
                    wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
                    wr.writerow(("End Time", "In", "Out", "Total Inside"))
                    wr.writerows(export_data)
            if self.writer is not None:
                self.writer.write(vidStreamFrame)

            cv2.imshow("Real-Time Monitoring/Analysis Window", vidStreamFrame)
            if cv2.waitKey(20) & 0xFF == ord('q'):
                break
            self.totalFrames += 1
            self.fps.update()
            if config.Timer:
                t1 = time.time()
                num_seconds = (t1 - self.t0)
                if num_seconds > 28800:
                    break
        self.videoStream.release()
        cv2.destroyAllWindows()

    def run(self):
        self.loadModel()
        self.startFPS()


D = DoorBell()
D.run()
