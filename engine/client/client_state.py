# engine/client/client_state.py
"""Client state management module"""
import os
import json
import socket
import config

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

    server_host = server_ip or "127.0.0.1"
    server_port = server_port or config.SERVER_PORT

    client_dir  = client_dir or os.getcwd()
    data_dir    = os.path.join(client_dir, "data")
    log_path    = os.path.join(data_dir, config.COMMANDS_LOG_FILE)

    os.makedirs(data_dir, exist_ok=True)

    # Ensure the log file exists and is **empty** (not "[]")
    if not os.path.exists(log_path):
        open(log_path, "w").close()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    return {
        "username": username,
        "client_dir": client_dir,
        "data_dir": data_dir,
        "commands_path": log_path,
        "socket": sock,
        "sequencer_process": None,
        "server_host": server_host,
        "server_port": server_port,
    }