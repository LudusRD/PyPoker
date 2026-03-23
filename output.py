import json

def do_print(text, p_ip="Server"):
    print(f"[{p_ip}] {text}")

def response(message):
    if isinstance(message, bytes):
        message = json.loads(message.decode())

    request = message.get('Request', '')
    p_ip = message.get('Ip', 'Unknown IP')
    p_name = message.get('Name', 'Unknown')

    if request == "Init":
        do_print(f"Player '{p_name}' connected", p_ip)
    elif request == "Create_lobby":
        specs = message.get('Rq_spec', {})
        do_print(f"Player '{p_name}' creating lobby '{specs.get('Name','?')}' with password '{specs.get('Password','?')}'", p_ip)
    elif request == "Join_room":
        specs = message.get('Rq_spec', {})
        do_print(f"Player '{p_name}' joining room {specs.get('id','?')}", p_ip)
    elif request == "Get_lobbies":
        do_print(f"Player '{p_name}' browsing lobbies", p_ip)
    elif request == "start game":
        do_print(f"Player '{p_name}' attempting to start game", p_ip)
    elif request == "close lobby":
        do_print(f"Player '{p_name}' closing lobby", p_ip)
    elif request == "leave":
        do_print(f"Player '{p_name}' left lobby", p_ip)
    elif request == "fold":
        do_print(f"Player '{p_name}' folded", p_ip)
    elif request == "check":
        do_print(f"Player '{p_name}' checked", p_ip)
    elif request == "bet":
        amount = message.get('Rq_spec', {}).get('amount', '?')
        do_print(f"Player '{p_name}' bet {amount}", p_ip)
    elif request == "call":
        amount = message.get('Rq_spec', {}).get('amount', '?')
        do_print(f"Player '{p_name}' called {amount}", p_ip)
    elif request:
        do_print(f"Unknown request: {request} | full message: {message}", p_ip)