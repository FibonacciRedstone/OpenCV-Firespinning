import Utility as util
import speech_recognition as sr
from enum import Enum
import threading

class VoiceControlInterface:
    voiceProperties = {}
    propertyTypes = {}
    voiceInputArray = []
    aliases = {"enable" : "set _ to true", "disable" : "set _ to false"}

    def __init__(self, enableDictation=True):
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

        if len(commands) <= 1:
            return

        for alias in self.aliases:
            if alias in commands:
                index = commands.index(alias)
                commandString = self.getCommandFromAlias(alias, commands[index+1])
                commands = commandString.split()
                break

        for action in VoiceAction:
            if action.name.lower() in commands:
                startingIndex = commands.index(action.name.lower())
                commands = commands[startingIndex + 1:]
                action.value[1](self, commands)
                return

        print("No command executed")



    def getCommandFromAlias(self, alias, propertyName):

        for aliasString, commandString in self.aliases.items():
            if alias == aliasString:
                command = commandString.replace("_", propertyName)
                return command

        return None


    def getVoiceActionFromString(self, actionString):
        commandAction = None

        for action in VoiceAction:
            if action.name.lower() == actionString.lower():
                commandAction = action
                break
        if commandAction is None:
            raise Exception("Voice Action(", actionString, ") does not exist!")
        else:
            return commandAction


    def getPropertyValue(self, propertyName):
        try:
            return self.voiceProperties[propertyName]
        except:
            raise Exception("Invalid Property Name")


    def createProperty(self, propertyName, propertyType, initalValue):

        self.voiceProperties[propertyName] = initalValue
        self.propertyTypes[propertyName] = propertyType



    def createActionAlias(self, aliasName, actionName, actionValue):

        if len(aliasName) <= 0:
            raise Exception("Could not create alias, empty alias name")

        if not self.actionExists(actionName):
            raise Exception("Could not create alias, action does not exist")

        aliasString = aliasName + " {}"
        actionString = actionName




    def actionExists(self, actionName):
        try:
            _ = self.getVoiceActionFromString(actionName)
            return True
        except:
           return False

    def SET(self, remainingWordData):
        toIndex = -1
        if "to" in remainingWordData:
            toIndex = remainingWordData.index("to")
            propertyWords = remainingWordData[:toIndex]
        else:
            #Sometimes Speech recognizes "to 40" as "2:40", This fixes that
            for word in remainingWordData:
                if ":" in word:
                    colonIndex = word.index(":")
                    toIndex = remainingWordData.index(word)
                    propertyWords = remainingWordData[:toIndex]
                    remainingWordData.append(word[colonIndex+1:])
                    break

        if toIndex == -1:
            return

        propertyName = ""
        for word in propertyWords:
            propertyName += (word + "_")
        propertyName = propertyName[:-1]

        #Add possibility for negative numbers
        if remainingWordData[toIndex+1] == "negative" and self.voiceProperties[propertyName] == "int":
            propertyValue = remainingWordData[toIndex+2]
        else:
            propertyValue = remainingWordData[toIndex+1]

        self.setPropertyValue(propertyName, propertyValue)



    def setPropertyValue(self, propName, propValue):

        if propName not in self.voiceProperties:
            print("Property ", propName, " does not exist!")
            return

        propertyType = self.propertyTypes[propName]

        if propertyType == "bool":
            setterValue = util.stringToBool(propValue)

        elif propertyType == "int":
            if propValue == "zero":
                propValue = "0"
            setterValue = int(propValue)

        elif propertyType == "string":
            setterValue = propValue

        else:
            raise Exception("Invalid property name: ", propName)

        self.voiceProperties[propName] = setterValue
        print("Set " + propName + " to " + str(setterValue))

class VoiceAction(Enum):
    SET = ("set", VoiceControlInterface.SET)