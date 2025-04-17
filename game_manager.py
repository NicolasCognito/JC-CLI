"""
JC-CLI Game Manager: Manages game turn progression and state transitions
"""
import json
import os

class GameManager:
    def __init__(self, engine):
        """Initialize game manager"""
        self.engine = engine
        
        # Keep track of current turn
        self.current_turn = 0
        
        # Track players who have ended their turn
        self.ended_turns = set()
        
        # Load current turn from main.json
        self._load_current_turn()
    
    def _load_current_turn(self):
        """Load current turn from game state"""
        try:
            with open("main.json", "r") as f:
                game_state = json.load(f)
                self.current_turn = game_state.get("game", {}).get("turn", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            self.current_turn = 0
    
    def check_turn_end(self, player=None):
        """
        Check if a turn should end
        
        Args:
            player (str, optional): Player who ended their turn
            
        Returns:
            bool: True if all players ended turn
        """
        # Record player's turn end if provided
        if player:
            self.ended_turns.add(player)
        
        # Read main.json to get player list
        try:
            with open("main.json", "r") as f:
                game_state = json.load(f)
            
            # Get list of players
            players = list(game_state.get("game", {}).get("state", {}).get("players", {}).keys())
            
            # Check if all players ended turn
            all_ended = all(p in self.ended_turns for p in players)
            
            return all_ended
            
        except (FileNotFoundError, json.JSONDecodeError):
            return False
    
    def register_turn_end(self, player):
        """
        Register that a player has ended their turn
        
        Args:
            player (str): Player ID
            
        Returns:
            bool: True if all players have ended their turn
        """
        self.ended_turns.add(player)
        
        # Check if all players ended turn
        if self.check_turn_end():
            # Generate a system command for turn end
            next_index = self._get_next_index()
            
            # Create a system command to register turn end
            sys_command = {
                "index": next_index,
                "player": "sys",
                "command": "sys register_endturn",
                "applied": False
            }
            
            # Add to sequencer
            self.engine.command_sequencer.add_command(sys_command)
            
            return True
        
        return False
    
    def advance_turn(self):
        """
        Advance to the next game turn
        
        Note: This doesn't modify main.json - that's done by Lua scripts
        """
        self.current_turn += 1
        self.ended_turns.clear()
        
        # Run postprocessing
        self.run_postprocessing()
    
    def run_postprocessing(self):
        """Run turn postprocessing"""
        # Read main.json to determine what cards need to be executed
        try:
            with open("main.json", "r") as f:
                game_state = json.load(f)
            
            # Get active cards that need to be executed
            # This is simplified and would be more complex in a real game
            # Would typically iterate through cards in play
            
            # For example, execute all cards in player hands
            for player_id, player in game_state.get("game", {}).get("state", {}).get("players", {}).items():
                for card_id in player.get("hand", {}).get("cards", []):
                    # Create a system command to execute card
                    next_index = self._get_next_index()
                    
                    sys_command = {
                        "index": next_index,
                        "player": "sys",
                        "command": f"sys exec {card_id}",
                        "applied": False
                    }
                    
                    # Add to sequencer
                    self.engine.command_sequencer.add_command(sys_command)
        
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    def _get_next_index(self):
        """Get next available command index"""
        next_index = 0
        
        try:
            with open("history.json", "r") as f:
                history = json.load(f)
            
            # Find highest index
            for turn in history.get("history", {}).get("turns", []):
                for action in turn.get("actions", []):
                    next_index = max(next_index, action.get("index", -1) + 1)
                for post in turn.get("postprocessing", []):
                    next_index = max(next_index, post.get("index", -1) + 1)
                    
        except (FileNotFoundError, json.JSONDecodeError):
            pass
            
        return next_index