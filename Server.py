import socket
from os import environ
import threading
from time import sleep
import json

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
Capacity = 4


#reminder to future self: (and roman i guess)
# If you use firewall it will not be able to recieve anything
clients = []
def Check_for_connections():
    while True:
        global clients
        client,addr = server.accept()
        clients.append((client,addr))


server.bind(('192.168.0.49',6677))
print("server bound")

print (server)

def Match_requests(Request):
    pass

server.listen()

Connection_thread = threading.Thread(target=Check_for_connections)
Connection_thread.start()

print("pluh")

clients_dict = {

}


while True:
    for client in clients:
        Request = client[0].recv(2048).decode()
        print(json.load(Request))
        sleep(0.5)

