#!/usr/bin/env python3
# Command: display help information
NAME = "help"

import json
import sys
import os

# Get player who issued the command from environment variable
player = os.environ.get("PLAYER", "unknown")

# Get optional command name
command = sys.argv[1] if len(sys.argv) > 1 else None

# Command descriptions
commands = {
    "join": {
        "syntax": "join <position>",
        "description": "Join the game at the specified seat position",
        "example": "join 3"
    },
    "leave": {
        "syntax": "leave",
        "description": "Leave the game and forfeit current hand"
    },
    "start": {
        "syntax": "start",
        "description": "Start the poker game when enough players have joined"
    },
    "check": {
        "syntax": "check",
        "description": "Pass action without betting (when no bet to match)"
    },
    "call": {
        "syntax": "call",
        "description": "Match the current bet"
    },
    "bet": {
        "syntax": "bet <amount>",
        "description": "Make an initial bet",
        "example": "bet 20"
    },
    "raise": {
        "syntax": "raise <amount>",
        "description": "Increase the current bet to specified total amount",
        "example": "raise 50"
    },
    "fold": {
        "syntax": "fold",
        "description": "Discard hand and exit current round"
    },
    "all-in": {
        "syntax": "all-in",
        "description": "Bet all remaining chips"
    },
    "status": {
        "syntax": "status",
        "description": "Show current game status"
    },
    "help": {
        "syntax": "help [command]",
        "description": "Show this help message or details for a specific command",
        "example": "help raise"
    }
}

# If a specific command was requested
if command and command in commands:
    cmd = commands[command]
    print(f"\n=== Help: {command} ===")
    print(f"Syntax: {cmd['syntax']}")
    print(f"Description: {cmd['description']}")
    if "example" in cmd:
        print(f"Example: {cmd['example']}")
else:
    # Show all commands
    print("\n=== Poker Game Commands ===")
    
    print("\nGame Setup:")
    print("  join <position> - Join the game at the specified seat position")
    print("  leave - Leave the game and forfeit current hand")
    print("  start - Start the poker game when enough players have joined")
    
    print("\nPlayer Actions:")
    print("  check - Pass action without betting (when no bet to match)")
    print("  call - Match the current bet")
    print("  bet <amount> - Make an initial bet")
    print("  raise <amount> - Increase the current bet to specified total amount")
    print("  fold - Discard hand and exit current round")
    print("  all-in - Bet all remaining chips")
    
    print("\nInformation:")
    print("  status - Show current game status")
    print("  help [command] - Show this help message or details for a specific command")
    
    print("\nFor more details on a specific command, type: help <command>")

sys.exit(0)