#!/usr/bin/env python3
# jc-cli.py (Located in project root, outside 'engine' folder)
"""
JC-CLI - Interactive Session Manager (Network-Enabled Version)
Provides an interactive shell for managing game sessions, clients, projects, and versions.

Run from the project root directory:
  python jc-cli.py

Available commands:
  start-session <session-name> [template]  - Start a new game session
  continue-session <session-name>          - Continue an existing session
  join-session <session-name> <client-name> [server-ip]
                                          - Join a session as a client
  list-sessions                            - List available sessions

Project Management:
  create-project <project-name> [description]   - Create a new project
  list-projects                                 - List all available projects
  switch-project <project-name> [version]       - Switch to a project and version
  describe-project [project-name]               - Show project details and versions

Version Management:
  create-version <version-name> [description]   - Create a new version from current files
  list-versions [project-name]                  - List all versions for a project
  switch-version <version-name>                 - Switch to a version in current project
  export-version <project-name> <version-name> <output-path>
                                              - Export a version to a zip file

General:
  help                                     - Show available commands
  exit                                     - Exit the shell
"""

import sys
import shlex
# Use absolute imports assuming 'engine' is a package in the current directory
# or accessible via PYTHONPATH
from engine.core import config
from engine.core import utils
from engine.core import session_manager
from engine.core import client_manager
from engine.core import project_manager

def show_help():
    """Display available commands"""
    print("Available commands:")
    # Use config.DEFAULT_TEMPLATE for dynamic help text
    print(f"  start-session <session-name> [template={config.DEFAULT_TEMPLATE}] - Start a new game session")
    print("  continue-session <session-name>                                    - Continue an existing session")
    print("  join-session <session-name> <client-name> [server-ip]              - Join a session as a client")
    print("  list-sessions                                                      - List available sessions")
    
    # Project management commands
    print("\nProject Management:")
    print("  create-project <project-name> [description]                        - Create a new project")
    print("  list-projects                                                      - List all available projects")
    print("  switch-project <project-name> [version]                            - Switch to a project and version")
    print("  describe-project [project-name]                                    - Show project details and versions")
    
    # Version management commands
    print("\nVersion Management:")
    print("  create-version <version-name> [description]                        - Create a new version from current files")
    print("  list-versions [project-name]                                       - List all versions for a project")
    print("  switch-version <version-name>                                      - Switch to a version in current project")
    print("  export-version <project-name> <version-name> <output-path>         - Export a version to a zip file")
    
    print("\nGeneral:")
    print("  help                                                               - Show this help message")
    print("  delete-all [--force]                                               - Delete ALL sessions and clients")
    print("  exit                                                               - Exit the shell")

def interactive_shell():
    """Run the interactive shell"""
    print("JC-CLI Interactive Shell (Network-Enabled Version)")
    print("Enter 'help' for available commands, 'exit' to quit")
    
    # Show current project status on startup
    current_project, current_version = project_manager.get_current_project()
    if current_project:
        version_info = f", version '{current_version}'" if current_version else ""
        print(f"Current project: '{current_project}'{version_info}")

    while True:
        try:
            # Get input from user
            user_input = input("> ")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        # Parse input using shlex
        args = shlex.split(user_input)
        if not args:
            continue

        command = args[0].lower()

        # Process commands using imported functions from engine.core modules
        if command == "exit":
            break
        elif command == "help":
            show_help()
        elif command == "list-sessions":
            session_manager.list_sessions() # Call function from session_manager module
        elif command == "start-session":
            if len(args) < 2:
                print("Error: Missing session name")
                print(f"Usage: start-session <session-name> [template={config.DEFAULT_TEMPLATE}]")
                continue
            session_name = args[1]
            template = args[2] if len(args) > 2 else config.DEFAULT_TEMPLATE # Use config constant
            session_manager.start_session(session_name, template) # Call function from session_manager
        elif command == "continue-session":
            if len(args) < 2:
                print("Error: Missing session name")
                print("Usage: continue-session <session-name>")
                continue
            session_name = args[1]
            session_manager.continue_session(session_name) # Call function from session_manager
        elif command == "join-session":
            if len(args) < 3:
                print("Error: Missing session name or client name")
                print("Usage: join-session <session-name> <client-name> [server-ip]")
                continue
            session_name = args[1]
            client_name = args[2]
            server_ip = args[3] if len(args) > 3 else None
            client_manager.join_session(session_name, client_name, server_ip) # Call function from client_manager
            
        # Project management commands
        elif command == "create-project":
            if len(args) < 2:
                print("Error: Missing project name")
                print("Usage: create-project <project-name> [description]")
                continue
            project_name = args[1]
            description = " ".join(args[2:]) if len(args) > 2 else ""
            project_manager.create_project(project_name, description)
            
        elif command == "list-projects":
            projects = project_manager.list_projects()
            if projects:
                print("\nAvailable Projects:")
                for project in projects:
                    version_count = len(project.get("versions", []))
                    active = project.get("active_version", "None")
                    print(f"  {project['name']} - {project.get('description', '')}")
                    print(f"    Versions: {version_count}, Active: {active}")
            else:
                print("No projects available. Create one with 'create-project'.")
                
        elif command == "switch-project":
            if len(args) < 2:
                print("Error: Missing project name")
                print("Usage: switch-project <project-name> [version]")
                continue
            project_name = args[1]
            version_name = args[2] if len(args) > 2 else ""
            project_manager.switch_project(project_name, version_name)
            
        elif command == "describe-project":
            project_name = args[1] if len(args) > 1 else ""
            project_manager.describe_project(project_name)
            
        # Version management commands
        elif command == "create-version":
            if len(args) < 2:
                print("Error: Missing version name")
                print("Usage: create-version <version-name> [description]")
                continue
            version_name = args[1]
            description = " ".join(args[2:]) if len(args) > 2 else ""
            current_project, _ = project_manager.get_current_project()
            if not current_project:
                print("No active project. Please switch to a project first.")
                continue
            project_manager.create_version(current_project, version_name, description)
            
        elif command == "list-versions":
            project_name = args[1] if len(args) > 1 else ""
            versions = project_manager.list_versions(project_name)
            if versions:
                current_project = project_name or project_manager.get_current_project()[0]
                print(f"\nVersions for project '{current_project}':")
                for version in versions:
                    print(f"  {version['name']} - {version.get('description', '')}")
                    print(f"    Created: {version.get('timestamp', 'Unknown')}")
            else:
                print("No versions available. Create one with 'create-version'.")
                
        elif command == "switch-version":
            if len(args) < 2:
                print("Error: Missing version name")
                print("Usage: switch-version <version-name>")
                continue
            version_name = args[1]
            project_manager.switch_version(version_name)
            
        elif command == "export-version":
            if len(args) < 4:
                print("Error: Missing required arguments")
                print("Usage: export-version <project-name> <version-name> <output-path>")
                continue
            project_name = args[1]
            version_name = args[2]
            output_path = args[3]
            project_manager.export_version(project_name, version_name, output_path)

        elif command == "delete-all":
            force = "--force" in args
            session_manager.delete_all_sessions_and_clients(force)
            
        else:
            print(f"Unknown command: {command}")
            print("Enter 'help' for available commands")

def main():
    """Main entry point: Setup directories and handle direct commands or start shell."""
    # Ensure base directories (like sessions/, templates/) exist
    utils.setup_directories() # Call function from utils module

    # Check if running interactively (no args) or with a direct command
    if len(sys.argv) == 1:
        interactive_shell()
    else:
        # Handle direct command-line execution
        command = sys.argv[1].lower()
        # Pass sys.argv directly for simplicity or use argparse for robust parsing
        args = sys.argv[1:] # Full arguments including command name

        if command == "start-session":
            if len(args) < 2: print(f"Usage: start-session <session-name> [template={config.DEFAULT_TEMPLATE}]"); return
            session_name = args[1]
            template = args[2] if len(args) > 2 else config.DEFAULT_TEMPLATE
            session_manager.start_session(session_name, template)
        elif command == "continue-session":
            if len(args) < 2: print("Usage: continue-session <session-name>"); return
            session_name = args[1]
            session_manager.continue_session(session_name)
        elif command == "join-session":
            if len(args) < 3: print("Usage: join-session <session-name> <client-name> [server-ip]"); return
            session_name = args[1]
            client_name = args[2]
            server_ip = args[3] if len(args) > 3 else None
            client_manager.join_session(session_name, client_name, server_ip)
        elif command == "list-sessions":
            session_manager.list_sessions()
            
        # Project management commands
        elif command == "create-project":
            if len(args) < 2: print("Usage: create-project <project-name> [description]"); return
            project_name = args[1]
            description = " ".join(args[2:]) if len(args) > 2 else ""
            project_manager.create_project(project_name, description)
            
        elif command == "list-projects":
            projects = project_manager.list_projects()
            if projects:
                print("\nAvailable Projects:")
                for project in projects:
                    version_count = len(project.get("versions", []))
                    active = project.get("active_version", "None")
                    print(f"  {project['name']} - {project.get('description', '')}")
                    print(f"    Versions: {version_count}, Active: {active}")
            else:
                print("No projects available. Create one with 'create-project'.")
            
        elif command == "switch-project":
            if len(args) < 2: print("Usage: switch-project <project-name> [version]"); return
            project_name = args[1]
            version_name = args[2] if len(args) > 2 else ""
            project_manager.switch_project(project_name, version_name)
            
        elif command == "describe-project":
            project_name = args[1] if len(args) > 1 else ""
            project_manager.describe_project(project_name)
            
        # Version management commands
        elif command == "create-version":
            if len(args) < 2: print("Usage: create-version <version-name> [description]"); return
            version_name = args[1]
            description = " ".join(args[2:]) if len(args) > 2 else ""
            current_project, _ = project_manager.get_current_project()
            if not current_project:
                print("No active project. Please switch to a project first.")
                return
            project_manager.create_version(current_project, version_name, description)
            
        elif command == "list-versions":
            project_name = args[1] if len(args) > 1 else ""
            versions = project_manager.list_versions(project_name)
            if versions:
                current_project = project_name or project_manager.get_current_project()[0]
                print(f"\nVersions for project '{current_project}':")
                for version in versions:
                    print(f"  {version['name']} - {version.get('description', '')}")
                    print(f"    Created: {version.get('timestamp', 'Unknown')}")
            else:
                print("No versions available. Create one with 'create-version'.")
                
        elif command == "switch-version":
            if len(args) < 2: print("Usage: switch-version <version-name>"); return
            version_name = args[1]
            project_manager.switch_version(version_name)
            
        elif command == "export-version":
            if len(args) < 4: print("Usage: export-version <project-name> <version-name> <output-path>"); return
            project_name = args[1]
            version_name = args[2]
            output_path = args[3]
            project_manager.export_version(project_name, version_name, output_path)
        
        elif command == "delete-all":
            force = "--force" in args
            session_manager.delete_all_sessions_and_clients(force)
            
        elif command == "help":
             show_help()
        else:
            print(f"Unknown command: {command}")
            # Print the docstring as usage instructions
            print(__doc__)

if __name__ == "__main__":
    # Ensure the main function is called when the script is executed directly
    main()