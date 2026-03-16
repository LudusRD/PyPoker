import socket
from os import environ
import threading
from time import sleep
import json
from P2P_testing import Print_match_list,Get_return_matches,Create_match,Join_match

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
Capacity = 4


#reminder to future self: (and roman i guess)
# If you use firewall it will not be able to recieve anything
hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)
print(ip)

#Basic connection logic
clients = []
def Check_for_connections():
    while True:
        global clients
        client,addr = server.accept()
        print(client)
        clients.append((client,addr))


server.bind((ip,6677))
print("server bound")

print (server)
def Decode_string_client(string):
    pass

def Get_client_using_id(id):
    for client in Standby_clients:
        if client['id'] == id:
            return client

def Match_lobby_requests(Packet,client):
    #Lobby handling
    global server
    Request = Packet['Request']
    if Request == 'Get_lobbies':
        Lobbies = json.dumps(Get_return_matches())
        client.sendto(Lobbies.encode(),(Packet['Ip'],6677))

    elif Request == "Join_room":
        specs = Packet['Rq_spec']
        result = Join_match(specs['id'],Packet,specs['Password'])
        #Changes serverside client variables, fuck this is a godamn mess
        if result[:6] == "Joined":
            Cl_Room = Get_client_using_id(Packet['id'])['Room']
            Cl_Room['ingame'] = True
            Cl_Room['id'] = specs['id']
            client.sendto("Sucess".encode(),(Packet['Ip'],6677))
        #Unsustainable as fuck

    elif Request == "Create_lobby":
        Specs = Packet['Rq_spec']
        Room_id = Create_match(Specs['Name'],Packet,Specs['Password'])
        client.sendto(f"Sucess:{Room_id}".encode(),(Packet['Ip'],6677))
        #Changes serverside client variables
        Cl_Room = Get_client_using_id(Packet['id'])['Room']
        Cl_Room['ingame'] = True
        Cl_Room['id'] = Room_id

    elif Request == "Init":
        Standby_clients.append(Packet)
        Client_dict = Get_client_using_id(Packet['id'])
        Client_dict.update({"Socket_obj":client})
        client.sendto("Initialized".encode(),(Packet['Ip'],6677))

def Match_ingame_requests(Packet,client,lobby):
    pass

def Lobby_handling(Lobby):
    while True:
        Game_started = False
        Game_initialized = False
        All_cards = []


        for player in Lobby['Players']:
                player['Cards'] = []
                socket = player['Socket_obj']
                Packet, addr = socket.recvfrom(2048)
                if Packet['Request'] == "start game":
                    if Packet['Room']['Is_host'] == True:
                        Game_started = True
                        socket.sendto("Sucess".encode(),(player['Ip'],6677))
                    else:
                        socket.sendto("Not_host".encode(),(player['Ip'],6677))

        while Game_started == True:
            if Game_initialized == False:
                for player in Lobby['Players']:
                    player['Cards'] = []
                    socket = player['Socket_obj']
                    socket.sendto("Lobby started".encode(),(player['Ip'],6677))

            for player in Lobby['Players']:
                socket.sendto("Your cards are: ")
    

#Listens for Capacity number players
server.listen(Capacity)

Connection_thread = threading.Thread(target=Check_for_connections)
Connection_thread.start()

print("pluh")

Standby_clients = [

]
Ingame_clients = [

]


#--__--              --__--

while True:
    for client in clients:
        #Takes string request and loads in json format
        try:
            Packet,addr = client[0].recvfrom(2048)
            Packet = json.loads(Packet.decode())
            print(Packet)
            print(addr)
            Match_lobby_requests(Packet,client[0])
            sleep(0.5)
        except WindowsError:
            print("Client disconnected or unresponsive")
            clients.remove(client)           
        except Exception as e:
            print("Request error 1")
            print(e)

