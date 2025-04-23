# engine/core/config.py
"""Configuration constants for the JC-CLI prototype."""

# ------------- folders & files -----------------
SESSIONS_DIR        = "sessions"
TEMPLATES_DIR       = "templates"
DEFAULT_TEMPLATE     = "default"
CLIENT_DIR          = "clients"
DATA_DIR            = "data"
SNAPSHOT_DIR        = "engine_snapshot"      # inside session

ENGINE_MANIFEST     = "engine_snapshot.json"
CLIENT_MANIFEST     = "client_snapshot.json"

ENGINE_ZIP_NAME     = "engine_snapshot.zip"
CLIENT_ZIP_NAME     = "client_snapshot.zip"

HISTORY_FILE        = "history.json"
WORLD_FILE          = "world.json"
INITIAL_WORLD_FILE  = "initial_world.json"

COMMANDS_LOG_FILE   = "commands.log"
CURSOR_FILE         = "cursor.seq"

# ------------- network -------------------------
SERVER_HOST         = "0.0.0.0"
SERVER_PORT         = 9000
BUFFER_SIZE         = 4096
FRAME_HEADER_BYTES  = 4
HISTORY_PAGE_SIZE   = 200 

# ------------- entry scripts -------------------
ORCHESTRATOR_SCRIPT = "orchestrator.py"
RULE_LOOP_SCRIPT    = "rule_loop.py"
SERVER_SCRIPT       = "thin_server.py"
CLIENT_SCRIPT       = "thin_client.py"
SEQUENCER_SCRIPT    = "sequencer.py"
SCRIPTS_DIR         = "scripts"
