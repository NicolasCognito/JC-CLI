#!/usr/bin/env python3
"""
Rule script: Counter Threshold
Checks if counter > 10 and trims it to 10 if needed
"""
import json
import sys

# Read world state from stdin
world_json = sys.stdin.buffer.read().decode('utf-8')
world = json.loads(world_json)

# The rule itself determines whether it should apply
if world["counter"] > 10:
    # Apply rule effect: trim the counter to 10
    world["counter"] = 10
    # Let the orchestrator know that we made a change by exiting with 0
    exit_code = 0
else:
    # No change needed
    exit_code = 9  # Exit with code 9 to notify rule wasn't needed

# Write the world back to stdout, whether changed or not
print(json.dumps(world))

# Exit with appropriate code
sys.exit(exit_code)