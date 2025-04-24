#!/usr/bin/env python3
"""
JC-CLI Thin Client - Network-Enabled Version with View System
A minimal client that sends commands to the server, appends received ordered
commands to a log file, and launches a local sequencer and view for command processing.
"""
import socket
import json
import threading
import sys
import os
import argparse
import subprocess
import atexit
import time
from pathlib import Path

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
    parser.add_argument("--view", help="View script to use", default="default_view")
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

    for cmd in config.INITIAL_COMMANDS:
        print(f"Automatically sending initial command: {cmd}")
        client_network.send_command(client, cmd)
    
    # Start the sequencer
    if not sequencer_control.start_sequencer(client):
        print("Failed to start sequencer.")
        client_network.disconnect(client)
        return
    
    print("Sequencer started successfully")
    
    # Set up command queue file
    cmd_queue = os.path.join(client['data_dir'], "command_queue.txt")
    Path(cmd_queue).touch(exist_ok=True)  # Ensure it exists
    client['cmd_queue'] = cmd_queue
    
    # Start the view system in a separate window
    if not start_view_in_new_window(client, args.view):
        print("Failed to start view system.")
        client_network.disconnect(client)
        return
    
    print("View system started in a new window")
    
    # Register cleanup function
    atexit.register(cleanup, client)
    
    # Start listener thread for network messages
    listen_thread = threading.Thread(
        target=client_network.listen_for_broadcasts,
        args=(client,)
    )
    listen_thread.daemon = True
    listen_thread.start()
    
    # Main command loop now reads from command queue file
    command_loop(client)

def start_view_in_new_window(client, view_name):
    """Start the view system in a new terminal window
    
    Args:
        client (dict): Client state
        view_name (str): Name of the view to use
        
    Returns:
        bool: True if started, False otherwise
    """
    try:
        # Path to view.py script
        view_script = os.path.join(os.path.dirname(__file__), "view.py")
        
        if not os.path.exists(view_script):
            print(f"Error: View script not found at '{view_script}'")
            return False
        
        # Build command for view.py
        view_cmd = f"{sys.executable} {view_script} --dir \"{client['client_dir']}\" --username \"{client['username']}\" --view {view_name} --cmd-queue \"{client['cmd_queue']}\""
        
        # Launch in a new terminal window
        window_title = f"JC-CLI View: {client['username']}"
        if not utils.launch_in_new_terminal(view_cmd, title=window_title):
            print("Failed to launch view in new terminal. Check terminal compatibility.")
            return False
        
        return True
    except Exception as e:
        print(f"Error starting view system: {e}")
        return False

def command_loop(client):
    """Read commands from command queue file and send to server"""
    print(f"Monitoring for commands in {client['cmd_queue']}")
    
    try:
        while True:
            # Check for commands in the queue
            try:
                if os.path.exists(client['cmd_queue']):
                    with open(client['cmd_queue'], 'r') as f:
                        commands = [line.strip() for line in f if line.strip()]
                    
                    if commands:
                        # Clear the queue
                        open(client['cmd_queue'], 'w').close()
                        
                        # Process commands
                        for command in commands:
                            print(f"Sending command: {command}")
                            client_network.send_command(client, command)
            except Exception as e:
                print(f"Error reading command queue: {e}")
            
            # Don't burn CPU - sleep briefly
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nDisconnecting from server...")
    finally:
        client_network.disconnect(client)

def cleanup(client):
    """Clean up resources when exiting
    
    Args:
        client (dict): Client state
    """
    if client.get('sequencer_process'):
        print("Terminating sequencer process...")
        try:
            client['sequencer_process'].terminate()
            client['sequencer_process'].wait(timeout=2)
        except:
            # Force kill if termination fails
            try:
                client['sequencer_process'].kill()
            except:
                pass

if __name__ == "__main__":
    main()