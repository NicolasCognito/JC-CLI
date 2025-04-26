#!/usr/bin/env python3
# Chess board view
NAME = "chess"

def render(world, context):
    """Render the chess board and game state"""
    username = context.get("username", "observer")
    player_color = "white" if username == "player1" else "black"
    
    # Unicode chess pieces
    pieces = {
        "WK": "♔", "WQ": "♕", "WR": "♖", "WB": "♗", "WN": "♘", "WP": "♙",
        "BK": "♚", "BQ": "♛", "BR": "♜", "BB": "♝", "BN": "♞", "BP": "♟",
        "": " "
    }
    
    board = world["board"]
    current_turn = world["current_turn"]
    game_state = world["game_state"]
    
    # Print game header
    print(f"\n=== Chess Game [{username}] ===")
    print(f"Current turn: {current_turn.upper()}")
    print(f"Game state: {game_state.upper()}")
    
    # Print the board
    print("\n    a b c d e f g h")
    print("  +-----------------+")
    
    # Flip board for black player's view
    rows = range(8) if player_color == "white" else range(7, -1, -1)
    
    for i in rows:
        rank = 8 - i if player_color == "white" else i + 1
        print(f"{rank} | ", end="")
        
        cols = range(8) if player_color == "white" else range(7, -1, -1)
        for j in cols:
            piece = board[i][j]
            print(f"{pieces[piece]} ", end="")
        
        print(f"| {rank}")
    
    print("  +-----------------+")
    print("    a b c d e f g h\n")
    
    # Print captured pieces
    white_captured = " ".join(pieces[p] for p in world["captured_pieces"]["white"])
    black_captured = " ".join(pieces[p] for p in world["captured_pieces"]["black"])
    
    print("Pieces captured by White:", white_captured or "None")
    print("Pieces captured by Black:", black_captured or "None")
    
    # Print last few moves from history
    print("\nMove history:")
    last_moves = world["move_history"][-5:] if len(world["move_history"]) > 5 else world["move_history"]
    for i, move in enumerate(last_moves):
        move_num = len(world["move_history"]) - len(last_moves) + i + 1
        print(f"{move_num}. {move}")
    
    # Print available commands
    print("\nCommands:")
    print("move <from> <to>    - Move a piece (e.g., 'move e2 e4')")
    print("castle kingside     - Castle on the kingside")
    print("castle queenside    - Castle on the queenside")
    print("view chess          - Show the chess board")