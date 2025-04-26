#!/usr/bin/env python3
# Validator: rook move
NAME = "rook_move"

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

# Rooks move horizontally or vertically
valid_move = False

# Check if move is horizontal or vertical
is_horizontal = from_row == to_row
is_vertical = from_col == to_col

if not (is_horizontal or is_vertical):
    print("Rooks must move horizontally or vertically")
    sys.exit(1)

# Check for pieces in the path
valid_move = True

if is_horizontal:
    # Horizontal move
    step = 1 if to_col > from_col else -1
    col = from_col + step
    while col != to_col:
        if board[from_row][col]:
            valid_move = False
            break
        col += step
elif is_vertical:
    # Vertical move
    step = 1 if to_row > from_row else -1
    row = from_row + step
    while row != to_row:
        if board[row][from_col]:
            valid_move = False
            break
        row += step

# Return result
if valid_move:
    sys.exit(0)
else:
    print("There are pieces blocking the rook's path")
    sys.exit(1)