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
Game_sockets = set()

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
        #Not done actually
        #asyncio.run(Handle_client_lobby((client,addr)))


server.bind((ip,6677))
print("server bound")

print (server)

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
                lobby = match
                lobby_thread = threading.Thread(target=Lobby_handling, args=(lobby,))
                lobby_thread.daemon = True
                lobby_thread.start()

def Match_lobby_requests(Packet,client):
    #Lobby handling
    print("pluh")
    global server
    global Game_sockets
    try:
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
            #Not unsustainable as fuck anymore
                Game_sockets.add(client)

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
            Game_sockets.add(client)

        elif Request == "Init":
            Standby_clients.append(Packet)
            Client_dict = Get_client_using_id(Packet['id'])
            Client_dict.update({"Socket_obj":client})
            client.sendto("Initialized".encode(),(Packet['Ip'],6677))

        else:
            client.sendto("Invalid code, Error".encode(),(Packet['Ip'],6677))
    except Exception as e:
        print(e)

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
    try:
        Request = Packet['Request']
        player_ip = Packet['Ip']

        if Request == "fold":
            for player in lobby['Active_players']:
                if player['id'] == Packet['id']:
                    player['folded'] = True
                    P2P_testing.Transfer_player_state(lobby,[player],'Active_players','Players')
            client.sendto("Folded".encode(),(player_ip,6677))

        elif Request == "check":
            client.sendto("Checked".encode(),(player_ip,6677))

        elif Request == "bet":
            bet_amount = Packet['Rq_spec'].get('amount', 0)
            lobby['current_bet'] = bet_amount
            for player in lobby['Active_players']:
                if player['id'] == Packet['id']:
                    player['chips'] = player.get('chips', 1000) - bet_amount
            #Tell everyone about new bet
            for player in lobby['Active_players']:
                p_sock = Get_client_using_id(player['id'])['Socket_obj']
                p_sock.sendto(f"Bet:{bet_amount}".encode(),(player['Ip'],6677))

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
    except Exception as e:
        print(e)

def Lobby_handling(Lobby):
    Game_started = False
    Game_initialized = False
    Lobby_active = True

    while Lobby_active:
        #Wait for host to start game
        #Poll all players until host sends "start game"
        while Game_started == False:
            Lobby = P2P_testing.find_room(Lobby['Room_id'])
            if Lobby is None:
                Lobby_active = False
                break

            for player in list(Lobby['Players']):
                try:
                    sock = Get_client_using_id(player['id'])['Socket_obj']
                    sock.settimeout(0.1)
                    raw, addr = sock.recvfrom(2048)
                    Packet = json.loads(raw.decode())
                    print(Packet)

                    if Packet['Request'] == "start game":
                        if Check_for_host(Packet['id'],Match=Lobby):
                            Game_started = True
                            sock.sendto("Sucess".encode(),(player['Ip'],6677))
                        else:
                            sock.sendto("Not_host".encode(),(player['Ip'],6677))

                    elif Packet['Request'] == "close lobby":
                        if Check_for_host(Packet['id'],Match=Lobby):
                            sock.sendto("Sucess".encode(),(player['Ip'],6677))
                            Delete_match(Lobby['Room_id'])
                            Lobby_active = False
                            Game_started = False    # break out of while loop too
                            break
                        else:
                            sock.sendto("Not_host".encode(),(player['Ip'],6677))

                    elif Packet['Request'] == "leave":
                        Leave_match(Lobby['Room_id'], Packet)
                        sock.sendto("Sucess".encode(),(player['Ip'],6677))
                        Game_sockets.discard(sock)
                        break   #restart the player loop with refreshed lobby

                except socket.timeout:
                    #The server doesn't need to print, it's too common of an occurance
                    pass
                except Exception as e:
                    print(e)
            sleep(0.3)

        while Game_started == True:
            if Game_initialized == False:
                Lobby['current_bet'] = 0  #Bet reset
                deck = Distribute_cards(Lobby['Players'])
                for player in Lobby['Players']:
                    try:
                        sock = Get_client_using_id(player['id'])['Socket_obj'] #Gets form dict instead of json
                        sock.sendto(
                            f"Lobby started{json.dumps(player['Cards'])}".encode(),
                            (player['Ip'],6677)
                        )
                    except Exception as e:
                        print(e)
                    #Roman i removed the second sendto because it sends so fast that it becomes 1 message either way.
                    # (quandale dingle here,  rehehehehehehehe)
                Game_initialized = True
                Lobby = P2P_testing.Transfer_player_state(
                    Lobby, Lobby['Players'], 'Players', 'Active_players'
                )
                sleep(3) #To make sure client gets 1 msg at a time

            #This part i basicly gambeled on, i hope it works
            #It suppose to poll all players for their actions, then process them and send the results back to the clients
            for player in list(Lobby['Active_players']):
                try:
                    sock = Get_client_using_id(player['id'])['Socket_obj'] #Gets form dict instead of json
                    sock.sendto("Your turn".encode(),(player['Ip'],6677))

                    #We were using waiter['Socket_obj'] which is a str from JSON,
                    #not an actual socket. Now we use Get_client_using_id instead
                    for waiter in Lobby['Active_players']:
                        if waiter['id'] != player['id']:
                            waiter_sock = Get_client_using_id(waiter['id'])['Socket_obj']
                            waiter_sock.sendto(
                                f"Waiting for player {player['Name']}".encode(),
                                (waiter['Ip'],6677)
                            )

                    sock.settimeout(30)
                    raw, addr = sock.recvfrom(2048)
                    Packet = json.loads(raw.decode())
                    Match_ingame_requests(Packet, sock, Lobby)

                    #Refresh lobby
                    Lobby = P2P_testing.find_room(Lobby['Room_id']) or Lobby

                except socket.timeout:
                    #player['folded'] = True
                    #sock.sendto("Folded".encode(),(player['Id'],6677)) #Hey, remember to implement folding
                    pass #Player hasn't sent anything yet
                except Exception as e:
                    print(e)

            #After everyone did their moves - notify everyone
            all_player_ids = (
                [p['id'] for p in Lobby.get('Active_players', [])] +
                [p['id'] for p in Lobby.get('Players', [])]
            )
            for pid in all_player_ids:
                try:
                    c = Get_client_using_id(pid)
                    if c:
                        c['Socket_obj'].sendto(
                            "Round_over".encode(), (c['Ip'], 6677)
                        )
                except Exception:
                    pass

            #If 1 or 0 active players left = gameover
            if len(Lobby.get('Active_players', [])) <= 1:
                for pid in all_player_ids:
                    try:
                        c = Get_client_using_id(pid)
                        if c:
                            c['Socket_obj'].sendto(
                                "Game_over".encode(), (c['Ip'], 6677)
                            )
                    except Exception:
                        pass
                Game_started = False
                Game_initialized = False
                break

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
    global Game_sockets
    afk = False
    while True:
        if client[0] in Game_sockets:
            sleep(0.1)
            continue

        if afk == False:
            try: 
                #Use a short timeout so we recheck GameSockets regularly
                client[0].settimeout(1.0)
                Packet,addr = client[0].recvfrom(2048)
                Packet = json.loads(Packet.decode())
                print(Packet)
                print(client[0])
                Match_lobby_requests(Packet,client[0])
            except socket.timeout:
                pass    #just loop back and check GameSockets again
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