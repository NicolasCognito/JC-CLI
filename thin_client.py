#!/usr/bin/env python3
"""
JC-CLI Thin Client - Improved Version
A minimal client that sends commands to the server, appends received ordered
commands to a log file, and launches a local sequencer for command processing.
Now with clearer output handling.
"""
import socket
import json
import threading
import sys
import os
import argparse
import subprocess
import signal
import atexit

# Configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 9000
BUFFER_SIZE = 4096
DATA_DIR = "data"  # Default data directory
COMMANDS_FILE = "commands.json"

class ThinClient:
    def __init__(self, client_dir=None, username=None):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sequencer_process = None
        
        # Set up client directory
        self.client_dir = client_dir or os.getcwd()
        self.data_dir = os.path.join(self.client_dir, DATA_DIR)
        self.commands_path = os.path.join(self.data_dir, COMMANDS_FILE)
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize commands file if it doesn't exist
        if not os.path.exists(self.commands_path):
            with open(self.commands_path, 'w') as f:
                json.dump([], f)
        
        # Get username
        self.username = username
        while not self.username:
            self.username = input("Enter your username: ").strip()
            if not self.username:
                print("Username cannot be empty.")
                
        print(f"Client initialized. User: {self.username}, Data directory: {self.data_dir}")
        
        # Register cleanup function
        atexit.register(self.cleanup)

    def start_sequencer(self):
        """Start the sequencer as a separate process"""
        try:
            # Prepare sequencer command with client directory
            sequencer_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "sequencer.py"  # Use improved sequencer
            )
            
            sequencer_cmd = [
                sys.executable, 
                sequencer_path, 
                "--dir", self.client_dir
            ]
            
            print(f"Starting sequencer: {' '.join(sequencer_cmd)}")
            
            # Start sequencer process - let output flow directly to console
            # This ensures proper order of messages
            self.sequencer_process = subprocess.Popen(sequencer_cmd)
            
            print("Sequencer started successfully")
            
        except Exception as e:
            print(f"Error starting sequencer: {e}")

    def cleanup(self):
        """Clean up resources when exiting"""
        if self.sequencer_process:
            print("Terminating sequencer process...")
            try:
                self.sequencer_process.terminate()
                self.sequencer_process.wait(timeout=2)
            except:
                # Force kill if termination fails
                try:
                    self.sequencer_process.kill()
                except:
                    pass

    def connect(self):
        """Connect to the server"""
        try:
            self.client_socket.connect((SERVER_HOST, SERVER_PORT))
            print(f"Connected to server at {SERVER_HOST}:{SERVER_PORT}")
            
            # Start the sequencer
            self.start_sequencer()
            
            # Start thread to listen for broadcasts
            listen_thread = threading.Thread(target=self.listen_for_broadcasts)
            listen_thread.daemon = True
            listen_thread.start()
            
            # Main loop for sending commands
            self.send_commands()
            
        except ConnectionRefusedError:
            print(f"Could not connect to server at {SERVER_HOST}:{SERVER_PORT}")
            print("Make sure the server is running.")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nDisconnecting from server...")
        finally:
            self.client_socket.close()

    def send_commands(self):
        """Read commands from user input and send to server"""
        print("Enter commands (Ctrl+C to exit):")
        try:
            while True:
                command_text = input("> ")
                if command_text.strip():
                    # Create command with username
                    command = {
                        "username": self.username,
                        "text": command_text
                    }
                    # Send as JSON
                    self.client_socket.sendall(json.dumps(command).encode('utf-8'))
        except KeyboardInterrupt:
            print("\nExiting...")

    def listen_for_broadcasts(self):
        """Listen for broadcasts from the server and log them"""
        try:
            while True:
                data = self.client_socket.recv(BUFFER_SIZE)
                if not data:
                    print("Disconnected from server")
                    break
                
                try:
                    # Parse the ordered command
                    ordered_command = json.loads(data.decode('utf-8'))
                    
                    # Append to commands file
                    self.append_command(ordered_command)
                    
                    # Display for user
                    seq = ordered_command["seq"]
                    username = ordered_command["command"]["username"]
                    cmd_text = ordered_command["command"]["text"]
                    
                    # Highlight own messages
                    if username == self.username:
                        print(f"[{seq}] You: {cmd_text}")
                    else:
                        print(f"[{seq}] {username}: {cmd_text}")
                    
                except json.JSONDecodeError as e:
                    print(f"Error decoding message: {e}")
        except Exception as e:
            print(f"Error while listening for broadcasts: {e}")

    def append_command(self, ordered_command):
        """Append the received command to the commands file"""
        try:
            # Read existing commands
            with open(self.commands_path, 'r') as f:
                commands = json.load(f)
            
            # Append new command
            commands.append(ordered_command)
            
            # Write back to file
            with open(self.commands_path, 'w') as f:
                json.dump(commands, f, indent=2)
                
        except Exception as e:
            print(f"Error appending to commands file: {e}")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="JC-CLI Thin Client")
    parser.add_argument("--dir", help="Client directory to use", default=None)
    parser.add_argument("--username", help="Username to use", default=None)
    args = parser.parse_args()
    
    client = ThinClient(client_dir=args.dir, username=args.username)
    client.connect()