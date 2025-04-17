"""
JC-CLI Command Parser: Parses text commands and routes to appropriate Lua scripts
"""
import re
import os

class CommandParser:
    def __init__(self):
        """Initialize command parser"""
        # Map of command prefixes to Lua scripts
        # This could be loaded from a configuration file
        self.command_map = {
            "mv": "scripts/commands/move_resource.lua",
            "use": "scripts/commands/use_card.lua",
            "draw": "scripts/commands/draw_card.lua",
            "endturn": "scripts/commands/end_turn.lua",
            "init": "scripts/commands/initialize_game.lua",
            "deck": "scripts/commands/setup_deck.lua",
            "exec": "scripts/commands/execute_card.lua",
            "register_endturn": "scripts/commands/register_endturn.lua"
        }
    
    def parse_command(self, command_text):
        """
        Parse a command string into structured format
        
        Args:
            command_text (str): Raw command text (e.g., "plr1 mv slot_1 slot_3")
            
        Returns:
            dict: Parsed command with player, action, params, and script path
        """
        # Basic validation
        if not command_text or not isinstance(command_text, str):
            return None
        
        # Split command by whitespace
        parts = command_text.strip().split()
        if len(parts) < 2:
            return None
        
        # Extract player and action
        player = parts[0]
        action = parts[1]
        
        # Extract parameters (everything after action)
        params = parts[2:] if len(parts) > 2 else []
        
        # Find appropriate script
        script_path = self.get_script_path(action)
        
        # Return structured command
        return {
            "player": player,
            "action": action,
            "params": params,
            "script_path": script_path,
            "raw_command": command_text
        }
    
    def get_script_path(self, action):
        """
        Get the Lua script path for a given action
        
        Args:
            action (str): Command action (e.g., "mv", "use")
            
        Returns:
            str: Path to Lua script or None if not found
        """
        script_path = self.command_map.get(action)
        
        # Check if script exists
        if script_path and os.path.exists(script_path):
            return script_path
        
        return None
    
    def route_command(self, parsed_command):
        """
        Get the full routing information for a command
        
        Args:
            parsed_command (dict): Previously parsed command
            
        Returns:
            dict: Command with additional routing information
        """
        if not parsed_command or "action" not in parsed_command:
            return None
        
        # Just verify script path is available
        if "script_path" not in parsed_command or not parsed_command["script_path"]:
            parsed_command["script_path"] = self.get_script_path(parsed_command["action"])
        
        return parsed_command