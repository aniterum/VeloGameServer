import socket
import random
import time

RN = b"\r\n"

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('localhost', 43521)
sock.connect(server_address)

input("Press Enter to Connect")
sock.send(b"HELLO:ANTON" + RN)
uID = sock.recv(1024).strip()
print(b"uID : " + uID)

input("Press Enter to Disconnect")
sock.send(b"DISCONNECT:" + RN)
sock.close()

input("Press Enter to Try Reconnect 3 times")
for i in range(3):
    time.sleep(1)
    print("Try to connect %i time" % i)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    sock.send(b"RECONNECT:" + uID + RN)
    #input("Press Enter to Disconnect")
    sock.send(b"DISCONNECT:" + RN)
    sock.close()



##print("CREATE GAME")
##sock.send(b"CREATE_GAME|" + uID.encode() + b"|NOSETTINGS\r\n")
##gameID = sock.recv(1024).strip().decode()
##print("gameID : " + gameID)
##
##
##print("START GAME")
##sock.send(b"STARTGAME|" + uID.encode() + b"|" + gameID.encode() + b"\r\n")
##
##for a in range(2):
##    gpsTest = "|".join([gameID, uID, str(random.randint(30, 60) + random.random()), str(random.randint(30, 60) + random.random()), str(time.time())])
##    sock.send(asio.MSG_SEND_DATA + b"|" + asio.packAndBase(gpsTest) + b"\r\n")
##    time.sleep(0.5)
