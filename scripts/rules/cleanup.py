#!/usr/bin/env python3
NAME = "clear_last_command"

import json
import sys

# Read world from stdin (proper way for rules)
world = json.loads(sys.stdin.read())

# Check if last_command exists
made_changes = False
if "last_command" in world:
    # Remove the last_command from world state
    del world["last_command"]
    made_changes = True
    print(f"Rule {NAME}: Cleared last_command", file=sys.stderr)

# Output the world state to stdout
print(json.dumps(world))

# Exit with appropriate code
sys.exit(0 if made_changes else 9)