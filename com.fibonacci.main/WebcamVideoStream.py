from threading import Thread
import cv2
import Utility as util

class WebcamVideoStream:

    def __init__(self, srcPort=0, windowSize = (600, 600), fps=60):

        self.stream = util.initializeVideoCapture(srcPort, windowSize[0], windowSize[1], fps)
        (self.isGrabbed, self.frame) = self.stream.read()

        self.stopped = False

    def start(self):
        # start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                return

            # otherwise, read the next frame from the stream
            (self.isGrabbed, self.frame) = self.stream.read()

    def read(self):
        # return the frame most recently read
        return self.frame

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True