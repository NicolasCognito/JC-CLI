#!/usr/bin/env python3
# Rule: post blinds when a new hand starts
NAME = "post_blinds"

import json
import sys

# Load the world state FROM STDIN
world = json.loads(sys.stdin.read())

# Check if we're in the pre-flop phase
if world["game_state"]["phase"] != "pre_flop":
    # Rule doesn't apply
    print(json.dumps(world))
    sys.exit(9)  # No changes

# Check if blinds have already been posted (pot > 0)
if world["game_state"]["pot"] > 0:
    # Blinds already posted
    print(json.dumps(world))
    sys.exit(9)  # No changes

# Get small and big blind positions and amounts
sb_pos = world["game_state"]["small_blind_position"]
bb_pos = world["game_state"]["big_blind_position"]
sb_amount = world["metadata"]["small_blind"]
bb_amount = world["metadata"]["big_blind"]

# Find seats for these positions
sb_seat = None
bb_seat = None
for seat in world["seats"]:
    if seat["position"] == sb_pos:
        sb_seat = seat
    if seat["position"] == bb_pos:
        bb_seat = seat

# Post small blind
if sb_seat and sb_seat["player_id"]:
    player_id = sb_seat["player_id"]
    chips = world["players"][player_id]["chips"]
    
    # Cap the blind at available chips
    actual_sb = min(sb_amount, chips)
    world["players"][player_id]["chips"] -= actual_sb
    sb_seat["current_bet"] = actual_sb
    sb_seat["total_bet_this_round"] = actual_sb
    world["game_state"]["pot"] += actual_sb
    
    print(f"Small Blind: {player_id} posted {actual_sb} chips", file=sys.stderr)

# Post big blind
if bb_seat and bb_seat["player_id"]:
    player_id = bb_seat["player_id"]
    chips = world["players"][player_id]["chips"]
    
    # Cap the blind at available chips
    actual_bb = min(bb_amount, chips)
    world["players"][player_id]["chips"] -= actual_bb
    bb_seat["current_bet"] = actual_bb
    bb_seat["total_bet_this_round"] = actual_bb
    world["game_state"]["pot"] += actual_bb
    world["game_state"]["current_bet"] = actual_bb
    
    print(f"Big Blind: {player_id} posted {actual_bb} chips", file=sys.stderr)

# OUTPUT MODIFIED WORLD TO STDOUT
print(json.dumps(world))

# Signal that we modified the world
sys.exit(0)