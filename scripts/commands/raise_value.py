NAME = "raise"

#!/usr/bin/env python3
"""
Command: raise
Adds a value to the counter in world state
"""
import json
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: raise <value>", file=sys.stderr)
        sys.exit(1)

    value = int(sys.argv[1])
    world = json.load(sys.stdin)
    world["counter"] += value
    print(f"Counter raised to {world['counter']}", file=sys.stderr)
    json.dump(world, sys.stdout)
    sys.exit(0)


if __name__ == "__main__":
    main()