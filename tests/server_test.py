import socket
import asyncio_test as asio
import random
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('localhost', 43521)
sock.connect(server_address)

uID = None
#uID = "47d40942126a4bea9b2639d1412fbdaacdaaad1e"

#gpsTest = "|".join(["", uID, str(random.randint(30, 60) + random.random()), str(random.randint(30, 60) + random.random())])

print("SEND HELLO, GET USERID")
if uID == None:
    sock.send(b"HELLO|ANTON\r\n")
    uID = sock.recv(1024).strip().decode()
    print("uID : " + uID)


print("CREATE GAME")
sock.send(b"CREATE_GAME|" + uID.encode() + b"|NOSETTINGS\r\n")
gameID = sock.recv(1024).strip().decode()
print("gameID : " + gameID)


print("START GAME")
sock.send(b"STARTGAME|" + uID.encode() + b"|" + gameID.encode() + b"\r\n")

for a in range(2):
    gpsTest = "|".join([gameID, uID, str(random.randint(30, 60) + random.random()), str(random.randint(30, 60) + random.random()), str(time.time())])
    sock.send(asio.MSG_SEND_DATA + b"|" + asio.packAndBase(gpsTest) + b"\r\n")
    time.sleep(0.5)
