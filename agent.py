import requests
import json
from time import sleep

# This Agent will buy every house he lands on

IP = "localhost"
PORT = 5000
time_sleep = 2

def user_register(name):
    # Register a new user
    # Returns the user id
    url = f"http://{IP}:{PORT}/user/{name}"
    response = requests.post(url)
    if response.status_code == 201 or response.status_code == 409:
        return response.json()["id"]
    else:
        raise Exception("Could not register user")

def get_user_state(user_id):
    # Get the current state of the user
    url = f"http://{IP}:{PORT}/user/{user_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Could not get user state")

def get_state(user_id):
    # Get the current state of the game
    url = f"http://{IP}:{PORT}/game/status/{user_id}"
    response = requests.get(url)
    if response.status_code == 200:
        # Send position of user
        return response.json()["order"]
    else:
        raise Exception("Could not get state")

def roll_dice(user_id):
    # Role the dice
    url = f"http://{IP}:{PORT}/game/roll_dice/{user_id}"
    response = requests.post(url)
    print(response.content)
    if response.status_code == 200:
        print("We can't buy anything")
        return 1
    elif response.status_code == 202:
        print("We should buy this house")
        return 2
    elif response.status_code == 401:
        print("We can't buy anything")
        return 1
    elif response.status_code == 203:
        return 3
    else:
        raise Exception("Could not role dice")

def buy_house(user_id):
    # Buy the house
    url = f"http://{IP}:{PORT}/game/buy/{user_id}"
    response = requests.post(url)
    if response.status_code == 200:
        return True
    elif response.status_code == 400:
        print("Dosen't have enough money")
        return False

def get_game_state():
    # Get the current state of the game
    url = f"http://{IP}:{PORT}/game/status"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["state"]
    else:
        raise Exception("Could not get state")

def end_turn(user_id):
    # End turn
    url = f"http://{IP}:{PORT}/game/end_turn/{user_id}"
    response = requests.post(url)
    if response.status_code == 200:
        return True
    else:
        raise Exception("Could not end turn")

def get_user_pos(user_id):
    # Get the current state of the user
    url = f"http://{IP}:{PORT}/game/status/{user_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()


position = []
round = 0

# Register user
id=user_register("bot01")
print(f"User ID is {id}")

while get_game_state() == 'wait for players':
    print("Waiting for players")
    sleep(time_sleep)
if get_game_state() == 'started':
    user = get_user_state(id)
    position.append(user['position'])
    while True:
        user = get_user_state(id)
        if user['turn'] == True and user['role_the_dice'] == False:
            print()
            print(f"Trace location: {position}")
            print("=============================================")
            print()
            a = roll_dice(id)
            if a == 2:
                if buy_house(id):
                    print("Bought house")
                else:
                    print("Could not buy house")
            elif a == 3:
                print("GAME END")
                exit(0)
            if user['position'] < position[-1]:
                round += 1
            user = get_user_state(id)
            position.append(user['position'])
            pos = get_user_pos(id)
            print("+++++++++++++++++++")
            print(json.dumps(pos, sort_keys=True, indent=4))
            print(json.dumps(user, sort_keys=True, indent=4))
            print("+++++++++++++++++++")
            if end_turn(id):
                print("Turn ended")
                sleep(time_sleep)
            print()
            print("=============================================")
            print()

        elif user['turn'] == False and user['role_the_dice'] == False:
            print("Not our turn")
            sleep(time_sleep)
