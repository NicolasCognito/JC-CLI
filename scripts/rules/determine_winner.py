#!/usr/bin/env python3
# Rule: determine the winner at showdown
NAME = "determine_winner"

import json
import sys
from collections import Counter

# Load the world state FROM STDIN
world = json.loads(sys.stdin.read())

# Check if we're in the showdown phase
if world["game_state"]["phase"] != "showdown":
    # Rule doesn't apply
    print(json.dumps(world))
    sys.exit(9)  # No changes

# Check if we already processed this showdown (pot is 0)
if world["game_state"]["pot"] == 0:
    # Already processed
    print(json.dumps(world))
    sys.exit(9)  # No changes

# Get all players still in the hand
active_players = []
for seat in world["seats"]:
    if seat["player_id"] and not seat["is_folded"]:
        active_players.append(seat)

# If only one player left, they win automatically
if len(active_players) == 1:
    winner = active_players[0]
    player_id = winner["player_id"]
    
    # Award pot to winner
    pot = world["game_state"]["pot"]
    world["players"][player_id]["chips"] += pot
    
    # Mark this player as winner with "Default Win" combo
    winner["combo"] = "Default Win"
    winner["combo_rank"] = 0
    winner["combo_cards"] = winner["cards"]
    
    print(f"{player_id} wins {pot} chips (everyone else folded)", file=sys.stderr)
    world["game_state"]["pot"] = 0
    
    # OUTPUT MODIFIED WORLD TO STDOUT
    print(json.dumps(world))
    
    # Signal that we modified the world
    sys.exit(0)

# Multiple players remain, evaluate hands
board = world["board"]
card_defs = world["card_definitions"]

# Hand type mapping
hand_names = {
    10: "Royal Flush",
    9: "Straight Flush",
    8: "Four of a Kind",
    7: "Full House",
    6: "Flush",
    5: "Straight",
    4: "Three of a Kind",
    3: "Two Pair",
    2: "Pair",
    1: "High Card"
}

# Function to evaluate hand strength
def evaluate_hand(hole_cards, board):
    # Combine hole cards and board
    all_cards = hole_cards + board
    all_card_objects = [card_defs[card] for card in all_cards]
    
    # Sort by value (high to low)
    all_card_objects.sort(key=lambda x: x["value"], reverse=True)
    
    # Check for flush
    suits = [card["suit"] for card in all_card_objects]
    flush_suit = None
    for suit in set(suits):
        if suits.count(suit) >= 5:
            flush_suit = suit
            break
    
    flush_cards = [card for card in all_card_objects if card["suit"] == flush_suit] if flush_suit else []
    
    # Check for straight
    values = [card["value"] for card in all_card_objects]
    unique_values = sorted(set(values), reverse=True)
    
    # Handle Ace low straight (A-5-4-3-2)
    if 14 in unique_values:
        unique_values.append(1)  # Add low Ace
    
    straight = False
    straight_high = 0
    straight_values = []
    
    for i in range(len(unique_values) - 4):
        if unique_values[i] - unique_values[i+4] == 4:
            straight = True
            straight_high = unique_values[i]
            straight_values = unique_values[i:i+5]
            break
    
    # Find the cards that form the straight
    straight_cards = []
    if straight:
        # Handle special case of Ace low straight
        if 1 in straight_values:
            straight_values.remove(1)
            straight_values.append(14)  # Use the high Ace
        
        # Find cards matching the straight values
        for value in straight_values:
            for card_id in all_cards:
                card = card_defs[card_id]
                if card["value"] == value and card_id not in straight_cards:
                    straight_cards.append(card_id)
                    break
    
    # Check for straight flush
    straight_flush = False
    straight_flush_cards = []
    
    if flush_suit and straight:
        flush_values = [card["value"] for card in flush_cards]
        if 14 in flush_values:
            flush_values.append(1)  # Add low Ace
        flush_values = sorted(set(flush_values), reverse=True)
        
        for i in range(len(flush_values) - 4):
            if flush_values[i] - flush_values[i+4] == 4:
                straight_flush = True
                straight_high = flush_values[i]
                flush_straight_values = flush_values[i:i+5]
                
                # Find the cards that form the straight flush
                for value in flush_straight_values:
                    for card_id in all_cards:
                        card = card_defs[card_id]
                        if card["value"] == value and card["suit"] == flush_suit and card_id not in straight_flush_cards:
                            straight_flush_cards.append(card_id)
                            break
                break
    
    # Count pairs, trips, quads
    value_counts = Counter(values)
    pairs = [v for v, count in value_counts.items() if count == 2]
    trips = [v for v, count in value_counts.items() if count == 3]
    quads = [v for v, count in value_counts.items() if count == 4]
    
    pairs.sort(reverse=True)
    trips.sort(reverse=True)
    quads.sort(reverse=True)
    
    # Find cards for each combination
    pair_cards = []
    trip_cards = []
    quad_cards = []
    
    # Find quad cards
    if quads:
        for card_id in all_cards:
            card = card_defs[card_id]
            if card["value"] == quads[0]:
                quad_cards.append(card_id)
    
    # Find trips cards
    if trips:
        for card_id in all_cards:
            card = card_defs[card_id]
            if card["value"] == trips[0] and card_id not in quad_cards:
                trip_cards.append(card_id)
    
    # Find pair cards
    if pairs:
        for value in pairs[:2]:  # Get top two pairs if available
            for card_id in all_cards:
                card = card_defs[card_id]
                if card["value"] == value and card_id not in quad_cards and card_id not in trip_cards:
                    pair_cards.append(card_id)
                    if len([c for c in pair_cards if card_defs[c]["value"] == value]) == 2:
                        break  # Only need 2 cards per pair
    
    # Find high cards (for kickers)
    high_cards = []
    for card_id in all_cards:
        card = card_defs[card_id]
        if (card_id not in quad_cards and 
            card_id not in trip_cards and 
            card_id not in pair_cards and 
            card_id not in straight_cards and 
            card_id not in straight_flush_cards):
            high_cards.append((card_id, card["value"]))
    
    high_cards.sort(key=lambda x: x[1], reverse=True)
    high_card_ids = [card_id for card_id, _ in high_cards]
    
    # Determine hand type and rank
    # 10: Royal Flush
    if straight_flush and straight_high == 14:
        return (10, [straight_high], straight_flush_cards[:5])
    
    # 9: Straight Flush
    if straight_flush:
        return (9, [straight_high], straight_flush_cards[:5])
    
    # 8: Four of a Kind
    if quads:
        kicker = high_card_ids[0] if high_card_ids else None
        result_cards = quad_cards.copy()
        if kicker:
            result_cards.append(kicker)
        return (8, [quads[0]], result_cards[:5])
    
    # 7: Full House
    if trips and pairs:
        return (7, [trips[0], pairs[0]], trip_cards[:3] + pair_cards[:2])
    if len(trips) >= 2:
        trip1_cards = []
        trip2_cards = []
        for card_id in all_cards:
            card = card_defs[card_id]
            if card["value"] == trips[0] and len(trip1_cards) < 3:
                trip1_cards.append(card_id)
            elif card["value"] == trips[1] and len(trip2_cards) < 2:
                trip2_cards.append(card_id)
        return (7, [trips[0], trips[1]], trip1_cards + trip2_cards[:2])
    
    # 6: Flush
    if flush_cards:
        flush_card_ids = []
        for card in flush_cards[:5]:
            for card_id in all_cards:
                if card_defs[card_id]["suit"] == flush_suit and card_defs[card_id]["value"] == card["value"] and card_id not in flush_card_ids:
                    flush_card_ids.append(card_id)
                    break
                if len(flush_card_ids) == 5:
                    break
        return (6, [card["value"] for card in flush_cards[:5]], flush_card_ids[:5])
    
    # 5: Straight
    if straight:
        return (5, [straight_high], straight_cards[:5])
    
    # 4: Three of a Kind
    if trips:
        kickers = high_card_ids[:2]
        result_cards = trip_cards.copy()
        result_cards.extend(kickers)
        return (4, [trips[0]], result_cards[:5])
    
    # 3: Two Pair
    if len(pairs) >= 2:
        kicker = high_card_ids[0] if high_card_ids else None
        result_cards = [c for c in pair_cards if card_defs[c]["value"] in [pairs[0], pairs[1]]]
        if kicker:
            result_cards.append(kicker)
        return (3, [pairs[0], pairs[1]], result_cards[:5])
    
    # 2: One Pair
    if pairs:
        kickers = high_card_ids[:3]
        result_cards = [c for c in pair_cards if card_defs[c]["value"] == pairs[0]]
        result_cards.extend(kickers)
        return (2, [pairs[0]], result_cards[:5])
    
    # 1: High Card
    return (1, values[:5], high_card_ids[:5])

# Evaluate all active hands
hand_rankings = []
for seat in active_players:
    player_id = seat["player_id"]
    hole_cards = seat["cards"]
    
    hand_type, values, combo_cards = evaluate_hand(hole_cards, board)
    hand_rankings.append((player_id, seat, hand_type, values, combo_cards))
    
    # Store the hand evaluation in the seat
    seat["combo"] = hand_names.get(hand_type, "Unknown")
    seat["combo_rank"] = hand_type
    seat["combo_cards"] = combo_cards

# Sort by hand strength (hand type, then values)
def compare_hands(hand1, hand2):
    _, _, type1, values1, _ = hand1
    _, _, type2, values2, _ = hand2
    
    if type1 != type2:
        return type1 - type2
    
    # Compare values in order
    for v1, v2 in zip(values1, values2):
        if v1 != v2:
            return v1 - v2
    
    return 0

hand_rankings.sort(key=lambda x: (x[2], x[3]), reverse=True)

# Find winners (could be multiple in case of tie)
winners = [hand_rankings[0]]
for hand in hand_rankings[1:]:
    if compare_hands(hand, winners[0]) == 0:
        winners.append(hand)
    else:
        break

# Award pot to winners
pot = world["game_state"]["pot"]
pot_per_winner = pot // len(winners)
remainder = pot % len(winners)  # Give remainder to first winner

for i, (player_id, seat, hand_type, _, _) in enumerate(winners):
    award = pot_per_winner
    if i == 0:
        award += remainder
    
    world["players"][player_id]["chips"] += award
    
    # Mark this player as a winner
    seat["is_winner"] = True
    
    print(f"{player_id} wins {award} chips with {hand_names.get(hand_type, 'Unknown')}", file=sys.stderr)

# Reset pot
world["game_state"]["pot"] = 0

# OUTPUT MODIFIED WORLD TO STDOUT
print(json.dumps(world))

# Signal that we modified the world
sys.exit(0)