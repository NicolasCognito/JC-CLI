#!/usr/bin/env python3
NAME = "turn_switch"

import json
import sys
import os

# Read world from stdin (this is the proper way for rules)
world = json.loads(sys.stdin.read())

# Get the last command
last_command = os.environ.get("COMMAND", "")
command_args = os.environ.get("COMMAND_ARGS", "")

# Debug info to stderr
print(f"Rule fired: {NAME}", file=sys.stderr)
print(f"Last command: '{last_command}'", file=sys.stderr)
print(f"Command args: '{command_args}'", file=sys.stderr)
print(f"Current turn: {world['current_turn']}", file=sys.stderr)

# Only switch turns if the last command was a move
made_changes = False
if last_command.lower() == "move":
    # Switch turns
    if world["current_turn"] == "white":
        world["current_turn"] = "black"
        made_changes = True
        print(f"Switched turn to black", file=sys.stderr)
    else:
        world["current_turn"] = "white"
        made_changes = True
        print(f"Switched turn to white", file=sys.stderr)

# Output the world state to stdout
print(json.dumps(world))

# Exit with success code if changes were made
sys.exit(0 if made_changes else 9)