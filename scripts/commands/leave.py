#!/usr/bin/env python3
# Command: leave the poker game
NAME = "leave"

import json
import sys
import os

# Load the world state
with open("data/world.json", "r") as f:
    world = json.load(f)

# Get player who issued the command from environment variable
player = os.environ.get("PLAYER", "unknown")

# Find the player's seat
player_seat = None
for i, seat in enumerate(world["seats"]):
    if seat["player_id"] == player:
        player_seat = seat
        seat_index = i
        break

# Validate that the player is in the game
if not player_seat:
    print(f"{player} is not seated at the table")
    sys.exit(1)

# If in active hand, fold first
if world["game_state"]["phase"] not in ["waiting", "ready_to_start", "showdown"]:
    player_seat["is_folded"] = True
    print(f"{player} folds and leaves the game")
    
    # If it was this player's turn, move to next player
    if world["game_state"]["current_turn"] == player_seat["position"]:
        active_positions = []
        for seat in world["seats"]:
            if seat["player_id"] is not None and not seat["is_folded"] and seat["player_id"] != player:
                active_positions.append(seat["position"])
        
        if active_positions:
            active_positions.sort()
            world["game_state"]["current_turn"] = active_positions[0]
else:
    print(f"{player} leaves the game")

# Clear the player's seat
player_seat["player_id"] = None
player_seat["cards"] = []
player_seat["current_bet"] = 0
player_seat["total_bet_this_round"] = 0
player_seat["has_acted"] = False
player_seat["is_folded"] = False

# Update active players count
active_players = sum(1 for seat in world["seats"] if seat["player_id"] is not None)

# If we're below minimum players, reset game state
if active_players < world["metadata"]["min_players"] and world["game_state"]["phase"] != "waiting":
    world["game_state"]["phase"] = "waiting"
    world["game_state"]["current_turn"] = None
    world["game_state"]["pot"] = 0
    world["game_state"]["current_bet"] = 0
    world["board"] = []
    world["deck"] = []
    
    print(f"Game reset due to insufficient players ({active_players})")

# Save the world state
with open("data/world.json", "w") as f:
    json.dump(world, f, indent=2)

sys.exit(0)