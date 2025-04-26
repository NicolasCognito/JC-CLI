#!/usr/bin/env python3
NAME = "turn_switch"

import json
import sys

# Read world from stdin
world = json.loads(sys.stdin.read())

# Switch turns
if world["current_turn"] == "white":
    world["current_turn"] = "black"
else:
    world["current_turn"] = "white"
    # Increment fullmove number when black's turn ends
    world["fullmove_number"] += 1

# Output the updated world
print(json.dumps(world))

# Exit with code 0 to indicate changes were made
sys.exit(0)