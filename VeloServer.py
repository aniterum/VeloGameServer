#
# Здесь находится реализация игрового сервера,
# который будет отвечать на запросы приложений
# и отдавать данные в зависимости от типа игры
# и статуса игрока, если тип игры предусматривает
# различные данные для разных игроков
#
# Концепция сервера с asyncio взята с http://habrahabr.ru/post/217143/
#

import asyncio
import logging
import concurrent.futures
import hashlib
import zlib
import base64
import time
from VeloGameDatabase import VeloGameDatabase
import GameTypes

debug = True

GAME_DATABASE_NAME = "velogames.db"

VG = VeloGameDatabase(GAME_DATABASE_NAME)

USER_BASE = {}
#{"ip":(ip, port), "name":userName, "gameMaster":False, "gameID":None, "gameStatus":None}
USER_PSEUDONIMES = {}
#{userID:pseudonimeID}
GAMES_BASE = {}
#gameID: {type:"chase", canViewEveryone:True, gameMaster:"GameMasterIDHash"}


##MSG_DISCONNECT  = b"DISCONNECT"
##MSG_SEND_DATA   = b"SEND"       #|ZLIB(GAMEID|USERID|LAT|LON|TIME)
##MSG_GET_DATA    = b"GET"        #|USERID  -> ZLIB(USERID|LAT|LON\r\nUSERID|LAT|LON)
##MSG_HELLO       = b"HELLO"      #|USERNAME -> USERID
##MSG_CREATE_GAME = b"CREATE_GAME"#|USERID|GAMETYPE 
##MSG_JOIN_GAME   = b"JOIN_GAME"  #|USERID|GAMEID
##MSG_GET_USERS   = b"GET_USERS"  # -> ZLIB (USERID:USERNAME\r\nUSERID:USERNAME)
##MSG_GAME_START  = b"STARTGAME"  #|USERID|GAMEID

##DIVISOR = b"|"
bRN = b"\r\n"
RN = "\r\n"

PEERNAME = 'peername'

MSG_OK     = b"0" + bRN
MSG_NOCOMMAND = b"99" + bRN

MSG_NOUSER = b"10" + bRN
TXT_NOUSER = "Пир {} послал команду БЕЗ ЛОГИНА"

MSG_CANTCREATE         = b"20" + bRN
MSG_CANTREMOVE         = b"21" + bRN
MSG_NOMASTER           = b"22" + bRN
MSG_GAMENOTEXIST       = b"23" + bRN
MSG_GAMEALREADYSTARTED = b"24" + bRN
MSG_GAMENOTSTARTED     = b"25" + bRN
MSG_NOTALLREADY        = b"26" + bRN
MSG_NOSET              = b"27" + bRN


MSG_MASTERCANTJOIN     = b"30" + bRN
MSG_MASTERCANTLEAVE    = b"31" + bRN
MSG_ERRORDATASEND      = b"32" + bRN

TXT_GAMESTARTED = "Пир {} НАЧАЛ игру."
TXT_GAMESTOPPED = "Пир {} ОСТАНОВИЛ игру."






##START -> RESULT - начать созданную игру;
##STOP -> RESULT - останавливает начатую игру;
##RECONNECT:USERID -> RESULT - передключение после разрыва связи, заменит IP:PORT в данных пользователя;
##SEND(LAT, LON, TIME, uState):RESULT - отправить текущие координаты и собственное время, если вы были допущены в игру, и игра началась;
##GET:zLib(u1:(LAT, LON, uState), .... uN:(LAT, LON, uState)) - отдаёт координаты и текущий статус игрока (онлайн, оффлайн, потеряны координаты и т.д.;
##USERS:zLib(u1:(Name, GAMEROLE),  ... uN:(Name, GAMEROLE)) - даёт имена пользователей и их роли в игре.
##DISCONNECT:RESULT - разъединяет с сервером, указывает статус "оффлайн".


##HELLO:USERNAME -> USERID - подключение к серверу;
def HELLO(writer, userName):
    peername = writer.get_extra_info(PEERNAME)

    userIDHash = str(hash(peername))
    
    if userName:
        try:
            _userName = userName.decode()
            if userIDHash in USER_BASE:
                USER_BASE[peername]["name"] = _userName
            else:
                USER_BASE[peername] = {"uID":userIDHash,
                                       "name":_userName,
                                       "pseudonime": hashlib.md5(userIDHash.encode()).hexdigest(),
                                       "gameMaster":False,
                                       "gameID":None,
                                       "gameState":None,
                                       "regTime":time.time(),
                                       "readyToGame":False}
            logging.info('Пир {} ПРИСОЕДИНИЛСЯ с именем : '.format(peername) + _userName)            
            writer.write(userIDHash.encode() + bRN)
            
        except UnicodeDecodeError:
            logging.info('Пир {} задал ошибочное имя : '.format(peername))            
            writer.write(MSG_NOUSER)
    else:
        logging.info('Пир {} задал пустое имя : '.format(peername))            
        writer.write(MSG_NOUSER)

## BYE: -> отключение игрока без возможности сделать RECONNECT
def BYE(writer, empty):
    peername = writer.get_extra_info(PEERNAME)
    try:
        
        del USER_BASE[peername]
        logging.info('Пир {} удалил себя из записей игры'.format(peername))            
        writer.write(MSG_OK)
    except KeyError:
        logging.info(TXT_NOUSER.format(peername))            
        writer.write(MSG_NOUSER)


##CREATE:OPTIONS -> GAMEID - создаёт игру, в данных игрока-создателя указывается, что он её создал.
def CREATE(writer, options):
    peername = writer.get_extra_info(PEERNAME)
    try:
        USER_INFO = USER_BASE[peername]
        if not USER_INFO["gameMaster"]:
            USER_INFO["gameMaster"] = True
            gameID = "G" + hashlib.sha1(str(time.time()).encode() + b"GAMEID").hexdigest()
            USER_INFO["gameID"] = gameID
            USER_INFO["gameState"] = "player"
            GAMES_BASE[gameID] = {"settings":{},
                                  "name":"TempGameName",
                                  "gameMaster":USER_INFO["uID"],
                                  "started":False,
                                  "regtime":time.time(),
                                  "players":None}
            
            writer.write(gameID.encode() + bRN)
            logging.info('Пир {} создал игру с ID : '.format(peername) + gameID)
        else:
            logging.info('Пир {} пытался создать игру, являсь создателем другой с ID : '.format(peername) + USER_INFO["gameID"])            
            writer.write(MSG_CANTCREATE)
    except KeyError:
        logging.info(TXT_NOUSER.format(peername))            
        writer.write(MSG_NOUSER)

        
##REMOVE: -> RESULT - удаляет не начатую игру и отсоединяет всех пользователей, если команду вызвал создатель игры
def REMOVE(writer, empty):
    peername = writer.get_extra_info(PEERNAME)
    try:
        USER_INFO = USER_BASE[peername]
        if USER_INFO["gameMaster"]:
            gameID = USER_INFO["gameID"]
            if gameID in GAMES_BASE.keys():
                if not GAMES_BASE[gameID]["started"]:
                    USER_INFO["gameID"] = None
                    USER_INFO["gameMaster"] = False
                    del GAMES_BASE[gameID]
                    writer.write(MSG_OK)
                    logging.info('Пир {} удалил игру с ID : '.format(peername) + gameID)

                    for player in USER_BASE:
                        if USER_BASE[player]["gameID"] == gameID:
                            USER_BASE[player]["gameID"] = None
                            USER_INFO["readyToGame"] = False
                            USER_INFO["gameState"] = None
                            logging.info('Пир {} был удалён из игры с ID : '.format(player) + gameID)
                    
                else:
                    writer.write(MSG_CANTREMOVE)
                    logging.info('Пир {} попытался удалить начатую игру с ID : '.format(peername) + gameID)
                    
        else:
            writer.write(MSG_CANTREMOVE)
            logging.info('Пир {} попытался удалить игру без права на это'.format(peername))

    except KeyError:
        logging.info(TXT_NOUSER.format(peername))
        writer.write(MSG_NOUSER)
                            

##RENAME:NEWUSERNAME -> RESULT - изменить имя пользователя
def RENAME(writer, newUserName):
    peername = writer.get_extra_info(PEERNAME)
    try:
        USER_INFO = USER_BASE[peername]
        if len(newUserName) > 3:
            USER_INFO["name"] = newUserName.decode()
            writer.write(MSG_OK)
            logging.info('Пир {} переименован в '.format(peername) + newUserName.decode())
        else:
            logging.info('Пир {} выбрал слишком короткое имя: '.format(peername) + newUserName.decode())
        
    except KeyError:
        logging.info(TXT_NOUSER.format(peername))
        writer.write(MSG_NOUSER)


##JOIN:GAMEID -> OPTIONS - подключиться к созданной игре;
##если игра еще не началась, игрок получает статус "player",
##а если началась, то "spectrator"
def JOIN(writer, gameID):
    peername = writer.get_extra_info(PEERNAME)
    try:
        USER_INFO = USER_BASE[peername]
        if not USER_INFO["gameMaster"]:
            _gameID = gameID.decode()
            if _gameID in GAMES_BASE.keys():
                USER_INFO["gameID"] = _gameID
                if not GAMES_BASE[_gameID]["started"]:
                    USER_INFO["gameState"] = "player"
                else:
                    USER_INFO["gameState"] = "spectrator"
                writer.write(MSG_OK)
                logging.info('Пир {} присоединился к игре gameID:'.format(peername) + _gameID)
                
            else:
                logging.info('Пир {} попытался присоединиться к несуществующей игре'.format(peername))
                writer.write(MSG_GAMENOTEXIST)
        else:
            logging.info('Пир {}, создавший другую игру пытается соединиться с другой игрой'.format(peername))
            writer.write(MSG_MASTERCANTJOIN)
    except KeyError:
        logging.info(TXT_NOUSER.format(peername))
        writer.write(MSG_NOUSER)
    

##LEAVE: -> RESULT - покинуть игру, может любой, кроме мастер-пира
def LEAVE(writer, empty):
    peername = writer.get_extra_info(PEERNAME)
    try:
        USER_INFO = USER_BASE[peername]
        if not USER_INFO["gameMaster"]:
            if USER_INFO["gameID"] != None:
                _gameID = USER_INFO["gameID"]
                USER_INFO["gameID"] = None
                USER_INFO["gameState"] = None
                USER_INFO["readyToGame"] = False
                logging.info('Пир {} отключился от игры с ID: '.format(peername) + _gameID)
                writer.write(MSG_OK)
            else:
                logging.info('Пир {} попытался отключиться от игры, не подключенным к ней'.format(peername))
                writer.write(MSG_MASTERCANTLEAVE)
        else:
            logging.info('Мастер-пир {} попытался отключиться от игры'.format(peername))
            writer.write(MSG_GAMENOTEXIST)
    except KeyError:
        logging.info(TXT_NOUSER.format(peername))
        writer.write(MSG_NOUSER)
        
#READY: -> RESULT - команда, говорящая о том, что игрок готов к игре,
#а именно, найдена ли его координата GPS
def READY(writer, empty):
    peername = writer.get_extra_info(PEERNAME)
    try:
        USER_INFO = USER_BASE[peername]
        if USER_INFO["gameID"] != None:
            USER_INFO["readyToGame"] = True
            logging.info('Пир {} ГОТОВ к игре'.format(peername))
            writer.write(MSG_OK)
        else:
            logging.info('Пир {} готов в неизвестной игре'.format(peername))
            writer.write(MSG_GAMENOTEXIST)

    except KeyError:
        logging.info(TXT_NOUSER.format(peername))
        writer.write(MSG_NOUSER)
        

def UNREADY(writer, empty):
    peername = writer.get_extra_info(PEERNAME)
    try:
        USER_INFO = USER_BASE[peername]
        if USER_INFO["gameID"] != None:
            USER_INFO["readyToGame"] = False
            writer.write(MSG_OK)
        else:
            logging.info('Пир {} неготов к неизвестной игре'.format(peername))
            writer.write(MSG_GAMENOTEXIST)

    except KeyError:
        logging.info(TXT_NOUSER.format(peername))
        writer.write(MSG_NOUSER)


def SET(write, data):
    #USERPSEUDONIME:GAMESTATE
    peername = writer.get_extra_info(PEERNAME)
    try:
        USER_INFO = USER_BASE[peername]
        

    except KeyError:
        logging.info(TXT_NOUSER.format(peername))
        writer.write(MSG_NOUSER)
    

#Начинаем игру, но только если все игроки послали команду
# READY: , иначе игра не начнется
def START(writer, empty):
    peername = writer.get_extra_info(PEERNAME)
    try:
        USER_INFO = USER_BASE[peername]
        if (USER_INFO["gameMaster"] and (USER_INFO["gameID"] != None)):
            gameID = USER_INFO["gameID"]
            _game = GAMES_BASE[gameID]
            USER_INFO["readyToGame"] = True

            if not _game["started"]:

                allReady = True
                for player in USER_BASE:
                    _player = USER_BASE[player]
                    if _player["gameID"] == gameID:
                        allReady &= _player["readyToGame"]

                if allReady:
                    _game["started"] = True
                    
                    VG.createGameTable(gameID)
                    logging.info('Создана таблица базы данных', _game)

                    allPlayers = []
                
                    for player in USER_BASE:
                        _player = USER_BASE[player]
                        if _player["gameID"] == gameID:
                            allPlayers.append(_player["uID"])
                            VG.addUserData(_player["uID"], _player["name"], _player["gameID"], _player["regTime"])
                    logging.info('В базу данных занесены имена пользователей')

                    _game["players"] = allPlayers

                    _gameData = _game["name"], _game["regtime"], _game["settings"]
                    VG.addGameInfo(gameID, _gameData)
                    
                    logging.info(TXT_GAMESTARTED.format(peername))
                    writer.write(MSG_OK)
                    
                else:
                    logging.info('Пир {} пытался начать игру когда НЕ ВСЕ ИГРОКИ ГОТОВЫ'.format(peername))
                    writer.write(MSG_NOTALLREADY)
            else:
                logging.info('Пир {} попытался начать уже начатую игру'.format(peername))
                writer.write(MSG_GAMEALREADYSTARTED)
        else:
            logging.info('Пир {} попытался начать игру без мастер-прав'.format(peername))
            writer.write(MSG_NOMASTER)
        
    except KeyError:
        logging.info(TXT_NOUSER.format(peername))
        writer.write(MSG_NOUSER)


def STOP(writer, empty):
    peername = writer.get_extra_info(PEERNAME)
    try:
        USER_INFO = USER_BASE[peername]
        if (USER_INFO["gameMaster"] and (USER_INFO["gameID"] != None)):
            _game = GAMES_BASE[USER_INFO["gameID"]]
            if _game["started"]:
                _game["started"] = False
                VG.db.commit()
                writer.write(MSG_OK)
                logging.info(TXT_GAMESTOPPED.format(peername))
            else:
                logging.info('Пир {} попытался остановить неначатую игру'.format(peername))
                writer.write(MSG_GAMENOTSTARTED)
        else:
            logging.info('Пир {} попытался остановить игру без мастер-прав'.format(peername))
            writer.write(MSG_NOMASTER)
        
    except KeyError:
        logging.info(TXT_NOUSER.format(peername))
        writer.write(MSG_NOUSER)


def RECONNECT(writer, userID):
    peername = writer.get_extra_info(PEERNAME)

    if peername in USER_BASE.keys():
        logging.info('Пир {} попытался сделать реконнект, не выходя'.format(peername))
        return
    
    _userID = userID.decode()
    foundedKey = None
    for ip in USER_BASE.keys():
        if USER_BASE[ip]["uID"] == _userID:
            foundedKey = ip

    if foundedKey != None:
        USER_BASE[peername] = USER_BASE[foundedKey]
        del USER_BASE[foundedKey]
        logging.info('Pier {} reconnected with uID : '.format(peername) + _userID)
        writer.write(MSG_OK)
    else:
        writer.write(MSG_NOUSER)


def SEND(writer, data):
    #LAT:LON:TIME:(STATE:BATTERY:SIGNAL:ACCURACY)
    #xx000000 - статус игрока
    #00xx0000 - заряд батареи 00-99
    #0000xx00 - мощность сигнала GPS
    #000000xx - точность координаты 00-99
    peername = writer.get_extra_info(PEERNAME)
    try:
        USER_INFO = USER_BASE[peername]
        gameID = USER_INFO["gameID"]
        if gameID != None:
            if GAMES_BASE[gameID]["started"]:
                _data = data.decode()
                
                try:
                    lat, lon, time, status = _data.split(":")
                    float(lat)
                    float(lon)
                    float(time)

                    databaseText = USER_INFO["uID"], lat, lon, time, status
                    VG.addRawData(gameID, databaseText)
                    
                    writer.write(MSG_OK)
                    
                except ValueError:
                    logging.info('Пир {} прислал неверные данные: '.format(peername) + _data)
                    writer.write(MSG_ERRORDATASEND)
                except AttributeError:
                    logging.info('Пир {} прислал неверные данные: '.format(peername) + _data)
                    writer.write(MSG_ERRORDATASEND)
            else:
                logging.info("Пир {} шлет данные к неначатой игре".format(peername))
                writer.write(MSG_GAMENOTSTARTED)
        else:
            logging.info("Пир {} шлет данные не присоединившись к игре".format(peername))
            writer.write(MSG_GAMENOTEXIST)
            
    except KeyError:
        logging.info(TXT_NOUSER.format(peername))
        writer.write(MSG_NOUSER)


def GET(writer, empty):
    peername = writer.get_extra_info(PEERNAME)
    try:
        USER_INFO = USER_BASE[peername]
        uID = USER_INFO["uID"]
        gameID = USER_INFO["gameID"]
        _game = GAMES_BASE[gameID]
        
        if _game["started"]:
 
            gameHandler = GameTypes.GAMETYPES['SimpleChase']
            result = gameHandler(USER_BASE, VG, gameID)
            writer.write(result + bRN)

        else:
            logging.info("Пир {} запросил данные к НЕНАЧАТОЙ игре".format(peername))
            writer.write(MSG_GAMENOTSTARTED)
        
    except KeyError:
        logging.info(TXT_NOUSER.format(peername))
        writer.write(MSG_NOUSER)


##GETGAMESETS: -> id, имена и комментарии к типам игр, разделенных по \n
def GETGAMESETS(writer, empty):
    peername = writer.get_extra_info(PEERNAME)
    try:
        USER_INFO = USER_BASE[peername]
        
        sets = GameTypes.getGameSets()
        
        s = str(sets).encode() + bRN
        
        writer.write(s)
        
    except KeyError:
        logging.info(TXT_NOUSER.format(peername))
        writer.write(MSG_NOUSER)
    

def GETSETOPTIONS(writer, gameSetId):
    peername = writer.get_extra_info(PEERNAME)
    try:
        USER_INFO = USER_BASE[peername]

        options = GameTypes.getSetConfig(gameSetId.decode())

        if options != None:
            writer.write(str(options).replace("'", "").encode() + bRN)
        else:
            logging.info('Пир {} запросил настройки НЕСУЩЕСТВУЮЩЕГО СЕТА'.format(peername))
            writer.write(MSG_NOSET)

    except KeyError:
        logging.info(TXT_NOUSER.format(peername))
        writer.write(MSG_NOUSER)
    

def USERS(writer, empty):
    peername = writer.get_extra_info(PEERNAME)
    try:
        USER_INFO = USER_BASE[peername]
        _gameID = USER_INFO["gameID"]
        if _gameID != None:
            inGameUsers = []
            inGameUsersAppend = inGameUsers.append
            for user in USER_BASE:
                _user = USER_BASE[user]
                if _user["gameID"] == _gameID:
                    inGameUsersAppend(":".join([_user["pseudonime"], _user["name"], str(_user["gameState"])]))

            result = "\n".join(inGameUsers)
            #writer.write(zlib.compress(result.encode()))
            writer.write(result.encode() + bRN)
                 
            
        else:
            logging.info('Пир {} неготов к неизвестной игре'.format(peername))
            writer.write(MSG_GAMENOTEXIST)

    except KeyError:
        logging.info(TXT_NOUSER.format(peername))
        writer.write(MSG_NOUSER)

        
def DISCONNECT(writer, empty):
    peername = writer.get_extra_info(PEERNAME)
    writer.write(MSG_OK)
    logging.info('Connection from {} closed by DISCONNECT command'.format(peername))
    writer.close()



def _USERS(writer, empty):
    if debug:
        for user in USER_BASE:
            print(USER_BASE[user])
    writer.write(MSG_OK)
        
def _GAMES(writer, empty):
     if debug:
        for game in GAMES_BASE:
            print(GAMES_BASE[game])
     writer.write(MSG_OK)

def _TERMINATE(writer, empty):
    if debug:
        writer.write(MSG_OK)
        raise KeyboardInterrupt
    




MESSAGE_HANDLERS = {b"HELLO"        :HELLO,
                    b"BYE"          :BYE,
                    b"RENAME"       :RENAME,
                    b"CREATE"       :CREATE,
                    b"REMOVE"       :REMOVE,
                    b"JOIN"         :JOIN,
                    b"LEAVE"        :LEAVE,
                    b"SET"          :SET,
                    b"START"        :START,
                    b"STOP"         :STOP,
                    b"READY"        :READY,
                    b"UNREADY"      :UNREADY,
                    b"RECONNECT"    :RECONNECT,
                    b"SEND"         :SEND,
                    b"GETGAMESETS"  :GETGAMESETS,
                    b"GETSETOPTIONS":GETSETOPTIONS,
                    b"GET"          :GET,
                    b"USERS"        :USERS,
                    b"DISCONNECT"   :DISCONNECT,
                    b"_USERS"       :_USERS,
                    b"_GAMES"       :_GAMES,
                    b"_TERMINATE"   :_TERMINATE}

    

def packAndBase(text):
    compressed = zlib.compress(text.encode())
    return base64.b64encode(compressed)

def unbaseAndUnPack(basedPack):
    debased = base64.b64decode(basedPack)
    return zlib.decompress(debased)

def getCommandAndData(data):
    if data == b"\n":
        return [None, None]
    colonSymbol = data.find(b":")
    if colonSymbol == -1:
        return [None, None]
    else:
        command = data[:colonSymbol]
        params = data[colonSymbol + 1:]
        return [command, params.strip()]


#============ Запуск и работа сервера ===============

@asyncio.coroutine
def handle_connection(reader, writer):
    peername = writer.get_extra_info(PEERNAME)
    logging.info('Accepted connection from {}'.format(peername))
    while True:
        try:
            data = yield from asyncio.wait_for(reader.readline(), timeout=1000.0)
            if data:
                command, params = getCommandAndData(data)
                if ((command != None) and (command in MESSAGE_HANDLERS)):
                    func = MESSAGE_HANDLERS[command]
                    func(writer, params)
                else:
                    if not data == b"\n":
                        writer.write(MSG_NOCOMMAND)
            else:
                logging.info('Connection from {} closed by peer'.format(peername))
                break
        except concurrent.futures.TimeoutError:
            logging.info('Connection from {} closed by timeout'.format(peername))
            break
    writer.close()
  



def main():
    loop = asyncio.get_event_loop()
    logging.basicConfig(level=logging.INFO)
    server_gen = asyncio.start_server(handle_connection, port=43521)
    server = loop.run_until_complete(server_gen)
    logging.info('Listening established on {0}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass # Press Ctrl+C to stop
    finally:
        server.close()
        loop.close()
        VG.closeDB()

        
if __name__ == '__main__':
    main()


        
##    import profile
##
##    profile.run('main()')




