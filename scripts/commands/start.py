#!/usr/bin/env python3
# Command: start the poker game
NAME = "start"

import json
import sys
import random

# Load the world state
with open("data/world.json", "r") as f:
    world = json.load(f)

# Get player who issued the command
player = sys.argv[1] if len(sys.argv) > 1 else "unknown"

# Check if game is in the ready state
if world["game_state"]["phase"] != "ready_to_start":
    if world["game_state"]["phase"] == "waiting":
        print("Not enough players to start the game")
    else:
        print("Game is already in progress")
    sys.exit(1)

# Count active players
active_players = sum(1 for seat in world["seats"] if seat["player_id"] is not None)
if active_players < world["metadata"]["min_players"]:
    print(f"Need at least {world['metadata']['min_players']} players to start")
    sys.exit(1)

# Initialize the deck with all cards
seed = world["metadata"]["session_seed"]
random.seed(seed + str(world["metadata"]["current_hand_id"]))
world["deck"] = list(world["card_definitions"].keys())
random.shuffle(world["deck"])

# Clear the board
world["board"] = []

# Reset player states
for seat in world["seats"]:
    if seat["player_id"] is not None:
        seat["cards"] = []
        seat["current_bet"] = 0
        seat["total_bet_this_round"] = 0
        seat["has_acted"] = False
        seat["is_folded"] = False

# Increment hand ID
world["metadata"]["current_hand_id"] += 1

# Update game state
world["game_state"]["phase"] = "pre_flop"
world["game_state"]["pot"] = 0
world["game_state"]["current_bet"] = 0
world["game_state"]["side_pots"] = []

# Determine dealer, small blind, big blind positions
active_positions = [seat["position"] for seat in world["seats"] if seat["player_id"] is not None]
active_positions.sort()  # Sort for predictability

# Set dealer position - for first hand, it's the first seat, otherwise it rotates
if world["metadata"]["current_hand_id"] == 1:
    world["game_state"]["dealer_position"] = active_positions[0]
else:
    # Find next active position after dealer
    current_dealer = world["game_state"]["dealer_position"]
    next_index = 0
    for i, pos in enumerate(active_positions):
        if pos > current_dealer:
            next_index = i
            break
    world["game_state"]["dealer_position"] = active_positions[next_index % len(active_positions)]

# Set blinds positions
dealer_index = active_positions.index(world["game_state"]["dealer_position"])
sb_index = (dealer_index + 1) % len(active_positions)
bb_index = (dealer_index + 2) % len(active_positions)
world["game_state"]["small_blind_position"] = active_positions[sb_index]
world["game_state"]["big_blind_position"] = active_positions[bb_index]

# Find player after big blind for first action
next_index = (dealer_index + 3) % len(active_positions)
if next_index >= len(active_positions):
    next_index = 0
world["game_state"]["current_turn"] = active_positions[next_index]

print(f"Game started! Hand #{world['metadata']['current_hand_id']}")
print(f"Dealer: Seat {world['game_state']['dealer_position']}")
print(f"Small Blind: Seat {world['game_state']['small_blind_position']}")
print(f"Big Blind: Seat {world['game_state']['big_blind_position']}")

# Save the world state
with open("data/world.json", "w") as f:
    json.dump(world, f, indent=2)

sys.exit(0)