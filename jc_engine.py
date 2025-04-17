"""
JC-CLI Engine: Main coordination module
"""
import json
import os
from command_parser import CommandParser
from lua_bridge import LuaBridge
from command_sequencer import CommandSequencer
from game_manager import GameManager
from view import View
from cli import CLI
from thin_server import ThinServer
from client_connector import ClientConnector

class JCEngine:
    def __init__(self, config=None):
        """Initialize the JC-CLI engine"""
        self.config = config or {}
        
        # Ensure main.json and history.json exist
        if not os.path.exists("main.json"):
            with open("main.json", "w") as f:
                json.dump({"game": {}}, f)
        
        if not os.path.exists("history.json"):
            with open("history.json", "w") as f:
                json.dump({"history": {"turns": []}}, f)
        
        # Initialize components
        self.lua_bridge = LuaBridge()
        self.command_parser = CommandParser()
        self.command_sequencer = CommandSequencer(self)
        self.game_manager = GameManager(self)
        self.view = View()
        
        # Initialize networking if multiplayer
        if self.config.get("multiplayer", False):
            if self.config.get("is_server", False):
                self.server = ThinServer(self)
                self.client = None
            else:
                self.server = None
                self.client = ClientConnector(self)
        else:
            self.server = None
            self.client = None
        
        # CLI should be initialized last
        self.cli = CLI(self)
    
    def run(self):
        """Start the main engine loop"""
        # Start server if applicable
        if self.server:
            self.server.start()
        
        # Connect client if applicable
        if self.client:
            self.client.connect(self.config.get("server_address", "localhost:8080"))
        
        # Start CLI
        self.cli.start()
    
    def process_command(self, command_text):
        """Process a command from local player"""
        if self.client:
            # In multiplayer mode, send to server for indexing
            self.client.send_command(command_text)
        else:
            # In single player, directly add to sequencer with new index
            # Self-assign next index
            with open("history.json", "r") as f:
                history = json.load(f)
            
            # Calculate next index
            next_index = 0
            for turn in history.get("history", {}).get("turns", []):
                for action in turn.get("actions", []):
                    next_index = max(next_index, action.get("index", -1) + 1)
                for post in turn.get("postprocessing", []):
                    next_index = max(next_index, post.get("index", -1) + 1)
            
            # Create indexed command
            player = command_text.split()[0]
            indexed_command = {
                "index": next_index,
                "player": player,
                "command": command_text,
                "applied": False
            }
            
            # Add to sequencer
            self.command_sequencer.add_command(indexed_command)
    
    def execute_command(self, parsed_command):
        """Execute a parsed command through lua bridge"""
        self.lua_bridge.execute_command(parsed_command)
    
    def notify_view_update(self):
        """Notify view to update based on current state"""
        self.view.update()

if __name__ == "__main__":
    engine = JCEngine()
    engine.run()