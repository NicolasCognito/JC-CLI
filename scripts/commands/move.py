#!/usr/bin/env python3
# Command: move a chess piece
NAME = "move"

import json
import sys
import os
import subprocess

# Get player who issued the command
player = os.environ.get("PLAYER", "unknown")
command_args = os.environ.get("COMMAND_ARGS", "")

# Parse move argument (e.g., "e2 e4" or "a1 h8")
try:
    from_pos, to_pos = command_args.strip().split()    # Convert chess notation to array indices
    from_file, from_rank = from_pos[0], int(from_pos[1])
    to_file, to_rank = to_pos[0], int(to_pos[1])
    
    from_col = ord(from_file) - ord('a')
    from_row = 8 - from_rank
    to_col = ord(to_file) - ord('a')
    to_row = 8 - to_rank
except ValueError:
    print(f"Invalid move format. Use: move <from> <to> (e.g., 'move e2 e4')")
    sys.exit(1)

# Load the world state
with open("data/world.json", "r") as f:
    world = json.load(f)

# Check if game is still in progress
if world["game_state"] not in ["in_progress", "check"]:
    print(f"Game is over. Result: {world['game_state']}")
    sys.exit(1)

# Check if it's the player's turn
player_color = "white" if player == "player1" else "black"
if world["current_turn"] != player_color:
    print(f"Not your turn. Current turn: {world['current_turn']}")
    sys.exit(1)

# Check if the positions are valid
if not (0 <= from_row < 8 and 0 <= from_col < 8 and 0 <= to_row < 8 and 0 <= to_col < 8):
    print("Invalid position. Board is 8x8 (a1 to h8).")
    sys.exit(1)

# Check if there's a piece at the from_position
piece = world["board"][from_row][from_col]
if not piece:
    print(f"No piece at {from_pos}")
    sys.exit(1)

# Check if the piece belongs to the player
piece_color = "white" if piece[0] == "W" else "black"
if piece_color != player_color:
    print(f"The piece at {from_pos} belongs to the opponent")
    sys.exit(1)

# Get piece type
piece_type = piece[1]

# Validate the move with the appropriate validator script
validator_script = f"scripts/validators/{piece_type.lower()}_move.py"
if os.path.exists(validator_script):
    # Prepare input for validator
    validation_input = {
        "from_row": from_row,
        "from_col": from_col,
        "to_row": to_row,
        "to_col": to_col,
        "piece": piece,
        "board": world["board"]
    }
    
    # Call validator as subprocess
    process = subprocess.run(
        ["python3", validator_script],
        input=json.dumps(validation_input),
        text=True,
        capture_output=True
    )
    
    # Check validator result
    if process.returncode != 0:
        print(f"Invalid move: {process.stdout}")
        sys.exit(1)
else:
    print(f"Error: No validator found for piece type {piece_type}")
    sys.exit(1)

# Capture logic
target_piece = world["board"][to_row][to_col]
if target_piece:
    target_color = "white" if target_piece[0] == "W" else "black"
    if target_color == player_color:
        print("Cannot capture your own piece")
        sys.exit(1)
    # Add the captured piece to the list
    world["captured_pieces"][player_color].append(target_piece)

# Execute the move
world["board"][to_row][to_col] = piece
world["board"][from_row][from_col] = ""

# Record the move in algebraic notation
from_notation = f"{chr(from_col + ord('a'))}{8 - from_row}"
to_notation = f"{chr(to_col + ord('a'))}{8 - to_row}"
move_record = f"{piece_type}{from_notation}-{to_notation}"
if target_piece:
    move_record += f"x{target_piece}"
world["move_history"].append(move_record)

# Update castling rights if king or rook moves
if piece_type == "K":
    world["castle_rights"][player_color]["kingside"] = False
    world["castle_rights"][player_color]["queenside"] = False
elif piece_type == "R":
    # Kingside rook
    if from_col == 7:
        world["castle_rights"][player_color]["kingside"] = False
    # Queenside rook
    elif from_col == 0:
        world["castle_rights"][player_color]["queenside"] = False

# Save the updated world state
with open("data/world.json", "w") as f:
    json.dump(world, f, indent=2)

print(f"Moved {piece} from {from_pos} to {to_pos}")
sys.exit(0)