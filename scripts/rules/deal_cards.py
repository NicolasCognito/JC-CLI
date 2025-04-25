#!/usr/bin/env python3
# Rule: deal cards to players at the start of a hand
NAME = "deal_cards"

import json
import sys

# Load the world state FROM STDIN
world = json.loads(sys.stdin.read())

# Check if we're in the pre-flop phase
if world["game_state"]["phase"] != "pre_flop":
    # Rule doesn't apply
    print(json.dumps(world))
    sys.exit(9)  # No changes

# Check if cards have already been dealt
active_seats = [seat for seat in world["seats"] if seat["player_id"] is not None]
if active_seats and len(active_seats[0]["cards"]) > 0:
    # Cards already dealt
    print(json.dumps(world))
    sys.exit(9)  # No changes

# Make sure we have a deck
if not world["deck"]:
    print("Error: Deck is empty!", file=sys.stderr)
    print(json.dumps(world))
    sys.exit(1)  # Error

# Deal 2 cards to each active player
for seat in world["seats"]:
    if seat["player_id"] is not None:
        # Deal first card to each player
        if world["deck"]:
            card = world["deck"].pop(0)
            seat["cards"].append(card)
        else:
            print("Error: Ran out of cards while dealing!", file=sys.stderr)
            print(json.dumps(world))
            sys.exit(1)
            
        # Deal second card to each player
        if world["deck"]:
            card = world["deck"].pop(0)
            seat["cards"].append(card)
        else:
            print("Error: Ran out of cards while dealing!", file=sys.stderr)
            print(json.dumps(world))
            sys.exit(1)

print("Cards dealt to all active players", file=sys.stderr)

# OUTPUT MODIFIED WORLD TO STDOUT
print(json.dumps(world))

# Signal that we modified the world
sys.exit(0)