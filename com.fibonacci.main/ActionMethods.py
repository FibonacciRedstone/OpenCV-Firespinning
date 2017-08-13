import Utility as util
from VoiceControlInterface import VoiceControlInterface


# remainingWordData = list of words after the action name is called.
def SET(voiceInterface: VoiceControlInterface, remainingWordData):
    # Command: set [property] to [value]

    try:
        toIndex = util.getToIndex(remainingWordData)
    except:
        return
    propertyName = util.getPropertyNameBeforeIndex(remainingWordData, toIndex)

    # Add possibility for negative numbers
    if remainingWordData[toIndex + 1] == "negative" and voiceInterface.getPropertyType(propertyName) == "int":
        propertyValue = "-" + remainingWordData[toIndex + 2]
    else:
        propertyValue = remainingWordData[toIndex + 1]

    voiceInterface.setPropertyValue(propertyName, propertyValue)


def INDEX(voiceInterface: VoiceControlInterface, remainingWordData):
    # Sets current index of list
    # Command: index [listProperty] to [indexNumber]
    try:
        toIndex = util.getToIndex(remainingWordData)
    except:
        return
    listName = util.getPropertyNameBeforeIndex(remainingWordData, toIndex)

    if voiceInterface.getPropertyType(listName) != "list":
        print("Invalid property name")
        return

    try:
        if remainingWordData[toIndex + 1] == "negative":
            listIndex = -int(remainingWordData[toIndex + 2])
        else:
            listIndex = int(remainingWordData[toIndex + 1])
    except ValueError:
        print("Index not integer")
        return

    # List property value in form of tuple (list, currentIndex)
    list = voiceInterface.getPropertyValue(listName)[0]
    if listIndex < 0 or listIndex >= len(list):
        print("Spoken index out of bounds")
        return

    voiceInterface.setPropertyValue(listName, (list, listIndex))
