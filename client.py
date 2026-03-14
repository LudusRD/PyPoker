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
    print("1. Find server from enviorment file")
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
    except:
        print("damn, i don't know what error you got?")
    sleep(0.5)
#------------------____________---------------------

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
Packet = {
    "Name":"",
    "id":"",
    "Ip":"",
    "Is_host":False,
    "Request":""
}
Packet['id'] = Generate_random_num_id()
Packet['Ip'] = ip

Packet['Name'] = input("Please input a suitable Name, (there are no curse filters)")


while True:
    print("1. Check/join Available lobbies")
    print("2. Create Lobby")
    print("3. exit")
    Lobby_choice = input("")
    if Lobby_choice == "1":
        Packet['Request'] = "Get_lobbies"
        lobby_list = json.loads(Send_request())

        Checking_lobby_list = True
        print(lobby_list)

    elif Lobby_choice == "2":
        Packet['Request'] = "Create_lobby"
        status = Send_request()
        In_lobby = True

    elif Lobby_choice == "3":
        break
    else:
        print("Invalid option")



    client.sendto(("Hello from client".encode()),(Server_ip,6677))