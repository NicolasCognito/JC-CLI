#!/usr/bin/env python3
"""
JC-CLI View System
Launches appropriate game-specific view script.
"""
import os, sys, argparse, subprocess
from pathlib import Path

DEFAULT_VIEW = "default_view.py"

def find_view_script(view_name, client_dir):
    """Locate the requested view script."""
    if not view_name.endswith('.py'):
        view_name += '.py'
    
    # Check in scripts/views directory
    views_dir = os.path.join(client_dir, "scripts", "views")
    view_path = os.path.join(views_dir, view_name)
    
    if os.path.exists(view_path):
        return view_path
    
    # If not found, try default
    default_path = os.path.join(views_dir, DEFAULT_VIEW)
    if os.path.exists(default_path):
        print(f"View '{view_name}' not found, using default")
        return default_path
    
    return None

def main():
    parser = argparse.ArgumentParser(description="JC-CLI View System")
    parser.add_argument("--dir", help="Client directory", required=True)
    parser.add_argument("--username", help="Username", required=True)
    parser.add_argument("--view", help="View script to use", default=DEFAULT_VIEW)
    parser.add_argument("--cmd-queue", help="Command queue file path", required=True)
    args = parser.parse_args()
    
    # Ensure client directory is absolute
    client_dir = os.path.abspath(args.dir)
    
    # Ensure command queue directory exists
    Path(os.path.dirname(args.cmd_queue)).mkdir(parents=True, exist_ok=True)
    
    # Find view script
    view_script = find_view_script(args.view, client_dir)
    if not view_script:
        print(f"No view script found for '{args.view}'. Exiting.")
        return 1
    
    print(f"Launching view script: {view_script}")
    
    # Launch the appropriate view script directly
    # This will take over the terminal window
    try:
        result = subprocess.run([
            sys.executable, 
            view_script,
            "--dir", client_dir,
            "--username", args.username,
            "--cmd-queue", args.cmd_queue
        ])
        return result.returncode
    except Exception as e:
        print(f"Error launching view script: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())