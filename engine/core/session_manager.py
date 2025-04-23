# engine/core/session_manager.py
"""Functions for managing game sessions"""

import os
import sys
import json
import shutil
from . import config
from . import utils

def list_sessions():
    """List all available game sessions"""
    if not os.path.exists(config.SESSIONS_DIR):
        print("No sessions directory found.")
        return

    sessions = [d for d in os.listdir(config.SESSIONS_DIR)
                if os.path.isdir(os.path.join(config.SESSIONS_DIR, d))]

    if not sessions:
        print("No sessions found.")
        return

    print("Available sessions:")
    for session in sessions:
        session_dir = os.path.join(config.SESSIONS_DIR, session)
        history_file = os.path.join(session_dir, config.HISTORY_FILE)

        # Count commands in history
        command_count = 0
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
                    command_count = len(history)
            except json.JSONDecodeError:
                command_count = "ERROR reading history"

        # Count clients
        client_base_dir = os.path.join(session_dir, config.CLIENT_DIR)
        clients = []
        if os.path.exists(client_base_dir):
            clients = [d for d in os.listdir(client_base_dir)
                      if os.path.isdir(os.path.join(client_base_dir, d))]

        print(f"  - {session} (Commands: {command_count}, Clients: {len(clients)})")
        if clients:
            print(f"    Clients: {', '.join(clients)}")

def start_session(session_name, template_name=config.DEFAULT_TEMPLATE):
    """Start a new game session
    
    Args:
        session_name (str): Name of the session
        template_name (str, optional): Template to use
    
    Returns:
        bool: True if started successfully, False otherwise
    """
    session_dir = os.path.join(config.SESSIONS_DIR, session_name)
    if os.path.exists(session_dir):
        print(f"Error: Session '{session_name}' already exists")
        print("Use 'continue-session' to continue an existing session")
        return False

    # Check if template exists
    template_dir = os.path.join(config.TEMPLATES_DIR, template_name)
    template_initial_world = os.path.join(template_dir, config.INITIAL_WORLD_FILE)
    if not os.path.exists(template_initial_world):
        print(f"Error: Template initial world file not found at '{template_initial_world}'")
        if not os.path.exists(template_dir):
             print(f"Error: Template directory '{template_dir}' not found.")
        return False

    # Create session directory structure
    os.makedirs(session_dir, exist_ok=True)
    os.makedirs(os.path.join(session_dir, config.CLIENT_DIR), exist_ok=True)

    # Copy initial world from template
    session_initial_world = os.path.join(session_dir, config.INITIAL_WORLD_FILE)
    try:
        shutil.copy2(template_initial_world, session_initial_world)
    except Exception as e:
        print(f"Error copying template world file: {e}")
        return False

    # Create empty history file
    history_path = os.path.join(session_dir, config.HISTORY_FILE)
    try:
        with open(history_path, 'w') as f:
            json.dump([], f)
    except IOError as e:
        print(f"Error creating history file '{history_path}': {e}")
        return False

    print(f"Created new session '{session_name}' using template '{template_name}' in '{session_dir}'")

    # Launch the server in a new terminal
    server_cmd = f"{sys.executable} {config.SERVER_SCRIPT} --session-dir \"{session_dir}\""
                  
    if utils.launch_in_new_terminal(server_cmd, title=f"JC Server: {session_name}"):
        print(f"Server for session '{session_name}' launched in a new terminal.")
        return True
    else:
        print(f"Failed to launch server automatically.")
        print(f"You can start it manually with:")
        print(f"  {server_cmd}")
        return False

def continue_session(session_name):
    """Continue an existing game session by launching its server
    
    Args:
        session_name (str): Name of the session
    
    Returns:
        bool: True if continued successfully, False otherwise
    """
    session_dir = os.path.join(config.SESSIONS_DIR, session_name)
    if not os.path.exists(session_dir):
        print(f"Error: Session '{session_name}' not found at '{session_dir}'")
        return False

    # Check if server script exists relative to CWD
    if not os.path.exists(config.SERVER_SCRIPT):
         print(f"Error: Server script '{config.SERVER_SCRIPT}' not found in current directory.")
         return False

    print(f"Attempting to continue session '{session_name}'...")

    # Launch the server in a new terminal with network parameters
    server_cmd = f"{sys.executable} {config.SERVER_SCRIPT} --session-dir \"{session_dir}\""
                  
    if utils.launch_in_new_terminal(server_cmd, title=f"JC Server: {session_name}"):
        print(f"Server for session '{session_name}' launched in a new terminal.")
        return True
    else:
        print(f"Failed to launch server for session '{session_name}'.")
        print(f"You can start it manually with:")
        print(f"  {server_cmd}")
        return False