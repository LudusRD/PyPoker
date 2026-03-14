import socket
from os import environ,getenv
from dotenv import load_dotenv,dotenv_values
from time import sleep

load_dotenv()

client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
Server_ip = getenv('Server_ip')

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


while True:
    client.sendto(("Hello from client".encode()),(Server_ip,6677))