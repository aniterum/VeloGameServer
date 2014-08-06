#Взято с http://habrahabr.ru/post/217143/
import asyncio
import logging
import concurrent.futures
import hashlib
import zlib
import base64
import time
from VeloGameDatabase import VeloGameDatabase

GAME_DATABASE_NAME = "velogames.db"

VG = VeloGameDatabase(GAME_DATABASE_NAME)

USER_BASE = {}
#{"ip":(ip, port), "name":userName, "gameMaster":False, "gameID":None, "gameStatus":None}
USER_PSEUDONIMES = {}
#{userID:pseudonimeID}
GAMES_BASE = {}
#gameID: {type:"chase", canViewEveryone:True, gameMaster:"GameMasterIDHash"}


MSG_DISCONNECT  = b"DISCONNECT"
MSG_SEND_DATA   = b"SEND"       #|ZLIB(GAMEID|USERID|LAT|LON|TIME)
MSG_GET_DATA    = b"GET"        #|USERID  -> ZLIB(USERID|LAT|LON\r\nUSERID|LAT|LON)
MSG_HELLO       = b"HELLO"      #|USERNAME -> USERID
MSG_CREATE_GAME = b"CREATE_GAME"#|USERID|GAMETYPE 
MSG_JOIN_GAME   = b"JOIN_GAME"  #|USERID|GAMEID
MSG_GET_USERS   = b"GET_USERS"  # -> ZLIB (USERID:USERNAME\r\nUSERID:USERNAME)
MSG_GAME_START  = b"STARTGAME"  #|USERID|GAMEID

DIVISOR = b"|"
bRN = b"\r\n"
RN = "\r\n"

##HELLO(USERNAME):USERID - подключение к серверу; HELLO:USERNAME
##RENAME(NEWUSERNAME):RESULT - изменить имя пользователя
##CREATE(OPTIONS):GAMEID - создаёт игру, в данных игрока-создателя указывается, что он её создал.
##JOIN(GAMEID):OPTIONS - подключиться к созданной игре;
##START_GAME(GAMEID):RESULT - начать созданную игру;
##STOP_GAME(GAMEID):RESULT - останавливает начатую игру;
##RECONNECT(USERID):RESULT - передключение после разрыва связи, заменит IP:PORT в данных пользователя;
##SEND(LAT, LON, TIME, uState):RESULT - отправить текущие координаты и собственное время, если вы были допущены в игру, и игра началась;
##GET:zLib(u1:(LAT, LON, uState), .... uN:(LAT, LON, uState)) - отдаёт координаты и текущий статус игрока (онлайн, оффлайн, потеряны координаты и т.д.;
##USERS:zLib(u1:(Name, GAMEROLE),  ... uN:(Name, GAMEROLE)) - даёт имена пользователей и их роли в игре.
##DISCONNECT:RESULT - разъединяет с сервером, указывает статус "оффлайн".


def HELLO(writer, userName):
        peername = writer.get_extra_info('peername')
        logging.info('Pier {} want to has name'.format(peername))

        userIDHash = str(hash(peername))

        writer.write(userIDHash.encode() + bRN)

        if userIDHash in USER_BASE:
            USER_BASE[peername]["name"] = userName.decode()
        else:
            USER_BASE[peername] = {"uID":userIDHash, "name":userName.decode(), "gameMaster":False, "gameID":None, "gameStatus":None, "regTime":time.time()}

        print(USER_BASE)


def CREATE(writer, options):
    gameID = None
    print("CREATE()")
    return gameID



def RENAME(writer, newUserName):
    result = None
    print("RENAME()")
    return result

def JOIN(writer, gameID):
    options = None
    print("JOIN()")
    return options

def START(writer, gameID):
    result = None
    print("START()")
    return result

def STOP(writer, gameID):
    result = None
    print("STOP()")
    return result



def RECONNECT(writer, userID):
    peername = writer.get_extra_info('peername')

    if peername in USER_BASE.keys():
        print("No need reconnect")
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
            

    print(USER_BASE)



def SEND(writer, data):
    result = None
    print("SEND()")
    return result

def GET(writer, data):
    result = None
    print("GET()")
    return result

def USERS(writer, data):
    result = None
    print("USERS()")
    return result

def DISCONNECT(writer, data):
    peername = writer.get_extra_info('peername')
    logging.info('Connection from {} closed by DISCONNECT command'.format(peername))
    writer.close()



MESSAGE_HANDLERS = {b"HELLO":HELLO,
                    b"RENAME":RENAME,
                    b"CREATE":CREATE,
                    b"JOIN":JOIN,
                    b"START":START,
                    b"STOP":STOP,
                    b"RECONNECT":RECONNECT,
                    b"SEND":SEND,
                    b"GET":GET,
                    b"USERS":USERS,
                    b"DISCONNECT":DISCONNECT}

    

def packAndBase(text):
    compressed = zlib.compress(text.encode())
    return base64.b64encode(compressed)

def unbaseAndUnPack(basedPack):
    debased = base64.b64decode(basedPack)
    return zlib.decompress(debased)

def getCommandAndData(data):
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
    peername = writer.get_extra_info('peername')
    logging.info('Accepted connection from {}'.format(peername))
    while True:
        try:
            data = yield from asyncio.wait_for(reader.readline(), timeout=1000.0)
            if data: 
                command, params = getCommandAndData(data)
                if ((command != None) and (command in MESSAGE_HANDLERS.keys())):
                    func = MESSAGE_HANDLERS[command]
                    func(writer, params)
                    print("params:", params.decode())
 
            else:
                logging.info('Connection from {} closed by peer'.format(peername))
                break
        except concurrent.futures.TimeoutError:
            logging.info('Connection from {} closed by timeout'.format(peername))
            break
    writer.close()
  



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    logging.basicConfig(level=logging.INFO)
    server_gen = asyncio.start_server(handle_connection, port=43521)
    server = loop.run_until_complete(server_gen)
    logging.info('Listening established on {0}'.format(server.sockets[0].getsockname()))
    try:
        VG = VeloGameDatabase(GAME_DATABASE_NAME)
        loop.run_forever()
    except KeyboardInterrupt:
        pass # Press Ctrl+C to stop
    finally:
        server.close()
        loop.close()
        VG.closeDB()




