# engine/core/config.py
"""Configuration constants for the JC engine/CLI"""

# Directory constants
SESSIONS_DIR = "sessions"
TEMPLATES_DIR = "templates"
CLIENT_DIR = "clients" # Subdirectory within a session
DATA_DIR = "data" # Data directory within client or session dirs

# Network configuration
SERVER_HOST = '0.0.0.0'  # Listen on all interfaces by default
SERVER_PORT = 9000
BUFFER_SIZE = 4096

# Template constants
DEFAULT_TEMPLATE = "default"

# File constants within session/client dirs
HISTORY_FILE = "history.json"       # In session dir
WORLD_FILE = "world.json"           # In client data dir / template dir
INITIAL_WORLD_FILE = "initial_world.json" # In session dir / template dir
COMMANDS_FILE = "commands.json"     # In client data dir

# Script names assumed to exist
ORCHESTRATOR_SCRIPT = "orchestrator.py"
RULE_LOOP_SCRIPT = "rule_loop.py"
SERVER_SCRIPT = "thin_server.py"
CLIENT_SCRIPT = "thin_client.py"
SEQUENCER_SCRIPT = "sequencer.py"
SCRIPTS_DIR = "scripts" # Directory containing game logic scripts