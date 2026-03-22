import socket
from os import environ
import threading
from time import sleep
import json
import random
from P2P_testing import Print_match_list,Get_return_matches,Create_match,Join_match,Check_for_host,Delete_match,Leave_match,Hard_reset_json
import P2P_testing

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
Capacity = 4
Hard_reset_json()

#reminder to future self: (and roman i guess)
# If you use firewall it will not be able to recieve anything

# Using selectors module would probably be more efficient than using 
# asynch functions, but if we use selectors we would have to rewrite
# alot of server and client logic, and figure out selectors.
# So witha  2 day deadline maybe not (𖦹﹏𖦹;)
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
        #print(clients)
        Thread = threading.Thread(target=Handle_client_lobby,kwargs={"client": (client,addr)})
        Thread.daemon = True
        Thread.start()
        # Figure out this later, for now use the inefficient threading method
        #asyncio.create_task(Handle_client_lobby((client,addr)))
        #Done actually
        #asyncio.run(Handle_client_lobby((client,addr)))


server.bind((ip,6677))
print("server bound")

print (server)
def Decode_string_client(string):
    pass

def Get_client_using_id(id):
    for client in Standby_clients:
        if client['id'] == id:
            return client

Started_lobby_ids = set()

def Poll_json_for_lobbies():
    while True:
        sleep(3)
        matches = Get_return_matches(raw=True)
        for match in matches:
            room_id = match['Room_id']
            if room_id not in Started_lobby_ids:
                Started_lobby_ids.add(room_id)
                players_in_lobby = []
                for player_data in match['Players']:
                    client_dict = Get_client_using_id(player_data['id'])
                    if client_dict:
                        players_in_lobby.append(client_dict)
                lobby = match
                lobby_thread = threading.Thread(target=Lobby_handling, args=(lobby,))
                lobby_thread.daemon = True
                lobby_thread.start()

def Match_lobby_requests(Packet,client):
    #Lobby handling
    print("pluh")
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
        Cl_Room['Is_host'] = True
        Cl_Room['id'] = Room_id
        #Start lobby thread so it can wait for "start game"
        for i in clients:
            if i[0] == client:
                clients.remove(i)
                Ingame_clients.append(i)

    elif Request == "Init":
        Standby_clients.append(Packet)
        Client_dict = Get_client_using_id(Packet['id'])
        Client_dict.update({"Socket_obj":client})
        client.sendto("Initialized".encode(),(Packet['Ip'],6677))
    
    else:
        client.sendto("Invalid code, Error".encode(),(Packet['Ip'],6677))

#Roman compare Packet['Request'] to the different actions you can do
#//Done
def Create_deck():
    suits = ['♠', '♥', '♦', '♣']
    ranks = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
    deck = [{'rank': r, 'suit': s} for s in suits for r in ranks]
    random.shuffle(deck)
    return deck

#Distributes cards to players, returns the remaining deck. Also updates player dicts with their cards
def Distribute_cards(players):
    deck = Create_deck()
    for player in players:
        player['Cards'] = [deck.pop(), deck.pop()]
    return deck

#Main game loop, it will be called when the host starts the game
def Match_ingame_requests(Packet,client,lobby):
    Request = Packet['Request']
    player_ip = Packet['Ip']

    if Request == "fold":
        for player in lobby['Players']:
            if player['id'] == Packet['id']:
                player['folded'] = True
        client.sendto("Folded".encode(),(player_ip,6677))

    elif Request == "check":
        client.sendto("Checked".encode(),(player_ip,6677))

    elif Request == "bet":
        bet_amount = Packet['Rq_spec'].get('amount', 0)
        lobby['current_bet'] = bet_amount
        for player in lobby['Players']:
            if player['id'] == Packet['id']:
                player['chips'] = player.get('chips', 1000) - bet_amount
        #Tell everyone about new bet
        for player in lobby['Players']:
            player['Socket_obj'].sendto(
                f"Bet:{bet_amount}".encode(),
                (player['Ip'],6677)
            )

    elif Request == "call":
        #If no current bet, can't call
        if lobby.get('current_bet', 0) == 0:
            client.sendto("No_bet".encode(),(player_ip,6677))
        else:
            bet_amount = lobby['current_bet']
            for player in lobby['Players']:
                if player['id'] == Packet['id']:
                    player['chips'] = player.get('chips', 1000) - bet_amount
            client.sendto(f"Called:{bet_amount}".encode(),(player_ip,6677))

    else:
        client.sendto("Unknown_request".encode(),(player_ip,6677))

def Lobby_handling(Lobby):
    Game_started = False
    Game_initialized = False
    Lobby_active = True
    while Lobby_active == True:
        All_cards = []

        #Wait for host to start game
        #Poll all players until host sends "start game"
        while Game_started == False:

            for player in Lobby['Players']:
                Lobby = P2P_testing.find_room(Lobby['Room_id'])
                sleep(0.5)
                player['Cards'] = []
                try:
                    sock = Get_client_using_id(player['id'])['Socket_obj']
                    sock.settimeout(0.1)
                    raw, addr = sock.recvfrom(2048)
                    Packet = json.loads(raw.decode())
                    print(Packet)
                    if Packet['Request'] == "start game":
                        if Check_for_host(Packet['id'],Match=Lobby) == True:
                            Game_started = True
                            sock.sendto("Sucess".encode(),(player['Ip'],6677))
                        else:
                            sock.sendto("Not_host".encode(),(player['Ip'],6677))
                    elif Packet['Request'] == "close lobby":
                        if Check_for_host(Packet['id'],Match=Lobby) == True:
                            sock.sendto("Sucess".encode(),(player['Ip'],6677))
                            Delete_match(Lobby['Room_id'])
                            Lobby_active = False
                            break
                        else:
                            sock.sendto("f".encode(),(player['Ip'],6677))
                            Leave_match(Lobby['Room_id'])
                except socket.timeout:
                    #The server doesn't need to print, it's too common of an occurance
                    pass
                except Exception as e:
                    print(e)
        while Game_started == True:
            if Game_initialized == False:
                Lobby['current_bet'] = 0  #Bet reset
                deck = Distribute_cards(Lobby['Players'])
                for player in Lobby['Players']:
                    try:
                        sock = Get_client_using_id(player['id'])['Socket_obj'] #Gets form dict instead of json
                        sock.sendto(f"Lobby started{json.dumps(player['Cards'])}".encode(),(player['Ip'],6677))
                    except Exception as e:
                        print(e)
                    #Roman i removed the second sendto because it sends so fast that it becomes 1 message either way.
                    # (quandale dingle here,  rehehehehehehehe)
                Game_initialized = True
                P2P_testing.Transfer_player_state(Lobby,Lobby['Players'],'Players','Active_players')
                sleep(3) #To make sure client gets 1 msg at a time

            #This part i basicly gambeled on, i hope it works
            #It suppose to poll all players for their actions, then process them and send the results back to the clients
            for player in Lobby['Active_players']: 
                try:
                    sock = Get_client_using_id(player['id'])['Socket_obj'] #Gets form dict instead of json
                    sock.sendto("Your turn".encode(),(player['Ip'],6677))
                    for waiter in Lobby['Players']:
                        if waiter != player:
                            waiter['Socket_obj'].sendto(f"Waiting for player{player['Name']}".encode(),(waiter['Ip'],6677))
                    sock.settimeout(30)
                    raw, addr = sock.recvfrom(2048)
                    Packet = json.loads(raw.decode())
                    Match_ingame_requests(Packet, sock, Lobby)
                except socket.timeout:
                    #player['folded'] = True
                    #sock.sendto("Folded".encode(),(player['Id'],6677)) #Hey, remember to implement folding
                    pass #Player hasn't sent anything yet
                except Exception as e:
                    print(e)
    

#Listens for Capacity number players
server.listen(Capacity)

Connection_thread = threading.Thread(target=Check_for_connections)
Connection_thread.start()

print("pluh")
Afk_clients = [

]

Standby_clients = [

]
Ingame_clients = [

]

Poll_thread = threading.Thread(target=Poll_json_for_lobbies)
Poll_thread.daemon = True
Poll_thread.start()

#--__--              --__--

def Handle_client_lobby(client):
    global Afk_clients
    global clients
    afk = False
    while True:
        if afk == False:
            try: 
                Packet,addr = client[0].recvfrom(2048)
                Packet = json.loads(Packet.decode())
                print(Packet)
                print(client[0])
                Match_lobby_requests(Packet,client[0])
            except WindowsError as e:
                print("Client disconnected or unresponsive")
                print(f'error:{e}')
                afk = True
            except Exception as e:
                print("Request error 1")
                print(e)

# No need to do async for ingame clients
# Since they take turns either way


'''
while True:
    for client in clients:
        #Takes string request and loads in json format
        try:
            Packet,addr = client[0].recvfrom(2048)
            Packet = json.loads(Packet.decode())
            print(Packet)
            print(addr)
            Match_lobby_requests(Packet,client[0])
        except WindowsError as e:
            print("Client disconnected or unresponsive")
            print(f'error:{e}')
            clients.remove(client) 
            Afk_clients.append(client)
        except Exception as e:
            print("Request error 1")
            print(e)
'''