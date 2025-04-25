# engine/core/utils.py
"""Utility functions for file operations and process management"""

import os
import sys
import platform
import subprocess
import shutil
import json
import config  # Use relative import within the package

def setup_directories():
    """Ensure required base directories exist and create default template"""
    os.makedirs(config.SESSIONS_DIR, exist_ok=True)
    os.makedirs(config.TEMPLATES_DIR, exist_ok=True)

    # Create default template if it doesn't exist
    default_template_dir = os.path.join(config.TEMPLATES_DIR, config.DEFAULT_TEMPLATE)
    default_template_initial_world_file = os.path.join(default_template_dir, config.INITIAL_WORLD_FILE)

    os.makedirs(default_template_dir, exist_ok=True)

    if not os.path.exists(default_template_initial_world_file):
        # Create a simple default template world
        with open(default_template_initial_world_file, 'w') as f:
            json.dump({
                "counter": 0,
                "rule_map": {
                    "trim_counter": "counter_threshold.py"
                }
            }, f, indent=2)
        print(f"Created default template at {default_template_initial_world_file}")

def copy_directory(src, dst):
    """Copy a directory recursively"""
    if not os.path.exists(src):
        print(f"Warning: Source directory {src} not found")
        return False
    try:
        os.makedirs(dst, exist_ok=True)
        for item in os.listdir(src):
            src_item = os.path.join(src, item)
            dst_item = os.path.join(dst, item)
            if os.path.isdir(src_item):
                copy_directory(src_item, dst_item)
            else:
                shutil.copy2(src_item, dst_item)
        return True
    except Exception as e:
        print(f"Error copying directory: {e}")
        return False

def launch_in_new_terminal(cmd, title=None):
    """Launch a command in a new terminal window based on OS"""
    # … existing code …

# ──────────────────────────────────────────────────────────────────────────────

def clear_client_state(commands_path: str, cursor_path: str, scripts_dir: str) -> None:
    """
    Clear the client’s command log, reset the cursor file to zero,
    and wipe & recreate the scripts directory.
    """
    # Clear commands log file
    open(commands_path, "w").close()
    print("Command log file reset")

    # Reset cursor file to 0
    with open(cursor_path, "w") as f:
        f.write("0")
    print("Cursor sequence reset to 0")

    # Clear scripts directory if it exists
    if os.path.exists(scripts_dir):
        print(f"Clearing scripts directory: {scripts_dir}")
        shutil.rmtree(scripts_dir)
    os.makedirs(scripts_dir, exist_ok=True)
