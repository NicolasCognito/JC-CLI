#!/usr/bin/env python3
"""
Command: raise
Adds a value to the counter in world state
"""
import json
import sys

# No validation - pure JC-CLI approach
# Just try to convert the argument to an int and let it fail if invalid
value = int(sys.argv[1])

# Read world state
with open("data/world.json", "r") as f:
    world = json.load(f)

# Update counter
world["counter"] += value
print(f"Counter raised to {world['counter']}")

# Write world state
with open("data/world.json", "w") as f:
    json.dump(world, f, indent=2)

# Exit with success - let the rule loop handle any automatic effects
sys.exit(0)