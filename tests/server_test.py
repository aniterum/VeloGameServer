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
    return sock.recv(1024).strip()



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



input("Enter для регистрации пользователей")
for name in userNames:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    
    uID = send(sock, HELLO, name)
    
    ids.append({"name":name, "uID":uID})
    print("uID:", uID, name)
    
    send(sock, DISCONNECT)

    time.sleep(1)
    sock.close()


input("Enter для создания игры и регистрации пользователей")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(server_address)
if send(sock, RECONNECT, ids[0]["uID"]) == MSG_OK:
    gID = send(sock, CREATE)
    if send(sock, READY) == MSG_OK:
        send(sock, DISCONNECT)
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
                send(sock, DISCONNECT)
                time.sleep(1)
                sock.close()
            else:
                print("READY error")
                time.sleep(1)
                sock.close()

sendCount = 20
input("Enter начала игры")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(server_address)
if send(sock, RECONNECT, ids[0]["uID"]) == MSG_OK:
    if send(sock, START) == MSG_OK:
        input("Enter для отправки данных")
        for i in range(sendCount):
            if send(sock, SEND, makeFakeCoords()) == MSG_OK:
                time.sleep(0.5)
            else:
                break



        
    



