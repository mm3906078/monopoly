# Monopoly with agent programing

## Overview
This is a simple implementation of the game Monopoly. We create to category of endpoints:
- user
- game

with the user category endpoint you can handel users controls, like create user, remove user, get list of users and etc.
with the game category endpoint you can handel the game, like start game, stop game, get game status, roll the dice, move the player, etc.

## Setup
Create virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
then run the model:
```bash
python3 model.py
```

The apidocs avalible in `localhost:5000/apidocs/` and you can use it to control the game.
For agent you can start it with:
```bash
python3 agent.py
```
