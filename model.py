
import flask,json,random
import uuid
import logging

from flasgger import Swagger, LazyJSONEncoder
from flasgger import swag_from

app = flask.Flask(__name__)

app.json_encoder = LazyJSONEncoder

swagger_template ={
    "swagger": "2.0",
    "info": {
      "title": "Model for playing Monopoly",
      "description": "API Documentation for Monopoly",
      "contact": {
        "name": "Mohammad Reza Mollasalehi",
        "email": "info@mrsalehi.info",
        "url": "https://info@mrsalehi.info",
        },
      "version": "1.0",
      "basePath":"http://localhost:5000",
    },
    "schemes": [
        "http"
    ]
}

swagger_config = {
    "headers": [
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', "GET, POST"),
    ],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
    
}
swagger = Swagger(app, template=swagger_template,config=swagger_config)

level = logging.DEBUG
logging_format = "[%(levelname)s] %(asctime)s - %(message)s"
logging.basicConfig(level = level, format=logging_format)

board = open("Database/board.json","r")
board = json.load(board)
cards = open("Database/cards.json","r")
cards = json.load(cards)
players = open("Database/players.json","r")
players = json.load(players)

# Game state
# - Wait for players
# - started
# - ended
game = "wait for players"
rank = {}

def clear_game():
    players["players"] = []
    with open("Database/players.json","w") as file:
        json.dump(players,file,indent=4)
    for i in range(len(board["board"])):
        board["board"][i]["owner"] = None
    with open("Database/board.json","w") as file:
        json.dump(board,file,indent=4)

@swag_from("docs/users/users.yml" )
@app.route("/users",methods=["GET"])
def users():
    players = open("Database/players.json","r")
    players = json.load(players)
    return flask.jsonify(players),200

@swag_from("docs/users/user.yml")
@app.route("/user/<name>",methods=["POST"])
def new_user(name):
    # Check if user exist or not
    for player in players["players"]:
        if player["name"] == name:
            return flask.jsonify(player),409
    if game != "wait for players":
        return "Game already started",401
    player_id = str(uuid.uuid4())
    player = {
        "name": name,
        "money": 1500,
        "position": 0,
        "properties": [],
        "id": player_id,
        "jail": False,
        "jail_turns": 0,
        "jail_card": False,
        "role_the_dice": False,
        "asset": [],
        "turn": False
    }

    players["players"].append(player)
    return flask.jsonify(player),201

@swag_from("docs/game/start.yml")
@app.route("/game/start",methods=["POST"])
def start():
    global game
    global rank
    if game != "wait for players":
        return "Game already started",401
    for player in players["players"]:
        if player["turn"] == True:
            return f"{player['name']} already started",401
    if len(players["players"]) < 2:
        return "Not enough players",406
    players["players"][0]["turn"] = True
    with open("Database/players.json","w") as file:
        json.dump(players,file,indent=4)
    for player in players["players"]:
        print(player["name"])
        rank[str(player["name"])] = "Unknown"
    game = "started"
    return f'turn of {players["players"][0]["name"]}',200

@swag_from("docs/users/specific_user.yml")
@app.route("/user/<player_id>",methods=["GET"])
def user(player_id):
    players = open("Database/players.json","r")
    players = json.load(players)
    for i in range(len(players['players'])):
        if players['players'][i]["id"] == str(player_id):
            player_id = i
            return flask.jsonify(players['players'][player_id]),200
    return "Player not found",404

@swag_from("docs/users/delete_user.yml")
@app.route("/user/<player_id>",methods=["DELETE"])
def delete_user(player_id):
    for player in players["players"]:
        if player["id"] == player_id:
            players["players"].remove(player)
            with open("Database/players.json","w") as file:
                json.dump(players,file,indent=4)
            return "Player deleted",200
    return "Player not found",404

@swag_from("docs/users/delete_all_users.yml")
@app.route("/users",methods=["DELETE"])
def delete_all_users():
    players["players"] = []
    with open("Database/players.json","w") as file:
        json.dump(players,file,indent=4)
    return "All players deleted",200

@swag_from("docs/game/roll_dice.yml")
@app.route("/game/roll_dice/<player_id>",methods=["POST"])
def roll_dice(player_id):
    if game != "started":
        return "Game not started",401
    players = open("Database/players.json","r")
    players = json.load(players)
    if len(players["players"]) < 2:
        rank[players['players'][player_id]['name']] = 1
        return f"{players['players'][player_id]['name']} win the game",203
    for i in range(len(players['players'])):
        if players['players'][i]["id"] == player_id:
            player_id = i
            print(player_id)
    if  players['players'][player_id]["jail"] == True:
        return f"{players['players'][player_id]['name']} is in jail",401
    if players['players'][player_id]["turn"] == True and players['players'][player_id]["role_the_dice"] == False:
        dice = random.randint(1,6)
        players['players'][player_id]["role_the_dice"] = True
        players['players'][player_id]["position"] += dice
        if players['players'][player_id]["position"] >= 40:
            players['players'][player_id]["position"] -= 40
            players['players'][player_id]["money"] += 200
        housetype = board["board"][players['players'][player_id]["position"]]["space_type"]
        logging.info(f"USER: {players['players'][player_id]['name']} ROLLED A {dice} AND LANDED ON {board['board'][players['players'][player_id]['position']]['name']}")
        if housetype == "properties" or housetype == "railroad" or housetype == "utility":
            logging.debug(board["board"][players['players'][player_id]["position"]])
            if board["board"][players['players'][player_id]["position"]]["owner"] == None:
                with open("Database/players.json","w") as file:
                    json.dump(players,file,indent=4)
                return f"{players['players'][player_id]['name']} rolled a {dice} and landed on {board['board'][players['players'][player_id]['position']]['name']}. Would you like to buy it?",202
            elif board["board"][players['players'][player_id]["position"]]["owner"] != None and players['players'][player_id]["position"] in players['players'][player_id]["properties"]:
                with open("Database/players.json","w") as file:
                    json.dump(players,file,indent=4)
                return f"{players['players'][player_id]['name']} rolled a {dice} and landed on {board['board'][players['players'][player_id]['position']]['name']}. You already own it.",200
            elif board["board"][players['players'][player_id]["position"]]["owner"] != None and players['players'][player_id]["position"] not in players['players'][player_id]["properties"]:
                if board["board"][players['players'][player_id]["position"]]["space_type"] == "properties":
                    if players['players'][player_id]["money"] >= board["board"][players['players'][player_id]["position"]]["rent"]["alone"]:
                        owner_id = board['board'][players['players'][player_id]['position']]['owner']
                        players['players'][player_id]['money'] -= board["board"][players['players'][player_id]["position"]]["rent"]["alone"]
                        players['players'][owner_id]['money'] += board["board"][players['players'][player_id]["position"]]["rent"]["alone"]
                        with open("Database/players.json","w") as file:
                            json.dump(players,file,indent=4)
                        return f"{players['players'][player_id]['name']} rolled a {dice} and landed on {board['board'][players['players'][player_id]['position']]['name']}. You payed rent to {players['players'][owner_id]['name']}",200
                    else:
                        print("RENT LOGIC")
                        print(f"{players['players'][player_id]['name']} is kiked becuse of broked")
                        rank[players['players'][player_id]['name']] = len(players['players'])
                        name = players['players'][player_id]['name']
                        pos = board['board'][players['players'][player_id]['position']]['name']
                        players["players"].remove(players['players'][player_id])
                        with open("Database/players.json","w") as file:
                            json.dump(players,file,indent=4)
                        return f"{name} rolled a {dice} and landed on {name}. You don't have enough money to pay rent & you kiked from game",203
                elif board["board"][players['players'][player_id]["position"]]["space_type"] in ["utility", "railroad"]:
                    if players['players'][player_id]["money"] >= board["board"][players['players'][player_id]["position"]]["rent"]["owned_1"]:
                        owner_id = board['board'][players['players'][player_id]['position']]['owner']
                        players['players'][player_id]['money'] -= board["board"][players['players'][player_id]["position"]]["rent"]["owned_1"]
                        players['players'][owner_id]['money'] += board["board"][players['players'][player_id]["position"]]["rent"]["owned_1"]
                        with open("Database/players.json","w") as file:
                            json.dump(players,file,indent=4)
                        return f"{players['players'][player_id]['name']} rolled a {dice} and landed on {board['board'][players['players'][player_id]['position']]['name']}. You payed rent to {players['players'][owner_id]['name']}",200
                    else:
                        print("RENT LOGIC")
                        print(f"{players['players'][player_id]['name']} is kiked becuse of broked")
                        rank[players['players'][player_id]['name']] = len(players['players'])
                        name = players['players'][player_id]['name']
                        pos = board['board'][players['players'][player_id]['position']]['name']
                        players["players"].remove(players['players'][player_id])
                        with open("Database/players.json","w") as file:
                            json.dump(players,file,indent=4)
                        return f"{name} rolled a {dice} and landed on {name}. You don't have enough money to pay rent & you kiked from game",203
        elif housetype == "chance" or housetype == "community_chest":
            card_num = random.randint(0,15)
            if housetype == "chance":
                card_type = "chance_card"
            else:
                card_type = "community_card"

            # TODO: Unhandeled cards
            while True:
                if card_type == "chance_card" and card_num + 1 in [5,6,7,10]:
                    card_num = random.randint(0,15)
                else:
                    break

            print(json.dumps( cards[card_type][card_num],indent=4))

            match cards[card_type][card_num]['action']:
                case "move":
                    players['players'][player_id]["position"] = cards[card_type][card_num]['move']['properties']
                    print(players['players'][player_id]["name"])
                    with open("Database/players.json","w") as file:
                        json.dump(players,file,indent=4)
                    return f"{players['players'][player_id]['name']} rolled a {dice} and get {cards[card_type][card_num]['narration']}",200
                case "money":
                    try:
                        players['players'][player_id]["money"] += cards[card_type][card_num]['money']['amount']
                    except:
                        pass
                    try:
                        players['players'][player_id]["money"] += cards[card_type][card_num]['money']['amount']['house']
                    except:
                        pass
                    with open("Database/players.json","w") as file:
                        json.dump(players,file,indent=4)
                    return f"{players['players'][player_id]['name']} rolled a {dice} and get {card_type}",200
                case "asset":
                    players['players'][player_id]["asset"].append({card_type: cards[card_type][card_num]})
                    with open("Database/players.json","w") as file:
                        json.dump(players,file,indent=4)
                    return f"{players['players'][player_id]['name']} rolled a {dice} and get {card_type}",200
                case "move_money":
                    players['players'][player_id]["position"] = cards[card_type][card_num]["move"]['properties']
                    players['players'][player_id]["money"] += cards[card_type][card_num]["money"]['amount']
                    with open("Database/players.json","w") as file:
                        json.dump(players,file,indent=4)
                    return f"{players['players'][player_id]['name']} rolled a {dice} and get {card_type}",200
                case default:
                    print(cards[card_type][card_num]['action'])
                    return "ERROR",500
        elif housetype == "luxury_tax" or housetype == "income_tax":
            if players['players'][player_id]["money"] >= board["board"][players['players'][player_id]["position"]]["money"]['amount']:
                players['players'][player_id]["money"] -= board["board"][players['players'][player_id]["position"]]["money"]['amount']
                with open("Database/players.json","w") as file:
                    json.dump(players,file,indent=4)
                return f"{players['players'][player_id]['name']} rolled a {dice} and landed on {board['board'][players['players'][player_id]['position']]['name']}. You payed tax.",200
            else:
                print("RENT LOGIC")
                print(f"{players['players'][player_id]['name']} is kiked becuse of broked")
                rank[players['players'][player_id]['name']] = len(players['players'])
                name = players['players'][player_id]['name']
                pos = board['board'][players['players'][player_id]['position']]['name']
                players["players"].remove(players['players'][player_id])
                with open("Database/players.json","w") as file:
                    json.dump(players,file,indent=4)
                return f"{name} rolled a {dice} and landed on {name}. You don't have enough money to pay rent & you kiked from game",203
        elif housetype == "corner_square":
            if board["board"][players['players'][player_id]["position"]]["name"] == "Go to Jail":
                if players['players'][player_id]["jail_card"] == True:
                    players['players'][player_id]["jail_card"] = False
                    with open("Database/players.json","w") as file:
                        json.dump(players,file,indent=4)
                    return f"{players['players'][player_id]['name']} rolled a {dice} and landed on {board['board'][players['players'][player_id]['position']]['name']}. You have Jail out cards",200
                players['players'][player_id]["position"] = 10
                players['players'][player_id]["jail"] = True
                with open("Database/players.json","w") as file:
                    json.dump(players,file,indent=4)
                return f"{players['players'][player_id]['name']} rolled a {dice} and landed on {board['board'][players['players'][player_id]['position']]['name']}. You go to jail.",200
            elif board["board"][players['players'][player_id]["position"]]["name"] == "Free Parking":
                with open("Database/players.json","w") as file:
                    json.dump(players,file,indent=4)
                return f"{players['players'][player_id]['name']} rolled a {dice} and landed on {board['board'][players['players'][player_id]['position']]['name']}.",200
            elif board["board"][players['players'][player_id]["position"]]["name"] == "Go":
                with open("Database/players.json","w") as file:
                    json.dump(players,file,indent=4)
                return f"{players['players'][player_id]['name']} rolled a {dice} and landed on {board['board'][players['players'][player_id]['position']]['name']}.",200
            elif board["board"][players['players'][player_id]["position"]]["name"] == "Jail":
                with open("Database/players.json","w") as file:
                    json.dump(players,file,indent=4)
                return f"{players['players'][player_id]['name']} rolled a {dice} and landed on {board['board'][players['players'][player_id]['position']]['name']}.",200
        else:
            return f"{players['players'][player_id]['name']} rolled a {dice} and landed on {board['board'][players['players'][player_id]['position']]['name']}.",500
    elif players['players'][player_id]["turn"] == False:
        return f"{players['players'][player_id]['name']} not on turn",401
    elif players['players'][player_id]["role_the_dice"] == True:
        return f"{players['players'][player_id]['name']} already rolled the dice",401
    else:
        print(players['players'][player_id])
        return "ERROR",500

@swag_from("docs/game/buy.yml")
@app.route("/game/buy/<player_id>",methods=["POST"])
def buy(player_id):
    if game != "started":
        return "Game not started",401
    players = open("Database/players.json","r")
    players = json.load(players)
    for i in range(len(players['players'])):
        if players['players'][i]["id"] == player_id:
            player_id = i
    if players['players'][player_id]["turn"] == True and players['players'][player_id]["role_the_dice"] == True:
        if board["board"][players['players'][player_id]["position"]]["owner"] == None and board["board"][players['players'][player_id]["position"]]["money"]["amount"] != 0:
            if players['players'][player_id]["money"] >= board["board"][players['players'][player_id]["position"]]["money"]["amount"]:
                players['players'][player_id]["money"] -= board["board"][players['players'][player_id]["position"]]["money"]["amount"]
                players['players'][player_id]["properties"].append(players['players'][player_id]["position"])
                board["board"][players['players'][player_id]["position"]]["owner"] = player_id
                with open("Database/players.json","w") as file:
                    json.dump(players,file,indent=4)
                with open("Database/board.json","w") as file:
                    json.dump(board,file,indent=4)
                return f"{players['players'][player_id]['name']} bought {board['board'][players['players'][player_id]['position']]['name']}",200
            else:
                return f"{players['players'][player_id]['name']} doesn't have enough money",401
        else:
            with open("Database/players.json","w") as file:
                json.dump(players,file,indent=4)
            return f"{board['board'][players['players'][player_id]['position']]['name']} already owned",201
    elif players['players'][player_id]["turn"] == False:
        return f"{players['players'][player_id]['name']} not on turn",401
    elif players['players'][player_id]["role_the_dice"] == False:
        return f"{players['players'][player_id]['name']} didn't roll the dice",401
    else:
        return "ERROR",400

@app.route("/game/board",methods=["GET"])
def status():
    # Show the status of the game
    msg = {}
    players = open("Database/players.json","r")
    players = json.load(players)
    for user in players["players"]:
        msg.update({user["id"]: board["board"][user["position"]]})
    return flask.jsonify(msg),200

@swag_from("docs/game/status.yml")
@app.route("/game/status",methods=["GET"])
def game_status():
    return {"state": game},200

@swag_from("docs/game/end_turn.yml")
@app.route("/game/end_turn/<player_id>",methods=["POST"])
def end_turn(player_id):
    if game != "started":
        return "Game not started",401
    players = open("Database/players.json","r")
    players = json.load(players)
    for i in range(len(players['players'])):
        if players['players'][i]["id"] == player_id:
            player_id = i
    if players['players'][player_id]["turn"] == True and players['players'][player_id]["role_the_dice"] == True:
        players['players'][player_id]["turn"] = False
        players['players'][player_id]["role_the_dice"] = False
        if player_id == len(players['players']) - 1:
            players['players'][0]["turn"] = True
        else:
            players['players'][player_id + 1]["turn"] = True
        with open("Database/players.json","w") as file:
            json.dump(players,file,indent=4)
        return f"Turn of {players['players'][player_id]['name']} ended",200
    elif players['players'][player_id]["jail"] == True and players['players'][player_id]["turn"] == True:
        players['players'][player_id]["turn"] = False
        players['players'][player_id]["role_the_dice"] = False
        if players['players'][player_id]["jail_turns"] == 3:
            players['players'][player_id]["jail"] = False
            players['players'][player_id]["jail_turns"] = 0
        else:
            players['players'][player_id]["jail_turns"] += 1
        if player_id == len(players['players']) - 1:
            players['players'][0]["turn"] = True
        else:
            players['players'][player_id + 1]["turn"] = True
        with open("Database/players.json","w") as file:
            json.dump(players,file,indent=4)
        return f"Turn of {players['players'][player_id]['name']} ended",200
    elif players['players'][player_id]["turn"] == True and players['players'][player_id]["role_the_dice"] == False and players['players'][player_id]["jail"] == False:
        return f"{players['players'][player_id]['name']} didn't roll the dice",401
    elif players['players'][player_id]["turn"] == False:
        return f"{players['players'][player_id]['name']} not on turn",401

@swag_from("docs/game/get_rank.yml")
@app.route("/game/get_rank",methods=["GET"])
def get_rank():
    return flask.jsonify(rank),200

@swag_from("docs/game/status_player.yml")
@app.route("/game/status/<player_id>",methods=["GET"])
def status_player(player_id):
    players = open("Database/players.json","r")
    players = json.load(players)
    for i in range(len(players['players'])):
        if players['players'][i]["id"] == player_id:
            return flask.jsonify(board["board"][players['players'][i]["position"]]),200

def end_game():
    pass

if __name__ =='__main__':
    clear_game()
    app.run(debug = True)
