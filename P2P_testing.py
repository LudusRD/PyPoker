import json
from os import path
import random
import socket
import rich

Hostname = socket.gethostname()
Ip_addr = socket.gethostbyname(Hostname)

Base_dir = path.dirname(path.realpath(__file__))
Json_path = path.join(Base_dir,"Logic_json.json")
#print("Base dir is: " + Base_dir)
#print("Json path is: " + Json_path)
def Setup_Logic_Json():
    with open(Json_path,"a") as json_file:
        Hard_reset_json()

def Hard_reset_json():
    hard_reset_data={
        "C_room_id": 0,
        "Matches": [
            
        ]
    }
    with open(Json_path,"w") as json_file:
        json.dump(hard_reset_data,json_file,indent=4)


def Create_match(Room_name,Host,Password=None):
    Host['Is_host'] = True

    with open(Json_path, "r+") as json_file:
        data = json.load(json_file)
        match = {
            "Room_name":Room_name,
            "Password":Password,
            "Room_id":data['C_room_id'],
            "Full_lobby":False,
            "Has_started":False,
            "Is_open":True,
            "Players":[
                Host
            ]
        }
        #-

        data['C_room_id'] += 1
        data['Matches'].append(match)
        json_file.seek(0)
        with open(Json_path,"w") as json_file:
            json.dump(data,json_file,indent=4)
        return match['Room_id']

local_player = {
    "Name":"",
    "id":"",
    "Ip":"",
    "Is_host":False
}

def Generate_random_num_id():
    id = ""
    for i in range(15):
        num = random.randint(0,9)
        id += str(num)
    return id

def Set_local_player(name):
    global local_player
    local_player = {
        "Name":name,
        "id":Generate_random_num_id(),
        "Ip":Ip_addr,
        "Is_host":False
    }

def Get_return_matches(raw=False):
    Matches = []
    with open(Json_path,"r") as json_file:
        data = json.load(json_file)
        if raw == True:
            return data['Matches']
        else:
            for match in data['Matches']:
                Matches.append({"1": f"Lobby_name: {match['Room_name']}",
                               "2": f"Player_amount: {len(match['Players'])}",
                               "3": f"Id: {match['Room_id']}",
                               "4": f"Has_password: {match['Password']!=None}",
                               "5": ""})
            return json.dumps(Matches) 

def Print_match_list(matches):  
    print("Open_matches: \n")
    for match in matches:
        if match['Is_open'] == True:
            print(f"Lobby_name: {match['Room_name']}")
            print(f"Player_amount: {len(match['Players'])}")
            print(f"Id:{match['Room_id']}")
            if match['Password'] != None: print(f"Password_required!!")
            print("")

def Join_match(Room_id,client,Password=None):
    with open(Json_path,"r") as json_file:
        data = json.load(json_file)
    #Get Room
    Room = None
    for match in data['Matches']:
        for player in match['Players']:
            if player['id'] == client['id']:
                print("greedy goblin, you are already in a different room")
                return "Client in different lobby"
        #.
        if Room == None:
            if match['Room_id'] == Room_id:
                Room = match 
    if Room == None:
        print("!!Invalid Room Id!!")
        return "Invalid room Id"
    #Try Joining
    if Room['Password'] == Password or Room['Password']==None:
        client['Is_host'] = False
        Room['Players'].append(client)
        with open(Json_path,"w") as json_file:
            json.dump(data,json_file,indent=4)
            json_file.seek(0)
            print(f"Joined room({Room_id}) succesfully")
            Display_players(Room_id)
            return f"Joined:{Room_id}"

def Display_players(Room_id):
    with open(Json_path,"r") as json_file:
        data = json.load(json_file)
        matches = data['Matches']
    
    for match in matches:
        if match['Room_id'] == Room_id:
            print("Players in Room Are:")
            for Player in match['Players']:
                print(f"Player: {Player['Name']}")
                print(f"Is_host: {Player['Is_host']}")
                print("")

if path.exists(Json_path) == False:
    Setup_Logic_Json()

Set_local_player("Adam")
#print(local_player)
#Hard_reset_json()
#Create_match("Test_room3",local_player)

Print_match_list(Get_return_matches(True))

#Join_match(2,local_player)

