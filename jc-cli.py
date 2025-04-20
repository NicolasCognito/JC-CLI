#!/usr/bin/env python3
"""
JC-CLI - Interactive Session Manager
Provides an interactive shell for managing game sessions and clients.

Simply run the script without arguments to enter interactive mode:
  python jc-cli.py

Available commands:
  start-session <session-name> [template]  - Start a new game session
  continue-session <session-name>           - Continue an existing session
  join-session <session-name> <client-name> - Join a session as a client
  list-sessions                             - List available sessions
  help                                      - Show available commands
  exit                                      - Exit the shell
"""

import os
import sys
import json
import shlex
import subprocess
import platform
import shutil
import time

# Constants
SESSIONS_DIR = "sessions"
TEMPLATES_DIR = "templates"
DEFAULT_TEMPLATE = "default"
HISTORY_FILE = "history.json"
WORLD_FILE = "world.json"
INITIAL_WORLD_FILE = "initial_world.json"
CLIENT_DIR = "clients"

def setup_directories():
    """Ensure required directories exist"""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    
    # Create default template if it doesn't exist
    default_template = os.path.join(TEMPLATES_DIR, DEFAULT_TEMPLATE, INITIAL_WORLD_FILE)
    os.makedirs(os.path.dirname(default_template), exist_ok=True)
    
    if not os.path.exists(default_template):
        # Create a simple default template
        with open(default_template, 'w') as f:
            json.dump({
                "counter": 0,
                "rule_map": {
                    "trim_counter": "counter_threshold.py"
                }
            }, f, indent=2)
        print(f"Created default template at {default_template}")

def list_sessions():
    """List all available game sessions"""
    if not os.path.exists(SESSIONS_DIR):
        print("No sessions directory found.")
        return
    
    sessions = [d for d in os.listdir(SESSIONS_DIR) 
                if os.path.isdir(os.path.join(SESSIONS_DIR, d))]
    
    if not sessions:
        print("No sessions found.")
        return
    
    print("Available sessions:")
    for session in sessions:
        session_dir = os.path.join(SESSIONS_DIR, session)
        history_file = os.path.join(session_dir, HISTORY_FILE)
        
        # Count commands in history
        command_count = 0
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                try:
                    commands = json.load(f)
                    command_count = len(commands)
                except json.JSONDecodeError:
                    command_count = "ERROR"
        
        # Count clients
        client_dir = os.path.join(session_dir, CLIENT_DIR)
        clients = []
        if os.path.exists(client_dir):
            clients = [d for d in os.listdir(client_dir) 
                      if os.path.isdir(os.path.join(client_dir, d))]
        
        print(f"  - {session} (Commands: {command_count}, Clients: {len(clients)})")
        if clients:
            print(f"    Clients: {', '.join(clients)}")

def copy_directory(src, dst):
    """Copy a directory recursively"""
    if not os.path.exists(src):
        print(f"Warning: Source directory {src} not found")
        return False
        
    try:
        # Create destination if it doesn't exist
        os.makedirs(dst, exist_ok=True)
        
        # Copy contents
        for item in os.listdir(src):
            src_item = os.path.join(src, item)
            dst_item = os.path.join(dst, item)
            
            if os.path.isdir(src_item):
                # Recursive copy for directories
                copy_directory(src_item, dst_item)
            else:
                # Copy files
                shutil.copy2(src_item, dst_item)
        
        return True
    except Exception as e:
        print(f"Error copying directory: {e}")
        return False

def launch_in_new_terminal(cmd, title=None):
    """Launch a command in a new terminal window based on OS"""
    system = platform.system()
    cwd = os.getcwd()
    
    try:
        if system == "Windows":
            # Windows: Use PowerShell with start command
            window_title = f'"{title}"' if title else ""
            ps_cmd = f'cd "{cwd}"; {cmd}'
            subprocess.Popen([
                "powershell", "-Command",
                f'Start-Process powershell -ArgumentList \'-NoExit\', \'-Command "{ps_cmd}"\' -WindowStyle Normal'
            ])
            
        elif system == "Darwin":  # macOS
            # macOS: Use AppleScript to tell Terminal to open a new window/tab
            window_title = f' with title "{title}"' if title else ""
            apple_cmd = f'cd "{cwd}" && {cmd}'
            subprocess.Popen([
                "osascript", "-e",
                f'tell app "Terminal" to do script "{apple_cmd}"{window_title}'
            ])
            
        elif system == "Linux":
            # Linux: Try to detect terminal and use appropriate command
            # This tries gnome-terminal first, then falls back to xterm
            try:
                window_title = f'--title="{title}"' if title else ""
                subprocess.Popen([
                    "gnome-terminal", window_title, "--", "bash", "-c",
                    f'cd "{cwd}" && {cmd}; exec bash'
                ])
            except FileNotFoundError:
                window_title = f'-T "{title}"' if title else ""
                subprocess.Popen([
                    "xterm", window_title, "-e",
                    f'cd "{cwd}" && {cmd}; exec bash'
                ])
                
        else:
            print(f"Unsupported OS: {system}")
            print(f"Please run this command manually: {cmd}")
            return False
            
        return True
        
    except Exception as e:
        print(f"Error launching terminal: {e}")
        print(f"Please run this command manually: {cmd}")
        return False

def start_session(session_name, template_name=DEFAULT_TEMPLATE):
    """Start a new game session"""
    # Check if session already exists
    session_dir = os.path.join(SESSIONS_DIR, session_name)
    if os.path.exists(session_dir):
        print(f"Error: Session '{session_name}' already exists")
        print("Use 'continue-session' to continue an existing session")
        return False
    
    # Check if template exists
    template_dir = os.path.join(TEMPLATES_DIR, template_name)
    template_world = os.path.join(template_dir, WORLD_FILE)
    if not os.path.exists(template_world):
        print(f"Error: Template '{template_name}' not found")
        return False
    
    # Create session directory
    os.makedirs(session_dir, exist_ok=True)
    
    # Create client directory
    os.makedirs(os.path.join(session_dir, CLIENT_DIR), exist_ok=True)
    
    # Copy world template
    shutil.copy2(template_world, os.path.join(session_dir, INITIAL_WORLD_FILE))
    
    # Create empty history file
    with open(os.path.join(session_dir, HISTORY_FILE), 'w') as f:
        json.dump([], f)
    
    print(f"Created new session '{session_name}' with template '{template_name}'")
    
    # Launch the server in a new terminal
    server_cmd = f"{sys.executable} thin_server.py --session-dir {session_dir}"
    if launch_in_new_terminal(server_cmd, f"JC-CLI Server: {session_name}"):
        print(f"Server for session '{session_name}' launched in a new terminal")
        return True
    return False

def continue_session(session_name):
    """Continue an existing game session"""
    # Check if session exists
    session_dir = os.path.join(SESSIONS_DIR, session_name)
    if not os.path.exists(session_dir):
        print(f"Error: Session '{session_name}' not found")
        return False
    
    print(f"Continuing session '{session_name}'")
    
    # Launch the server in a new terminal
    server_cmd = f"{sys.executable} thin_server.py --session-dir {session_dir}"
    if launch_in_new_terminal(server_cmd, f"JC-CLI Server: {session_name}"):
        print(f"Server for session '{session_name}' launched in a new terminal")
        return True
    return False

def join_session(session_name, client_name):
    """Join an existing game session as a client"""
    # Check if session exists
    session_dir = os.path.join(SESSIONS_DIR, session_name)
    if not os.path.exists(session_dir):
        print(f"Error: Session '{session_name}' not found")
        return False
    
    # Create client directory
    client_dir = os.path.join(session_dir, CLIENT_DIR, client_name)
    os.makedirs(client_dir, exist_ok=True)
    
    # Create data directory
    data_dir = os.path.join(client_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Copy world file from session
    session_world = os.path.join(session_dir, INITIAL_WORLD_FILE)
    client_world = os.path.join(data_dir, WORLD_FILE)
    
    if os.path.exists(session_world):
        shutil.copy2(session_world, client_world)
    else:
        print(f"Warning: Session world file not found, creating empty world")
        with open(client_world, 'w') as f:
            json.dump({"counter": 0}, f, indent=2)
    
    # Initialize empty commands file
    with open(os.path.join(data_dir, "commands.json"), 'w') as f:
        json.dump([], f)
    
    # SIMPLE APPROACH:
    # 1. Just copy the entire scripts directory if it exists
    if os.path.exists("scripts"):
        # Copy the entire scripts directory to the client
        copy_directory("scripts", os.path.join(client_dir, "scripts"))
        print("Copied scripts directory to client")
    else:
        print("Warning: scripts directory not found - game logic may not work")
    
    # 2. Copy orchestrator and rule_loop to the client root
    for script_file in ["orchestrator.py", "rule_loop.py"]:
        if os.path.exists(script_file):
            shutil.copy2(script_file, os.path.join(client_dir, script_file))
            print(f"Copied {script_file} to client directory")
        else:
            print(f"Warning: {script_file} not found")
    
    print(f"Created client '{client_name}' for session '{session_name}'")
    
    # Launch the client in a new terminal
    client_cmd = f"{sys.executable} thin_client.py --dir {client_dir} --username {client_name}"
    if launch_in_new_terminal(client_cmd, f"JC-CLI Client: {client_name} ({session_name})"):
        print(f"Client '{client_name}' launched in a new terminal")
        return True
    return False

def show_help():
    """Display available commands"""
    print("Available commands:")
    print("  start-session <session-name> [template]  - Start a new game session")
    print("  continue-session <session-name>          - Continue an existing session")
    print("  join-session <session-name> <client-name> - Join a session as a client")
    print("  list-sessions                            - List available sessions")
    print("  help                                     - Show this help message")
    print("  exit                                     - Exit the shell")

def main():
    # Set up required directories
    setup_directories()
    
    # Start interactive shell if no arguments provided
    if len(sys.argv) == 1:
        interactive_shell()
    else:
        # Parse command line arguments for direct execution
        if sys.argv[1] == "start-session" and len(sys.argv) >= 3:
            template = sys.argv[3] if len(sys.argv) >= 4 else DEFAULT_TEMPLATE
            start_session(sys.argv[2], template)
        elif sys.argv[1] == "continue-session" and len(sys.argv) >= 3:
            continue_session(sys.argv[2])
        elif sys.argv[1] == "join-session" and len(sys.argv) >= 4:
            join_session(sys.argv[2], sys.argv[3])
        elif sys.argv[1] == "list-sessions":
            list_sessions()
        else:
            print(__doc__)

def interactive_shell():
    """Run the interactive shell"""
    print("JC-CLI Interactive Shell")
    print("Enter 'help' for available commands, 'exit' to quit")
    
    while True:
        # Get input from user
        try:
            user_input = input("> ")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break
        
        # Parse input
        args = shlex.split(user_input)
        if not args:
            continue
        
        command = args[0].lower()
        
        # Process commands
        if command == "exit":
            break
        elif command == "help":
            show_help()
        elif command == "list-sessions":
            list_sessions()
        elif command == "start-session":
            if len(args) < 2:
                print("Error: Missing session name")
                print("Usage: start-session <session-name> [template]")
                continue
                
            session_name = args[1]
            template = args[2] if len(args) > 2 else DEFAULT_TEMPLATE
            start_session(session_name, template)
            
        elif command == "continue-session":
            if len(args) < 2:
                print("Error: Missing session name")
                print("Usage: continue-session <session-name>")
                continue
                
            session_name = args[1]
            continue_session(session_name)
            
        elif command == "join-session":
            if len(args) < 3:
                print("Error: Missing session name or client name")
                print("Usage: join-session <session-name> <client-name>")
                continue
                
            session_name = args[1]
            client_name = args[2]
            join_session(session_name, client_name)
            
        else:
            print(f"Unknown command: {command}")
            print("Enter 'help' for available commands")

if __name__ == "__main__":
    main()