#!/usr/bin/env python3
# Validator: queen move
NAME = "queen_move"

import json
import sys
import subprocess

# Read validation input from stdin
validation_input = json.loads(sys.stdin.read())
from_row = validation_input["from_row"]
from_col = validation_input["from_col"]
to_row = validation_input["to_row"]
to_col = validation_input["to_col"]
piece = validation_input["piece"]
board = validation_input["board"]

# Queens move like rooks or bishops
# Check if move is horizontal/vertical (rook-like) or diagonal (bishop-like)
row_diff = abs(to_row - from_row)
col_diff = abs(to_col - from_col)

is_rook_move = from_row == to_row or from_col == to_col
is_bishop_move = row_diff == col_diff

if not (is_rook_move or is_bishop_move):
    print("Queens must move horizontally, vertically, or diagonally")
    sys.exit(1)

# Use the appropriate validator based on move type
if is_rook_move:
    # Use rook validator
    process = subprocess.run(
        ["python3", "scripts/validators/r_move.py"],
        input=json.dumps(validation_input),
        text=True,
        capture_output=True
    )
    if process.returncode != 0:
        print(process.stdout)
        sys.exit(1)
else:
    # Use bishop validator
    process = subprocess.run(
        ["python3", "scripts/validators/b_move.py"],
        input=json.dumps(validation_input),
        text=True,
        capture_output=True
    )
    if process.returncode != 0:
        print(process.stdout)
        sys.exit(1)

# If we made it here, the move is valid
sys.exit(0)