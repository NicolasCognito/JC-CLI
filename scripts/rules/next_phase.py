#!/usr/bin/env python3
# Rule: advance to the next phase when betting round is complete
NAME = "next_phase"

import json
import sys

# Load the world state FROM STDIN
world = json.loads(sys.stdin.read())

# Check if we're in a betting phase
valid_phases = ["pre_flop", "flop", "turn", "river"]
if world["game_state"]["phase"] not in valid_phases:
    # Not in a betting phase
    print(json.dumps(world))
    sys.exit(9)  # No changes

# Count active players (not folded)
active_players = []
for seat in world["seats"]:
    if seat["player_id"] and not seat["is_folded"]:
        active_players.append(seat)

# If only one player remains, go to showdown
if len(active_players) <= 1:
    world["game_state"]["phase"] = "showdown"
    print("Only one player remains - going to showdown", file=sys.stderr)
    print(json.dumps(world))
    sys.exit(0)  # World changed

# Check if betting round is complete
# Everyone must have acted and either folded or matched the current bet
current_bet = world["game_state"]["current_bet"]
round_complete = True

for seat in active_players:
    if not seat["has_acted"] or (seat["current_bet"] != current_bet and not seat["is_folded"]):
        round_complete = False
        break

if not round_complete:
    # Betting round not complete
    print(json.dumps(world))
    sys.exit(9)  # No changes

# Betting round is complete, advance to next phase
current_phase = world["game_state"]["phase"]
if current_phase == "pre_flop":
    # Deal the flop (3 cards)
    for _ in range(3):
        if world["deck"]:
            card = world["deck"].pop(0)
            world["board"].append(card)
    world["game_state"]["phase"] = "flop"
    print("Advancing to FLOP", file=sys.stderr)
elif current_phase == "flop":
    # Deal the turn (1 card)
    if world["deck"]:
        card = world["deck"].pop(0)
        world["board"].append(card)
    world["game_state"]["phase"] = "turn"
    print("Advancing to TURN", file=sys.stderr)
elif current_phase == "turn":
    # Deal the river (1 card)
    if world["deck"]:
        card = world["deck"].pop(0)
        world["board"].append(card)
    world["game_state"]["phase"] = "river"
    print("Advancing to RIVER", file=sys.stderr)
elif current_phase == "river":
    # Go to showdown
    world["game_state"]["phase"] = "showdown"
    print("Advancing to SHOWDOWN", file=sys.stderr)

# Reset betting for the new phase
for seat in world["seats"]:
    if seat["player_id"]:
        seat["current_bet"] = 0
        seat["total_bet_this_round"] = 0
        seat["has_acted"] = False

world["game_state"]["current_bet"] = 0

# Set first player to act (after dealer in all rounds after pre-flop)
dealer_pos = world["game_state"]["dealer_position"]
active_positions = []
for seat in world["seats"]:
    if seat["player_id"] and not seat["is_folded"]:
        active_positions.append(seat["position"])

active_positions.sort()
if active_positions:
    # Find first active player after dealer
    next_turn = active_positions[0]  # Default to first position
    for pos in active_positions:
        if pos > dealer_pos:
            next_turn = pos
            break
    world["game_state"]["current_turn"] = next_turn

# OUTPUT MODIFIED WORLD TO STDOUT
print(json.dumps(world))

# Signal that we modified the world
sys.exit(0)