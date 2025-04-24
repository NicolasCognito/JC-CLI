# engine/core/session_manager.py
"""Session start / continue with manifest-driven snapshots."""

import os, sys, json, shutil, base64

from ... import config
from . import utils, snapshot

# ---------------------------------------------------------------------- #
def _create_snapshots(template_dir: str, session_dir: str) -> bool:
    eng_manifest = os.path.join(template_dir, config.ENGINE_MANIFEST)
    cli_manifest = os.path.join(template_dir, config.CLIENT_MANIFEST)

    if not (os.path.exists(eng_manifest) and os.path.exists(cli_manifest)):
        print("ERROR: Template is missing snapshot manifests.")
        return False

    snap_dir = os.path.join(session_dir, config.SNAPSHOT_DIR)
    os.makedirs(snap_dir, exist_ok=True)

    eng_zip = os.path.join(snap_dir, config.ENGINE_ZIP_NAME)
    cli_zip = os.path.join(snap_dir, config.CLIENT_ZIP_NAME)

    print("Building engine snapshot zip …")
    eng_hash = snapshot.build_snapshot(eng_manifest, eng_zip)
    print("Building client snapshot zip …")
    cli_hash = snapshot.build_snapshot(cli_manifest, cli_zip)

    manifest = {
        "engine_zip": os.path.basename(eng_zip),
        "engine_sha256": eng_hash,
        "client_zip": os.path.basename(cli_zip),
        "client_sha256": cli_hash,
    }
    with open(os.path.join(snap_dir, "snapshot_meta.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)
    return True

# ---------------------------------------------------------------------- #
def start_session(session_name, template_name=config.DEFAULT_TEMPLATE):
    session_dir  = os.path.join(config.SESSIONS_DIR, session_name)
    if os.path.exists(session_dir):
        print("Session already exists, abort.")
        return False

    template_dir = os.path.join(config.TEMPLATES_DIR, template_name)
    init_world   = os.path.join(template_dir, config.INITIAL_WORLD_FILE)
    if not os.path.exists(init_world):
        print("Template missing initial world.")
        return False

    os.makedirs(session_dir, exist_ok=True)
    os.makedirs(os.path.join(session_dir, config.CLIENT_DIR), exist_ok=True)
    shutil.copy2(init_world, os.path.join(session_dir, config.INITIAL_WORLD_FILE))
    with open(os.path.join(session_dir, config.HISTORY_FILE), "w") as fh:
        json.dump([], fh)

    if not _create_snapshots(template_dir, session_dir):
        return False

    print(f"Session '{session_name}' created.")
    server_cmd = f"{sys.executable} {config.SERVER_SCRIPT} --session-dir \"{session_dir}\""
    if utils.launch_in_new_terminal(server_cmd, title=f"JC Server: {session_name}"):
        return True

    print("Manual launch:", server_cmd)
    return False

# continue_session unchanged
def continue_session(session_name):
    session_dir = os.path.join(config.SESSIONS_DIR, session_name)
    if not os.path.exists(session_dir):
        print("Session not found.")
        return False

    server_cmd = f"{sys.executable} {config.SERVER_SCRIPT} --session-dir \"{session_dir}\""
    if utils.launch_in_new_terminal(server_cmd, title=f"JC Server: {session_name}"):
        return True

    print("Manual launch:", server_cmd)
    return False

def delete_all_sessions_and_clients(force=False):
    """Delete all sessions and clients completely."""
    if not force:
        confirm = input("WARNING: This will delete ALL sessions and clients. Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("Operation canceled.")
            return False
    
    try:
        # Delete sessions directory
        if os.path.exists(config.SESSIONS_DIR):
            shutil.rmtree(config.SESSIONS_DIR)
            print("All sessions deleted.")
            
        # Delete clients directory
        clients_dir = "clients"  # This appears to be hardcoded in the codebase
        if os.path.exists(clients_dir):
            shutil.rmtree(clients_dir)
            print("All clients deleted.")
            
        # Recreate empty directories
        os.makedirs(config.SESSIONS_DIR, exist_ok=True)
        
        return True
    except Exception as e:
        print(f"Error during deletion: {e}")
        return False