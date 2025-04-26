#!/usr/bin/env python3
NAME = "move"

import json
import sys
import os

# Get player who issued the command
player = os.environ.get("PLAYER", "unknown")

# Get command arguments (e.g., "e2e4")
args = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""

# Load the world state
with open("data/world.json", "r") as f:
    world = json.load(f)

# Verify it's the correct player's turn
current_color = world["current_turn"]
if (current_color == "white" and not player.startswith("player_white")) or \
   (current_color == "black" and not player.startswith("player_black")):
    print(f"Not your turn. It's {current_color}'s turn.")
    sys.exit(1)

# Parse chess coordinates (e.g., "e2e4")
if len(args) != 4:
    print("Invalid move format. Use format like 'e2e4'")
    sys.exit(1)

src_col, src_row = args[0], args[1]
dst_col, dst_row = args[2], args[3]

# Convert algebraic notation to array indices
try:
    # Convert columns (a=0, b=1, ..., h=7)
    src_col_idx = ord(src_col.lower()) - ord('a')
    dst_col_idx = ord(dst_col.lower()) - ord('a')
    
    # Convert rows (1=7, 2=6, ..., 8=0) - inverted because arrays are 0-indexed from top
    src_row_idx = 8 - int(src_row)
    dst_row_idx = 8 - int(dst_row)
    
    # Check if indices are valid
    if not (0 <= src_col_idx <= 7 and 0 <= src_row_idx <= 7 and 
            0 <= dst_col_idx <= 7 and 0 <= dst_row_idx <= 7):
        raise ValueError("Coordinates out of bounds")
except:
    print("Invalid chess coordinates")
    sys.exit(1)

# Get the piece at the source position
piece = world["board"][src_row_idx][src_col_idx]

# Check if there is a piece at the source position
if not piece:
    print("No piece at the source position")
    sys.exit(1)

# Check if the piece belongs to the current player
piece_color = piece[0]  # First character of piece code (W/B)
expected_color = "W" if current_color == "white" else "B"
if piece_color != expected_color:
    print(f"That piece doesn't belong to you")
    sys.exit(1)

# Check if source and destination are different
if src_row_idx == dst_row_idx and src_col_idx == dst_col_idx:
    print("Source and destination are the same")
    sys.exit(1)

# Record captured piece if any
dst_piece = world["board"][dst_row_idx][dst_col_idx]
if dst_piece:
    captured_color = "black" if dst_piece[0] == "B" else "white"
    if captured_color != current_color:  # Ensure we're not capturing our own piece
        world["captured_pieces"][current_color].append(dst_piece)
    else:
        print("Cannot capture your own piece")
        sys.exit(1)

# Make the move
world["board"][dst_row_idx][dst_col_idx] = piece
world["board"][src_row_idx][src_col_idx] = ""

# Update the move history using algebraic notation
move_notation = f"{src_col}{src_row}-{dst_col}{dst_row}"
world["move_history"].append(move_notation)

# Increment the move counters
if piece[1] == "P" or dst_piece:  # Pawn move or capture
    world["halfmove_clock"] = 0
else:
    world["halfmove_clock"] += 1

if current_color == "black":
    world["fullmove_number"] += 1

# Record the command in the world state
world["last_command"] = {
    "name": NAME,
    "args": args,
    "player": player
}

# Save the updated world state
with open("data/world.json", "w") as f:
    json.dump(world, f, indent=2)

print(f"Moved {piece} from {src_col}{src_row} to {dst_col}{dst_row}")
sys.exit(0)