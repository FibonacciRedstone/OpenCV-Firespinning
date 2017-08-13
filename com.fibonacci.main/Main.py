import cv2

import ActionMethods
import Utility as util
from HSVCalibrator import HSVCalibrator
from VoiceControlInterface import VoiceControlInterface
from WebcamVideoStream import WebcamVideoStream

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
enableDictation = True

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


def createSettingsTrackbars():
    cv2.namedWindow(windowTitle)

    cv2.createTrackbar("Rotation Speed", windowTitle, abs(rotationAmount), 90, updateRotationSpeed)
    cv2.createTrackbar("Disable Accidental Face Detection", windowTitle, int(disableMistakenFace), 1,
                       updateDisableMistakenFace)
    cv2.createTrackbar("Enable Debug Mode", windowTitle, int(showDebugView), 1, updateShowDebug)


def detectHandViaHSV(videoCapture, hsvRange, voiceInput, isThreaded=False):
    global currentRotationAngle, showDebugView
    cv2.namedWindow(windowTitle)
    cv2.moveWindow(windowTitle, 350, 100)
    util.bringWindowToFront()

    if displaySettings:
        createSettingsTrackbars()

    while (True):
        # Capture frame-by-frame
        try:
            showDebugView = voiceInput.getPropertyValue("debug")
            rotationAmount = voiceInput.getPropertyValue("rotation_speed")
        except:
            print("Unable to recieve voice properties")

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
            try:
                palmX = int(moment["m10"] / moment["m00"])
                palmY = int(moment["m01"] / moment["m00"])
            except ZeroDivisionError:
                palmX = 0
                palmY = 0

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
            voiceInterface.enableVoiceDictation = False
            if isThreaded:
                videoCapture.stop()
            else:
                videoCapture.release()
            cv2.destroyAllWindows()
            raise SystemExit
        if key & 0xFF == ord('r'):
            print("Restarting....")
            util.restartProgram()


calibrator = HSVCalibrator(0, windowSize)
hsvRange = calibrator.calibrateHSVRange()

threadedVideoCapture = WebcamVideoStream(windowSize=windowSize).start()
calibrator.videoCapture.release()

voiceInterface = VoiceControlInterface()

# Create Properties
voiceInterface.createProperty("debug", "bool", False)
voiceInterface.createProperty("rotation_speed", "int", -30)
voiceInterface.createProperty("effect", "list", (["Hello", "World", "Goodbye", "Hell"], 0))

# Create Actions
voiceInterface.createVoiceAction("SET", ActionMethods.SET)
voiceInterface.createVoiceAction("INDEX", ActionMethods.INDEX)

# Create Aliases
voiceInterface.createActionAlias("enable", "set _ to true")
voiceInterface.createActionAlias("disable", "set _ to false")

voiceInterface.createActionAlias("first", "index _ to 0")
voiceInterface.createActionAlias("next", "index _ to [i+1]", True)
voiceInterface.createActionAlias("previous", "index _ to [i-1]", True)

detectHandViaHSV(threadedVideoCapture, hsvRange, voiceInterface, True)
cv2.destroyAllWindows()

threadedVideoCapture.stop()
