#!/usr/bin/env python3
# cli.py (Located in project root, outside 'engine' folder)
"""
JC-CLI - Interactive Session Manager (Modular Version)
Provides an interactive shell for managing game sessions and clients.

Run from the project root directory:
  python cli.py

Available commands:
  start-session <session-name> [template]  - Start a new game session
  continue-session <session-name>           - Continue an existing session
  join-session <session-name> <client-name> - Join a session as a client
  list-sessions                             - List available sessions
  help                                      - Show available commands
  exit                                      - Exit the shell
"""

import sys
import shlex
# Use absolute imports assuming 'engine' is a package in the current directory
# or accessible via PYTHONPATH
from engine.core import config
from engine.core import utils
from engine.core import session_manager
from engine.core import client_manager

def show_help():
    """Display available commands"""
    print("Available commands:")
    # Use config.DEFAULT_TEMPLATE for dynamic help text
    print(f"  start-session <session-name> [template={config.DEFAULT_TEMPLATE}] - Start a new game session")
    print("  continue-session <session-name>          - Continue an existing session")
    print("  join-session <session-name> <client-name> - Join a session as a client")
    print("  list-sessions                            - List available sessions")
    print("  help                                     - Show this help message")
    print("  exit                                     - Exit the shell")

def interactive_shell():
    """Run the interactive shell"""
    print("JC-CLI Interactive Shell (Modular Version)")
    print("Enter 'help' for available commands, 'exit' to quit")

    while True:
        try:
            # Get input from user
            user_input = input("> ")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        # Parse input using shlex
        args = shlex.split(user_input)
        if not args:
            continue

        command = args[0].lower()

        # Process commands using imported functions from engine.core modules
        if command == "exit":
            break
        elif command == "help":
            show_help()
        elif command == "list-sessions":
            session_manager.list_sessions() # Call function from session_manager module
        elif command == "start-session":
            if len(args) < 2:
                print("Error: Missing session name")
                print(f"Usage: start-session <session-name> [template={config.DEFAULT_TEMPLATE}]")
                continue
            session_name = args[1]
            template = args[2] if len(args) > 2 else config.DEFAULT_TEMPLATE # Use config constant
            session_manager.start_session(session_name, template) # Call function from session_manager
        elif command == "continue-session":
            if len(args) < 2:
                print("Error: Missing session name")
                print("Usage: continue-session <session-name>")
                continue
            session_name = args[1]
            session_manager.continue_session(session_name) # Call function from session_manager
        elif command == "join-session":
            if len(args) < 3:
                print("Error: Missing session name or client name")
                print("Usage: join-session <session-name> <client-name>")
                continue
            session_name = args[1]
            client_name = args[2]
            client_manager.join_session(session_name, client_name) # Call function from client_manager
        else:
            print(f"Unknown command: {command}")
            print("Enter 'help' for available commands")

def main():
    """Main entry point: Setup directories and handle direct commands or start shell."""
    # Ensure base directories (like sessions/, templates/) exist
    utils.setup_directories() # Call function from utils module

    # Check if running interactively (no args) or with a direct command
    if len(sys.argv) == 1:
        interactive_shell()
    else:
        # Handle direct command-line execution
        command = sys.argv[1].lower()
        # Pass sys.argv directly for simplicity or use argparse for robust parsing
        args = sys.argv[1:] # Full arguments including command name

        if command == "start-session":
            if len(args) < 2: print(f"Usage: start-session <session-name> [template={config.DEFAULT_TEMPLATE}]"); return
            session_name = args[1]
            template = args[2] if len(args) > 2 else config.DEFAULT_TEMPLATE
            session_manager.start_session(session_name, template)
        elif command == "continue-session":
            if len(args) < 2: print("Usage: continue-session <session-name>"); return
            session_name = args[1]
            session_manager.continue_session(session_name)
        elif command == "join-session":
            if len(args) < 3: print("Usage: join-session <session-name> <client-name>"); return
            session_name = args[1]
            client_name = args[2]
            client_manager.join_session(session_name, client_name)
        elif command == "list-sessions":
            session_manager.list_sessions()
        elif command == "help":
             show_help()
        else:
            print(f"Unknown command: {command}")
            # Print the docstring as usage instructions
            print(__doc__)

if __name__ == "__main__":
    # Ensure the main function is called when the script is executed directly
    main()