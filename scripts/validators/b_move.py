#!/usr/bin/env python3
# Validator: bishop move
NAME = "bishop_move"

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

# Bishops move diagonally
row_diff = abs(to_row - from_row)
col_diff = abs(to_col - from_col)

# Check if move is diagonal
if row_diff != col_diff:
    print("Bishops must move diagonally")
    sys.exit(1)

# Determine direction of movement
row_step = 1 if to_row > from_row else -1
col_step = 1 if to_col > from_col else -1

# Check for pieces in the path
valid_move = True
row, col = from_row + row_step, from_col + col_step

while row != to_row and col != to_col:
    if board[row][col]:
        valid_move = False
        break
    row += row_step
    col += col_step

# Return result
if valid_move:
    sys.exit(0)
else:
    print("There are pieces blocking the bishop's path")
    sys.exit(1)