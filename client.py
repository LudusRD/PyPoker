import socket
from os import environ,getenv
from dotenv import load_dotenv,dotenv_values
from time import sleep
import json
from P2P_testing import Generate_random_num_id


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
    except ConnectionRefusedError:
        print("Server refused connection")
    except ConnectionAbortedError:
        print("Server had an abortion")
    except ConnectionError:
        print("Idk, some error in connection")
    except OSError:
        print("Already connected")
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
            Packet['Request'] = "Join_room"
            Packet['Rq_spec'] = {"id":id,"Password":Password}
            Result = Send_request()
            if Result == "Sucess":
                Packet['Room']['ingame'] = True
                Packet['Room']['id'] = id
        #Else goes back to main page
        else:
            Browsing_lobbies = False
            break

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
                if status[:6] == "Sucess":
                    Packet['Is_host'] = True
                    Packet['Room']['id'] = status[7:]
                    Packet['Room']['Room_name'] = Room_name
                    In_lobby = True
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


            #Maybe just recieve info and don't send a whole ass package


            #Packet['Request'] = "Room_status"
            #Room_status = json.loads(json.loads(Send_request()))
            #print("Game started = False")
            #print("Players: ")
            #for dict in Room_status:
            #    print("Player: ")
            #    for item in dict.items():
            #        print(item)
            #    print("")
            pass

            



    #client.sendto(("Hello from client".encode()),(Server_ip,6677))

print("thanks for playing pypoker!")