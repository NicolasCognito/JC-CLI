#!/usr/bin/env python3
"""
Default View for JC-CLI
A simple text-based view that displays world state and captures commands.
"""
import os
import sys
import json
import time
import argparse
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class WorldFileHandler(FileSystemEventHandler):
    def __init__(self, view):
        self.view = view
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path == self.view.world_file:
            self.view.render_world()

class DefaultView:
    def __init__(self, client_dir, username, cmd_queue):
        self.client_dir = client_dir
        self.username = username
        self.cmd_queue = cmd_queue
        self.data_dir = os.path.join(client_dir, "data")
        self.world_file = os.path.join(self.data_dir, "world.json")
        self.commands_log = os.path.join(self.data_dir, "commands.log")
        
        # Set up file observer for world changes
        self.observer = Observer()
        self.observer.schedule(WorldFileHandler(self), self.data_dir, recursive=False)
        
        # Initial render
        self.render_world()
    
    def render_world(self):
        """Render the current world state"""
        try:
            # Clear screen
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print("=" * 60)
            print(f"JC-CLI VIEW - Player: {self.username}")
            print("=" * 60)
            
            # Load and display world
            if os.path.exists(self.world_file):
                with open(self.world_file, 'r') as f:
                    world = json.load(f)
                
                print("\nWorld State:")
                print(f"- Counter: {world.get('counter', 0)}")
                
                # Display entities if present
                if 'entities' in world:
                    print("\nEntities:")
                    for entity_id, entity in world['entities'].items():
                        print(f"- {entity_id}: {entity.get('name', 'Unnamed')}")
                
                # Display player state if present
                if 'players' in world and self.username in world['players']:
                    player = world['players'][self.username]
                    print(f"\nYour Status:")
                    for key, value in player.items():
                        if key != 'secrets':  # Don't display secret information
                            print(f"- {key}: {value}")
            else:
                print("\nWorld file not found or empty.")
            
            # Display recent commands
            self.display_recent_commands()
            
            print("\nEnter commands (type 'help' for available commands):")
        except Exception as e:
            print(f"Error rendering world: {e}")
    
    def display_recent_commands(self):
        """Display the most recent commands from the log"""
        try:
            if os.path.exists(self.commands_log):
                commands = []
                with open(self.commands_log, 'r') as f:
                    for line in f:
                        if line.strip():
                            try:
                                cmd = json.loads(line)
                                username = cmd.get("command", {}).get("username", "unknown")
                                text = cmd.get("command", {}).get("text", "")
                                seq = cmd.get("seq", 0)
                                commands.append((seq, username, text))
                            except:
                                pass
                
                if commands:
                    print("\nRecent Commands:")
                    # Show the last 5 commands (or fewer if there aren't that many)
                    for seq, username, text in sorted(commands, reverse=True)[:5]:
                        who = "You" if username == self.username else username
                        print(f"[{seq}] {who}: {text}")
        except Exception as e:
            print(f"Error displaying commands: {e}")
    
    def start(self):
        """Start the view"""
        self.observer.start()
        
        try:
            while True:
                command = input("> ").strip()
                if command:
                    self.handle_command(command)
        except KeyboardInterrupt:
            print("\nShutting down view...")
            self.stop()
    
    def stop(self):
        """Stop the view"""
        self.observer.stop()
        self.observer.join()
    
    def handle_command(self, command):
        """Process user input"""
        # Check for view-specific commands
        if command.lower() == 'refresh':
            self.render_world()
            return
        elif command.lower() == 'clear':
            os.system('cls' if os.name == 'nt' else 'clear')
            return
        elif command.lower() == 'help':
            self.show_help()
            return
        
        # Queue command for thin_client
        try:
            with open(self.cmd_queue, 'a') as f:
                f.write(command + '\n')
            print(f"Command sent: {command}")
        except Exception as e:
            print(f"Error queueing command: {e}")
    
    def show_help(self):
        """Display help information"""
        print("\nView Commands:")
        print("  refresh - Refresh the world display")
        print("  clear   - Clear the screen")
        print("  help    - Show this help")
        print("\nGame Commands:")
        print("  These are sent to the game server through thin_client.")
        print("  Try 'inc' to increment the counter if using the default scripts.")

def main():
    parser = argparse.ArgumentParser(description="JC-CLI Default View")
    parser.add_argument("--dir", help="Client directory", required=True)
    parser.add_argument("--username", help="Username", required=True)
    parser.add_argument("--cmd-queue", help="Command queue file", required=True)
    args = parser.parse_args()
    
    view = DefaultView(args.dir, args.username, args.cmd_queue)
    try:
        view.start()
    except Exception as e:
        print(f"View error: {e}")
    finally:
        view.stop()

if __name__ == "__main__":
    main()