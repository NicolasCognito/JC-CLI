# JC-CLI: Network-First Deterministic Command Shell

JC-CLI (JSON-Controller-CLI) is a network-first, deterministic command-line shell designed for rapid game rule experimentation. It enables designers to validate that typed commands can traverse a network, drive rule logic, mutate shared world data, and render identically on every client—with **zero infrastructure ceremony**.

# Table of Contents

- [Core Architecture](#core-architecture)
- [Implementation Structure](#implementation-structure)
  - [Entry Points](#entry-points)
  - [Engine Components](#engine-components)
  - [Directory Structure](#directory-structure)
- [Key Principles](#key-principles)
  - [Absolute Minimalism](#absolute-minimalism)
  - [Script-Based Modularity](#script-based-modularity)
  - [Let It Fail Philosophy](#let-it-fail-philosophy)
  - [Exit Codes as Signals](#exit-codes-as-signals)
- [Detailed Command Flow](#detailed-command-flow)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Basic Usage](#basic-usage)
- [Interactive Shell Commands](#interactive-shell-commands)
  - [Session Management](#session-management)
  - [Project Management](#project-management)
  - [Version Management](#version-management)
- [Command Script Development](#command-script-development)
- [Rule Script Development](#rule-script-development)
- [View System](#view-system)
- [Network Protocol](#network-protocol)
- [Project and Version Management](#project-and-version-management)
- [Atomic Experiments Development Approach](#atomic-experiments-development-approach)
- [Replays and Archiving](#replays-and-archiving)
- [Troubleshooting](#troubleshooting)
  - [Common Issues](#common-issues)
  - [Debugging Techniques](#debugging-techniques)
- [Advanced Topics](#advanced-topics)
  - [Custom Templates](#custom-templates)
  - [Multi-Client Synchronization](#multi-client-synchronization)
  - [Performance Considerations](#performance-considerations)
- [Extending JC-CLI](#extending-jc-cli)
  - [Adding New Command Types](#adding-new-command-types)
  - [Custom Rule Systems](#custom-rule-systems)
  - [Alternative View Systems](#alternative-view-systems)
- [Decommissioning Checklist](#decommissioning-checklist)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Core Architecture

JC-CLI draws an inviolable line between two realms:

- **Infrastructure Realm** (Python engine) owns networking, command ordering, persistence, and rendering. It may only *append* to the command list and *read* the world.
- **Logic Realm** (Lua scripts or disciplined Python) owns every state mutation. It may only *read* the command list and *write* the world. It is isolated from sockets, clocks and operating‑system APIs.

Communication passes exclusively through two files:
1. **World File** (`data/world.json`) - Contains the mutable world state
2. **Commands File** (`data/commands.log`) - Contains the chronological list of player commands

## Implementation Structure

The implementation consists of several key components that work together to deliver the architectural vision:

### Entry Points

- **jc-cli.py** - Interactive CLI shell that provides session, project, and version management
- **thin_server.py** - Networked server that coordinates command distribution
- **thin_client.py** - Client that connects to the server and processes commands locally
- **orchestrator.py** - Core component that discovers and executes commands and rule scripts
- **rule_loop.py** - Executes automatic effects after each command
- **sequencer.py** - Ensures commands are processed in the same order on all clients
- **view.py** - Launches appropriate game-specific view scripts

### Engine Components

The `engine/` directory contains the infrastructure realm:

```
engine/
├─ core/              # Core utilities and configuration
│   ├─ config.py      # System-wide configuration constants
│   ├─ netcodec.py    # Network protocol encoding/decoding
│   ├─ project_manager.py  # Project and version management
│   ├─ session_manager.py  # Session creation and continuation
│   ├─ client_manager.py   # Client session management
│   ├─ snapshot.py    # Creates deterministic snapshots of code
│   └─ utils.py       # Utility functions
├─ client/            # Client-side network logic
│   ├─ client_network.py  # Network communication
│   ├─ client_state.py    # Client state management
│   └─ sequencer_control.py  # Manages sequencer process
└─ server/            # Server-side network logic
    ├─ server_state.py     # Server state initialization
    ├─ client_handling.py  # Client connection handling
    └─ command_processing.py  # Command sequencing and distribution
```

### Directory Structure

```
project_root/
├─ jc-cli.py          # Interactive session manager
├─ orchestrator.py    # Command discovery and execution
├─ rule_loop.py       # Automatic effects execution
├─ sequencer.py       # Ordered command processing
├─ thin_client.py     # Networked client
├─ thin_server.py     # Networked server
├─ view.py            # View system launcher
├─ engine/            # Infrastructure realm (described above)
├─ scripts/           # Logic realm (physically separate from engine)
│   ├─ commands/      # One file per player command keyword
│   ├─ rules/         # Rule scripts executed after commands
│   ├─ recipes/       # Reusable rule capsules
│   └─ views/         # View templates for rendering the world
├─ data/              # Persistent surface between realms
│   ├─ world.json     # Mutable world snapshot
│   └─ commands.log   # Ordered list of player commands
├─ templates/         # Seed worlds for quick restarts
│   ├─ default/       # Default template
│   │   ├─ initial_world.json  # Starting world state
│   │   ├─ engine_snapshot.json  # Engine files manifest
│   │   └─ client_snapshot.json  # Client files manifest
│   └─ ... (other templates)
├─ sessions/          # Active game sessions
│   └─ <session_name>/  # Each session gets its own directory
│       ├─ data/        # Session-specific data
│       ├─ engine_snapshot/  # Fixed engine code snapshot
│       ├─ history.json  # Command history
│       └─ initial_world.json  # Starting world state
├─ clients/           # Client-specific data
│   └─ <session_name>/
│       └─ <client_name>/  # Each client gets its own directory
│           ├─ data/      # Client-local data
│           └─ ... (client scripts and resources)
└─ projects/          # Project management
    └─ <project_name>/  # Each project gets its own directory
        ├─ metadata.json  # Project metadata
        ├─ v1.zip         # Version snapshots
        └─ ... (other version files)
```

## Key Principles

### Absolute Minimalism

1. **No validation layer** - Commands are trusted inputs. If a malformed command breaks the game, the break becomes observable data rather than a swallowed error.
2. **No hidden abstraction** - There is no ORM, no service locator, no private protocol translation. Raw data structures are stored exactly as they appear on disk.
3. **No alternative modes** - The engine is always networked. Even single-player spins up a local coordinator.
4. **No extra features without purpose** - Sound, UI widgets, and asset pipelines belong in later stages.

### Script-Based Modularity

All game logic must be called by script name via subprocesses, never as imported functions - even when called from other game logic. This enforces true modularity and makes components trivially replaceable.

### "Let It Fail" Philosophy

We don't need graceful error handling. The system should crash visibly when something is wrong rather than attempting to recover or hide errors, maximizing transparency and debug speed.

### Exit Codes as Signals

Communication between processes happens primarily through exit codes (0 for success, non-zero for failure). Passing complex data between scripts violates the design principles - world state changes should happen through the world file.

## Detailed Command Flow

The detailed command flow in JC-CLI follows these steps:

1. **Input Capture**: 
   - User enters a command in the client terminal
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

This flow ensures that:
- Commands are processed in the same order on all clients
- World state evolution is deterministic
- Game logic is cleanly separated from infrastructure

## Getting Started

### Prerequisites

- Python 3.6 or higher
- Network connectivity (even for local testing)
- Required Python packages:
  - watchdog (for file monitoring)

### Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/jc-cli.git
cd jc-cli
```

2. Set up a virtual environment (optional but recommended):
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install watchdog
```

### Basic Usage

1. Start the interactive shell:
```
python jc-cli.py
```

2. Create a new project:
```
> create-project my_game "My first experimental game"
```

3. Start a new session:
```
> start-session test_session default
```

4. Join the session:
```
> join-session test_session player1
```

## Interactive Shell Commands

JC-CLI provides a rich interactive shell with commands for session, project, and version management.

### Session Management

```
> start-session <session-name> [template=default]
```
Creates a new game session with the specified name. Optionally uses a template other than the default.

```
> continue-session <session-name>
```
Continues an existing session by starting the server for that session.

```
> join-session <session-name> <client-name> [server-ip]
```
Joins an existing session as a client. If server-ip is not specified, localhost is used.

```
> list-sessions
```
Lists all available sessions.

### Project Management

```
> create-project <project-name> [description]
```
Creates a new project with the given name and optional description.

```
> list-projects
```
Lists all available projects, showing the version count and active version for each.

```
> switch-project <project-name> [version]
```
Switches to the specified project and optional version.

```
> describe-project [project-name]
```
Shows detailed information about the current project or the specified project.

### Version Management

```
> create-version <version-name> [description]
```
Creates a new version from the current files with the given name and optional description.

```
> list-versions [project-name]
```
Lists all versions for the current project or the specified project.

```
> switch-version <version-name>
```
Switches to the specified version within the current project.

```
> export-version <project-name> <version-name> <output-path>
```
Exports a version to a zip file at the specified path.

## Command Script Development

Command scripts live in the `scripts/commands/` directory and follow a simple convention:

```python
#!/usr/bin/env python3
# scripts/commands/my_command.py

NAME = "my_command"  # Must be the first non-comment line

import json, sys

# Command implementation
def main():
    # Read the current world state
    with open("data/world.json", "r") as f:
        world = json.load(f)
    
    # Modify the world state
    world["some_property"] = "new value"
    
    # Write the updated world state
    with open("data/world.json", "w") as f:
        json.dump(world, f, indent=2)
    
    # Return success
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

Important conventions:
- The first non-comment line must define `NAME = "command_name"`
- The script must read and write the world file directly
- The script should return 0 for success, non-zero for failure
- No network or timing operations should be performed

## Rule Script Development

Rule scripts live in the `scripts/rules/` directory and follow a similar pattern:

```python
#!/usr/bin/env python3
# scripts/rules/my_rule.py

NAME = "my_rule_id"  # Must be the first non-comment line

import json, sys

# Rule implementation
def main():
    # Read world from stdin (provided by rule_loop.py)
    world = json.loads(sys.stdin.read())
    
    # Check if conditions for the rule are met
    if "trigger_condition" in world and world["trigger_condition"]:
        # Apply rule effects
        world["effect_property"] = "rule effect"
        # Signal that the world changed
        exit_code = 0
    else:
        # No changes needed
        exit_code = 9
    
    # Output modified world to stdout
    print(json.dumps(world))
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
```

Important conventions:
- The first non-comment line must define `NAME = "rule_id"`
- The rule reads world state from stdin and writes to stdout
- Exit with code 0 if the world was changed
- Exit with code 9 if no changes were made
- Any other exit code indicates an error

## View System

The view system renders the game state to the player. Views are scripts in the `scripts/views/` directory:

```python
#!/usr/bin/env python3
# scripts/views/my_view.py

import json, os, time, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--cmd-queue", required=True)
    args = parser.parse_args()
    
    world_file = os.path.join(args.dir, "data", "world.json")
    cmd_queue = args.cmd_queue
    
    # Main view loop
    try:
        while True:
            # Read and render world state
            with open(world_file, "r") as f:
                world = json.load(f)
            
            # Clear screen
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Render game state
            print(f"=== Game View for {args.username} ===")
            print(f"Counter: {world.get('counter', 0)}")
            # ... more rendering code ...
            
            # Get user input
            cmd = input("> ")
            if cmd.strip():
                # Write to command queue file for processing
                with open(cmd_queue, "a") as f:
                    f.write(cmd + "\n")
            
            # Brief pause to prevent CPU spinning
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting view...")
    
    return 0

if __name__ == "__main__":
    main()
```

Views have specific responsibilities:
- Reading the world file to get the current state
- Rendering the state according to view-specific rules
- Capturing user input and writing to the command queue
- Implementing appropriate permissions (player vs. admin views)

## Network Protocol

JC-CLI uses a simple length-prefixed JSON protocol for network communication:

1. Each message is prefixed with a 4-byte big-endian unsigned integer length
2. The payload is JSON encoded as UTF-8
3. The `netcodec.py` module handles encoding and decoding

Message types include:
- Command messages: `{"username": "player1", "text": "command text"}`
- Ordered commands: `{"seq": 42, "timestamp": 1234567890, "command": {...}}`
- Snapshot messages: `{"type": "snapshot_zip", "name": "client_snapshot.zip", "b64": "base64data"}`
- Initial world: `{"type": "initial_world", "world": {...}}`
- History metadata: `{"type": "history_meta", "highest_seq": 42, "page_size": 200}`
- History pages: `{"type": "history_page", "commands": [...]}`

## Project and Version Management

JC-CLI includes a comprehensive project and version management system:

1. **Projects** are collections of game rules, command scripts, and templates
2. **Versions** are snapshots of a project at a specific point in time
3. The system maintains metadata about projects and versions

When you create a version, JC-CLI:
1. Creates a zip file containing scripts and templates
2. Updates the project metadata
3. Sets the created version as active

When switching projects or versions:
1. Checks for uncommitted changes and backs them up if needed
2. Clears existing scripts and templates
3. Extracts the selected version
4. Updates the project tracking file

This enables:
- Working on multiple game prototypes simultaneously
- Maintaining multiple versions of each prototype
- Quick rollback to previous versions
- Sharing game rules between team members

## Atomic Experiments Development Approach

JC-CLI development follows an "atomic experiments" approach - isolated, minimal implementations that test a single architectural principle or component.

An atomic experiment should be:
1. **Focused** - Tests exactly one architectural principle
2. **Minimal** - Contains only what's needed to verify the principle
3. **Self-contained** - Functions independently of other components
4. **Verifiable** - Success criteria are clear and testable
5. **Reusable** - Patterns can be incorporated into the final implementation
6. **Disposable** - Can be discarded after the principle is validated

## Replays and Archiving

A replay consists of:
- The initial world snapshot
- The ordered player command list
- The exact rule scripts used during the session

The deterministic nature of JC-CLI guarantees that replaying the same commands with the same scripts will produce identical results on any machine.

To archive a session:
1. The session directory contains the complete history
2. The engine and client snapshots preserve the exact code
3. The world file shows the final state

This can be used for:
- Regression testing
- Sharing game sessions with other designers
- Analyzing gameplay patterns
- Documenting the evolution of game rules

## Troubleshooting

### Common Issues

**Command not found error:**
```
Unknown command: my_command
```
- Ensure the command script exists in scripts/commands/
- Check that the NAME variable is correctly set
- Verify the script has executable permissions

**Sequencer not processing commands:**
- Check if the sequencer process is running
- Verify the commands.log file exists and is being updated
- Ensure the cursor.seq file is present and contains a valid number

**Network connection failures:**
- Confirm the server is running
- Check firewall settings
- Verify correct IP address and port
- Ensure network interfaces are properly configured

**World state not updating:**
- Check if command scripts are writing to the correct world.json path
- Verify the rule loop is being triggered after commands
- Look for permission issues with file writing

### Debugging Techniques

1. **Examine logs**: 
   - Check the terminal output for error messages
   - Look for exit codes from command and rule scripts

2. **Inspect files**:
   - Examine commands.log to see if commands are being recorded
   - Check world.json to see the current state
   - Look at cursor.seq to see which commands have been processed

3. **Test command scripts manually**:
   ```
   python scripts/commands/my_command.py arg1 arg2
   ```

4. **Run the orchestrator directly**:
   ```
   python orchestrator.py "command_name arg1 arg2"
   ```

## Advanced Topics

### Custom Templates

Templates provide starter worlds and configurations for game sessions. To create a custom template:

1. Create a new directory in the templates/ folder:
   ```
   mkdir -p templates/my_template
   ```

2. Create an initial_world.json file with your starting state:
   ```json
   {
     "game_name": "My Custom Game",
     "turn": 0,
     "players": {},
     "rules_in_power": ["rule1", "rule2"]
   }
   ```

3. Create engine_snapshot.json and client_snapshot.json manifests listing required files

4. Use your template when starting a session:
   ```
   > start-session my_session my_template
   ```

### Multi-Client Synchronization

JC-CLI ensures synchronization between clients through:

1. **Sequenced commands**: Every command gets a unique, monotonically increasing sequence number
2. **Deterministic execution**: Given the same commands in the same order, all clients reach the same state
3. **History synchronization**: New clients receive the full command history when joining

This model requires minimal bandwidth and avoids complex state reconciliation algorithms.

### Performance Considerations

For larger games, consider:

1. **Command batching**: Group related commands to reduce network overhead
2. **Selective rule application**: Only run rules that might be affected by a command
3. **View optimization**: Only re-render changed portions of the view
4. **History management**: Implement pruning strategies for very long sessions

## Extending JC-CLI

### Adding New Command Types

To add a new command type:

1. Create a new script in scripts/commands/:
   ```python
   #!/usr/bin/env python3
   # scripts/commands/new_command.py
   
   NAME = "new_command"
   
   import json, sys
   
   def main():
       # Implementation
       return 0
   
   if __name__ == "__main__":
       sys.exit(main())
   ```

2. The command becomes immediately available without any registration

### Custom Rule Systems

To create a custom rule system:

1. Define rule scripts in scripts/rules/
2. Specify active rules in world.json:
   ```json
   {
     "rules_in_power": ["rule1", "rule2"]
   }
   ```

3. The rule_loop.py script will automatically discover and apply these rules

### Alternative View Systems

To create custom views:

1. Create a new script in scripts/views/:
   ```python
   #!/usr/bin/env python3
   # scripts/views/fancy_view.py
   
   # Implementation
   ```

2. When joining a session, specify the view:
   ```
   > join-session my_session player1 --view fancy_view
   ```

## Decommissioning Checklist

When you're ready to move beyond the prototype phase:

1. Freeze at least three significant sessions (world, command list, rule scripts)
2. Tag the repository and archive the prototype
3. Carry only the design insights and replay bundles into the production engine

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Contributors and maintainers
- Inspiration from deterministic game engines
- Early testers and feedback providers