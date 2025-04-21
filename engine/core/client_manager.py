# engine/core/client_manager.py
"""Functions for managing game clients"""

import os
import sys
import json
import shutil
from . import config
from . import utils

def join_session(session_name, client_name):
    """Join an existing game session as a client"""
    session_dir = os.path.join(config.SESSIONS_DIR, session_name)
    if not os.path.exists(session_dir):
        print(f"Error: Session '{session_name}' not found at '{session_dir}'")
        return False

    # Check if client script exists relative to CWD
    if not os.path.exists(config.CLIENT_SCRIPT):
         print(f"Error: Client script '{config.CLIENT_SCRIPT}' not found in current directory.")
         return False


    # Define client directory structure
    client_base_dir = os.path.join(session_dir, config.CLIENT_DIR)
    client_dir = os.path.join(client_base_dir, client_name)
    client_data_dir = os.path.join(client_dir, "data") # 'data' subdir as in original

    # Create client directories
    try:
        os.makedirs(client_dir, exist_ok=True) # Create specific client dir
        os.makedirs(client_data_dir, exist_ok=True) # Create client data dir
    except OSError as e:
        print(f"Error creating client directories in '{client_dir}': {e}")
        return False

    # Copy initial world file from session to client data directory
    session_initial_world = os.path.join(session_dir, config.INITIAL_WORLD_FILE)
    client_world_file = os.path.join(client_data_dir, config.WORLD_FILE) # Client uses WORLD_FILE

    if os.path.exists(session_initial_world):
        try:
            shutil.copy2(session_initial_world, client_world_file)
        except Exception as e:
            print(f"Error copying session initial world file: {e}")
            # Consider cleanup?
            return False
    else:
        # Original behavior: warning and create empty world
        print(f"Warning: Session initial world file '{session_initial_world}' not found.")
        print(f"Creating empty world file for client at '{client_world_file}'")
        try:
            with open(client_world_file, 'w') as f:
                # Default content from original script
                json.dump({"counter": 0}, f, indent=2)
        except IOError as e:
            print(f"Error creating empty world file: {e}")
            return False

    # Initialize empty commands file in client data directory
    client_commands_file = os.path.join(client_data_dir, config.COMMANDS_FILE)
    try:
        with open(client_commands_file, 'w') as f:
            json.dump([], f)
    except IOError as e:
        print(f"Error creating empty commands file '{client_commands_file}': {e}")
        return False

    # --- Copying Scripts ---
    # Original logic copied specific scripts and optionally the 'scripts' dir
    # Copy orchestrator and rule_loop to the client root directory
    scripts_to_copy_to_root = [config.ORCHESTRATOR_SCRIPT, config.RULE_LOOP_SCRIPT]
    for script_file in scripts_to_copy_to_root:
        src_script_path = script_file # Assumes these are in CWD
        dst_script_path = os.path.join(client_dir, os.path.basename(script_file))
        if os.path.exists(src_script_path):
            try:
                shutil.copy2(src_script_path, dst_script_path)
                print(f"Copied {script_file} to client directory '{client_dir}'")
            except Exception as e:
                 print(f"Warning: Failed to copy {script_file} to client: {e}")
        else:
            print(f"Warning: Script '{script_file}' not found in current directory, could not copy to client.")

    # Copy the entire 'scripts' directory if it exists
    src_scripts_dir = config.SCRIPTS_DIR # Assumes relative to CWD
    dst_scripts_dir = os.path.join(client_dir, config.SCRIPTS_DIR)
    if os.path.exists(src_scripts_dir):
        if utils.copy_directory(src_scripts_dir, dst_scripts_dir):
            print(f"Copied '{src_scripts_dir}' directory to client '{client_dir}'")
        else:
            print(f"Warning: Failed to copy '{src_scripts_dir}' directory to client.")
    else:
        print(f"Warning: '{src_scripts_dir}' directory not found - game logic may be missing for client.")
    # --- End Copying Scripts ---


    print(f"Client '{client_name}' setup complete in '{client_dir}' for session '{session_name}'.")

    # Launch the client in a new terminal
    # Pass relative path to client directory and username
    client_cmd = f"{sys.executable} {config.CLIENT_SCRIPT} --dir \"{client_dir}\" --username \"{client_name}\"" # Quote args
    if utils.launch_in_new_terminal(client_cmd, title=f"JC Client: {client_name} ({session_name})"):
        print(f"Client '{client_name}' launched in a new terminal.")
        return True
    else:
        print(f"Failed to launch client '{client_name}' automatically.")
        return False # Indicate launch failure