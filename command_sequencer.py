"""
JC-CLI Command Sequencer: Manages ordered processing of commands
"""
import json
import os

class CommandSequencer:
    def __init__(self, engine):
        """Initialize command sequencer"""
        self.engine = engine
        self.command_queue = {}  # Index -> Command mapping
        self.last_processed_index = -1  # Start at -1 (no commands processed)
        
        # Load history to find highest processed index
        self._load_last_index()
    
    def _load_last_index(self):
        """Load the last processed index from history.json"""
        try:
            with open("history.json", "r") as f:
                history = json.load(f)
            
            # Find highest applied command
            highest_index = -1
            for turn in history.get("history", {}).get("turns", []):
                for action in turn.get("actions", []):
                    if action.get("applied", False):
                        highest_index = max(highest_index, action.get("index", -1))
                for post in turn.get("postprocessing", []):
                    if post.get("applied", False):
                        highest_index = max(highest_index, post.get("index", -1))
            
            self.last_processed_index = highest_index
            
        except (FileNotFoundError, json.JSONDecodeError):
            # If history doesn't exist or is invalid, keep default -1
            self.last_processed_index = -1
    
    def add_command(self, indexed_command):
        """
        Add a new command to the queue
        
        Args:
            indexed_command (dict): Command with index assigned
        """
        if not indexed_command or "index" not in indexed_command:
            return
        
        index = indexed_command["index"]
        self.command_queue[index] = indexed_command
        
        # Try to process as many commands as possible
        self.process_sequence()
    
    def process_sequence(self):
        """Process all available commands in sequence"""
        # Keep processing next available command until we can't anymore
        while self.try_process_next_command():
            pass
    
    def try_process_next_command(self):
        """
        Try to process the next command in sequence
        
        Returns:
            bool: True if a command was processed, False otherwise
        """
        next_index = self.last_processed_index + 1
        
        # Check if the next command exists in queue
        if next_index not in self.command_queue:
            return False
        
        command = self.command_queue[next_index]
        
        # Skip if already applied (shouldn't happen, but check anyway)
        if command.get("applied", False):
            self.last_processed_index = next_index
            return True
        
        # Parse the command
        parsed_command = self.engine.command_parser.parse_command(command["command"])
        if not parsed_command:
            # Invalid command, but still mark as processed to avoid getting stuck
            command["applied"] = True
            self._update_history(command)
            self.last_processed_index = next_index
            return True
        
        # Execute the command through lua bridge
        success = self.engine.execute_command(parsed_command)
        
        # Mark as applied
        command["applied"] = True
        self._update_history(command)
        self.last_processed_index = next_index
        
        # Notify view update
        self.engine.notify_view_update()
        
        return True
    
    def _update_history(self, command):
        """
        Update the command's status in history.json
        
        Args:
            command (dict): Command that was processed
        """
        try:
            # Load current history
            with open("history.json", "r") as f:
                history = json.load(f)
            
            # Find and update command
            found = False
            for turn in history.get("history", {}).get("turns", []):
                for action in turn.get("actions", []):
                    if action.get("index") == command["index"]:
                        action["applied"] = True
                        found = True
                        break
                
                if not found:
                    for post in turn.get("postprocessing", []):
                        if post.get("index") == command["index"]:
                            post["applied"] = True
                            found = True
                            break
                
                if found:
                    break
            
            # If not found, add to current turn
            if not found:
                # Get current turn
                current_turn = None
                turns = history.get("history", {}).get("turns", [])
                if turns:
                    current_turn = turns[-1]  # Last turn is current
                else:
                    # Create first turn if none exists
                    current_turn = {"turn": 0, "actions": [], "postprocessing": []}
                    if "history" not in history:
                        history["history"] = {}
                    if "turns" not in history["history"]:
                        history["history"]["turns"] = []
                    history["history"]["turns"].append(current_turn)
                
                # Add to appropriate section
                if command["player"] == "sys" and command["command"].startswith("sys "):
                    if command["command"].split()[1] in ["exec"]:
                        # System postprocessing commands
                        current_turn["postprocessing"].append(command)
                    else:
                        # Regular system commands
                        current_turn["actions"].append(command)
                else:
                    # Player commands
                    current_turn["actions"].append(command)
            
            # Save updated history
            with open("history.json", "w") as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            print(f"Error updating history: {e}")