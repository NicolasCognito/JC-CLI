#!/usr/bin/env python3
# Command: raise the current bet
NAME = "raise"

import json
import sys
import os

# Load the world state
with open("data/world.json", "r") as f:
    world = json.load(f)

# Get player who issued the command from environment variable
player = os.environ.get("PLAYER", "unknown")

# Get the raise amount (total, not the increment)
try:
    amount = int(sys.argv[1]) if len(sys.argv) > 1 else 0
except ValueError:
    print("Raise amount must be a number")
    sys.exit(1)

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

# Check if raising is even possible
if world["game_state"]["phase"] in ["waiting", "ready_to_start", "showdown"]:
    print(f"Cannot raise during {world['game_state']['phase']} phase")
    sys.exit(1)

if player_seat["is_folded"]:
    print("You've already folded this hand")
    sys.exit(1)

# Check if there is a bet to raise
current_bet = world["game_state"]["current_bet"]
if current_bet == 0:
    print("There's no bet to raise. Use 'bet' instead.")
    sys.exit(1)

# Calculate minimum raise amount
min_raise = current_bet * 2

# Validate raise amount
if amount < min_raise:
    print(f"Minimum raise is {min_raise}")
    sys.exit(1)

# Calculate how much more the player needs to add
player_current_bet = player_seat["current_bet"]
additional_amount = amount - player_current_bet

# Check if player has enough chips
player_chips = world["players"][player]["chips"]
if additional_amount > player_chips:
    print(f"You only have {player_chips} chips")
    sys.exit(1)

# Update player's state
world["players"][player]["chips"] -= additional_amount
player_seat["current_bet"] = amount
player_seat["total_bet_this_round"] += additional_amount
player_seat["has_acted"] = True
world["game_state"]["pot"] += additional_amount
world["game_state"]["current_bet"] = amount

print(f"{player} raises to {amount}")

# Reset 'has_acted' for all other players since they need to respond to the raise
for seat in world["seats"]:
    if seat["player_id"] and seat["player_id"] != player and not seat["is_folded"]:
        seat["has_acted"] = False

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