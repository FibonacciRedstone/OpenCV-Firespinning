import os
import sys
from enum import Enum
from platform import system as platform

import cv2
import numpy as np


def bringWindowToFront(windowName="Python"):
    if platform() == 'Darwin':  # How Mac OS X is identified by Python
        os.system(
            '''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "%s" to true' ''' % windowName)


def restartProgram():
    os.execv(sys.executable, ['python3'] + sys.argv)


def areaOfIntersectingRects(aExtremeValues, bExtremeValues):  # returns None if rectangles don't intersect

    (aMinX, aMinY, aMaxX, aMaxY) = aExtremeValues
    (bMinX, bMinY, bMaxX, bMaxY) = bExtremeValues

    dx = min(aMaxX, bMaxX) - max(aMinX, bMinX)
    dy = min(aMaxY, bMaxY) - max(aMinY, bMinY)
    if (dx >= 0) and (dy >= 0):
        return dx * dy
    return 0


def drawImageOverFrame(image, frame, origin, width, height, withAlpha=False, rotationAngle=None):
    (x1, y1) = origin

    x1 = int(x1)
    y1 = int(y1)
    width = int(width)
    height = int(height)

    x2 = x1 + width
    y2 = y1 + height

    resizedImage = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    if rotationAngle is not None:
        rotationMatrix = cv2.getRotationMatrix2D((width / 2, height / 2), int(rotationAngle), 1)
        resizedImage = cv2.warpAffine(resizedImage, rotationMatrix, (width, height))

    if withAlpha:
        alpha_s = resizedImage[:, :, 3] / 255.0
        alpha_l = 1.0 - alpha_s

        for c in range(0, 3):
            try:

                frame[y1:y2, x1:x2, c] = (alpha_s * resizedImage[:, :, c] + alpha_l * frame[y1:y2, x1:x2, c])
            except ValueError as e:
                print("Something went wrong: " + e.message)
    else:
        frame[y1: y2, x1: x2] = resizedImage
    return frame


def findLargestContour(inputFrame, outputFrame, maxContourArea=None, shouldDraw=False):
    (_, contours, _) = cv2.findContours(inputFrame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    returnFrame = outputFrame
    largestContourIndex = 0

    for index in range(1, len(contours)):
        currentContourArea = cv2.contourArea(contours[index])
        if currentContourArea > cv2.contourArea(contours[largestContourIndex]):
            if maxContourArea is not None:
                if currentContourArea <= maxContourArea:
                    largestContourIndex = index
            else:
                largestContourIndex = index

    if len(contours) > 0:
        if shouldDraw:
            cv2.drawContours(returnFrame, contours, largestContourIndex, (0, 255, 0), 1)
    else:
        emptyArray = np.array([[]])
        return (returnFrame, None)
    return (returnFrame, contours[largestContourIndex])


def thresholdFrameFromRange(inputFrame, minValues, maxValues, filter, resizeSize=None):
    if len(minValues) != 3:
        raise Exception("Not enough minimum values: 3 needed, " + str(len(minValues)) + " found.")
    if len(maxValues) != 3:
        raise Exception("Not enough maximum values: 3 needed, " + str(len(maxValues)) + " found.")

    # Min Filter Values
    minF1 = minValues[0]
    minF2 = minValues[1]
    minF3 = minValues[2]

    # Max Filter Values
    maxF1 = maxValues[0]
    maxF2 = maxValues[1]
    maxF3 = maxValues[2]

    returnFrame = cv2.cvtColor(inputFrame, filter)
    returnFrame = cv2.flip(returnFrame, 1)

    if resizeSize is not None:
        returnFrame = cv2.resize(returnFrame, resizeSize)

    lowerBound = np.array([minF1, minF2, minF3], dtype=np.uint8)
    upperBound = np.array([maxF1, maxF2, maxF3], dtype=np.uint8)
    returnFrame = cv2.inRange(returnFrame, lowerBound, upperBound)

    return returnFrame


def blurFrame(inputFrame, blurSize, elementSize):
    returnFrame = cv2.medianBlur(inputFrame, blurSize)
    element = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * elementSize + 1, 2 * elementSize + 1),
                                        (elementSize, elementSize))
    cv2.dilate(returnFrame, element)
    return returnFrame


def boundingBoxesAreOverlapping(boundingBox1, boundingBox2, marginOfError=0.30):
    (bbx, bby, bbw, bbh) = boundingBox1

    bbx2 = bbx + bbw
    bby2 = bby + bbh

    (bb2x, bb2y, bb2w, bb2h) = boundingBox2
    bb2x2 = bb2x + bb2w
    bb2y2 = bb2y + bb2h

    boundingBox1Area = bbw * bbh
    boundingBox2Area = bb2w * bb2h
    overlappingArea = areaOfIntersectingRects(
        (bbx, bby, bbx2, bby2),
        (bb2x, bb2y, bb2x2, bb2y2)
    )

    if boundingBox1Area >= boundingBox2Area:
        overlapPercentage = float(overlappingArea) / float(boundingBox2Area)
    else:
        overlapPercentage = float(overlappingArea) / float(boundingBox1Area)

    # If covering (marginOfError * 100)% or more of the smallest box
    if overlapPercentage >= marginOfError:
        return True

    return False


def drawRectFromBoundingBox(inputFrame, boundingBox, color, thickness=None, lineType=None, shift=None):
    (x, y, w, h) = boundingBox
    x2 = x + w
    y2 = y + h

    returnFrame = inputFrame

    # Perform Changes
    if thickness is None:
        if lineType is None:
            if shift is None:
                cv2.rectangle(returnFrame, (x, y), (x2, y2), color)
            else:
                cv2.rectangle(returnFrame, (x, y), (x2, y2), color, shift=shift)
        else:
            if shift is None:
                cv2.rectangle(returnFrame, (x, y), (x2, y2), color, lineType=lineType)
            else:
                cv2.rectangle(returnFrame, (x, y), (x2, y2), color, lineType=lineType, shift=shift)
    else:
        if lineType is None:
            if shift is None:
                cv2.rectangle(returnFrame, (x, y), (x2, y2), color, thickness)
            else:
                cv2.rectangle(returnFrame, (x, y), (x2, y2), color, thickness, shift=shift)
        else:
            if shift is None:
                cv2.rectangle(returnFrame, (x, y), (x2, y2), color, thickness, lineType=lineType)
            else:
                cv2.rectangle(returnFrame, (x, y), (x2, y2), color, thickness, lineType=lineType, shift=shift)

    return returnFrame


def initializeVideoCapture(capturePort, width, height, fps):
    capture = cv2.VideoCapture(capturePort)
    # Set Width and Height of video
    capture.set(3, width)
    capture.set(4, height)
    # Set FPS
    capture.set(5, fps)
    return capture


def getNumberOfVertices(inputContour):
    perimeter = cv2.arcLength(inputContour, True)
    approximation = cv2.approxPolyDP(inputContour, 0.04 * perimeter, True)

    return len(approximation)

def stringToBool(inputString):
    text = str.lower(inputString)
    if text == "true":
        return True
    return False


def addCasesToEnum(inputEnum: Enum, inputEnumName, newNameArray, newValueArray=None):
    if len(inputEnumName) <= 0:
        raise Exception("Invalid Enum Name")

    if newValueArray is not None:
        if len(newNameArray) != len(newValueArray):
            raise Exception("Different sized name and value arrays")

    outputCaseArray = []

    for case in inputEnum:
        outputCaseArray.append((case.name, case.value))

    if newValueArray is None:
        outputCaseArray += newNameArray
    else:
        for newName in newNameArray:
            currentIndex = newNameArray.index(newName)
            outputCaseArray.append((newName, newValueArray[currentIndex]))

    outputEnum = Enum(inputEnumName, outputCaseArray, module=__name__)
    return outputEnum


def getToIndex(remainingWordData):
    toIndex = -1
    if "to" in remainingWordData:
        toIndex = remainingWordData.index("to")
    else:
        # Sometimes Speech recognizes "to 40" as "2:40", This fixes that


        for word in remainingWordData:
            if ":" in word:
                colonIndex = word.index(":")
                toIndex = remainingWordData.index(word)
                remainingWordData.append(word[colonIndex + 1:])
                break

            if word == "2":
                toIndex = remainingWordData.index("2")
                break

        if "-" in remainingWordData:
            toIndex = remainingWordData.index("-")

    if toIndex == -1:
        raise Exception("To not present in word data")
    return toIndex


def getPropertyNameBeforeIndex(remainingWordData, wordIndex):
    propertyWords = remainingWordData[:wordIndex]

    propertyName = ""
    for word in propertyWords:
        propertyName += (word + "_")
    propertyName = propertyName[:-1]
    return propertyName
