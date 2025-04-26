#!/usr/bin/env python3
# Validator: pawn move
NAME = "pawn_move"

import json
import sys

# Read validation input from stdin
validation_input = json.loads(sys.stdin.read())
from_row = validation_input["from_row"]
from_col = validation_input["from_col"]
to_row = validation_input["to_row"]
to_col = validation_input["to_col"]
piece = validation_input["piece"]
board = validation_input["board"]

# Determine direction based on piece color
color = "white" if piece[0] == "W" else "black"
forward = -1 if color == "white" else 1  # White moves up, Black moves down

# Check target square
target_piece = board[to_row][to_col]
target_occupied = target_piece != ""
target_enemy = target_piece and target_piece[0] != piece[0]

# Valid move patterns for pawns:
valid_move = False

# 1. Forward one square (if not occupied)
if from_col == to_col and to_row == from_row + forward and not target_occupied:
    valid_move = True

# 2. Forward two squares from starting position (if path clear)
starting_row = 6 if color == "white" else 1
if from_col == to_col and from_row == starting_row and to_row == from_row + 2*forward:
    # Check if path is clear
    middle_row = from_row + forward
    if not board[middle_row][from_col] and not target_occupied:
        valid_move = True

# 3. Diagonal capture
if abs(to_col - from_col) == 1 and to_row == from_row + forward and target_enemy:
    valid_move = True

# Return result
if valid_move:
    sys.exit(0)
else:
    print("Invalid pawn move")
    sys.exit(1)