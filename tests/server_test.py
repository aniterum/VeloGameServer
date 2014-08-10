import socket
import random
import time

RN = b"\r\n"
DIV = b":"

HELLO=b"HELLO"
RENAME=b"RENAME"
CREATE=b"CREATE"
REMOVE=b"REMOVE"
JOIN=b"JOIN"
LEAVE=b"LEAVE"
START=b"START"
STOP=b"STOP"
READY=b"READY"
UNREADY=b"UNREADY"
RECONNECT=b"RECONNECT"
SEND=b"SEND"
GET=b"GET"
GETGAMESETS = b"GETGAMESETS"
USERS=b"USERS"
DISCONNECT=b"DISCONNECT"
_USERS=b"_USERS"
_GAMES=b"_GAMES"
_TERMINATE=b"_TERMINATE"

MSG_OK = b"0"

userNames = "Антон, Вася, Женя, Лиза, Пикачу, Чубака".split(", ")
ids = []

server_address = ('localhost', 43521)

def send(sock, command, data = ""):
    if type(data) != type(b""):
        _msg = DIV.join([command, data.encode()]) + RN
    else:
        _msg = DIV.join([command, data]) + RN
        
    sock.send(_msg)
    allReceived = b""
    receivedBytesCount = 256
    
    while True:
        tmprec = sock.recv(receivedBytesCount)
        allReceived += tmprec
        if tmprec.find(b"\r\n") != -1:
            break
        
    return allReceived.strip()



def makeFakeCoords():
    Lat = str(random.randint(40,60) + random.random())
    Lon = str(random.randint(10,30) + random.random())
    Time = str(time.time())
    state = random.randint(0, 99)
    battery = random.randint(0, 99)
    signal = random.randint(0, 99)
    accuracy = random.randint(0, 99)

    template = (Lat, Lon, Time,
                state, battery, signal, accuracy)

    result = "%s:%s:%s:%02i%02i%02i%02i" % template
    
    return result.encode()


print("Регистрации пользователей")
for name in userNames:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    
    uID = send(sock, HELLO, name)
    
    ids.append({"name":name, "uID":uID})
    print("uID:", uID, name)
    
    #send(sock, DISCONNECT)

    time.sleep(1)
    sock.close()


print("Создание игры и подключение игроков")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(server_address)
if send(sock, RECONNECT, ids[0]["uID"]) == MSG_OK:
    gameTypes = send(sock, GETGAMESETS).decode()

    print(gameTypes)
    
    gID = send(sock, CREATE)
    if send(sock, READY) == MSG_OK:
        #send(sock, DISCONNECT)
        time.sleep(1)
        sock.close()
    else:
        print("READY error")
        time.sleep(1)
        sock.close()

for user in ids[1:]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    
    if send(sock, RECONNECT, user["uID"]) == MSG_OK:
        if send(sock, JOIN, gID) == MSG_OK:
            if send(sock, READY) == MSG_OK:
                #send(sock, DISCONNECT)
                time.sleep(1)
                sock.close()
            else:
                print("READY error")
                time.sleep(1)
                sock.close()


print("Запрос данных игроков")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(server_address)
if send(sock, RECONNECT, ids[0]["uID"]) == MSG_OK:
    users = send(sock, USERS)
    print(users.decode().split("\n"))

if send(sock, START) == MSG_OK:
    print("Начало игры")


    sendCount = 10
    for userData in ids:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(server_address)
        if send(sock, RECONNECT, userData["uID"]) == MSG_OK:
            time.sleep(1)
            print("Игрок", userData["name"], "шлёт координаты")
            for i in range(sendCount):
                result = send(sock, SEND, makeFakeCoords())
                if  result == MSG_OK:
                    time.sleep(0.1)
                else:
                    print(result)





        
    



