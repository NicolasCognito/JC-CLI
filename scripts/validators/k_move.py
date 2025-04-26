#!/usr/bin/env python3
# Validator: king move
NAME = "king_move"

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

# Kings move one square in any direction
row_diff = abs(to_row - from_row)
col_diff = abs(to_col - from_col)

# Normal king move (one square in any direction)
if row_diff <= 1 and col_diff <= 1:
    sys.exit(0)

# Check for castling (we'll implement a simplified version)
color = "white" if piece[0] == "W" else "black"
back_rank = 7 if color == "white" else 0

# Validate kingside castling
if from_row == back_rank and from_col == 4 and to_row == back_rank and to_col == 6:
    # Check if spaces between king and rook are empty
    if not board[back_rank][5] and not board[back_rank][6]:
        # Check if the rook is in place
        if board[back_rank][7] == (piece[0] + "R"):
            # Castle is valid (we're not checking for check)
            sys.exit(0)

# Validate queenside castling
if from_row == back_rank and from_col == 4 and to_row == back_rank and to_col == 2:
    # Check if spaces between king and rook are empty
    if not board[back_rank][1] and not board[back_rank][2] and not board[back_rank][3]:
        # Check if the rook is in place
        if board[back_rank][0] == (piece[0] + "R"):
            # Castle is valid (we're not checking for check)
            sys.exit(0)

# If we get here, the move is invalid
print("Invalid king move. Kings move one square in any direction, or castle under specific conditions.")
sys.exit(1)