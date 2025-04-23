# engine/client/client_state.py
"""Client state management module"""
import os
import json
import socket
from engine.core import config

def initialize(client_dir=None, username=None, server_ip=None, server_port=None):
    """Initialize client state
    
    Args:
        client_dir (str, optional): Directory for client data
        username (str, optional): Client username
        server_ip (str, optional): Server IP to connect to
        server_port (int, optional): Server port to connect to
        
    Returns:
        dict: Client state or None if initialization failed
    """
    # Get username if not provided
    while not username:
        username = input("Enter your username: ").strip()
        if not username:
            print("Username cannot be empty.")
    
    # Get server host if not provided
    server_host = server_ip if server_ip else '127.0.0.1'  # Default to localhost
    server_port = server_port if server_port else config.SERVER_PORT
    
    # Set up client directory
    client_dir = client_dir or os.getcwd()
    data_dir = os.path.join(client_dir, "data")
    commands_path = os.path.join(data_dir, config.COMMANDS_FILE)
    
    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Initialize commands file if it doesn't exist
    if not os.path.exists(commands_path):
        with open(commands_path, 'w') as f:
            json.dump([], f)
    
    # Create client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Return client state
    return {
        'username': username,
        'client_dir': client_dir,
        'data_dir': data_dir,
        'commands_path': commands_path,
        'socket': client_socket,
        'sequencer_process': None,
        'server_host': server_host,
        'server_port': server_port
    }