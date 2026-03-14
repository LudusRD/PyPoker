import socket
from os import environ

client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
Server_ip = environ.get('Server_ip',None)

if Server_ip != None:
    try:
        client.connect(Server_ip,6677)
    except ConnectionRefusedError:
        print("Server refused connection")
    except ConnectionAbortedError:
        print("Timedout, server not found")
    except ConnectionError:
        print("Idk, some error in connection")


while True:
    client.sendto(("Hello from client".encode()),(Server_ip,6677))