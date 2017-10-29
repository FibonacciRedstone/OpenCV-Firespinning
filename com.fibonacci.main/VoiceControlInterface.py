import threading

import speech_recognition as sr

global opencvIsInstalled
try:
    import cv2

    opencvIsInstalled = True
except ImportError:
    print("OpenCV is not installed, no trackbar support!")
    opencvIsInstalled = False

import Utility as util


class VoiceControlInterface:

    def __init__(self, enableDictation=True):

        self.voiceProperties = {}
        self.propertyTypes = {}
        self.trackbarInfoDict = {}

        self.voiceInputArray = []
        self.aliases = {}
        self.voiceActions = {}

        self.enableVoiceDictation = enableDictation
        self.currentThread = threading.Thread(target=self.recognizeVoice)
        self.currentThread.start()

    def recognizeVoice(self):

        if not self.enableVoiceDictation:
            return

        r = sr.Recognizer()

        r.pause_threshold = 0.05
        r.non_speaking_duration = 0.05
        # r.energy_threshold = 450

        with sr.Microphone() as source:

            print("Listening...")
            while True:

                if not self.enableVoiceDictation:
                    break

                audio = r.listen(source)

                try:
                    textFromAudio = r.recognize_google(audio)
                    if textFromAudio != "":
                        self.voiceInputArray.append(textFromAudio)
                        self.executeCommand()
                except sr.UnknownValueError:
                    print("...")
                except sr.RequestError as e:
                    print("Could not request results from Google Cloud Speech service; {0}".format(e))

    def executeCommand(self):

        lastCommand = self.voiceInputArray[-1]
        lastCommand = lastCommand.lower()
        commands = lastCommand.split()

        if len(self.voiceActions) <= 0:
            raise Exception("No Voice Actions added")

        if len(commands) <= 1:
            return

        for alias in self.aliases:
            if alias in commands:
                index = commands.index(alias)
                commandString = self.getCommandFromAlias(alias, commands[index + 1])
                commands = commandString.split()
                break

        for (actionName, actionFunction) in self.voiceActions.items():
            if actionName.lower() in commands:
                startingIndex = commands.index(actionName.lower())
                commands = commands[startingIndex + 1:]
                actionFunction(self, commands)
                return

        print("No command executed")

    def getCommandFromAlias(self, alias, propertyName):

        for (aliasString, (commandString, shouldEval)) in self.aliases.items():
            if alias == aliasString:
                command = commandString.replace("_", propertyName)
                if shouldEval:
                    expressionIndex = command.index("[")
                    endExpressionIndex = command.index("]")

                    expression = command[expressionIndex + 1: endExpressionIndex]
                    if "i" in expression:
                        if self.getPropertyType(propertyName) == "list":
                            expression = expression.replace("i", "self.voiceProperties[propertyName][1]")
                        else:
                            if self.getPropertyType(propertyName) is None:
                                return
                            expression = expression.replace("i", "self.voiceProperties[propertyName]")

                    evaluation = str(eval(expression))
                    command = command[:expressionIndex]
                    command += evaluation
                    print(command)

                return command

        return None

    def createVoiceAction(self, actionName, actionFunction):
        if actionName in self.voiceActions:
            raise Exception("Could not create voice action: Action already exists with the name \"", actionName, "\"")
        if actionFunction is None:
            raise Exception("Could not create voice action: Invalid function")
        self.voiceActions[actionName.lower()] = actionFunction

    def getPropertyValue(self, propertyName):
        try:
            return self.voiceProperties[propertyName]
        except:
            raise Exception("Invalid Property Name")

    def createProperty(self, propertyName, propertyType, initalValue, trackbarInfo=None):

        self.voiceProperties[propertyName] = initalValue
        self.propertyTypes[propertyName] = propertyType
        self.trackbarInfoDict[propertyName] = trackbarInfo

    def createActionAlias(self, aliasName, actionText, shouldEval=False):
        # Action text in form of sample command with "_" indicating property
        # Example "set _ to True"

        if len(aliasName) <= 0:
            raise Exception("Could not create alias, empty alias name")

        if len(actionText) <= 0:
            raise Exception("Could not create alias, empty action text")

        actionName = actionText.split()[0]
        if not self.actionExists(actionName):
            raise Exception("Could not create alias, action does not exist")

        self.aliases[aliasName] = (actionText, shouldEval)

    def actionExists(self, actionName):
        try:
            _ = self.voiceActions[actionName.lower()]
            return True
        except:
            return False

    def getPropertyType(self, propName):
        if propName not in self.propertyTypes:
            print("Property ", propName, " does not exist!")
            return

        return self.propertyTypes[propName]

    def setPropertyValue(self, propName, propValue):

        if propName not in self.voiceProperties:
            print("Property ", propName, " does not exist!")
            return

        propertyType = self.propertyTypes[propName]

        if propertyType == "bool":
            if type(propValue) is bool:
                setterValue = propValue
            elif type(propValue) is int:

                if propValue != 0 and propValue != 1:
                    raise Exception("Invalid value for property: ", propName)
                setterValue = bool(propValue)
            else:
                setterValue = util.stringToBool(propValue)

        elif propertyType == "int":
            if propValue == "zero":
                propValue = "0"
            setterValue = int(propValue)

        elif propertyType == "string":
            setterValue = propValue

        elif propertyType == "list":
            if type(propValue) == tuple:
                setterValue = propValue
            else:
                raise Exception("Invalid set value for type \"list\"")

        else:
            raise Exception("Invalid property name: ", propName)

        self.voiceProperties[propName] = setterValue
        global opencvIsInstalled
        if opencvIsInstalled:
            trackbarInfo = self.trackbarInfoDict[propName]
            if trackbarInfo is not None:
                trackbarName = trackbarInfo[0]
                trackbarWindowName = trackbarInfo[1]
                cv2.setTrackbarPos(trackbarName, trackbarWindowName, int(setterValue))

        print("Set " + propName + " to " + str(setterValue))
