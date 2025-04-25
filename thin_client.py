#!/usr/bin/env python3
"""
JC-CLI Thin Client - Network-Enabled Version with Built-in CLI
A minimal client that sends commands to the server, appends received ordered
commands to a log file, and launches a local sequencer.  Also provides a
direct CLI prompt so you can prototype without any view scripts at all.
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
import config
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
    parser.add_argument("--view", help="View script to use", default=None)
    parser.add_argument("--no-view", help="Skip launching any view", action="store_true")
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

    # Send any initial commands
    cmd = config.INITIAL_COMMAND
    print(f"→ Automatically sending initial command: {cmd}")
    client_network.send_command(client, cmd)

    # Start the sequencer process
    if not sequencer_control.start_sequencer(client):
        print("Failed to start sequencer.")
        client_network.disconnect(client)
        return

    print("Sequencer started successfully")

    # Set up command queue file
    cmd_queue = os.path.join(client['data_dir'], "command_queue.txt")
    Path(cmd_queue).touch(exist_ok=True)
    client['cmd_queue'] = cmd_queue

    # Launch view unless explicitly disabled
    if not args.no_view:
        view_name = args.view or config.DEFAULT_VIEW
        if start_view_in_new_window(client, view_name):
            print("View system started in a new window")
        else:
            print("Failed to start view system; continuing with CLI only")
    else:
        print("Running in CLI-only mode.")

    # Register cleanup
    atexit.register(cleanup, client)

    # Start network listener
    listen_thread = threading.Thread(
        target=client_network.listen_for_broadcasts,
        args=(client,)
    )
    listen_thread.daemon = True
    listen_thread.start()

    # Start built-in CLI thread (writes into the same queue file)
    cli_thread = threading.Thread(target=cli_loop, args=(client,))
    cli_thread.daemon = True
    cli_thread.start()

    # Main loop: watch the queue file and forward queued commands to server
    command_loop(client)


def start_view_in_new_window(client, view_name):
    """Start the view system in a new terminal window"""
    try:
        view_script = os.path.join(os.path.dirname(__file__), "view.py")
        if not os.path.exists(view_script):
            print(f"Error: View script not found at '{view_script}'")
            return False

        view_cmd = f"{sys.executable} {view_script} --dir \"{client['client_dir']}\" " \
                   f"--username \"{client['username']}\" --view {view_name} " \
                   f"--cmd-queue \"{client['cmd_queue']}\""
        title = f"JC-CLI View: {client['username']}"
        return utils.launch_in_new_terminal(view_cmd, title=title)
    except Exception as e:
        print(f"Error starting view system: {e}")
        return False


def cli_loop(client):
    """
    A simple REPL that writes your typed commands into the same queue file
    that view scripts use.  This way the sequencer processes them exactly
    the same way.
    """
    print("CLI> Type commands here (or use your IDE to edit world.json directly).")
    try:
        while True:
            cmd = input("CLI> ").strip()
            if not cmd:
                continue
            # Append to the queue file
            try:
                with open(client['cmd_queue'], 'a') as f:
                    f.write(cmd + '\n')
            except Exception as e:
                print(f"Error queueing CLI command: {e}")
    except KeyboardInterrupt:
        # Ctrl-C in the CLI just returns you to the command_loop
        print("\nCLI input stopped.")


def command_loop(client):
    """Read commands from the queue file and send to server"""
    print(f"Monitoring for commands in {client['cmd_queue']}")
    try:
        while True:
            if os.path.exists(client['cmd_queue']):
                with open(client['cmd_queue'], 'r') as f:
                    cmds = [line.strip() for line in f if line.strip()]
                if cmds:
                    open(client['cmd_queue'], 'w').close()
                    for command in cmds:
                        print(f"→ Sending command: {command}")
                        client_network.send_command(client, command)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nDisconnecting from server...")
    finally:
        client_network.disconnect(client)


def cleanup(client):
    """Clean up resources when exiting"""
    if client.get('sequencer_process'):
        print("Terminating sequencer process...")
        try:
            client['sequencer_process'].terminate()
            client['sequencer_process'].wait(timeout=2)
        except Exception:
            try:
                client['sequencer_process'].kill()
            except Exception:
                pass


if __name__ == "__main__":
    main()
