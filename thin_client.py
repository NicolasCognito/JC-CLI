#!/usr/bin/env python3
"""
JC-CLI Thin Client - Network-Enabled Version
A minimal client that sends commands to the server, appends received ordered
commands to a log file, and launches a local sequencer for command processing.
"""
import socket
import json
import threading
import sys
import os
import argparse
import subprocess
import atexit

# Import modules from engine
from engine.core import config
from engine.core import utils
from engine.client import client_state
from engine.client import client_network
from engine.client import sequencer_control

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="JC-CLI Thin Client")
    parser.add_argument("--dir", help="Client directory to use", default=None)
    parser.add_argument("--username", help="Username to use", default=None)
    parser.add_argument("--server-ip", help="Server IP address", default=None)
    parser.add_argument("--server-port", help=f"Server port (default: {config.SERVER_PORT})", 
                       type=int, default=config.SERVER_PORT)
    args = parser.parse_args()
    
    # Set up client state
    client = client_state.initialize(args.dir, args.username, args.server_ip, args.server_port)
    if not client:
        return
    
    # Connect to server
    if not client_network.connect(client):
        print(f"Could not connect to server at {client['server_host']}:{client['server_port']}")
        print("Make sure the server is running and network connection is available.")
        return
    
    print(f"Connected to server at {client['server_host']}:{client['server_port']}")
    
    # Start the sequencer
    if not sequencer_control.start_sequencer(client):
        print("Failed to start sequencer.")
        client_network.disconnect(client)
        return
    
    print("Sequencer started successfully")
    
    # Register cleanup function
    atexit.register(sequencer_control.cleanup, client)
    
    # Start listener thread
    listen_thread = threading.Thread(
        target=client_network.listen_for_broadcasts,
        args=(client,)
    )
    listen_thread.daemon = True
    listen_thread.start()
    
    # Main command loop
    command_loop(client)

def command_loop(client):
    """Read commands from user input and send to server"""
    print(f"Enter commands (Ctrl+C to exit):")
    try:
        while True:
            command_text = input("> ")
            if command_text.strip():
                client_network.send_command(client, command_text)
    except KeyboardInterrupt:
        print("\nDisconnecting from server...")
        client_network.disconnect(client)

if __name__ == "__main__":
    main()