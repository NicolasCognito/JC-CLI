#!/usr/bin/env python3
"""
JC-CLI Thin Server (Modified Version)
A minimal coordinator that receives commands, assigns sequence numbers,
and broadcasts them to all connected clients.

Modified to work with session directories and history.json.
"""
import socket
import json
import threading
import time
import os
import argparse
import sys

# Configuration
HOST = '127.0.0.1'
PORT = 9000
BUFFER_SIZE = 1024
HISTORY_FILE = "history.json"
INITIAL_WORLD_FILE = "initial_world.json"

class ThinServer:
    def __init__(self, session_dir=None):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.clients = []
        self.lock = threading.Lock()
        
        # Set session directory
        self.session_dir = session_dir or os.getcwd()
        self.history_path = os.path.join(self.session_dir, HISTORY_FILE)
        self.world_path = os.path.join(self.session_dir, INITIAL_WORLD_FILE)
        
        # Initialize sequence number from history file
        self.sequence_number = self.get_highest_sequence()
        
        print(f"Server initialized with session directory: {self.session_dir}")
        print(f"Starting with sequence number: {self.sequence_number}")

    def get_highest_sequence(self):
        """Get the highest sequence number from history file"""
        if not os.path.exists(self.history_path):
            # Create empty history file
            with open(self.history_path, 'w') as f:
                json.dump([], f)
            return 0
        
        try:
            with open(self.history_path, 'r') as f:
                history = json.load(f)
            
            if not history:
                return 0
            
            # Find highest sequence number
            highest_seq = max(cmd.get("seq", 0) for cmd in history)
            return highest_seq
            
        except Exception as e:
            print(f"Error reading history file: {e}")
            return 0

    def listen(self):
        """Listen for incoming client connections"""
        self.server_socket.listen(5)
        print(f"Server listening on {HOST}:{PORT}")
        
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                print(f"New connection from {addr}")
                
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, addr)
                )
                client_thread.daemon = True
                client_thread.start()
                
                self.clients.append(client_socket)
                
                # Send history to new client
                self.send_history(client_socket)
                
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.server_socket.close()

    def send_history(self, client_socket):
        """Send command history to a new client"""
        try:
            if os.path.exists(self.history_path):
                with open(self.history_path, 'r') as f:
                    history = json.load(f)
                
                print(f"Sending {len(history)} historical commands to new client")
                
                # Send each command in order
                for cmd in history:
                    # Convert to bytes and send
                    cmd_bytes = json.dumps(cmd).encode('utf-8')
                    client_socket.sendall(cmd_bytes)
                    time.sleep(0.05)  # Small delay to prevent flooding
        except Exception as e:
            print(f"Error sending history: {e}")

    def handle_client(self, client_socket, addr):
        """Handle messages from a client"""
        try:
            while True:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                    
                # Process command
                try:
                    # Parse the command JSON
                    command_json = json.loads(data.decode('utf-8'))
                    self.process_command(command_json)
                except json.JSONDecodeError as e:
                    print(f"Error decoding command: {e}")
                except Exception as e:
                    print(f"Error processing command: {e}")
                    
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()
            print(f"Connection closed: {addr}")

    def process_command(self, command):
        """Assign sequence number and broadcast to all clients"""
        with self.lock:
            # Assign sequence number
            self.sequence_number += 1
            
            # Create ordered command
            ordered_command = {
                "seq": self.sequence_number,
                "timestamp": time.time(),
                "command": command
            }
            
            # Broadcast to all clients
            self.broadcast(ordered_command)
            
            # Append to history file
            self.append_to_history(ordered_command)
            
            # Print command info
            username = command.get("username", "unknown")
            cmd_text = command.get("text", "")
            print(f"[{self.sequence_number}] {username}: {cmd_text}")

    def append_to_history(self, ordered_command):
        """Append command to history file"""
        try:
            # Read existing history
            if os.path.exists(self.history_path):
                with open(self.history_path, 'r') as f:
                    history = json.load(f)
            else:
                history = []
            
            # Append new command
            history.append(ordered_command)
            
            # Write back to file
            with open(self.history_path, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            print(f"Error appending to history file: {e}")

    def broadcast(self, ordered_command):
        """Send the command to all connected clients"""
        message = json.dumps(ordered_command).encode('utf-8')
        
        # List of clients to remove (in case of errors)
        dead_clients = []
        
        for client in self.clients:
            try:
                client.sendall(message)
            except Exception:
                dead_clients.append(client)
        
        # Remove any clients that failed
        for client in dead_clients:
            if client in self.clients:
                self.clients.remove(client)
                client.close()

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="JC-CLI Thin Server")
    parser.add_argument("--session-dir", help="Session directory to use", default=None)
    args = parser.parse_args()
    
    server = ThinServer(session_dir=args.session_dir)
    server.listen()