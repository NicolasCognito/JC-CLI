# JC-CLI: Game Designer's Guide

## Introduction

JC-CLI (JSON-Controller Command Line Interface) is a powerful but minimalist game prototyping engine designed for rapid experimentation. It enables you to validate game mechanics and rules with networked multiplayer functionality right from the start—with **zero infrastructure ceremony**.

This guide explains everything you need to know to start creating game prototypes with JC-CLI, focusing on practical usage rather than implementation details.

## Core Concepts

### The Two Realms

JC-CLI strictly separates two realms:

- **Infrastructure Realm**: Handles networking, command ordering, persistence, and rendering
- **Logic Realm**: Contains all your game rules and state mutations

This separation ensures determinism—every player sees the exact same game state at the same time.

### Everything is a Command

All player actions are structured as text commands that:
1. Get assigned a global order by the coordinator
2. Are executed in the exact same sequence on every client
3. Change the world state in an identical way everywhere

### Transparent Data Model

Your entire game state lives in two files:
- `world.json` - The current game state
- `commands.log` - The chronological list of player commands

This transparency makes debugging easy—you can directly inspect both files at any time.

## Getting Started

### Installation

1. Ensure Python 3.6+ is installed on your system
2. Clone the JC-CLI repository
3. Run `jc-cli.py` to start the interactive shell

### Creating a Session

```
> start-session my-first-game
```

This creates a session and launches a server in a new terminal window.

### Joining a Session

In a separate terminal:

```
> join-session my-first-game player1
```

This launches a client that connects to the server. You can launch multiple clients for multiplayer testing.

## Creating Game Logic

Game logic in JC-CLI is organized into command scripts and rule scripts.

### Command Scripts

Commands are the verbs of your game—the actions players can take. They are defined in Python scripts in the `scripts/commands/` directory.

Example command script (`scripts/commands/draw.py`):

```python
#!/usr/bin/env python3
# Command: draw a card from the deck
NAME = "draw"

import json, sys, random

# Load the world state
with open("data/world.json", "r") as f:
    world = json.load(f)

# Get player who issued the command
player = sys.argv[1] if len(sys.argv) > 1 else "unknown"

# Execute the command logic
if world["deck"]:
    # Draw a card
    card = world["deck"].pop(0)
    # Add to player's hand
    if player not in world["hands"]:
        world["hands"][player] = []
    world["hands"][player].append(card)
    print(f"{player} drew {card['name']}")
else:
    print("Deck is empty")

# Save the new world state
with open("data/world.json", "w") as f:
    json.dump(world, f, indent=2)

# Exit with success code
sys.exit(0)
```

### Rule Scripts

Rules are automatic effects that trigger after player commands. They are defined in Python scripts in the `scripts/rules/` directory.

Rules differ from commands in how they interact with the world state:
1. Rules read the world state from **stdin** (not from the file directly)
2. Rules output the modified world to **stdout** (not writing to the file)
3. Rules return exit code 0 if they made changes, 9 if no changes

The rule loop orchestrates the execution of all active rules after each command.

## Creating the Initial World

The initial world state is defined in `templates/default/initial_world.json`:

```json
{
  "deck": [
    {"id": 1, "name": "Fireball", "damage": 5},
    {"id": 2, "name": "Shield", "defense": 3},
    {"id": 3, "name": "Heal", "amount": 2}
  ],
  "hands": {},
  "players": {},
  "rules_in_power": ["refill_hand"]
}
```

The `rules_in_power` array determines which rules are active.

## Views and Rendering

Views determine how players see the game state. They are defined in Python scripts in the `scripts/views/` directory.

Example view (`scripts/views/default.py`):

```python
#!/usr/bin/env python3
# Simple card game view
NAME = "default"

def render(world, context):
    """Render the game state"""
    username = context.get("username", "observer")
    
    print(f"=== Card Game [{username}] ===")
    
    # Show deck
    print(f"\nDeck: {len(world.get('deck', []))} cards remaining")
    
    # Show all players' hand counts (public information)
    print("\nPlayers:")
    for player, hand in world.get("hands", {}).items():
        if player == username:
            print(f"  {player} (you): {len(hand)} cards")
        else:
            print(f"  {player}: {len(hand)} cards")
    
    # Show your hand details (private information)
    if username in world.get("hands", {}):
        print("\nYour hand:")
        for card in world.get("hands", {}).get(username, []):
            attributes = []
            if "damage" in card:
                attributes.append(f"DMG: {card['damage']}")
            if "defense" in card:
                attributes.append(f"DEF: {card['defense']}")
            if "amount" in card:
                attributes.append(f"AMT: {card['amount']}")
            
            attrs = ", ".join(attributes)
            print(f"  {card['name']} ({attrs})")
    
    print("\nCommands: draw, play <card_name>, help")
```

## Running Your Game

Once your session is started, here's the typical workflow:

1. Server coordinates all commands
2. Clients send commands via the built-in CLI:
   ```
   CLI> draw
   CLI> play Fireball
   ```
3. Commands are synchronized across all clients
4. Each command is followed by automatic rule triggers
5. Views update to reflect the new state

## Command Reference

Here are the most common commands for players:

- Any game command you've defined (e.g., `draw`, `play`, etc.)
- `help` - Show available commands
- `view <view_name>` - Switch to another view

And here are the session management commands:

- `start-session <name>` - Start a new game session
- `join-session <session> <player> [server-ip]` - Join a session
- `continue-session <name>` - Continue an existing session

## Detailed Command Flow

When a player enters a command, JC-CLI processes it as follows:

1. **Input Capture**: 
   - Player enters a command in the client terminal
   - Client sends command text to server along with username

2. **Server Processing**:
   - Server assigns a unique sequence number to the command
   - Server broadcasts the ordered command to all connected clients
   - Server appends the command to the history file

3. **Client Reception**:
   - Clients receive the ordered command
   - Clients append the command to their local commands.log file

4. **Sequencer**:
   - The sequencer process monitors the commands.log file
   - When a new command appears, it processes commands in strict sequence order
   - For each command, it calls the orchestrator to execute it

5. **Orchestrator**:
   - Orchestrator discovers appropriate command script based on command name
   - It executes the command script as a subprocess
   - After command completion, it triggers the rule loop

6. **Command Execution**:
   - Command script reads the world.json file
   - Script modifies the world state according to command logic
   - Script writes updated world.json file

7. **Rule Loop**:
   - Rule loop identifies all applicable rules
   - It executes each rule script in sequence
   - Each rule can further modify the world state

8. **View Rendering**:
   - View system reads the updated world.json file
   - It renders the game state according to view-specific rules
   - Different views can present the same data differently (player vs. admin)

## Key Principles

### Absolute Minimalism

1. **No validation layer** - Commands are trusted inputs. If a malformed command breaks the game, the break becomes observable data rather than a swallowed error.
2. **No hidden abstraction** - There is no ORM, no service locator, no private protocol translation. Raw data structures are stored exactly as they appear on disk.
3. **No alternative modes** - The engine is always networked. Even single-player spins up a local coordinator.
4. **No extra features without purpose** - Sound, UI widgets, and asset pipelines belong in later stages.

### "Let It Fail" Philosophy

We don't need graceful error handling. The system should crash visibly when something is wrong rather than attempting to recover or hide errors, maximizing transparency and debug speed.

### Exit Codes as Signals

Communication between processes happens primarily through exit codes (0 for success, non-zero for failure). For rules, exit code 9 indicates no changes were made to the world state.

## Best Practices

### Rapid Iteration

1. Start small with a minimal viable game
2. Test each command thoroughly
3. Launch multiple clients to test multiplayer scenarios
4. Use the built-in views for quick feedback
5. Directly inspect `world.json` for debugging

### Command Design

1. Keep commands simple and atomic
2. Use rules for complex cascading effects
3. Be explicit about success/failure via exit codes
4. Follow the "Let It Fail" philosophy for faster debugging

### State Management

1. Keep your state schema flat and simple
2. Prefix private state with player names (e.g., `player1_hand`)
3. Use the view system to hide private information

## Replays and Archiving

Sessions can be archived for replay:

1. The initial world state
2. The command log
3. The script versions used

This creates perfect replays and serves as living documentation.

## Conclusion

JC-CLI follows a "radical minimalism" philosophy that makes it powerful for prototyping yet simple enough to understand completely. By focusing on the core elements—commands and rules—you can quickly transform game design ideas into playable prototypes.

Remember that JC-CLI is designed for the earliest stages of experimentation. Once your prototype validates your core design, you'll want to transition to a production engine, carrying forward the design insights gained.

Happy prototyping!
