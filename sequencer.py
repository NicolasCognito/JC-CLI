#!/usr/bin/env python3
"""
JC-CLI Sequencer - Improved Version
Watches commands.json file and executes unprocessed commands in sequence order.
Now with clearer logging and proper execution order.
"""
import json
import os
import subprocess
import sys
import time
import argparse
import shlex

def run_sequencer(client_dir=None):
    """Main sequencer loop - minimalist implementation with improved logging"""
    # Set up paths
    client_dir = client_dir or os.getcwd()
    data_dir = os.path.join(client_dir, "data")
    commands_file = os.path.join(data_dir, "commands.json")
    
    # Ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    # Initialize commands file if it doesn't exist
    if not os.path.exists(commands_file):
        with open(commands_file, 'w') as f:
            json.dump([], f)
    
    print(f"Sequencer started. Client dir: {client_dir}")
    
    # Orchestrator path (same directory as this script)
    orchestrator_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 
        "orchestrator.py"
    )
    
    # Main processing loop
    while True:
        try:
            # Read commands
            with open(commands_file, 'r') as f:
                commands = json.load(f)
            
            # Find next unprocessed command in sequence
            next_cmd = None
            next_index = None
            
            # Find the last processed command sequence number
            last_seq = 0
            for cmd in commands:
                if cmd.get("processed", False):
                    last_seq = max(last_seq, cmd.get("seq", 0))
            
            # Look for the next command in sequence
            next_seq = last_seq + 1
            for i, cmd in enumerate(commands):
                if cmd.get("seq") == next_seq and not cmd.get("processed", False):
                    next_cmd = cmd
                    next_index = i
                    break
            
            # Process command if found
            if next_cmd:
                # Mark as processed immediately
                commands[next_index]["processed"] = True
                with open(commands_file, 'w') as f:
                    json.dump(commands, f, indent=2)
                
                # Get command text and username
                cmd_text = next_cmd['command']['text']
                username = next_cmd['command']['username']
                
                # Parse command to get the actual command and args
                cmd_parts = shlex.split(cmd_text)
                cmd_name = cmd_parts[0] if cmd_parts else ""
                cmd_args = cmd_parts[1:] if len(cmd_parts) > 1 else []
                
                # Log command execution BEFORE running it
                print(f"[Command:{next_seq}] Processing '{cmd_name}' from {username}")
                if cmd_args:
                    print(f"[Command:{next_seq}] Args: {cmd_args}")
                
                # Execute the command (without capturing output)
                # This ensures output appears in real-time and in correct order
                result = subprocess.run(
                    [sys.executable, orchestrator_path, cmd_text, username],
                    cwd=client_dir
                )
                
                if result.returncode != 0:
                    print(f"[Command:{next_seq}] '{cmd_name}' failed with code {result.returncode}")
            
            # Wait briefly before checking again
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            print("Sequencer stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)  # Wait a bit longer on error

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="JC-CLI Sequencer")
    parser.add_argument("--dir", help="Client directory to use", default=None)
    args = parser.parse_args()
    
    run_sequencer(client_dir=args.dir)