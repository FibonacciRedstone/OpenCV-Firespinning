import cv2
from HSVCalibrator import HSVCalibrator
import Utility as util
from WebcamVideoStream import WebcamVideoStream
import _thread as thread

# To Use Logitech Webcam-
#   If not connecting, run ./fixWebcam
#   Make sure settings are set as...
#       Auto-Focus: Off
#       White-Balance: Off
#       Anti-flicker: NTSC 60Hz

global windowSize
windowSize = (600, 600)
windowTitle = "Fire Spinning!"

faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

displaySettings = True
useCustomROI = False
disableMistakenFace = False
showDebugView = False

currentRotationAngle = 0
rotationAmount = -30

maxContourSize = 60000


def updateRotationSpeed(newSpeed):
    global rotationAmount
    rotationAmount = -newSpeed
    pass


def updateDisableMistakenFace(inputInt):
    global disableMistakenFace
    disableMistakenFace = bool(inputInt)
    pass


def updateShowDebug(inputInt):
    global showDebugView
    showDebugView = bool(inputInt)
    pass


def updateEnableVoice(inputInt):
    util.enableVoiceDictation = bool(inputInt)
    if util.enableVoiceDictation is True:
        thread.start_new_thread(util.recognizeVoice, (0,))
    pass


def createSettingsTrackbars():
    cv2.namedWindow(windowTitle)

    cv2.createTrackbar("Rotation Speed", windowTitle, abs(rotationAmount), 90, updateRotationSpeed)
    cv2.createTrackbar("Disable Accidental Face Detection", windowTitle, int(disableMistakenFace), 1,
                      updateDisableMistakenFace)
    cv2.createTrackbar("Enable Debug Mode", windowTitle, int(showDebugView), 1, updateShowDebug)
    cv2.createTrackbar("Enable Voice Dictation", windowTitle, int(util.enableVoiceDictation), 1, updateEnableVoice)


def detectHandViaHSV(videoCapture, hsvRange, isThreaded=False):
    global currentRotationAngle, showDebugView
    cv2.namedWindow(windowTitle)
    cv2.moveWindow(windowTitle, 350, 100)
    util.bringWindowToFront()

    if displaySettings:
        createSettingsTrackbars()
    lastVoiceInput = ""
    while (True):
        # Capture frame-by-frame
        if util.enableVoiceDictation and len(util.voiceInputArray) > 0:
            currentVoiceInput = util.voiceInputArray[-1]
            if lastVoiceInput != currentVoiceInput:
                print(currentVoiceInput)
                if "enable debug" in currentVoiceInput:
                    showDebugView = True
                elif "disable debug" in currentVoiceInput:
                    showDebugView = False
                cv2.setTrackbarPos("Enable Debug Mode", windowTitle, int(showDebugView))
                lastVoiceInput = currentVoiceInput

        if isThreaded:
            frame = videoCapture.read()
        else:
            ret, frame = videoCapture.read()

        minValues = (hsvRange[0], hsvRange[1], hsvRange[2])
        maxValues = (hsvRange[3], hsvRange[4], hsvRange[5])

        hsvThreshed = util.thresholdFrameFromRange(frame, minValues, maxValues, cv2.COLOR_BGR2HSV, windowSize)
        blurredImage = util.blurFrame(hsvThreshed, 5, 5)

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, windowSize)
        if showDebugView:
            (frameWithContour, contour) = util.findLargestContour(blurredImage, frame, maxContourSize, True)
        else:
            (frameWithContour, contour) = util.findLargestContour(blurredImage, frame, maxContourSize)

        shouldDraw = True

        # Bounding Boxes in the form of (x, y, w, h)
        if contour is None:
            handBoundingBox = (0, 0, 0, 0)
            vertexNum = 0
            shouldDraw = False
        else:
            handBoundingBox = cv2.boundingRect(contour)
            hullContour = cv2.convexHull(contour)
            vertexNum = util.getNumberOfVertices(hullContour)

            moment = cv2.moments(contour)

            palmX = int(moment["m10"] / moment["m00"])
            palmY = int(moment["m01"] / moment["m00"])

        if disableMistakenFace:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = faceCascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=3,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )

            if len(faces) > 0:
                faceBoundingBox = faces[0]
                if showDebugView:
                    frameWithContour = util.drawRectFromBoundingBox(frameWithContour, faceBoundingBox, (0, 255, 0), 2)
                if util.boundingBoxesAreOverlapping(handBoundingBox, faceBoundingBox):
                    shouldDraw = False

        # Draw Debug Data

        if showDebugView:
            # draw the contour and center of the shape on the image
            cv2.circle(frameWithContour, (palmX, palmY), 7, (255, 255, 255), -1)
            cv2.drawContours(frameWithContour, [hullContour], 0, (255, 0, 255), 5)
            frameWithContour = util.drawRectFromBoundingBox(frameWithContour, handBoundingBox, (255, 0, 0), 2)

            # hull = cv2.convexHull(contour, returnPoints=False)
            # convexDefects = cv2.convexityDefects(contour, hull)
            #
            # for i in range(convexDefects.shape[0]):
            #     s, e, f, d = convexDefects[i, 0]
            #     start = tuple(contour[s][0])
            #     end = tuple(contour[e][0])
            #     far = tuple(contour[f][0])
            #     cv2.line(frameWithContour, start, far, [0, 0, 255], 2)
            #     cv2.line(frameWithContour, far, end, [0, 0, 255], 2)
            #
            #     cv2.circle(frameWithContour, start, 3, [255, 255, 255], 3)

        if vertexNum > 6 or vertexNum < 3:
            shouldDraw = False

        if shouldDraw:

            newLength = handBoundingBox[2]

            (frameWidth, frameHeight, _) = frameWithContour.shape

            originX = palmX - (newLength / 2)
            originY = palmY - (newLength / 2)

            if (originX < 0):
                originX = 0
            if (originY < 0):
                originY = 0

            if (originX + newLength) > frameWidth:
                difference = ((originX + newLength) - frameWidth)
                newLength -= difference
            if (originY + newLength) > frameWidth:
                difference = ((originY + newLength) - frameWidth)
                newLength -= difference

            if newLength > 0:
                fireBallImage = cv2.imread("fireballAlpha.png", cv2.IMREAD_UNCHANGED)

                currentRotationAngle += rotationAmount

                frameWithContour = util.drawImageOverFrame(fireBallImage, frameWithContour, (originX, originY),
                                                           newLength,
                                                           newLength, True, currentRotationAngle)

        cv2.imshow(windowTitle, frameWithContour)

        key = cv2.waitKey(30)
        if key & 0xFF == ord('q'):
            print("Quitting....")
            cv2.destroyAllWindows()
            if isThreaded:
                videoCapture.stop()
            else:
                videoCapture.release()
            quit(0)
        if key & 0xFF == ord('r'):
            print("Restarting....")
            util.restartProgram()


calibrator = HSVCalibrator(0, windowSize)
hsvRange = calibrator.calibrateHSVRange()

threadedVideoCapture = WebcamVideoStream(windowSize=windowSize).start()
calibrator.videoCapture.release()

if util.enableVoiceDictation:
    thread.start_new_thread(util.recognizeVoice, (0,))
    detectHandViaHSV(threadedVideoCapture, hsvRange, True)
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Goodbye...")
else:
    detectHandViaHSV(threadedVideoCapture, hsvRange, True)
    cv2.destroyAllWindows()

threadedVideoCapture.stop()
