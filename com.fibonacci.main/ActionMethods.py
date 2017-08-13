from VoiceControlInterface import VoiceControlInterface


def SET(voiceInterface: VoiceControlInterface, remainingWordData):
    toIndex = -1
    if "to" in remainingWordData:
        toIndex = remainingWordData.index("to")
        propertyWords = remainingWordData[:toIndex]
    else:
        # Sometimes Speech recognizes "to 40" as "2:40", This fixes that
        for word in remainingWordData:
            if ":" in word:
                colonIndex = word.index(":")
                toIndex = remainingWordData.index(word)
                propertyWords = remainingWordData[:toIndex]
                remainingWordData.append(word[colonIndex + 1:])
                break

    if toIndex == -1:
        return

    propertyName = ""
    for word in propertyWords:
        propertyName += (word + "_")
    propertyName = propertyName[:-1]

    # Add possibility for negative numbers
    if remainingWordData[toIndex + 1] == "negative" and voiceInterface.getPropertyType(propertyName) == "int":
        propertyValue = "-" + remainingWordData[toIndex + 2]
    else:
        propertyValue = remainingWordData[toIndex + 1]

    voiceInterface.setPropertyValue(propertyName, propertyValue)
