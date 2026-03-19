import socket
from os import environ,getenv
#Im lazy to install it
from dotenv import load_dotenv,dotenv_values
from time import sleep
import json
from P2P_testing import Generate_random_num_id
import asyncio

# Initial connection __----__ 
host_name = socket.gethostname()
ip = socket.gethostbyname(host_name)

#-
print("Welcome to PyPoker, don't judge me for bad P2P networking")

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

async def Check_recv(socket):
    message = socket.recv(2048)
    return message
    


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
    Password = input("*optional, input password")
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
        print("Input the Id of the room you want to join")
        print("Or input exit")
        id = input("Input the Id of the room you want to join")
        Password = input("Input password(if password is none doesn't matter)")

        #Sends room join request
        if id.isnumeric():
            id = int(id)
            Packet['Request'] = "Join_room"
            Packet['Rq_spec'] = {"id":id,"Password":Password}
            Result = Send_request()
            if Result == "Sucess":
                Packet['Room']['ingame'] = True
                Packet['Room']['id'] = id
                In_lobby = True
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

Packet['Name'] = input("Please input a suitable Name, (there are no curse filters)")
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
            #Join_room()
            pass
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

                Checking_lobby_list = True
                for dict in lobby_list:
                    for item in dict.items():
                        print(item)
                    print("")
                Browsing_lobbies = True
                Join_room()  #Join lobby or not
            
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
            Lobby_choice = input()

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
                Packet['Request'] = "leave"
                Send_request()
            else:
                print("invalid choice")
        #Game loop
        else:
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
            while True:
                message = client.recvfrom(2048).decode()
                print(message)

                if message == "Your turn":
                    print("1. fold")
                    print("2. check")
                    print("3. bet")
                    print("4. call")
                    action_choice = input("")

                    if action_choice == "1":
                        result = Send_action("fold")
                        print(result)
                        break
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

    #client.sendto(("Hello from client".encode()),(Server_ip,6677))

print("thanks for playing pypoker!")