#!/usr/bin/env python3
# Command: show game status
NAME = "status"

import json
import sys
import os

# Load the world state
with open("data/world.json", "r") as f:
    world = json.load(f)

# Get player who issued the command from environment variable
player = os.environ.get("PLAYER", "unknown")

# Display game metadata
print("\n=== POKER GAME STATUS ===")
print(f"Game Type: {world['metadata']['game_type']}")
print(f"Hand #: {world['metadata']['current_hand_id']}")
print(f"Blinds: {world['metadata']['small_blind']}/{world['metadata']['big_blind']}")

# Game phase
phase = world["game_state"]["phase"]
print(f"\nPhase: {phase.upper()}")

# Active players count
active_seats = sum(1 for seat in world["seats"] if seat["player_id"] is not None)
active_in_hand = sum(1 for seat in world["seats"] if seat["player_id"] is not None and not seat["is_folded"])
print(f"Players: {active_seats} seated, {active_in_hand} active in hand")

# Pot and current bet
print(f"Pot: {world['game_state']['pot']} chips")
if world["game_state"]["current_bet"] > 0:
    print(f"Current bet: {world['game_state']['current_bet']} chips")

# Board
if world["board"]:
    print("\nBoard:")
    card_str = []
    for card_id in world["board"]:
        card = world["card_definitions"][card_id]
        card_str.append(f"{card['rank']} of {card['suit']}")
    print(", ".join(card_str))

# Players and seats
print("\nSeating arrangement:")
for seat in world["seats"]:
    position = seat["position"]
    player_id = seat["player_id"]
    
    if player_id:
        player_info = world["players"][player_id]
        chips = player_info["chips"]
        status = []
        
        if position == world["game_state"]["dealer_position"]:
            status.append("Dealer")
        if position == world["game_state"]["small_blind_position"]:
            status.append("SB")
        if position == world["game_state"]["big_blind_position"]:
            status.append("BB")
        if seat["is_folded"]:
            status.append("Folded")
        if position == world["game_state"]["current_turn"]:
            status.append("Current Turn")
            
        status_str = f" ({', '.join(status)})" if status else ""
        bet_str = f", bet: {seat['current_bet']}" if seat["current_bet"] > 0 else ""
        
        print(f"Seat {position}: {player_id} - {chips} chips{bet_str}{status_str}")
    else:
        print(f"Seat {position}: Empty")

# If the player is in the game, show their hand
player_seat = None
for seat in world["seats"]:
    if seat["player_id"] == player:
        player_seat = seat
        break

if player_seat and player_seat["cards"]:
    print(f"\nYour cards:")
    card_str = []
    for card_id in player_seat["cards"]:
        card = world["card_definitions"][card_id]
        card_str.append(f"{card['rank']} of {card['suit']}")
    print(", ".join(card_str))

sys.exit(0)