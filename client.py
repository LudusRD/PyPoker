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

# Initial connection __----__ 
host_name = socket.gethostname()
ip = socket.gethostbyname(host_name)

#-
print("Welcome to PyPoker, don't judge me for bad P2P networking")


global_char_lst = []
Inp_interupted = False
Inp_finished = False

def on_unp_press(key,msg=""):
    global Inp_finished
    if Inp_interupted == True:
        print("Input interupted")
        Inp_finished = True
    if hasattr(key,'char') and key.char != None:
        global_char_lst.append(key.char)
        print(msg + ''.join(global_char_lst),end='\r')
    elif key == Key.space:
        global_char_lst.append(' ')
        print(msg + ''.join(global_char_lst),end='\r')
    elif key == Key.backspace:
        if len(global_char_lst) > 0:
            global_char_lst.pop()
        print(' '*(len(global_char_lst)+1+len(msg)),end='\r')
        print(msg + ''.join(global_char_lst),end='\r')
    elif key == Key.enter:
        Inp_finished = True


async def Unpaused_input():
    global global_char_lst, Inp_finished
    Inp_finished = False
    global_char_lst = []
    listener = Listener(on_press=on_unp_press)
    listener.start()
    if Inp_finished == True:
        return ''.join(global_char_lst)

def Interuptable_input(Timeout=None,report_int=True,message=""):
    print(message,end='\r')
    global global_char_lst, Inp_finished
    global_char_lst = []
    if Timeout != None:
        Timeout_date = datetime.now() + timedelta(seconds=Timeout)

    Inp_interupted = False
    Inp_finished = False
    listener = Listener(on_press=lambda key: on_unp_press(key,message))
    listener.start()
    while True:
        if Timeout != None and datetime.now() == Timeout_date:
            print(' '*(len(global_char_lst)+1+len(message)),end='\r')
            if report_int == True:
                print("Timedout")
            listener.stop()
            return None
        elif Inp_interupted == True:
            print(' '*(len(global_char_lst)+1+len(message)),end='\r')
            if report_int == True:
                print("Interupted")
            listener.stop()
            return None
        elif Inp_finished == True:
            listener.stop()
            return ''.join(global_char_lst)


while True:
    print("1. Find server from environment file")
    print("2. Input custom ip address")
    server_choice = input(":")

    if server_choice == "1":
        load_dotenv()
        Server_ip = getenv('Server_ip')
        break
    elif server_choice == "2":
        Server_ip = input("Input server ip:")
        break
    else:
        print("Filthy monkey can't even follow instructions")


client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)


Connected = False
while Connected == False:
    try:
        client.connect((Server_ip,6677))
        break
    except ConnectionRefusedError:
        print("Server refused connection")
    except ConnectionAbortedError:
        print("Server had an abortion")
    except ConnectionError:
        print("Idk, some error in connection")
    except OSError as e:
        if e.errno == 11001:
            print("Learn how to type IP, you dummy")
        elif e.errno == 10048:
            print("Already connected")
        elif e.errno == 10060:
            print("Connection timed out, server unrespondant")
        else:
            print("We unfortynately got an error. We how now idea what is it, but here it is:")
            print(e)
        break
    except:
        print("damn, i don't know what error you got?")
    sleep(0.5)
#------------------____________---------------------

print(client)
#-
    


def Send_request():
    global Packet
    Request = json.dumps(Packet)
    client.send(Request.encode())
    data = None
    while data == None:
        try:
            data, addr = client.recvfrom(2048)
        except:
            print("Response request failed, server unrespondant")
    return data.decode()
#-
def Room_setup():
    global Packet
    Name = input("Input Room name: ")
    Password = input("*optional, input password: ")
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
        print("")
        print("Input Exit to exit or,")
        id = input("Input the Id of the room you want to join: ")

        #Sends room join request
        if id.isnumeric():
            id = int(id)
            Password = input("Input password(if password is none doesn't matter) :")
            Packet['Request'] = "Join_room"
            Packet['Rq_spec'] = {"id":id,"Password":Password}
            Result = Send_request()
            if Result == "Sucess":
                Packet['Room']['ingame'] = True
                Packet['Room']['id'] = id
                In_lobby = True
                break
            else:
                print("Join failed")
        #Else goes back to main page
        else:
            Browsing_lobbies = False
            break
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

Packet['Name'] = input("Please input a suitable Name, (there are no curse filters): ")
Packet['Request'] = "Init"
Send_request()

In_lobby = False
Game_started = False
Browsing_lobbies = False

#While loop
while True:
    if In_lobby == False:
        #Main screen where you can join, create and exit
        if Browsing_lobbies == True:
            Join_room()
        else:
            print("1. Check/join Available lobbies")
            print("2. Create Lobby")
            print("3. exit")
            Lobby_choice = input("")
            #sends request, server doesn't change player variables, server sends back
            # List of lobbies
            if Lobby_choice == "1": #See öabbies
                Packet['Request'] = "Get_lobbies"

                lobby_list = json.loads(json.loads(Send_request()))
                for dict in lobby_list:
                    for item in dict.items():
                        print(item)
                    print("")
                Browsing_lobbies = True
                #Join_room()  #Join lobby or not
            
            #sends request, server changes player variable 
            elif Lobby_choice == "2":  #Setup lobby
                Room_name = Room_setup()
                #Reminder for later, Room_setup changes Packet['Request']
                status = Send_request()
                print(status)
                if status[:6] == "Sucess":
                    Packet['Is_host'] = True
                    Packet['Room']['id'] = status[7:]
                    Packet['Room']['Room_name'] = Room_name
                    In_lobby = True
                else:
                    print('Create room failed')
            #--__--
            elif Lobby_choice == "3": #Rage quit
                break
            else: #Pretty self explanatory
                print("Invalid option")
    else:
        #Inside of a lobby
        if Game_started == False:
            print("1. start game")
            print("2. leave lobby/close lobby")
            Lobby_choice = None
            while Lobby_choice is None:
                try:
                    client.settimeout(0.1)
                    msg, addr = client.recvfrom(2048)
                    if msg.decode() == "start_game":
                        print("Host started the game!")
                        Game_started = True
                        break
                except socket.timeout:
                    pass
                finally:
                    client.settimeout(None)
                Lobby_choice = Interuptable_input(Timeout=2, report_int=False)
            if Game_started == True:
                continue

            if Lobby_choice == "1":
                Packet['Request'] = "start game"
                answer = Send_request()
                if answer == "Sucess":
                    Game_started = True
                elif answer == "Not_host":
                    print("Only host can start")
                else:
                    print("stargame failed")
            elif Lobby_choice == "2":
                if Packet['Room']['Is_host'] == True: #Checks if is_host on client side
                    Packet['Request'] = "close lobby"
                    answer = Send_request()
                    if answer == "Sucess":
                        print("closed lobby")
                        Reset_room_info()
                        In_lobby = False
                    else: #If the server returns failed then the client has tampered with it's own values somehow
                        print("!!Error, client and server packets don't line up. Defaulting to leaving lobby")
                        print("Left lobby")
                        Reset_room_info()
                        In_lobby = False
                else:
                    Packet['Request'] = "leave"
                    Send_request()
                    print("Left lobby")
                    Reset_room_info()
                    In_lobby = False
            else:
                print("invalid choice")
        #Game loop
        else:
            client.settimeout(40)
            #Receive game start message
            msg, addr = client.recvfrom(2048)
            msg = msg.decode()
            print(msg[:13])

            #Recieve cards
            Packet['Cards'] = json.loads(msg[13:])
            print("Your cards:")
            for card in Packet['Cards']:
                print(f"  {card['rank']} of {card['suit']}")

            #Client's actions
            folded = False  #tracks whether this player has folded or not this round
            while True:
                message = client.recv(2048).decode()
                print(message)

                if message == "Game_over":
                    print("Game over!")
                    Game_started = False
                    folded = False
                    Reset_room_info()
                    In_lobby = False
                    break
                if message == "Round_over":
                    print("Round over.")
                    folded = False
                    break
                if (message.startswith("Waiting for player") or
                        message.startswith("Bet:") or
                        message.startswith("Called:") or
                        message == "Folded" or
                        message == "Checked"):
                    continue
                if message == "Your turn":
                    if folded:
                        continue
                    print("1. fold")
                    print("2. check")
                    print("3. bet")
                    print("4. call")
                    action_choice = Interuptable_input(Timeout=30,report_int=False)

                    if action_choice != None:
                        if action_choice == "1":
                            result = Send_action("fold")
                            print(result)
                            folded = True
                        elif action_choice == "2":
                            result = Send_action("check")
                            print(result)
                        elif action_choice == "3":
                            amount = int(input("Bet amount: "))
                            result = Send_action("bet", amount)
                            print(result)
                        elif action_choice == "4":
                            amount = int(input("Call amount: "))
                            result = Send_action("call", amount)
                            print(result)
                        else:
                            print("invalid choice")
                    else:  #Timedout
                        print("Timed out,defaulting to fold")
    #client.sendto(("Hello from client".encode()),(Server_ip,6677))
                        folded = True

print("thanks for playing pypoker!")