import cv2
import numpy as np
import Utility as util


class HSVCalibrator:

    windowTitle = "Calibration Window"
    useCustomROI = False

    drawingCustomContour = False
    lastX, lastY = -1, -1
    contourPointArray = []
    currentCalibrationImage = None
    currentROI = None

    def __init__(self,capturePort=0, windowSize=(600, 600)):
        fps = 60
        self.videoCapture = util.initializeVideoCapture(capturePort, windowSize[0], windowSize[1], fps)
        self.windowSize = windowSize


    def updateCalibrationImage(self):
        global currentCalibrationImage, currentROI
        if currentCalibrationImage is not None:
            # Draw Polygon
            pts = np.array(contourPointArray, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(currentCalibrationImage, [pts], True, (0, 255, 255))

            # Gets selected area only
            mask = np.zeros((currentCalibrationImage.shape[0], currentCalibrationImage.shape[1]))

            cv2.fillPoly(mask, [pts], 1)
            mask = mask.astype(np.bool)

            outputImage = np.zeros_like(currentCalibrationImage)

            (x, y, width, height) = cv2.boundingRect(pts)

            backgroundColor = (0, 255, 0)

            # Use Color from inside hand to eliminate false range
            outputImage[:] = backgroundColor
            outputImage[mask] = currentCalibrationImage[mask]

            # Crops to get ROI
            roi = outputImage[y:(y + height), x:(x + width)]
            currentROI = roi

    def setCurentMousePosition(self, event, x, y, flags, param):
        global lastX, lastY, drawingCustomContour, contourPointArray, currentCalibrationImages
        if event == cv2.EVENT_LBUTTONDOWN:

            drawingCustomContour = not drawingCustomContour

            if not drawingCustomContour:
                self.updateCalibrationImage()
            print("Is Drawing: " + str(drawingCustomContour))

        if event == cv2.EVENT_MOUSEMOVE:
            if drawingCustomContour:
                if lastX != x or lastY != y:
                    contourPointArray.append((x, y))
                    lastX = x
                    lastY = y

    def calibrateHSVRange(self):

        cv2.namedWindow(self.windowTitle)
        cv2.moveWindow(self.windowTitle, 350, 100)
        # cv2.resizeWindow(windowTitle, windowSize[0], windowSize[1])
        util.bringWindowToFront()

        rectX = self.windowSize[0] - 150
        rectY = 150
        rectW = 30
        rectH = 30

        while True:
            # Capture Calibration Image
            currentFrame = self.videoCapture.read()[1]
            currentFrame = cv2.flip(currentFrame, 1)
            frameWidth = currentFrame.shape[0]
            cv2.putText(currentFrame, "Skin Tone Calibration", ((frameWidth // 2) - 100, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (255, 255, 255))

            if not self.useCustomROI:
                cv2.putText(currentFrame, "Fill Rectangle and press \"C\" to calibrate", ((frameWidth // 2) - 95, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 255, 255))
                cv2.rectangle(currentFrame, (rectX, rectY), (rectX + rectW, rectY + rectH), (0, 255, 0), 2)

            cv2.imshow(self.windowTitle, cv2.resize(currentFrame, self.windowSize))
            # Capture Frame

            key = cv2.waitKey(30)

            if key & 0xFF == ord('q'):
                print("Quitting....")
                break
            if key & 0xFF == ord('r'):
                print("Restarting....")
                util.restartProgram()
            if key & 0xFF == ord('c'):
                currentCalibrationImage = currentFrame
                if not self.useCustomROI:
                    currentROI = currentCalibrationImage[rectY: rectY + rectH, rectX: rectX + rectW]

                break

        # Create custom calibration ROI
        if self.useCustomROI:
            cv2.setMouseCallback(self.windowTitle, self.setCurentMousePosition)
            cv2.waitKey(30)

        # cv2.imshow("ROI", currentROI)

        if self.useCustomROI:
            key = cv2.waitKey()
            if key & 0xFF == ord('c'):
                print("Custom Roi Created")

        print("Roi Created")
        hsvROI = cv2.cvtColor(currentROI, cv2.COLOR_BGR2HSV)

        backgroundPixelColor = np.uint8([[[0, 255, 0]]])
        backgroundPixelHSV = cv2.cvtColor(backgroundPixelColor, cv2.COLOR_BGR2HSV)

        minH = 180
        minS = 255
        minV = 255

        maxH = 0
        maxS = 0
        maxV = 0

        # Row
        for y in hsvROI:
            # Column
            for x in y:

                if tuple(x) != tuple(backgroundPixelHSV[0][0]):
                    hValue = x[0]
                    sValue = x[1]
                    vValue = x[2]
                    if hValue < minH:
                        minH = hValue
                    elif hValue > maxH:
                        maxH = hValue

                    if sValue < minS:
                        minS = sValue
                    elif sValue > maxS:
                        maxS = sValue

                    if vValue < minV:
                        minV = vValue
                    elif vValue > maxV:
                        maxV = vValue

        cv2.destroyWindow(self.windowTitle)
        return minH, minS, minV, maxH, maxS, maxV
