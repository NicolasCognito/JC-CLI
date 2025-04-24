# engine/core/client_manager.py
"""Functions for managing game clients"""

import os
import sys
import json
import shutil
from ... import config
from . import utils

def join_session(session_name, client_name, server_ip=None):
    """Join a game session as a client, whether local or remote
    
    Args:
        session_name (str): Name of the session to join
        client_name (str): Name of the client
        server_ip (str, optional): IP address of the server (defaults to localhost if None)
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Check if client script exists relative to CWD
    if not os.path.exists(config.CLIENT_SCRIPT):
         print(f"Error: Client script '{config.CLIENT_SCRIPT}' not found in current directory.")
         return False

    # Define client directory structure - always create locally
    client_dir = os.path.join("clients", session_name, client_name)
    client_data_dir = os.path.join(client_dir, "data")

    # Create client directories
    try:
        os.makedirs(client_dir, exist_ok=True)
        os.makedirs(client_data_dir, exist_ok=True)
    except OSError as e:
        print(f"Error creating client directories in '{client_dir}': {e}")
        return False

    # Initialize empty world file that will be populated from server
    client_world_file = os.path.join(client_data_dir, config.WORLD_FILE)
    try:
        with open(client_world_file, 'w') as f:
            json.dump({"counter": 0}, f, indent=2)
    except IOError as e:
        print(f"Error creating empty world file: {e}")
        return False

    # Initialize empty commands file
    client_commands_log = os.path.join(client_data_dir, config.COMMANDS_LOG_FILE)
    open(client_commands_log, "w").close()

    # Copy required scripts to client directory
    scripts_to_copy_to_root = [config.ORCHESTRATOR_SCRIPT, config.RULE_LOOP_SCRIPT]
    for script_file in scripts_to_copy_to_root:
        src_script_path = script_file # Assumes these are in CWD
        dst_script_path = os.path.join(client_dir, os.path.basename(script_file))
        if os.path.exists(src_script_path):
            try:
                shutil.copy2(src_script_path, dst_script_path)
                print(f"Copied {script_file} to client directory")
            except Exception as e:
                 print(f"Warning: Failed to copy {script_file} to client: {e}")
        else:
            print(f"Warning: Script '{script_file}' not found, could not copy to client.")

    # Copy the entire 'scripts' directory if it exists
    src_scripts_dir = config.SCRIPTS_DIR # Assumes relative to CWD
    dst_scripts_dir = os.path.join(client_dir, config.SCRIPTS_DIR)
    if os.path.exists(src_scripts_dir):
        if utils.copy_directory(src_scripts_dir, dst_scripts_dir):
            print(f"Copied '{src_scripts_dir}' directory to client")
        else:
            print(f"Warning: Failed to copy '{src_scripts_dir}' directory to client.")
    else:
        print(f"Warning: '{src_scripts_dir}' directory not found - game logic may be missing for client.")

    # Set up command line arguments for client
    server_ip = server_ip or '127.0.0.1'  # Default to localhost if not specified
    
    client_args = [
        f"--dir \"{client_dir}\"",
        f"--username \"{client_name}\"",
        f"--server-ip \"{server_ip}\""
    ]
        
    # Create the final command string
    client_cmd = f"{sys.executable} {config.CLIENT_SCRIPT} {' '.join(client_args)}"

    print(f"Client '{client_name}' setup complete in '{client_dir}'")
    print(f"Connecting to session '{session_name}' at {server_ip}:{config.SERVER_PORT}")

    # Launch the client in a new terminal
    if utils.launch_in_new_terminal(client_cmd, title=f"JC Client: {client_name} ({session_name})"):
        print(f"Client '{client_name}' launched in a new terminal.")
        return True
    else:
        print(f"Failed to launch client '{client_name}' automatically.")
        print(f"You can start it manually with:")
        print(f"  {client_cmd}")
        return False