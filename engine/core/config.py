# engine/core/config.py
"""Configuration constants for the JC engine/CLI"""

# Directory constants
SESSIONS_DIR = "sessions"
TEMPLATES_DIR = "templates"
CLIENT_DIR   = "clients"
DATA_DIR     = "data"

# Network
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 9000
BUFFER_SIZE = 4096
FRAME_HEADER_BYTES = 4          # used by netcodec

# Template
DEFAULT_TEMPLATE = "default"

# File names
HISTORY_FILE       = "history.json"
WORLD_FILE         = "world.json"
INITIAL_WORLD_FILE = "initial_world.json"

COMMANDS_LOG_FILE  = "commands.log"   # ← append-only, JSON-lines
CURSOR_FILE        = "cursor.seq"     # ← sequencer progress marker

# Script names
ORCHESTRATOR_SCRIPT = "orchestrator.py"
RULE_LOOP_SCRIPT     = "rule_loop.py"
SERVER_SCRIPT        = "thin_server.py"
CLIENT_SCRIPT        = "thin_client.py"
SEQUENCER_SCRIPT     = "sequencer.py"
SCRIPTS_DIR          = "scripts"
