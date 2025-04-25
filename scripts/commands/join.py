#!/usr/bin/env python3
# Command: join a poker game
NAME = "join"

import json
import sys
import random
import string
import os

# Load the world state
with open("data/world.json", "r") as f:
    world = json.load(f)

# Get player who issued the command from environment variable
player = os.environ.get("PLAYER", "unknown")
# Get the seat position
position = int(sys.argv[1]) if len(sys.argv) > 1 else -1

# Check if position is valid
if position < 0 or position >= len(world["seats"]):
    print(f"Invalid seat position. Please choose 0-{len(world['seats'])-1}")
    sys.exit(1)

# Check if seat is available
if world["seats"][position]["player_id"] is not None:
    print(f"Seat {position} is already taken")
    sys.exit(1)

# Initialize player if they don't exist
if player not in world["players"]:
    world["players"][player] = {
        "display_name": player,
        "chips": 1000,  # Starting chips
        "status": "active"
    }

# Assign player to seat
world["seats"][position]["player_id"] = player
print(f"{player} joined the game at seat {position}")

# If we now have minimum players, update game state
active_seats = sum(1 for seat in world["seats"] if seat["player_id"] is not None)
if active_seats >= world["metadata"]["min_players"] and world["game_state"]["phase"] == "waiting":
    world["game_state"]["phase"] = "ready_to_start"
    print(f"Game ready to start with {active_seats} players")

# Save the world state
with open("data/world.json", "w") as f:
    json.dump(world, f, indent=2)

sys.exit(0)