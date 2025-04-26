#!/usr/bin/env python3
# Validator: knight move
NAME = "knight_move"

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

# Knights move in L-shape: 2 squares in one direction, then 1 square perpendicular
valid_move = False

# Calculate the move delta
row_diff = abs(to_row - from_row)
col_diff = abs(to_col - from_col)

# Valid knight move is (2,1) or (1,2)
if (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2):
    valid_move = True

# Return result
if valid_move:
    sys.exit(0)
else:
    print("Invalid knight move. Knights move in an L-shape (2 squares in one direction, 1 square perpendicular)")
    sys.exit(1)