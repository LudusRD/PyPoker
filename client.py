import socket
from os import environ,getenv
#I actually did install it
from dotenv import load_dotenv,dotenv_values
from time import sleep
import json
from P2P_testing import Generate_random_num_id
import asyncio
import signal
import threading
from pynput.keyboard import Listener, Key
from datetime import datetime,timedelta
from sys import stdin,stdout
import os


#UI ENGINE
os.system("") # Support for ANSI colors

#Colors settings
C = {
    'RES': '\033[0m', 'BOLD': '\033[1m', 'GREY': '\033[90m', 'RED': '\033[91m',
    'GREEN': '\033[92m', 'YELLOW': '\033[93m', 'BLUE': '\033[94m', 'CYAN': '\033[96m',
    'WHITE': '\033[97m', 'BG_GREEN': '\033[42m', 'BG_WHITE': '\033[47m', 'FG_BLACK': '\033[30m',
}

#Signs
F = {'H': '═', 'V': '║', 'TL': '╔', 'TR': '╗', 'BL': '╚', 'BR': '╝', 'SH': '─'}
S_MAP = {'S': '♠', 'H': f"{C['RED']}♥{C['RES']}", 'D': f"{C['RED']}♦{C['RES']}", 'C': '♣'}

def align(text, width, align_type='center', fill=' '):
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    visible_len = len(ansi_escape.sub('', text))
    pad = width - visible_len
    if pad <= 0: return text
    if align_type == 'left': return text + (fill * pad)
    if align_type == 'right': return (fill * pad) + text
    left_pad = pad // 2
    return (fill * left_pad) + text + (fill * (pad - left_pad))

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit 
    def __str__(self):
        r = f"{self.rank:>2}"
        return f"{C['BG_WHITE']}{C['FG_BLACK']}{S_MAP.get(self.suit, self.suit)}{r} {C['RES']}"

class UIPlayer:
    def __init__(self, name, chips, is_user=False, folded=False):
        self.name = name
        self.chips = chips
        self.cards = []
        self.is_user = is_user
        self.folded = folded

class PokerUI:
    def __init__(self):
        self.W = 70 
        self.game_log = []
        self.reset_game_state()

    def reset_game_state(self):
        self.board = []
        self.pot = 0
        self.u_players = [] 
        self.current_bet = 0

    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def add_log(self, msg):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.game_log.append(f"[{C['GREY']}{time_str}{C['RES']}] {msg}")
        if len(self.game_log) > 6: self.game_log.pop(0)

    def draw_header(self, title):
        print(f"{C['CYAN']}{F['TL']}{F['H']*(self.W-2)}{F['TR']}{C['RES']}")
        content = f"{C['BOLD']}{C['YELLOW']}{title.upper()}{C['RES']}"
        print(f"{C['CYAN']}{F['V']}{C['RES']}{align(content, self.W-2)}{C['CYAN']}{F['V']}{C['RES']}")
        print(f"{C['CYAN']}{F['BL']}{F['H']*(self.W-2)}{F['BR']}{C['RES']}\n")

    def draw_box_line(self, content, color=C['CYAN'], align_type='center'):
        colored_v = f"{color}{F['V']}{C['RES']}"
        print(f"{colored_v}{align(content, self.W-2, align_type)}{colored_v}")

    def draw_sep(self, color=C['CYAN']):
        print(f"{color}{F['V']}{F['SH']*(self.W-2)}{F['V']}{C['RES']}")

    def render_connect_screen(self, status_msg="Waiting for selection..."):
        self.clear()
        self.draw_header("PyPoker P2P: Connection")
        print(f"{C['WHITE']}Choose connection method:{C['RES']}\n")
        print(f" [{C['GREEN']}1{C['RES']}] Find server from .env")
        print(f" [{C['GREEN']}2{C['RES']}] Input custom IP")
        #print(f" [{C['RED']}4{C['RES']}] DEBUG MODE (Offline bypass)")
        #nobody knows but it exists
        #i wanted to check ui without a server
        
        print(f"\n{C['CYAN']}{F['TL']}{F['H']*(self.W-2)}{F['TR']}{C['RES']}")
        status_content = f"{C['BOLD']}STATUS:{C['RES']} {status_msg}"
        self.draw_box_line(status_content)
        print(f"{C['CYAN']}{F['BL']}{F['H']*(self.W-2)}{F['BR']}{C['RES']}")

    def render_main_menu(self, player_name):
        self.clear()
        self.draw_header(f"Main Menu | Welcome, {player_name}")
        print(f" [{C['GREEN']}1{C['RES']}] Check/Join available lobbies")
        print(f" [{C['GREEN']}2{C['RES']}] Create new lobby")
        print(f" [{C['RED']}3{C['RES']}] Exit game")
        print("\n" + F['SH']*self.W)

    def render_lobby_list(self, lobbies_data):
        self.clear()
        self.draw_header("Available Lobbies")
        if not lobbies_data or lobbies_data == "[]" or lobbies_data == '""':
            print(f"{C['GREY']}{'No lobbies available. Create one!':^self.W}{C['RES']}\n")
        else:
            try:
                lobbies = json.loads(lobbies_data)
                header = f"{'ID':<5} | {'Name':<25} | {'Players':<8} | {'Pass':<7}"
                print(f"{C['BOLD']}{header}{C['RES']}\n{F['SH']*self.W}")
                for l in lobbies:
                    l_id = str(l.get('3', 'Id: ?')).split(': ')[-1]
                    l_name = str(l.get('1', 'Lobby_name: ?')).split(': ')[-1][:23]
                    l_count = str(l.get('2', 'Player_amount: ?')).split(': ')[-1]
                    l_pass = "Yes" if l.get('4', 'Has_password: False') == 'Has_password: True' else "No"
                    print(f"{l_id:<5} | {l_name:<25} | {l_count:<8} | {l_pass:<7}")
            except: print(f"{C['RED']}Failed to parse lobbies.{C['RES']}")
        print(f"\n{F['SH']*self.W}")

    def render_in_lobby(self, room_name, room_id, players_list, is_host):
        self.clear()
        self.draw_header(f"Lobby: {room_name} (ID: {room_id})")
        print(f"{C['BOLD']}{C['WHITE']}Players List:{C['RES']}\n")
        for p in players_list:
            prefix = f"{C['YELLOW']}[HOST]{C['RES']} " if p['Room']['Is_host'] else "       "
            print(f" {prefix}{C['GREEN']}{p['Name']}{C['RES']}")
        print(f"\n{F['SH']*self.W}")
        if is_host:
            print(f" [{C['GREEN']}1{C['RES']}] Start Game\n [{C['RED']}2{C['RES']}] Close Lobby")
        else:
            print(f" Waiting for host...\n [{C['RED']}2{C['RES']}] Leave Lobby")

    def render_table(self):
        self.clear()
        content = f"{C['BOLD']}TEXAS HOLD'EM | POT: {C['GREEN']}${self.pot}{C['RES']}"
        print(f"{C['CYAN']}{F['TL']}{F['H']*(self.W-2)}{F['TR']}{C['RES']}")
        print(f"{C['CYAN']}{F['V']}{C['RES']}{align(content, self.W-2)}{C['CYAN']}{F['V']}{C['RES']}")
        
        empty_card = f"{C['GREY']}[   ]{C['RES']}"
        cards_raw = [str(c) for c in self.board]
        while len(cards_raw) < 5: cards_raw.append(empty_card)
        board_str = "  ".join(cards_raw)
        
        print(f"{C['CYAN']}{F['V']}{C['RES']}{align(board_str, self.W-2)}{C['CYAN']}{F['V']}{C['RES']}")
        print(f"{C['CYAN']}{F['BL']}{F['H']*(self.W-2)}{F['BR']}{C['RES']}\n")

        log_h = f"{C['BOLD']}{C['YELLOW']}GAME LOG{C['RES']}"
        print(f"{C['GREY']}{F['TL']}{F['H']*(self.W-2)}{F['TR']}{C['RES']}")
        self.draw_box_line(log_h, color=C['GREY'])
        self.draw_sep(color=C['GREY'])
        for log in self.game_log: self.draw_box_line(log, color=C['GREY'], align_type='left')
        for _ in range(6 - len(self.game_log)): self.draw_box_line("", color=C['GREY'])
        print(f"{C['GREY']}{F['BL']}{F['H']*(self.W-2)}{F['BR']}{C['RES']}\n")

        user = next((p for p in self.u_players if p.is_user), None)
        if user:
            u_cards = " ".join([str(c) for c in user.cards])
            info = f"{C['BOLD']}{C['GREEN']}${user.chips}{C['RES']}"
            f_status = f" {C['RED']}(Folded){C['RES']}" if user.folded else ""
            print(f" {C['WHITE']}[ YOU ]{C['RES']} Stack: {info}{f_status}")
            print(f"         Cards: {u_cards}\n")

ui = PokerUI()
#UI finished here

# Initial connection __----__ 
host_name = socket.gethostname()
ip = socket.gethostbyname(host_name)

#-
print("Welcome to PyPoker, don't judge me for bad P2P networking")


global_char_lst = []
Inp_interupted = False
Inp_finished = False
Need_buffer_clear = True #bool to check buffer

def on_unp_press(key,msg=""): 
    global Inp_finished
    global global_char_lst
    if Inp_interupted == True:
        #print("Input interupted")
        Inp_finished = True
    if hasattr(key,'char') and key.char != None:
        global_char_lst.append(key.char)
        print('\r' + msg + ''.join(global_char_lst) + ' ', end='\r')
    elif key == Key.space:
        global_char_lst.append(' ')
        print('\r' + msg + ''.join(global_char_lst) + ' ', end='\r')
    elif key == Key.backspace:
        if len(global_char_lst) > 0:
            global_char_lst.pop()
        print('\r' + msg + ''.join(global_char_lst) + '  ', end='\r')
    elif key == Key.enter:
        Inp_finished = True


async def Unpaused_input():
    global global_char_lst, Inp_finished
    Inp_finished = False
    global_char_lst = []
    listener = Listener(on_press=on_unp_press)
    listener.start()
    while not Inp_finished: sleep(0.05)
    listener.stop()
    return ''.join(global_char_lst)

def Interuptable_input(Timeout=None,report_int=True,message="",Ret_none=True, clear_buffer=True):
    global global_char_lst, Inp_finished, Inp_interupted, Need_buffer_clear
    
    #Check if we need to wipe the typing buffer
    if clear_buffer or Need_buffer_clear:
        global_char_lst = []
        Need_buffer_clear = False
        
    Inp_interupted = False
    Inp_finished = False

    if Timeout != None:
        Timeout_date = datetime.now() + timedelta(seconds=Timeout)

    listener = Listener(on_press=lambda key: on_unp_press(key,message))
    listener.start()
    
    #Just for a test
    print('\r' + message + ''.join(global_char_lst), end='\r')

    while True:
        if Timeout != None and datetime.now() >= Timeout_date:
            listener.stop()
            return None
            
        elif Inp_interupted == True:
            print(' '*(len(global_char_lst)+1+len(message)),end='\r')
            listener.stop()
            if Ret_none == True: return None
            else: return ''.join(global_char_lst)
            
        elif Inp_finished == True:
            listener.stop()
            Need_buffer_clear = True
            
            try:
                import msvcrt
                while msvcrt.kbhit(): msvcrt.getch()
            except ImportError:
                pass
                
            print('\r' + ' ' * (len(message) + len(global_char_lst) + 2), end='\r')
            return ''.join(global_char_lst)
        sleep(0.05)


DEBUG_MODE = False
Connected = False

while not Connected:
    ui.render_connect_screen()
    server_choice = input(f"{C['GREEN']}> {C['RES']}")

    if server_choice == "1":
        ui.render_connect_screen("Loading .env...")
        load_dotenv()
        Server_ip = getenv('Server_ip')
        if not Server_ip: 
            Server_ip = "INVALID" # Force error if file is missing
    elif server_choice == "2":
        ui.render_connect_screen("Waiting for IP...")
        Server_ip = input("Input server ip: ")
    elif server_choice == "4":
        DEBUG_MODE = True
        Server_ip = "127.0.0.1"
        ui.render_connect_screen("DEBUG MODE ACTIVATED. Bypassing server.")
        sleep(1)
        Connected = True
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        break
    else:
        ui.render_connect_screen(f"{C['RED']}Filthy monkey can't even follow instructions{C['RES']}")
        sleep(1)
        continue

    attempts = 0
    #try 5 times
    while attempts < 5 and not Connected:
        #Recreate socket per attempt, otherwise Python blocks retrying a dead connection
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect((Server_ip, 6677))
            Connected = True
        except Exception as e:
            attempts += 1
            if server_choice == "1":
                ui.render_connect_screen(f"{C['RED']}damn, i don't know what error you got? ({attempts}/5){C['RES']}")
            else:
                if isinstance(e, ConnectionRefusedError):
                    ui.render_connect_screen(f"Server refused connection ({attempts}/5)")
                elif isinstance(e, ConnectionAbortedError):
                    ui.render_connect_screen(f"Server had an abortion ({attempts}/5)")
                elif isinstance(e, OSError):
                    if e.errno == 11001:
                        ui.render_connect_screen(f"Learn how to type IP, you dummy ({attempts}/5)")
                    elif e.errno == 10048:
                        ui.render_connect_screen(f"Already connected ({attempts}/5)")
                    elif e.errno == 10060:
                        ui.render_connect_screen(f"Connection timed out, server unrespondant ({attempts}/5)")
                    else:
                        ui.render_connect_screen(f"Unknown Error: {e} ({attempts}/5)")
                else:
                    ui.render_connect_screen(f"damn, i don't know what error you got? ({attempts}/5)")
            sleep(1)

    if not Connected:
        ui.render_connect_screen(f"{C['RED']}Failed 5 times. Returning to main menu...{C['RES']}")
        sleep(2)

#------------------____________---------------------

def Send_request():
    global Packet
    if DEBUG_MODE:
        sleep(0.2)
        if Packet['Request'] == 'Get_lobbies': return "[]"
        if Packet['Request'] == 'Create_lobby': return "Sucess:999"
        if Packet['Request'] == 'Join_room': return "Sucess"
        return "Sucess"

    Request = json.dumps(Packet)
    client.send(Request.encode())
    data = None
    client.settimeout(3.0)
    try:
        data, addr = client.recvfrom(2048)
        return data.decode()
    except:
        return "Error: No Response"
    finally:
        client.settimeout(None)
#-
def Room_setup():
    global Packet
    ui.clear()
    ui.draw_header("Lobby Setup")
    Name = input(f"{C['YELLOW']}Input Room name:{C['RES']} ")
    Password = input(f"{C['YELLOW']}*optional, input password:{C['RES']} ")
    if Password == "": Password = None
    #-
    Packet['Request'] = 'Create_lobby'
    Packet['Rq_spec'] = {"Name":Name,"Password":Password}
    return Name

def Join_room():
    global Packet
    global Browsing_lobbies
    global In_lobby

    #
    while True:
        id_str = input(f"{C['GREEN']}Input the ID to join (or Exit):{C['RES']} ")
        
        if id_str.lower() == 'exit':
            Browsing_lobbies = False
            break

        #Sends room join request
        if id_str.isnumeric():
            id = int(id_str)
            Password = input(f"{C['YELLOW']}Input password:{C['RES']} ")
            Packet['Request'] = "Join_room"
            Packet['Rq_spec'] = {"id":id,"Password":Password}
            Result = Send_request()
            if Result == "Sucess":
                Packet['Room']['ingame'] = True
                Packet['Room']['id'] = id
                In_lobby = True
                global tot_message
                tot_message = ""
                break
            elif Result == "Game_already_started":
                print(f"{C['RED']}Cannot join- game is already in progress!{C['RES']}")
                sleep(1)
            else:
                print(f"{C['RED']}Join failed{C['RES']}")
                sleep(1)
        else:
            print(f"{C['RED']}Invalid ID{C['RES']}")
            sleep(0.5)
#
def Send_action(action, amount=None):
    global Packet
    Packet['Request'] = action
    if amount is not None:
        Packet['Rq_spec'] = {'amount': amount}
    else:
        Packet['Rq_spec'] = {}
    return Send_request()

#Packet to send to the server
Packet = {
    "Socket_obj":f"{client}",
    "Name":"",
    "id":Generate_random_num_id(),
    "Ip":ip,
    "Request":"",
    'Rq_spec':{},

    "Cards":[],
    "Room":{
        "ingame":False,
        "id":"",
        "Room_name":"",
        "Is_host":False,
    }
}

def Reset_room_info():  #Wait a second? Why have we put Cards outside of Packet['room']? eh im to tired to fix it...
    Packet['Cards'] = []
    Packet['Room'] ={
        "ingame":False,
        "id":"",
        "Room_name":"",
        "Is_host":False,
    }

ui.clear()
ui.draw_header("Player Registration")
Packet['Name'] = input(f"{C['YELLOW']}Please input a suitable Name, (there are no curse filters):{C['RES']} ")
Packet['Request'] = "Init"
Send_request()

In_lobby = False
Game_started = False
Browsing_lobbies = False


tot_message = ""
#While loop
while True:
    if In_lobby == False:
        #Main screen where you can join, create and exit
        if Browsing_lobbies == True:
            Join_room()
        else:
            ui.render_main_menu(Packet['Name'])
            Lobby_choice = input(f"{C['GREEN']}> {C['RES']}")
            #sends request, server doesn't change player variables, server sends back
            # List of lobbies
            if Lobby_choice == "1": #See öabbies
                Packet['Request'] = "Get_lobbies"
                raw_lobbies = Send_request()
                if "Error" not in raw_lobbies:
                    try:
                        #Safely handle double-encoded JSON strings from the server
                        parsed = json.loads(raw_lobbies)
                        if isinstance(parsed, str): 
                            parsed = json.loads(parsed)
                        ui.render_lobby_list(json.dumps(parsed))
                        Browsing_lobbies = True
                    except:
                        #If parsing fails entirely - we just show an empty list to avoid the red error
                        ui.render_lobby_list("[]")
                        Browsing_lobbies = True
            
            #sends request, server changes player variable 
            elif Lobby_choice == "2":  #Setup lobby
                Room_name = Room_setup()
                #Reminder for later, Room_setup changes Packet['Request']
                status = Send_request()
                if status[:6] == "Sucess":
                    Packet['Room']['Is_host'] = True
                    Packet['Room']['id'] = status[7:]
                    Packet['Room']['Room_name'] = Room_name
                    In_lobby = True
                    tot_message = ""
                else:
                    print(f"{C['RED']}Create room failed{C['RES']}"); sleep(1)
            #--__--
            elif Lobby_choice == "3": #Rage quit
                break
            else: #Pretty self explanatory
                print(f"{C['RED']}Invalid option{C['RES']}"); sleep(0.5)
    else:
        #Inside of a lobby
        if Game_started == False:
            Lobby_choice = None
            try:
                if not DEBUG_MODE:
                    client.settimeout(0.25)
                    msg, addr = client.recvfrom(2048)
                    tot_message += msg.decode()
                    if tot_message[:10] == "start_game" or "start_game" in tot_message:
                        ui.add_log("Host started the game!")
                        Game_started = True
                        continue
            except socket.timeout:
                pass
            finally:
                if not DEBUG_MODE: client.settimeout(None)
            
            Players = Send_action("GetPlayers")
            dummy_list = json.loads(Players)
            ui.render_in_lobby(Packet['Room']['Room_name'], Packet['Room']['id'], dummy_list, Packet['Room']['Is_host'])
            
            Lobby_choice = Interuptable_input(Timeout=2, report_int=False, Ret_none=True, message=f"{C['GREEN']}> {C['RES']}", clear_buffer=False)
            if Game_started == True:
                continue

            if Lobby_choice == "1":
                Packet['Request'] = "start game"
                answer = Send_request()
                if answer == "Sucess":
                    ui.add_log("Game started by you.")
                    Game_started = True
                elif answer == "Not_host":
                    print(f"\r{C['RED']}Only host can start{C['RES']}"); sleep(1)
                else:
                    print(f"\r{C['RED']}stargame failed{C['RES']}"); sleep(1)
            elif Lobby_choice == "2":
                if Packet['Room']['Is_host'] == True: #Checks if is_host on client side
                    Packet['Request'] = "close lobby"
                    answer = Send_request()
                    if answer == "Sucess":
                        ui.add_log("Closed lobby")
                        Reset_room_info()
                        In_lobby = False
                    else: #If the server returns failed then the client has tampered with it's own values somehow
                        ui.add_log("Error, client/server desync. Leaving.")
                        Reset_room_info()
                        In_lobby = False
                else:
                    Packet['Request'] = "leave"
                    Send_request()
                    ui.add_log("Left lobby")
                    Reset_room_info()
                    In_lobby = False
                sleep(1)
            elif Lobby_choice is None or Lobby_choice == "":
                pass
            else:
                pass
        #Game loop
        else:
            if not DEBUG_MODE:
                try:
                    client.settimeout(40)
                    #Receive game start message
                    msg, addr = client.recvfrom(2048)
                    msg = msg.decode()
                    
                    ui.reset_game_state()
                    #Recieve cards
                    try:
                        Packet['Cards'] = json.loads(msg[13:])
                    except:
                        try:
                            Packet['Cards'] = json.loads(msg[23:])
                        except:
                            try:
                                Packet['Cards'] = json.loads(tot_message[23:])
                            except:
                                print(msg)
                                print(tot_message)
                                print("Error loading")

                    user = UIPlayer(Packet['Name'], 1000, is_user=True)
                    user.cards = [Card(c['rank'], c['suit']) for c in Packet['Cards']]
                    ui.u_players = [user]
                    ui.add_log("Cards received. Game on!")
                    ui.render_table()
                except Exception as e:
                    ui.add_log(f"Error starting: {e}")
                    Game_started = False; In_lobby = False; continue
                finally:
                    client.settimeout(None)
            else:
                ui.reset_game_state()
                ui.add_log("Debug Mode: Bypassed card dealing.")
                ui.add_log("No server connected. Press Enter to exit...")
                ui.render_table()
                input() #Wait
                Game_started = False; In_lobby = False; continue

            #Client's actions
            folded = False  #tracks whether this player has folded or not this round
            current_bet = current_pot = 0
            while Game_started:
                try:
                    raw_msg = client.recv(2048)
                    if not raw_msg: break
                    message = raw_msg.decode()

                    if message == "Game_over":
                        ui.add_log("Game over!")
                        ui.render_table()
                        answer = input(f" {C['YELLOW']}Go to menu? (y/n):{C['RES']} ")
                        if answer.lower() != 'y':
                            print(f" {C['RED']}Sorry, gotta kick you out anyway.{C['RES']}")
                            sleep(1)
                        Game_started = False
                        folded = False
                        Reset_room_info()
                        In_lobby = False
                        break

                    if message == "Round_over":
                        ui.add_log("Round over.")
                        ui.current_bet = 0
                        ui.render_table()
                        answer = input(f" {C['YELLOW']}Go to menu? (y/n):{C['RES']} ")
                        if answer.lower() != 'y':
                            print(f" {C['RED']}Sorry, gotta kick you out anyway.{C['RES']}")
                            sleep(1)
                        Game_started = False
                        folded = False
                        Reset_room_info()
                        In_lobby = False
                        break

                    if message.startswith("Community:"):
                        community = json.loads(message[10:])
                        ui.board = [Card(c['rank'], c['suit']) for c in community]
                        ui.add_log("Community cards updated.")
                        ui.render_table()
                        continue

                    if message.startswith("Bet:") or message.startswith("Raise:"):
                        # Format is "Bet:XYZ:Pot:XYZ" or "Raise:XYZ:Pot:XYZ"
                        parts = message.split(":")
                        current_bet = int(parts[1])
                        current_pot = int(parts[3]) if len(parts) >= 4 else current_pot
                        ui.pot = current_pot
                        ui.current_bet = current_bet
                        act = "Bet" if message.startswith("Bet:") else "Raise"
                        ui.add_log(f"{act}: ${current_bet}")
                        ui.render_table()
                        continue
                        
                    if message.startswith("Called:"):
                        parts = message.split(":")
                        current_pot = int(parts[3]) if len(parts) >= 4 else current_pot
                        ui.pot = current_pot
                        ui.add_log(f"Player called. Pot: ${current_pot}")
                        ui.render_table()
                        continue

                    if message.startswith("Winner:"):
                        parts = message.split(":")
                        ui.add_log(f"{C['RED']}Winner: {parts[1]} ({parts[2]}){C['RES']}")
                        ui.render_table()
                        continue

                    if (message.startswith("Waiting for player") or
                            message.startswith("Cannot_") or
                            message == "Folded" or
                            message == "Checked"):
                        if message.startswith("Waiting"): pass #Keep silent to avoid spam
                        else: ui.add_log(message); ui.render_table()
                        continue
                        
                    if message == "Your turn" or message[10:] == "Your turn":
                        if folded:
                            continue
                        
                        ui.render_table()
                        print(f" {C['BOLD']}{C['YELLOW']}--- YOUR TURN ---{C['RES']}")
                        print(f" [Pot: {C['GREEN']}${ui.pot}{C['RES']} | Current bet: {C['RED']}${ui.current_bet}{C['RES']}]")
                        
                        if current_bet == 0:
                            print(f" [{C['GREY']}1{C['RES']}] Fold   [{C['BLUE']}2{C['RES']}] Check   [{C['YELLOW']}3{C['RES']}] Bet")
                        else:
                            print(f" [{C['GREY']}1{C['RES']}] Fold   [{C['BLUE']}2{C['RES']}] Call    [{C['YELLOW']}3{C['RES']}] Raise")
                        
                        action_choice = Interuptable_input(Timeout=30,report_int=False, message=f" {C['GREEN']}> {C['RES']}", clear_buffer=True)

                        if action_choice != None:
                            if action_choice == "1":
                                result = Send_action("fold")
                                ui.add_log("You folded.")
                                folded = True
                                user.folded = True
                            elif action_choice == "2":
                                if current_bet == 0:
                                    result = Send_action("check")
                                    ui.add_log("You checked.")
                                else:
                                    result = Send_action("call")
                                    ui.add_log("You called.")
                                    user.chips -= current_bet
                            elif action_choice == "3":
                                ui.render_table()
                                print(f" {C['BOLD']}{C['YELLOW']}--- AMOUNT ---{C['RES']}")
                                if current_bet == 0:
                                    try:
                                        amount = int(input(f" {C['YELLOW']}Bet amount:{C['RES']} "))
                                        result = Send_action("bet", amount)
                                        ui.add_log(f"Bet placed: ${amount}")
                                        user.chips -= amount
                                    except: ui.add_log("Invalid amount.")
                                else:
                                    try:
                                        amount = int(input(f" {C['YELLOW']}Raise to (> {current_bet}):{C['RES']} "))
                                        result = Send_action("raise", amount)
                                        ui.add_log(f"Raised to: ${amount}")
                                        user.chips -= amount
                                    except: ui.add_log("Invalid amount.")
                            else:
                                ui.add_log("Invalid choice.")
                            ui.render_table()
                        else:  #Timedout
                            ui.add_log("Timed out, defaulting to fold.")
                            folded = True
                            user.folded = True
                            Send_action("fold")
                            ui.render_table()
                except socket.timeout: pass
                except Exception as e:
                    ui.add_log(f"Error: {e}")
                    Game_started = False

print("Thanks for playing PyPoker!")