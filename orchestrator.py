#!/usr/bin/env python3
"""
JC-CLI Orchestrator - Improved Version
Executes a specific command and runs the rule loop.
Now with clearer logging.
"""
import subprocess
import sys
import shlex
import json
import os

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# World file path
WORLD_FILE = "data/world.json"

# Initialize world if it doesn't exist
if not os.path.exists(WORLD_FILE):
    with open(WORLD_FILE, "w") as f:
        json.dump({"counter": 0}, f)

# Simple command-to-script mapping
COMMANDS = {
    "raise": "scripts/commands/raise_value.py",
    "exit": None
}

def execute_command(command, args, username):
    """Execute a command script as a subprocess"""
    script = COMMANDS.get(command)
    
    if script is None:
        print(f"Unknown command: {command}")
        return False
    
    # Verify script exists
    if not os.path.exists(script):
        print(f"Error: Command script not found at {script}")
        return False
        
    # Execute the command - let output flow directly to console
    # This ensures output appears in real-time and in correct order
    cmd_args = [sys.executable, script] + args
    
    print(f"Executing: {script} with args: {args}")
    result = subprocess.run(cmd_args)
    
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        return False
    
    return True

def run_rule_loop():
    """Run the rule loop to apply automatic effects"""
    print("Running rule loop...")
    result = subprocess.run([sys.executable, "rule_loop.py"])
    
    if result.returncode != 0 and result.returncode != 9:
        print(f"Rule loop failed with exit code {result.returncode}")

def main():
    # Usage: orchestrator.py <command-text> <username>
    if len(sys.argv) < 2:
        print("Usage: orchestrator.py <command-text> <username>")
        sys.exit(1)
    
    # Get command text and username from args
    command_text = sys.argv[1]
    username = sys.argv[2] if len(sys.argv) >= 3 else "unknown"
    
    # Parse the command
    args = shlex.split(command_text)
    if not args:
        print("Empty command")
        sys.exit(1)
    
    command = args[0]
    if command == "exit":
        print("Exit command received")
        sys.exit(0)
    
    # Execute the command
    command_args = args[1:]
    if execute_command(command, command_args, username):
        # If command was successful, run the rule loop
        run_rule_loop()
        sys.exit(0)
    else:
        # Command failed
        sys.exit(1)

if __name__ == "__main__":
    main()