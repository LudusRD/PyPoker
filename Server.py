import socket
from os import environ

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
Capacity = 4

server.bind(('127.0.0.1',6677))
server.listen(Capacity)

print (server)
client = None

while client == None:
    client, addr = server.accept()

while True:
    print(client.recv(1024).decode())