
    

#Простая погоня, беглец видит охотников
def SimpleChase(USER_BASE, VG, gameID):
    allData = []

    for user in USER_BASE:
        _user = USER_BASE[user]
        if _user["gameID"] == gameID:
            #(9, '2172398289631200982', '51.046268731938646', '23.84547833037405', '1407690957.446274', '85301419')
            data = VG.getLastUserCoords(gameID, _user["uID"])
            if data != None:
                allData.append(_user["pseudonime"] + ":" + ":".join(data[1:]))

    result = "\n".join(allData).encode()
    return result

# ===============================================================================

def FootPrintHunt(USER_BASE, VG, gameID):
    pass


def HideNSeek(USER_BASE, VG, gameID):
    pass


def RandomRide(USER_BASE, VG, gameID):
    pass



GAMETYPES = {
             "SimpleChase" : SimpleChase,
             "FootPrintHunt" : FootPrintHunt,
             "HideNSeek" : HideNSeek,
             "RandomRide" : RandomRide
            }


import configparser
config = configparser.RawConfigParser()
#Для того, чтобы сделать имена опций не в lower-case
config.optionxform = str
config.read('GameRules.cfg')
gameSets = config.sections()

def getGameSets():
    return {gameSet:{
                     "name": config.get(gameSet, "Name"),
                     "comment": config.get(gameSet, "Comment")
                    } for gameSet in gameSets}


def getSetConfig(setName):
    if setName in gameSets:
        return {option:config.get(setName, option) for option in config.options(setName)}
    else:
        return None
