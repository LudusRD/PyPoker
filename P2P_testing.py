import json
from os import path
import random
import socket

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
    with open(Json_path, "r+") as json_file:
        data = json.load(json_file)
        Host['Room']['Is_host'] = True
        match = {
            "Room_name":Room_name,
            "Password":Password,
            "Room_id":data['C_room_id'],
            "Full_lobby":False,
            "Has_started":False,
            "Is_open":True,
            "current_bet":0,
            "pot":0,
            "Players":[
                Host
            ],
            "Active_players":[

            ]
        }
        #-

        data['C_room_id'] += 1
        data['Matches'].append(match)
        with open(Json_path,"w") as json_file:
            json.dump(data,json_file,indent=4)
        return match['Room_id']

def Delete_match(Room_id):
    match = find_room(Room_id)
    with open(Json_path,'r') as json_file:
        data = json.load(json_file)

    if match in data['Matches']:
        data['Matches'].remove(match)

    with open(Json_path,'w') as json_file:
        json.dump(data,json_file,indent=4)


def find_room(Room_id):
    with open(Json_path,'r') as json_file:
        data = json.load(json_file)
        for match in data['Matches']:
            if match['Room_id'] == Room_id:
                return match
    return None

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

def Check_for_host(client_id,Room_id=None,Match=None):
    with open(Json_path,"r") as json_file:
        data = json.load(json_file)
    if Room_id == None and Match == None:
        print("Specify atleaast one way to find it")
        return False

    if Match != None:
        for player in Match['Players']:
            if player['id'] == client_id:
                if player['Room']['Is_host'] == True:
                    return True

    if Room_id != None:
        for match in data['Matches']:
            if match['Room_id'] == Room_id:
                for player in match['Players']:
                    if player['id'] == client_id:
                        if player['Room']['Is_host'] == True:
                            return True

    return False




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
    if Room['Has_started'] == True:
        print("Game already in progress")
        return "Game_already_started"
    if (Room['Password'] == Password or Room['Password']== None):
        client['Is_host'] = False
        Room['Players'].append(client)
        with open(Json_path,"w") as json_file:
            json.dump(data,json_file,indent=4)
        print(f"Joined room({Room_id}) successfully")
        Display_players(Room_id)
        return f"Joined:{Room_id}"
    else:
        return "Wrong password"

def Transfer_player_state(Room,players,src_state,dst_state):
    with open(Json_path,'r') as json_file:
        data = json.load(json_file)

    for match in data['Matches']:
        if Room['Room_id'] == match['Room_id']:
            Room = match
            break

    if not isinstance(players, list):
        players = [players]

    for player in players:
        matched = None
        for pt_player in list(Room[src_state]):
            if pt_player['id'] == player['id']:
                matched = pt_player
                break
        if matched:
            Room[src_state].remove(matched)
            Room[dst_state].append(matched)

    # Single write after all transfers
    with open(Json_path,'w') as json_file:
        json.dump(data, json_file, indent=4)

    return Room


def Leave_match(Room_id,client):
    with open(Json_path,'r') as json_file:
        data = json.load(json_file)
    Room = None
    for match in data['Matches']:
        if match['Room_id'] == Room_id:
            Room = match
    if Room == None:
        print("!!Invalid Room Id!!")
        return
    player_to_remove = None
    for p in Room['Players']:
        if p['id'] == client['id']:
            player_to_remove = p
            break
    if player_to_remove:
        Room['Players'].remove(player_to_remove)
    with open(Json_path,"w") as json_file:
        json.dump(data,json_file,indent=4)


def Display_players(Room_id):
    with open(Json_path,"r") as json_file:
        data = json.load(json_file)
        matches = data['Matches']
    
    for match in matches:
        if match['Room_id'] == Room_id:
            print("Players in Room Are:")
            for Player in match['Players']:
                print(f"Player: {Player['Name']}")
                print(f"Is_host: {Player['Room']['Is_host'] == True}")
                print("")

#json cards handeling
def Save_player_cards(Room_id, players_with_cards):
    with open(Json_path, 'r') as json_file:
        data = json.load(json_file)
    for match in data['Matches']:
        if match['Room_id'] == Room_id:
            for json_player in match['Players']:
                for mem_player in players_with_cards:
                    if json_player['id'] == mem_player['id']:
                        json_player['Cards'] = mem_player['Cards']
    with open(Json_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

#Saves current bet in JSON, so it doesn't reset after find_room
def Save_current_bet(Room_id, amount):
    with open(Json_path, 'r') as f:
        data = json.load(f)
    for match in data['Matches']:
        if match['Room_id'] == Room_id:
            match['current_bet'] = amount
    with open(Json_path, 'w') as f:
        json.dump(data, f, indent=4)

#Saves player chips in JSON, so it doesn't reset after find_room
def Save_player_chips(Room_id, player_id, chips):
    with open(Json_path, 'r') as f:
        data = json.load(f)
    for match in data['Matches']:
        if match['Room_id'] == Room_id:
            for state in ['Players', 'Active_players']:
                for player in match[state]:
                    if player['id'] == player_id:
                        player['chips'] = chips
    with open(Json_path, 'w') as f:
        json.dump(data, f, indent=4)

#Saves total pot in jSON so that it doesn't reset after find_room
def Save_pot(Room_id, amount):
    with open(Json_path, 'r') as f:
        data = json.load(f)
    for match in data['Matches']:
        if match['Room_id'] == Room_id:
            match['pot'] = amount
    with open(Json_path, 'w') as f:
        json.dump(data, f, indent=4)

#Saves Has_started flag in json
def Save_has_started(Room_id, value):
    with open(Json_path, 'r') as f:
        data = json.load(f)
    for match in data['Matches']:
        if match['Room_id'] == Room_id:
            match['Has_started'] = value
    with open(Json_path, 'w') as f:
        json.dump(data, f, indent=4)

if path.exists(Json_path) == False:
    Setup_Logic_Json()

#Set_local_player("Adam")
#print(local_player)
#Hard_reset_json()
#Create_match("Test_room3",local_player)

#Print_match_list(Get_return_matches(True))

#Join_match(2,local_player)
