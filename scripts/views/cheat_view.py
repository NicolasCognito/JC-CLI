#!/usr/bin/env python3
# Default poker game view
NAME = "cheat"

def render(world, context):
    """Render the poker game state"""
    username = context.get("username", "observer")
    
    print(f"\n=== Poker Game [{username}] ===")
    
    # Game status info
    phase = world.get("game_state", {}).get("phase", "waiting")
    print(f"\nGame Phase: {phase.upper()}")
    
    # Show pot
    pot = world.get("game_state", {}).get("pot", 0)
    print(f"Pot: {pot} chips")
    
    # Show current bet
    current_bet = world.get("game_state", {}).get("current_bet", 0)
    if current_bet > 0:
        print(f"Current Bet: {current_bet} chips")
    
    # Show dealer and blinds
    if phase != "waiting" and phase != "ready_to_start":
        dealer_pos = world.get("game_state", {}).get("dealer_position", 0)
        sb_pos = world.get("game_state", {}).get("small_blind_position", 0)
        bb_pos = world.get("game_state", {}).get("big_blind_position", 0)
        print(f"Dealer: Seat {dealer_pos} | SB: Seat {sb_pos} | BB: Seat {bb_pos}")
    
    # Show board cards
    board = world.get("board", [])
    if board:
        board_str = []
        for card_id in board:
            card = world.get("card_definitions", {}).get(card_id, {})
            if card:
                board_str.append(f"{card['rank']}{card['suit'][0]}")
        print(f"\nBoard: {' '.join(board_str)}")
    elif phase not in ["waiting", "ready_to_start", "pre_flop"]:
        print("\nBoard: [Empty]")
    
    # Show players and their status
    print("\nPlayers:")
    seats = world.get("seats", [])
    current_turn = world.get("game_state", {}).get("current_turn")
    
    # Function to format a card display
    def format_card(card_id):
        card = world.get("card_definitions", {}).get(card_id, {})
        if card:
            suit_symbols = {"hearts": "♥", "diamonds": "♦", "clubs": "♣", "spades": "♠"}
            suit_symbol = suit_symbols.get(card["suit"], card["suit"][0])
            return f"{card['rank']}{suit_symbol}"
        return "??"
    
    for seat in seats:
        position = seat.get("position", 0)
        player_id = seat.get("player_id")
        
        if player_id:
            # Get player info
            player = world.get("players", {}).get(player_id, {})
            chips = player.get("chips", 0)
            current_bet = seat.get("current_bet", 0)
            folded = seat.get("is_folded", False)
            is_winner = seat.get("is_winner", False)
            
            # Format player status
            status = []
            if folded:
                status.append("FOLDED")
            if current_bet > 0:
                status.append(f"Bet: {current_bet}")
            if is_winner:
                status.append("WINNER!")
            
            status_str = f" ({', '.join(status)})" if status else ""
            
            # Turn marker
            turn_marker = "➤ " if position == current_turn else "  "
            
            # Basic player line
            line = f"{turn_marker}Seat {position}: {player_id} ({chips} chips){status_str}"
                
            # Show cards based on game state
            cards = seat.get("cards", [])
            if cards:
                card_str = []
                for card_id in cards:
                    card_str.append(format_card(card_id))
                line += f" - Cards: {' '.join(card_str)}"
                    
            print(line)
            
            # If in showdown phase, show hand evaluation details
            if phase == "showdown" and seat.get("combo"):
                combo = seat.get("combo")
                combo_cards = seat.get("combo_cards", [])
                
                # Format the combo cards
                combo_card_str = []
                for card_id in combo_cards:
                    combo_card_str.append(format_card(card_id))
                
                # Show the combo details indented under the player
                combo_line = f"    → {combo}: {' '.join(combo_card_str)}"
                print(combo_line)
        else:
            print(f"  Seat {position}: Empty")
    
    # Show available commands based on game state
    print("\nCommands:")
    if phase == "waiting":
        print("  join <position> - Join the game at a seat")
        if sum(1 for seat in seats if seat["player_id"] is not None) >= 2:
            print("  start - Start the game (when 2+ players ready)")
    elif phase == "ready_to_start":
        print("  start - Start the game (when 2+ players ready)")
    elif phase == "showdown":
        print("  start - Start a new hand")
    else:
        # Player's turn commands
        if any(seat.get("player_id") == username for seat in seats):
            player_seat = next(seat for seat in seats if seat.get("player_id") == username)
            
            # Only show relevant commands when it's the player's turn
            if player_seat.get("position") == current_turn:
                if not player_seat.get("is_folded", False):
                    if world.get("game_state", {}).get("current_bet", 0) == 0:
                        print("  check - Pass without betting")
                        print("  bet <amount> - Place a bet")
                    else:
                        print("  call - Match the current bet")
                        print("  raise <amount> - Increase the bet")
                    print("  fold - Discard your hand")
                    print("  all-in - Bet all your chips")
    
    # Always show general commands
    print("  status - Show game status")
    print("  leave - Leave the game")
    print("  help - Show more commands")