#!/usr/bin/env python3
# Command: check (pass without betting)
NAME = "check"

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
for seat in world["seats"]:
    if seat["player_id"] == player:
        player_seat = seat
        break

# Validate that the player is in the game
if not player_seat:
    print(f"{player} is not seated at the table")
    sys.exit(1)

# Validate that it's the player's turn
if world["game_state"]["current_turn"] != player_seat["position"]:
    print(f"Not your turn! It's seat {world['game_state']['current_turn']}'s turn")
    sys.exit(1)

# Check if checking is possible
if world["game_state"]["phase"] in ["waiting", "ready_to_start", "showdown"]:
    print(f"Cannot check during {world['game_state']['phase']} phase")
    sys.exit(1)

if player_seat["is_folded"]:
    print("You've already folded this hand")
    sys.exit(1)

# Check if there's already a bet
current_bet = world["game_state"]["current_bet"]
if current_bet > 0 and player_seat["current_bet"] < current_bet:
    print(f"There's a bet of {current_bet}. You must call, raise, or fold.")
    sys.exit(1)

# Check (pass)
player_seat["has_acted"] = True
print(f"{player} checks")

# Move to next player
active_positions = []
for seat in world["seats"]:
    if seat["player_id"] is not None and not seat["is_folded"]:
        active_positions.append(seat["position"])

active_positions.sort()
current_pos_index = active_positions.index(player_seat["position"])
next_pos_index = (current_pos_index + 1) % len(active_positions)
world["game_state"]["current_turn"] = active_positions[next_pos_index]

# Save the world state
with open("data/world.json", "w") as f:
    json.dump(world, f, indent=2)

sys.exit(0)