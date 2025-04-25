#!/usr/bin/env python3
# Command: place a bet
NAME = "bet"

import json
import sys

# Load the world state
with open("data/world.json", "r") as f:
    world = json.load(f)

# Get player who issued the command from environment variable
import os
player = os.environ.get("PLAYER", "unknown")
# Get the bet amount
try:
    amount = int(sys.argv[1]) if len(sys.argv) > 1 else 0
except ValueError:
    print("Bet amount must be a number")
    sys.exit(1)

# Find the player's seat
player_seat = None
for seat in world["seats"]:
    if seat["player_id"] == player:
        player_seat = seat
        break

# Validate that it's the player's turn
if not player_seat:
    print(f"{player} is not seated at the table")
    sys.exit(1)

if world["game_state"]["current_turn"] != player_seat["position"]:
    print(f"Not your turn! It's seat {world['game_state']['current_turn']}'s turn")
    sys.exit(1)

# Check if betting is even possible
if world["game_state"]["phase"] in ["waiting", "ready_to_start", "showdown"]:
    print(f"Cannot bet during {world['game_state']['phase']} phase")
    sys.exit(1)

if player_seat["is_folded"]:
    print("You've already folded this hand")
    sys.exit(1)

# Check if player can only check or call
current_bet = world["game_state"]["current_bet"]
if current_bet > 0:
    print(f"There's already a bet of {current_bet}. Use 'call', 'raise', or 'fold'")
    sys.exit(1)

# Check minimum bet (must be at least big blind)
min_bet = world["metadata"]["big_blind"]
if amount < min_bet:
    print(f"Minimum bet is {min_bet}")
    sys.exit(1)

# Check if player has enough chips
player_chips = world["players"][player]["chips"]
if amount > player_chips:
    print(f"You only have {player_chips} chips")
    sys.exit(1)

# Place the bet
world["players"][player]["chips"] -= amount
player_seat["current_bet"] = amount
player_seat["total_bet_this_round"] += amount
player_seat["has_acted"] = True
world["game_state"]["pot"] += amount
world["game_state"]["current_bet"] = amount

print(f"{player} bets {amount}")

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