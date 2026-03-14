import socket
from os import environ
import threading
from time import sleep
import json
from P2P_testing import Print_match_list,Get_return_matches

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
Capacity = 4


#reminder to future self: (and roman i guess)
# If you use firewall it will not be able to recieve anything

#Basic connection logic
clients = []
def Check_for_connections():
    while True:
        global clients
        client,addr = server.accept()
        clients.append((client,addr))


server.bind(('192.168.0.49',6677))
print("server bound")

print (server)


def Match_requests(Packet):
    if Packet['Request'] == 'Get_lobbies':
        Lobbies = json.dumps(Get_return_matches)
        server.sendto(Lobbies.encode(),(Packet['Ip'],6677))

    

#Listens for Capacity number players
server.listen(Capacity)

Connection_thread = threading.Thread(target=Check_for_connections)
Connection_thread.start()

print("pluh")

clients_dict = {

}


#--__--              --__--

while True:
    for client in clients:
        #Takes string request and loads in json format
        try:
            Request = client[0].recv(2048).decode()
            print(json.loads(Request))
            sleep(0.5)
        except:
            print("Request error 1")

