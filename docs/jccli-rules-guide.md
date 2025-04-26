# JC-CLI: Rule System Developer Guide

## Introduction

Rules are a critical component of the JC-CLI architecture, serving as automatic effects that trigger after player commands. They enable complex game behaviors with minimal code and ensure deterministic execution across all clients.

This guide explains the correct implementation patterns for JC-CLI rules, helping you avoid common pitfalls and leverage the full power of the rule system.

## Rule Script Fundamentals

Rules in JC-CLI:
- Are executed automatically after every command
- Process the world state in a deterministic manner
- Can trigger cascading effects
- Must follow specific I/O conventions

### Basic Rule Structure

```python
#!/usr/bin/env python3
# Name declaration MUST be the first non-comment line
NAME = "rule_id"

import json
import sys

# Input handling - ALWAYS read from stdin
world = json.loads(sys.stdin.read())

# Rule logic goes here
made_changes = False
if condition_is_met(world):
    # Modify world state
    world["some_property"] = new_value
    made_changes = True
    print(f"Rule {NAME}: Applied effect", file=sys.stderr)

# Output handling - ALWAYS write to stdout
print(json.dumps(world))

# Exit with the appropriate code
sys.exit(0 if made_changes else 9)
```

## Critical: Proper I/O Handling

The most common mistake when developing rules is incorrect I/O handling. 

### ✅ Correct Pattern

```python
# CORRECT: Read from stdin
world = json.loads(sys.stdin.read())

# ... process world ...

# CORRECT: Write to stdout
print(json.dumps(world))
```

### ❌ Incorrect Pattern

```python
# INCORRECT: Direct file I/O
with open("data/world.json", "r") as f:
    world = json.load(f)

# ... process world ...

# INCORRECT: Writing back to file
with open("data/world.json", "w") as f:
    json.dump(world, f, indent=2)
```

Direct file I/O bypasses the rule orchestration system and will lead to world state corruption. The rule engine expects to receive the modified world via stdout and will write an empty object (`{}`) to the world file if no output is provided.

## Available Environment Variables

JC-CLI provides environment variables that rules can access:

- `PLAYER` - The username of the player who issued the command

Example usage:

```python
import os

player = os.environ.get("PLAYER", "unknown")
command = os.environ.get("COMMAND", "")
args = os.environ.get("COMMAND_ARGS", "")

print(f"Rule triggered by {player} using command: {command} {args}", file=sys.stderr)
```

## Rule Execution Flow

1. A player issues a command
2. The orchestrator executes the command script
3. After the command completes, the rule loop activates
4. The rule loop checks which rules are active in `world["rules_in_power"]`
5. Each active rule is executed in sequence
6. If any rule makes changes (exits with code 0), the rule loop runs again
7. The loop continues until no rules make changes or a maximum iteration count is reached

## Exit Codes

Rules communicate their effect through exit codes:

- `0` - The rule made changes to the world
- `9` - The rule ran successfully but made no changes
- Any other value - Error during rule execution

The exit code is crucial for the rule loop to determine whether to continue running rules.

## Best Practices

### 1. Make rules atomic and focused

Each rule should do one thing well. Split complex behaviors into multiple rules.

### 2. Handle all code paths

Ensure that every code path in your rule outputs the world state to stdout and exits with the appropriate code.

```python
if condition:
    # Apply effect
    world["property"] = new_value
    print(json.dumps(world))
    sys.exit(0)
else:
    # No effect
    print(json.dumps(world))
    sys.exit(9)
```

### 3. Use debugging statements

Send debug information to stderr, not stdout:

```python
print(f"DEBUG: Rule condition check: {condition}", file=sys.stderr)
```

### 4. DO NOT Validate input data

JC-CLI is supposed to be used alongside LLMs, and every unnecessary check dilutes tokens.
We will still see error in raw form if it happens, and it will not crash whole app because each rule happens in subprocess.

Antipattern:
```python
if "required_property" not in world:
    print("ERROR: world is missing required_property", file=sys.stderr)
    print(json.dumps(world))  # Return unchanged world
    sys.exit(1)
```

### 5. Keep rules idempotent

Rules should be safe to run multiple times in a row without causing issues.

## Common Pitfalls

### 1. Direct file I/O

As emphasized earlier, never read from or write to `world.json` directly in rule scripts.

### 2. Missing stdout output

Always output the world state to stdout, even in error cases.

### 3. Inconsistent exit codes

Use 0 for changes, 9 for no changes, and other values for errors consistently.

### 4. Infinite rule loops

Be careful with rules that can trigger each other indefinitely.

### 5. Side effects

Rules should not have side effects outside the world state (like network calls).

## Example Rule Implementation

Here's a complete example of a rule that handles player turns:

```python
#!/usr/bin/env python3
NAME = "next_player_turn"

import json
import sys
import os

# Get environment variables
last_player = os.environ.get("PLAYER", "unknown")
last_command = os.environ.get("COMMAND", "")

# Read world from stdin
world = json.loads(sys.stdin.read())

# Check if this rule applies
if world.get("game_state", {}).get("phase") != "player_turns":
    print(json.dumps(world))  # Return unchanged world
    sys.exit(9)  # No changes

# Track if we made changes
made_changes = False

# Handle turn progression
current_player_idx = world["game_state"]["current_player_idx"]
active_players = world["game_state"]["active_players"]

# Only advance turn if the last command was from the current player
current_player = active_players[current_player_idx] if active_players else None
if current_player and last_player == current_player:
    # Move to the next player
    next_idx = (current_player_idx + 1) % len(active_players)
    world["game_state"]["current_player_idx"] = next_idx
    world["game_state"]["current_player"] = active_players[next_idx]
    made_changes = True
    print(f"Advanced turn to player {active_players[next_idx]}", file=sys.stderr)

# Output the world state
print(json.dumps(world))

# Exit with appropriate code
sys.exit(0 if made_changes else 9)
```

## Advanced Rule Techniques

### 1. Rule dependencies

You can create dependencies between rules using flags in the world state:

```python
# In rule1.py
world["flags"]["rule1_complete"] = True

# In rule2.py
if not world.get("flags", {}).get("rule1_complete", False):
    # Skip this rule if rule1 hasn't completed
    print(json.dumps(world))
    sys.exit(9)
```

### 2. Conditional rule activation

Dynamically activate rules based on game state:

```python
# In a command script
if condition:
    if "special_rule" not in world["rules_in_power"]:
        world["rules_in_power"].append("special_rule")
else:
    if "special_rule" in world["rules_in_power"]:
        world["rules_in_power"].remove("special_rule")
```

### 3. Rule recipes

For complex effect sequences, create recipe scripts that can be composed:

```python
#!/usr/bin/env python3
# In scripts/recipes/damage_and_status.py

def apply(world, target, damage, status=None):
    # Apply damage
    world["entities"][target]["health"] -= damage
    
    # Apply status if provided
    if status:
        world["entities"][target]["status"] = status
        
    return world
```

Then import and use in rules:

```python
import sys
import json
sys.path.append("scripts")
from recipes.damage_and_status import apply

# Read world
world = json.loads(sys.stdin.read())

# Apply recipe
world = apply(world, "player1", 5, "poisoned")

# Output world
print(json.dumps(world))
sys.exit(0)
```
### 4. Meta rules

Meta-rules in JC-CLI represent an architectural pattern where a single entry-point rule registered in rules_in_power acts as a custom rule processor, bypassing the standard sequential rule execution to implement sophisticated rule management strategies; this approach enables developers to organize rules into logical groups (phase-based, priority-based, or event-driven), establish rule dependencies, implement conditional activation, and create adaptive rule selection—all while maintaining JC-CLI's core deterministic execution model. By creating a structured directory of rule modules outside the standard rules directory and processing them through custom logic, meta-rules provide better organization, simplified debugging, improved modularity, and support for complex game mechanics without compromising the network-synchronized state that makes JC-CLI powerful for prototyping multiplayer experiences.

## Conclusion

Rules are the heart of game logic in JC-CLI. By following these guidelines, you'll create robust rules that work correctly within the JC-CLI architecture and provide deterministic results across all clients.

Remember the key principles:
1. Rules read from stdin and write to stdout
2. Exit codes signal whether changes occurred
3. Environment variables provide context
4. Keep rules focused and atomic

Happy prototyping!
