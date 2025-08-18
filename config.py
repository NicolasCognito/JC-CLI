# engine/core/config.py
"""Configuration constants for the JC-CLI prototype."""

# ------------- Utils ---------------------------

USE_WIZTERM = False

# ------------- folders & files -----------------
SESSIONS_DIR        = "var/sessions"
TEMPLATES_DIR       = "templates"
DEFAULT_TEMPLATE     = "default"
CLIENT_DIR          = "clients"  # per-session clients subdir
CLIENTS_ROOT        = "var/clients"  # local client workspaces root
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

# ------------- execution mode -----------------
# Modes:
#   "file"   – default; state is read/written via data/world.json
#   "memory" – sequencer maintains an in-memory world but still seeds
#              command scripts by writing the current world to disk
#              before each command and reading it back afterward.
# Switch with env var JC_WORLD_MODE without changing repo config.
WORLD_MODE          = "memory"

# ------------- network -------------------------
SERVER_HOST         = "0.0.0.0"
SERVER_PORT         = 9000
BUFFER_SIZE         = 4096
FRAME_HEADER_BYTES  = 4
HISTORY_PAGE_SIZE   = 200 


# ------------- entry scripts -------------------
ORCHESTRATOR_SCRIPT = "engine/orchestrator.py"
RULE_LOOP_SCRIPT    = "engine/rule_loop.py"
SERVER_SCRIPT       = "engine/thin_server.py"
CLIENT_SCRIPT       = "engine/thin_client.py"
SEQUENCER_SCRIPT    = "engine/sequencer.py"
SCRIPTS_DIR         = "scripts"
DEFAULT_VIEW        = "default"

# ---------- command keywords ----------
RESET_COMMAND      = "reset"
SEND_INITIAL       = True
INITIAL_COMMAND    = "client_joined"
SEND_DISCONNECT    = True
DISCONNECT_COMMAND = "client_disconnected"
