#!/usr/bin/env python3
# Command: castle (kingside or queenside)
NAME = "castle"

import json
import sys

# Get player who issued the command
player = sys.argv[1] if len(sys.argv) > 1 else "unknown"
args = sys.argv[2] if len(sys.argv) > 2 else "kingside"  # Default to kingside

# Parse castle type
castle_type = args.strip().lower()
if castle_type not in ["kingside", "queenside"]:
    print("Invalid castle type. Use: castle kingside or castle queenside")
    sys.exit(1)

# Load the world state
with open("data/world.json", "r") as f:
    world = json.load(f)

# Check if game is still in progress
if world["game_state"] not in ["in_progress", "check"]:
    print(f"Game is over. Result: {world['game_state']}")
    sys.exit(1)

# Get player's color
player_color = "white" if player == "player1" else "black"
if world["current_turn"] != player_color:
    print(f"Not your turn. Current turn: {world['current_turn']}")
    sys.exit(1)

# Check if king is in check
if world["game_state"] == "check":
    print("Cannot castle while in check")
    sys.exit(1)

# Check castling rights
if not world["castle_rights"][player_color][castle_type]:
    print(f"You have lost the right to castle {castle_type}")
    sys.exit(1)

# Get board position constants
back_rank = 7 if player_color == "white" else 0
king_pos = 4
king_piece = "WK" if player_color == "white" else "BK"
rook_piece = "WR" if player_color == "white" else "BR"

if castle_type == "kingside":
    # Check if squares are empty
    if world["board"][back_rank][5] != "" or world["board"][back_rank][6] != "":
        print("Cannot castle kingside: squares between king and rook are occupied")
        sys.exit(1)
    
    # Check if rook is in place
    if world["board"][back_rank][7] != rook_piece:
        print("Cannot castle kingside: rook is not in place")
        sys.exit(1)
    
    # Perform the kingside castle
    world["board"][back_rank][6] = king_piece  # Move king
    world["board"][back_rank][5] = rook_piece  # Move rook
    world["board"][back_rank][4] = ""  # Remove king from original position
    world["board"][back_rank][7] = ""  # Remove rook from original position
    
    # Record the move
    castle_notation = "O-O"
else:  # queenside
    # Check if squares are empty
    if world["board"][back_rank][1] != "" or world["board"][back_rank][2] != "" or world["board"][back_rank][3] != "":
        print("Cannot castle queenside: squares between king and rook are occupied")
        sys.exit(1)
    
    # Check if rook is in place
    if world["board"][back_rank][0] != rook_piece:
        print("Cannot castle queenside: rook is not in place")
        sys.exit(1)
    
    # Perform the queenside castle
    world["board"][back_rank][2] = king_piece  # Move king
    world["board"][back_rank][3] = rook_piece  # Move rook
    world["board"][back_rank][4] = ""  # Remove king from original position
    world["board"][back_rank][0] = ""  # Remove rook from original position
    
    # Record the move
    castle_notation = "O-O-O"

# Add the move to history
world["move_history"].append(castle_notation)

# Update castling rights
world["castle_rights"][player_color]["kingside"] = False
world["castle_rights"][player_color]["queenside"] = False

# Save the updated world state
with open("data/world.json", "w") as f:
    json.dump(world, f, indent=2)

print(f"Castled {castle_type}")
sys.exit(0)