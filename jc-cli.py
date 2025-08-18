#!/usr/bin/env python3
# jc-cli.py (Located in project root, outside 'engine' folder)
"""
JC-CLI - Interactive Session Manager (Network-Enabled Version)
Provides an interactive shell for managing game sessions and clients.

Run from the project root directory:
  python jc-cli.py

Available commands:
  start-session <session-name> [template]  - Start a new game session
  continue-session <session-name>          - Continue an existing session
  join-session <session-name> <client-name> [server-ip]
                                          - Join a session as a client
  list-sessions                            - List available sessions

General:
  help                                     - Show available commands
  delete-all [--force]                     - Delete ALL sessions and clients
  exit                                     - Exit the shell
"""

import sys
import shlex
import config
from engine.core import utils
from engine.core import session_manager
from engine.core import client_manager

def show_help():
    """Display available commands"""
    print("Available commands:")
    print(f"  start-session <session-name> [template={config.DEFAULT_TEMPLATE}] - Start a new game session")
    print("  continue-session <session-name>                                    - Continue an existing session")
    print("  join-session <session-name> <client-name> [server-ip]              - Join a session as a client")
    print("  list-sessions                                                      - List available sessions")
    # No project management — use git for versions/projects

    print("\nGeneral:")
    print("  help                                                               - Show this help message")
    print("  delete-all [--force]                                               - Delete ALL sessions and clients")
    print("  exit                                                               - Exit the shell")

def interactive_shell():
    """Run the interactive shell"""
    print("JC-CLI Interactive Shell (Network-Enabled Version)")
    print("Enter 'help' for available commands, 'exit' to quit")
    # No current project concept

    while True:
        try:
            user_input = input("> ")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        args = shlex.split(user_input)
        if not args:
            continue

        command = args[0].lower()

        if command == "exit":
            break
        elif command == "help":
            show_help()
        elif command == "list-sessions":
            session_manager.list_sessions()
        elif command == "start-session":
            if len(args) < 2:
                print("Error: Missing session name")
                print(f"Usage: start-session <session-name> [template={config.DEFAULT_TEMPLATE}]")
                continue
            session_name = args[1]
            template = args[2] if len(args) > 2 else config.DEFAULT_TEMPLATE
            session_manager.start_session(session_name, template)
        elif command == "continue-session":
            if len(args) < 2:
                print("Error: Missing session name")
                print("Usage: continue-session <session-name>")
                continue
            session_name = args[1]
            session_manager.continue_session(session_name)
        elif command == "join-session":
            if len(args) < 3:
                print("Error: Missing session name or client name")
                print("Usage: join-session <session-name> <client-name> [server-ip]")
                continue
            session_name = args[1]
            client_name = args[2]
            server_ip = args[3] if len(args) > 3 else None
            client_manager.join_session(session_name, client_name, server_ip)
        # Project management commands removed
        elif command == "delete-all":
            force = "--force" in args
            session_manager.delete_all_sessions_and_clients(force)
        else:
            print(f"Unknown command: {command}")
            print("Enter 'help' for available commands")

def main():
    """Main entry point: Setup directories and handle direct commands or start shell."""
    utils.setup_directories()

    if len(sys.argv) == 1:
        interactive_shell()
    else:
        command = sys.argv[1].lower()
        args = sys.argv[1:]

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
            if len(args) < 3: print("Usage: join-session <session-name> <client-name> [server-ip]"); return
            session_name = args[1]
            client_name = args[2]
            server_ip = args[3] if len(args) > 3 else None
            client_manager.join_session(session_name, client_name, server_ip)
        elif command == "list-sessions":
            session_manager.list_sessions()
        # Project management commands removed
        elif command == "delete-all":
            force = "--force" in args
            session_manager.delete_all_sessions_and_clients(force)
        elif command == "help":
            show_help()
        else:
            print(f"Unknown command: {command}")
            print(__doc__)

if __name__ == "__main__":
    main()
