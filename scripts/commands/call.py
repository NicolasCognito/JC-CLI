#!/usr/bin/env python3
# Command: call the current bet
NAME = "call"

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

# Check if calling is even possible
if world["game_state"]["phase"] in ["waiting", "ready_to_start", "showdown"]:
    print(f"Cannot call during {world['game_state']['phase']} phase")
    sys.exit(1)

if player_seat["is_folded"]:
    print("You've already folded this hand")
    sys.exit(1)

# Check if there is a bet to call
current_bet = world["game_state"]["current_bet"]
if current_bet == 0:
    print("There's no bet to call. You can check or bet.")
    sys.exit(1)

# Calculate how much more the player needs to add
player_current_bet = player_seat["current_bet"]
call_amount = current_bet - player_current_bet

# Check if player has enough chips
player_chips = world["players"][player]["chips"]
if call_amount > player_chips:
    # Player goes all-in
    call_amount = player_chips
    print(f"{player} calls and is all-in with {player_chips} chips")
else:
    print(f"{player} calls {call_amount}")

# Update player's state
world["players"][player]["chips"] -= call_amount
player_seat["current_bet"] += call_amount
player_seat["total_bet_this_round"] += call_amount
player_seat["has_acted"] = True
world["game_state"]["pot"] += call_amount

# Move to next player
active_positions = []
for seat in world["seats"]:
    if seat["player_id"] is not None and not seat["is_folded"]:
        active_positions.append(seat["position"])

if active_positions:
    active_positions.sort()
    current_pos_index = active_positions.index(player_seat["position"])
    next_pos_index = (current_pos_index + 1) % len(active_positions)
    world["game_state"]["current_turn"] = active_positions[next_pos_index]

# Save the world state
with open("data/world.json", "w") as f:
    json.dump(world, f, indent=2)

sys.exit(0)