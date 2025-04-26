#!/usr/bin/env python3
NAME = "check_game_end"

import json
import sys
import subprocess

# Read world from stdin
world = json.loads(sys.stdin.read())

# Only proceed if game is in progress
if world["game_state"] != "in_progress" and world["game_state"] != "check":
    print(json.dumps(world))
    sys.exit(9)  # No changes

# Helper function to find a piece on the board
def find_piece(board, piece_code):
    for r in range(8):
        for c in range(8):
            if board[r][c] == piece_code:
                return (r, c)
    return None

# Helper function to check if a square is under attack
def is_square_attacked(board, row, col, by_color):
    # For simplicity, we'll check each piece type that could attack this square
    
    # Check for pawn attacks
    pawn_code = "BP" if by_color == "black" else "WP"
    pawn_dirs = [(-1, -1), (-1, 1)] if by_color == "black" else [(1, -1), (1, 1)]
    
    for dr, dc in pawn_dirs:
        r, c = row + dr, col + dc
        if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == pawn_code:
            return True
    
    # Check for knight attacks
    knight_code = "BN" if by_color == "black" else "WN"
    knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
    
    for dr, dc in knight_moves:
        r, c = row + dr, col + dc
        if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == knight_code:
            return True
    
    # Check for king proximity (kings can't be adjacent)
    king_code = "BK" if by_color == "black" else "WK"
    king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    
    for dr, dc in king_moves:
        r, c = row + dr, col + dc
        if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == king_code:
            return True
    
    # Check for horizontal/vertical attacks (rook, queen)
    rook_code = "BR" if by_color == "black" else "WR"
    queen_code = "BQ" if by_color == "black" else "WQ"
    
    # Check horizontally and vertically
    for direction in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
        dr, dc = direction
        r, c = row + dr, col + dc
        while 0 <= r < 8 and 0 <= c < 8:
            if board[r][c] != "":
                if board[r][c] == rook_code or board[r][c] == queen_code:
                    return True
                break  # Blocked by some piece
            r += dr
            c += dc
    
    # Check for diagonal attacks (bishop, queen)
    bishop_code = "BB" if by_color == "black" else "WB"
    
    # Check diagonally
    for direction in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        dr, dc = direction
        r, c = row + dr, col + dc
        while 0 <= r < 8 and 0 <= c < 8:
            if board[r][c] != "":
                if board[r][c] == bishop_code or board[r][c] == queen_code:
                    return True
                break  # Blocked by some piece
            r += dr
            c += dc
    
    return False

# Find kings
white_king_pos = find_piece(world["board"], "WK")
black_king_pos = find_piece(world["board"], "BK")

if not white_king_pos or not black_king_pos:
    # This shouldn't happen in a valid chess game, but just in case
    if not white_king_pos:
        world["game_state"] = "black_wins"
    else:
        world["game_state"] = "white_wins"
    print(json.dumps(world))
    sys.exit(0)

# Check if kings are in check
white_in_check = is_square_attacked(world["board"], white_king_pos[0], white_king_pos[1], "black")
black_in_check = is_square_attacked(world["board"], black_king_pos[0], black_king_pos[1], "white")

# Update game state based on check status
changed = False
if world["current_turn"] == "white" and white_in_check:
    world["game_state"] = "check"
    changed = True
elif world["current_turn"] == "black" and black_in_check:
    world["game_state"] = "check"
    changed = True
elif world["game_state"] == "check":
    # Reset to in_progress if no longer in check
    if (world["current_turn"] == "white" and not white_in_check) or \
       (world["current_turn"] == "black" and not black_in_check):
        world["game_state"] = "in_progress"
        changed = True

# For simplicity, we're not implementing checkmate detection here
# A more complete implementation would check if the player in check has any legal moves

# Output the world state
print(json.dumps(world))

# Exit with appropriate code
sys.exit(0 if changed else 9)