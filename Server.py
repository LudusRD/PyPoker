import socket
from os import environ
import threading
from time import sleep
import json
import random
from P2P_testing import Print_match_list,Get_return_matches,Create_match,Join_match,Check_for_host,Delete_match,Leave_match,Hard_reset_json
import P2P_testing
from output import response, do_print
from itertools import combinations
from collections import Counter

RANK_MAP = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
HAND_NAMES = ["High Card", "One Pair", "Two Pair", "Three of a Kind", "Straight", "Flush", "Full House", "Four of a Kind", "Straight Flush"]

def evaluate_five_cards(cards):
    ranks = sorted([RANK_MAP[c['rank']] for c in cards], reverse=True)
    suits = [c['suit'] for c in cards]
    is_flush = len(set(suits)) == 1
    is_straight = (max(ranks) - min(ranks) == 4) and len(set(ranks)) == 5

    #Lower straight check
    if ranks == [14, 5, 4, 3, 2]:
        is_straight = True
        ranks = [5, 4, 3, 2, 1]

    counts = Counter(ranks).most_common()
    counts.sort(key=lambda x: (x[1], x[0]), reverse=True)
    sorted_ranks_by_freq = [item[0] for item in counts]
    frequencies = [item[1] for item in counts]

    #Straight Flush- five consecutive cards of the same suit
    if is_straight and is_flush: return (8, sorted_ranks_by_freq[0])

    #Four of a Kind- four cards of the same rank
    if frequencies[0] == 4: return (7, sorted_ranks_by_freq[0], sorted_ranks_by_freq[1])

    #Full House- three of a kind + a pair
    if frequencies[0] == 3 and frequencies[1] == 2: return (6, sorted_ranks_by_freq[0], sorted_ranks_by_freq[1])

    #Flush- five cards of the same suit (not in sequence)
    if is_flush: return (5, ranks)

    #Straight- five consecutive cards (not same suit)
    if is_straight: return (4, sorted_ranks_by_freq[0])

    #Three of a Kind- exactly three cards of the same rank, no pair
    if frequencies[0] == 3: return (3, sorted_ranks_by_freq[0], sorted_ranks_by_freq[1], sorted_ranks_by_freq[2])

    #Two Pair- two different pairs
    if frequencies[0] == 2 and frequencies[1] == 2: return (2, sorted_ranks_by_freq[0], sorted_ranks_by_freq[1], sorted_ranks_by_freq[2])

    #One Pair- exactly one pair
    if frequencies[0] == 2: return (1, sorted_ranks_by_freq[0], ranks)

    #High Card- no combination matched
    return (0, ranks)

def get_best_combination(seven_cards):
    return max(combinations(seven_cards, 5), key=evaluate_five_cards)

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

#We need to inizialize these already here because they are used in the lobby handling function, which is called in a thread before the main loop
Afk_clients = []
Standby_clients = []
Ingame_clients = []

def Check_for_connections():
    while True:
        global clients
        client,addr = server.accept()
        response({'Request': 'Init', 'Ip': addr[0]})
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
    #print("pluh")
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
            else:
                client.sendto(result.encode(),(Packet['Ip'],6677))

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
            if lobby.get('current_bet', 0) > 0:
                client.sendto("Cannot_check".encode(),(player_ip,6677))
                return
            client.sendto("Checked".encode(),(player_ip,6677))

        elif Request == "bet":
            if lobby.get('current_bet', 0) > 0:
                client.sendto("Cannot_bet:bet_exists".encode(),(player_ip,6677))
                return
            bet_amount = Packet['Rq_spec'].get('amount', 0)
            lobby['current_bet'] = bet_amount
            #Save bet in Json
            lobby['pot'] = lobby.get('pot', 0) + bet_amount
            P2P_testing.Save_current_bet(lobby['Room_id'], bet_amount)
            P2P_testing.Save_pot(lobby['Room_id'], lobby['pot'])
            for player in lobby['Active_players']:
                if player['id'] == Packet['id']:
                    player['chips'] = player.get('chips', 1000) - bet_amount
                    #Save chips in JSON
                    P2P_testing.Save_player_chips(lobby['Room_id'], player['id'], player['chips'])
            #Tell everyone about new bet and pot
            for player in lobby['Active_players']:
                p_sock = Get_client_using_id(player['id'])['Socket_obj']
                p_sock.sendto(f"Bet:{bet_amount}:Pot:{lobby['pot']}".encode(),(player['Ip'],6677))

        elif Request == "raise":
            if lobby.get('current_bet', 0) == 0:
                client.sendto("Cannot_raise:no_bet".encode(),(player_ip,6677))
                return
            raise_amount = Packet['Rq_spec'].get('amount', 0)
            if raise_amount <= lobby['current_bet']:
                client.sendto(f"Cannot_raise:must_exceed_{lobby['current_bet']}".encode(),(player_ip,6677))
                return
            lobby['current_bet'] = raise_amount
            lobby['pot'] = lobby.get('pot', 0) + raise_amount
            P2P_testing.Save_current_bet(lobby['Room_id'], raise_amount)
            P2P_testing.Save_pot(lobby['Room_id'], lobby['pot'])
            for player in lobby['Active_players']:
                if player['id'] == Packet['id']:
                    player['chips'] = player.get('chips', 1000) - raise_amount
                    P2P_testing.Save_player_chips(lobby['Room_id'], player['id'], player['chips'])
            #Tell everyone about raise and pot
            for player in lobby['Active_players']:
                p_sock = Get_client_using_id(player['id'])['Socket_obj']
                p_sock.sendto(f"Raise:{raise_amount}:Pot:{lobby['pot']}".encode(),(player['Ip'],6677))

        elif Request == "call":
            #If no current bet, can't call
            if lobby.get('current_bet', 0) == 0:
                client.sendto("No_bet".encode(),(player_ip,6677))
            else:
                bet_amount = lobby['current_bet']
                lobby['pot'] = lobby.get('pot', 0) + bet_amount
                P2P_testing.Save_pot(lobby['Room_id'], lobby['pot'])
                #We need to check for active players here
                for player in lobby['Active_players']:
                    if player['id'] == Packet['id']:
                        player['chips'] = player.get('chips', 1000) - bet_amount
                        #Chips save in JSON
                        P2P_testing.Save_player_chips(lobby['Room_id'], player['id'], player['chips'])
                client.sendto(f"Called:{bet_amount}:Pot:{lobby['pot']}".encode(),(player_ip,6677))

        else:
            client.sendto("Unknown_request".encode(),(player_ip,6677))
    except Exception as e:
        print(e)

#Broadcasts a message to all players in the lobby, used for community cards and stuff like that
def Broadcast_to_lobby(Lobby, message):
    all_player_ids = (
        [p['id'] for p in Lobby.get('Active_players', [])] +
        [p['id'] for p in Lobby.get('Players', [])]
    )
    for pid in all_player_ids:
        try:
            c = Get_client_using_id(pid)
            if c:
                c['Socket_obj'].sendto(message.encode(), (c['Ip'], 6677))
        except (ConnectionResetError, OSError):  #Catch WinError 10054
            pass

#Betting round logic, returns the updated lobby after the round is over
def Betting_round(Lobby):
    player_ids = [p['id'] for p in list(Lobby.get('Active_players', []))]
    for pid in player_ids:
        Lobby = P2P_testing.find_room(Lobby['Room_id']) or Lobby
        if not any(p['id'] == pid for p in Lobby.get('Active_players', [])):
            continue  #Fold = not active, skip their turn
        player = next(p for p in Lobby['Active_players'] if p['id'] == pid)
        try:
            sock = Get_client_using_id(player['id'])['Socket_obj']
            sock.sendto("Your turn".encode(),(player['Ip'],6677))

            for waiter in Lobby['Active_players']:
                if waiter['id'] != player['id']:
                    waiter_sock = Get_client_using_id(waiter['id'])['Socket_obj']
                    waiter_sock.sendto(
                        f"Waiting for player {player['Name']}".encode(),
                        (waiter['Ip'],6677)
                    )

            sock.settimeout(30)
            raw, addr = sock.recvfrom(2048)
            if not raw:
                continue
            Packet = json.loads(raw.decode())
            Match_ingame_requests(Packet, sock, Lobby)

            Lobby = P2P_testing.find_room(Lobby['Room_id']) or Lobby

        except socket.timeout:
            pass
        except Exception as e:
            print(e)
    return Lobby

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
            Lobby['Has_started'] = False
            P2P_testing.Save_has_started(Lobby['Room_id'], False)

            for player in list(Lobby['Players']):
                try:
                    sock = Get_client_using_id(player['id'])['Socket_obj']
                    sock.settimeout(1)
                    raw, addr = sock.recvfrom(2048)
                    Packet = json.loads(raw.decode())
                    response(Packet)

                    if Packet['Request'] == "start game":
                        if Check_for_host(Packet['id'],Match=Lobby):
                            Game_started = True
                            Lobby['Has_started'] = True
                            P2P_testing.Save_has_started(Lobby['Room_id'], True)
                            sock.sendto("Sucess".encode(),(player['Ip'],6677))
                            for pl_ayer in Lobby['Players']:
                                if player['id'] != pl_ayer['id']:
                                    sock = Get_client_using_id(pl_ayer['id'])['Socket_obj'] #Gets form dict instead of json         
                                    sock.sendto("start_game".encode(),(pl_ayer['Ip'],6677))            
                        else:
                            sock.sendto("Not_host".encode(),(player['Ip'],6677))

                    elif Packet['Request'] == "close lobby":
                        if Check_for_host(Packet['id'],Match=Lobby):
                            sock.sendto("Sucess".encode(),(player['Ip'],6677))
                            Delete_match(Lobby['Room_id'])
                            Lobby_active = False
                            Game_started = False    # break out of while loop too
                            for p in Lobby['Players']:
                                if p['id'] != Packet['id']:
                                    c = Get_client_using_id(p['id'])
                                    if c:
                                        c['Socket_obj'].sendto("Lobby_closed".encode(), (p['Ip'], 6677))
                                        Game_sockets.discard(c['Socket_obj'])
                            Game_sockets.discard(sock)
                            break
                        else:
                            sock.sendto("Not_host".encode(),(player['Ip'],6677))

                    elif Packet['Request'] == "leave":
                        Leave_match(Lobby['Room_id'], Packet)
                        sock.sendto("Sucess".encode(),(player['Ip'],6677))
                        Game_sockets.discard(sock)
                        break   #restart the player loop with refreshed lobby

                    elif Packet['Request'] == "GetPlayers":
                        Dict_players = json.dumps(Lobby['Players'])
                        sock.sendto(Dict_players.encode(),(player['Ip'],6677))
                        

                except socket.timeout:
                    #The server doesn't need to print, it's too common of an occurance
                    pass
                except Exception as e:
                    print(e)
            sleep(0.3)

        while Game_started == True:
            #Lobby update
            Lobby = P2P_testing.find_room(Lobby['Room_id']) or Lobby
            if Game_initialized == False:
                all_back = list(Lobby.get('Active_players', []))
                if all_back:
                    Lobby = P2P_testing.Transfer_player_state(Lobby, all_back, 'Active_players', 'Players')
                Lobby['current_bet'] = 0  #Bet reset
                Lobby['pot'] = 0          #Pot reset
                P2P_testing.Save_current_bet(Lobby['Room_id'], 0)
                P2P_testing.Save_pot(Lobby['Room_id'], 0)
                for player in Lobby['Players']:
                    player.setdefault('chips', 1000)
                deck = Distribute_cards(Lobby['Players'])
                P2P_testing.Save_player_cards(Lobby['Room_id'], Lobby['Players'])
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

                #Preflop
                Lobby = Betting_round(Lobby)
                Lobby['current_bet'] = 0
                P2P_testing.Save_current_bet(Lobby['Room_id'], 0)

                #Flop
                community_cards = [deck.pop(), deck.pop(), deck.pop()]
                Broadcast_to_lobby(Lobby, f"Community:{json.dumps(community_cards)}")
                sleep(1)
                Lobby = Betting_round(Lobby)
                Lobby['current_bet'] = 0
                P2P_testing.Save_current_bet(Lobby['Room_id'], 0)

                #Turn (?)
                community_cards.append(deck.pop())
                Broadcast_to_lobby(Lobby, f"Community:{json.dumps(community_cards)}")
                sleep(1)
                Lobby = Betting_round(Lobby)
                Lobby['current_bet'] = 0
                P2P_testing.Save_current_bet(Lobby['Room_id'], 0)

                #River
                community_cards.append(deck.pop())
                Broadcast_to_lobby(Lobby, f"Community:{json.dumps(community_cards)}")
                sleep(1)
                Lobby = Betting_round(Lobby)

                active = Lobby.get('Active_players', [])
                if active:
                    best_score = None
                    winner_name = ""
                    for player in active:
                        seven = player.get('Cards', []) + community_cards
                        score = evaluate_five_cards(get_best_combination(seven))
                        if best_score is None or score > best_score:
                            best_score = score
                            winner_name = player['Name']
                    Broadcast_to_lobby(Lobby, f"Winner:{winner_name}:{HAND_NAMES[best_score[0]]}")
                    sleep(0.2)
                else:
                    last = Lobby.get('Players', [])
                    if last:
                        Broadcast_to_lobby(Lobby, f"Winner:{last[-1]['Name']}:Last Standing")

                all_player_ids = (
                    [p['id'] for p in Lobby.get('Active_players', [])] +
                    [p['id'] for p in Lobby.get('Players', [])]
                )
                if len(Lobby.get('Active_players', [])) == 0:
                    for pid in all_player_ids:
                        try:
                            c = Get_client_using_id(pid)
                            if c:
                                c['Socket_obj'].sendto(
                                    "Game_over".encode(), (c['Ip'], 6677)
                                )
                                #Delete from Game_sockets so they can send lobby requests again without restarting
                                Game_sockets.discard(c['Socket_obj'])
                        except Exception:
                            pass
                    Game_started = False
                    Game_initialized = False
                    P2P_testing.Save_has_started(Lobby['Room_id'], False)
                else:
                    for pid in all_player_ids:
                        try:
                            c = Get_client_using_id(pid)
                            if c:
                                c['Socket_obj'].sendto(
                                    "Round_over".encode(), (c['Ip'], 6677)
                                )
                        except Exception:
                            pass
                    Game_initialized = False  # next cards distr

server.listen(Capacity)

Connection_thread = threading.Thread(target=Check_for_connections)
Connection_thread.start()

#print("pluh")

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
        else:
            afk = False

        if afk == False:
            try: 
                #Use a short timeout so we recheck GameSockets regularly
                client[0].settimeout(1.0)
                Packet,addr = client[0].recvfrom(2048)
                if not Packet:
                    continue
                Packet = json.loads(Packet.decode())
                response(Packet)
                Match_lobby_requests(Packet,client[0])
            except socket.timeout:
                pass    #just loop back and check GameSockets again
            except WindowsError:
                player_name = "Unknown"
                for sc in Standby_clients:
                    if sc.get('Socket_obj') == client[0]:
                        player_name = sc.get('Name', 'Unknown')
                        break
                response({'Request': 'disconnect', 'Ip': client[1][0], 'Name': player_name})
                afk = True
                return
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