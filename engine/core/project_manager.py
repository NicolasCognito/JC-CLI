#!/usr/bin/env python3
# engine/core/project_manager.py
"""
Project and Version Management for JC-CLI
Provides functionality for creating, switching between, and managing projects and versions.
"""

import os
import json
import shutil
import zipfile
import datetime
from typing import Dict, List, Optional, Tuple, Any
import config

# Constants
PROJECTS_DIR = "projects"
PROJECT_TRACKING_FILE = ".project"
DEFAULT_PROJECT_NAME = "default"

# Ensure projects directory exists
os.makedirs(PROJECTS_DIR, exist_ok=True)

def get_current_project() -> Tuple[str, str]:
    """Get the current project and version.
    
    Returns:
        Tuple[str, str]: (project_name, version_name)
    """
    if not os.path.exists(PROJECT_TRACKING_FILE):
        return (DEFAULT_PROJECT_NAME, "")
    
    try:
        with open(PROJECT_TRACKING_FILE, "r") as f:
            tracking = json.load(f)
            return (tracking.get("project", DEFAULT_PROJECT_NAME), 
                    tracking.get("version", ""))
    except Exception as e:
        print(f"Error reading project tracking: {e}")
        return (DEFAULT_PROJECT_NAME, "")

def set_current_project(project_name: str, version_name: str) -> bool:
    """Set the current project and version.
    
    Args:
        project_name (str): Project name
        version_name (str): Version name
        
    Returns:
        bool: Success or failure
    """
    try:
        with open(PROJECT_TRACKING_FILE, "w") as f:
            json.dump({"project": project_name, "version": version_name}, f, indent=2)
        return True
    except Exception as e:
        print(f"Error setting current project: {e}")
        return False

def list_projects() -> List[Dict[str, Any]]:
    """List all available projects.
    
    Returns:
        List[Dict[str, Any]]: List of project metadata
    """
    projects = []
    try:
        for item in os.listdir(PROJECTS_DIR):
            project_path = os.path.join(PROJECTS_DIR, item)
            if os.path.isdir(project_path):
                metadata_path = os.path.join(project_path, "metadata.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                        projects.append(metadata)
    except Exception as e:
        print(f"Error listing projects: {e}")
    
    return projects

def create_project(project_name: str, description: str = "") -> bool:
    """Create a new project.
    
    Args:
        project_name (str): Project name
        description (str, optional): Project description
        
    Returns:
        bool: Success or failure
    """
    project_dir = os.path.join(PROJECTS_DIR, project_name)
    metadata_path = os.path.join(project_dir, "metadata.json")
    
    # Check if project already exists
    if os.path.exists(project_dir):
        print(f"Project '{project_name}' already exists.")
        return False
    
    try:
        # Create project directory
        os.makedirs(project_dir, exist_ok=True)
        
        # Create metadata file
        metadata = {
            "name": project_name,
            "description": description,
            "created": datetime.datetime.now().isoformat(),
            "versions": [],
            "active_version": ""
        }
        
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Create initial version if scripts/templates exist
        if os.path.exists(config.SCRIPTS_DIR) or os.path.exists(config.TEMPLATES_DIR):
            create_version(project_name, "v1", "Initial version")
        
        # Set this as the current project
        set_current_project(project_name, "v1" if os.path.exists(config.SCRIPTS_DIR) else "")
        
        print(f"Project '{project_name}' created successfully.")
        return True
    except Exception as e:
        print(f"Error creating project: {e}")
        return False

def get_project_metadata(project_name: str) -> Optional[Dict[str, Any]]:
    """Get metadata for a specific project.
    
    Args:
        project_name (str): Project name
        
    Returns:
        Optional[Dict[str, Any]]: Project metadata or None if not found
    """
    metadata_path = os.path.join(PROJECTS_DIR, project_name, "metadata.json")
    
    if not os.path.exists(metadata_path):
        return None
    
    try:
        with open(metadata_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading project metadata: {e}")
        return None

def update_project_metadata(project_name: str, metadata: Dict[str, Any]) -> bool:
    """Update metadata for a specific project.
    
    Args:
        project_name (str): Project name
        metadata (Dict[str, Any]): Updated metadata
        
    Returns:
        bool: Success or failure
    """
    metadata_path = os.path.join(PROJECTS_DIR, project_name, "metadata.json")
    
    try:
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        return True
    except Exception as e:
        print(f"Error updating project metadata: {e}")
        return False

def create_version(project_name: str, version_name: str, description: str = "") -> bool:
    """Create a new version of a project from the current working copy.
    
    Args:
        project_name (str): Project name
        version_name (str): Version name
        description (str, optional): Version description
        
    Returns:
        bool: Success or failure
    """
    # Validate project exists
    metadata = get_project_metadata(project_name)
    if not metadata:
        print(f"Project '{project_name}' does not exist.")
        return False
    
    # Check if version already exists
    for version in metadata["versions"]:
        if version["name"] == version_name:
            print(f"Version '{version_name}' already exists for project '{project_name}'.")
            return False
    
    project_dir = os.path.join(PROJECTS_DIR, project_name)
    version_filename = f"{version_name}.zip"
    version_path = os.path.join(project_dir, version_filename)
    
    try:
        # Create zip file containing scripts and templates
        with zipfile.ZipFile(version_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add scripts directory if exists
            if os.path.exists(config.SCRIPTS_DIR):
                for root, _, files in os.walk(config.SCRIPTS_DIR):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.dirname(config.SCRIPTS_DIR))
                        zf.write(file_path, arcname)
            
            # Add templates directory if exists
            if os.path.exists(config.TEMPLATES_DIR):
                for root, _, files in os.walk(config.TEMPLATES_DIR):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.dirname(config.TEMPLATES_DIR))
                        zf.write(file_path, arcname)
        
        # Update metadata
        version_info = {
            "name": version_name,
            "filename": version_filename,
            "timestamp": datetime.datetime.now().isoformat(),
            "description": description
        }
        
        metadata["versions"].append(version_info)
        metadata["active_version"] = version_name
        
        update_project_metadata(project_name, metadata)
        set_current_project(project_name, version_name)
        
        print(f"Version '{version_name}' of project '{project_name}' created successfully.")
        return True
    except Exception as e:
        print(f"Error creating version: {e}")
        if os.path.exists(version_path):
            os.remove(version_path)
        return False

def switch_project(project_name: str, version_name: str = "") -> bool:
    """Switch to a specific project and optionally a specific version.
    
    Args:
        project_name (str): Project name
        version_name (str, optional): Version name (defaults to project's active version)
        
    Returns:
        bool: Success or failure
    """
    # Validate project exists
    metadata = get_project_metadata(project_name)
    if not metadata:
        print(f"Project '{project_name}' does not exist.")
        return False
    
    # If no version specified, use the project's active version
    if not version_name:
        version_name = metadata.get("active_version", "")
        if not version_name and metadata["versions"]:
            version_name = metadata["versions"][-1]["name"]
    
    # If still no version and project has versions, pick the latest
    if not version_name:
        print(f"Project '{project_name}' has no versions.")
        return False
    
    # Validate version exists
    version_info = None
    for version in metadata["versions"]:
        if version["name"] == version_name:
            version_info = version
            break
    
    if not version_info:
        print(f"Version '{version_name}' does not exist for project '{project_name}'.")
        return False
    
    # Switch to the specified project and version
    try:
        # Check for uncommitted changes and back them up if needed
        check_for_uncommitted_changes()
        
        # Clear scripts and templates directories
        if os.path.exists(config.SCRIPTS_DIR):
            shutil.rmtree(config.SCRIPTS_DIR)
        if os.path.exists(config.TEMPLATES_DIR):
            shutil.rmtree(config.TEMPLATES_DIR)
        
        # Create directories if they don't exist
        os.makedirs(config.SCRIPTS_DIR, exist_ok=True)
        os.makedirs(config.TEMPLATES_DIR, exist_ok=True)
        
        # Extract version zip
        version_path = os.path.join(PROJECTS_DIR, project_name, version_info["filename"])
        with zipfile.ZipFile(version_path, "r") as zf:
            for file in zf.infolist():
                # Extract to either scripts or templates based on path
                if file.filename.startswith("scripts/"):
                    target_dir = ""
                elif file.filename.startswith("templates/"):
                    target_dir = ""
                else:
                    # Skip files that aren't in scripts or templates
                    continue
                
                zf.extract(file, target_dir)
        
        # Update metadata and tracking
        metadata["active_version"] = version_name
        update_project_metadata(project_name, metadata)
        set_current_project(project_name, version_name)
        
        print(f"Switched to project '{project_name}', version '{version_name}'.")
        return True
    except Exception as e:
        print(f"Error switching project: {e}")
        return False

def check_for_uncommitted_changes() -> Optional[str]:
    """Check if there are uncommitted changes in the working copy.
    
    Returns:
        Optional[str]: Backup filename if changes found and backed up, None otherwise
    """
    current_project, current_version = get_current_project()
    if not current_project or not current_version:
        return None
    
    # Get project metadata
    metadata = get_project_metadata(current_project)
    if not metadata:
        return None
    
    # Find current version info
    version_info = None
    for version in metadata["versions"]:
        if version["name"] == current_version:
            version_info = version
            break
    
    if not version_info:
        return None
    
    try:
        # Check if working copy differs from version
        version_path = os.path.join(PROJECTS_DIR, current_project, version_info["filename"])
        has_changes = False
        
        with zipfile.ZipFile(version_path, "r") as zf:
            # Check each file in the zip
            for file in zf.infolist():
                # Map zip paths to filesystem paths
                if file.filename.startswith("scripts/"):
                    fs_path = file.filename
                elif file.filename.startswith("templates/"):
                    fs_path = file.filename
                else:
                    continue
                
                # Check if file exists and content matches
                if os.path.exists(fs_path):
                    with open(fs_path, "rb") as f:
                        fs_content = f.read()
                    zip_content = zf.read(file.filename)
                    if fs_content != zip_content:
                        has_changes = True
                        break
                else:
                    # File missing from filesystem
                    has_changes = True
                    break
            
            # Check for new files in filesystem not in zip
            for root, _, files in os.walk(config.SCRIPTS_DIR):
                for file in files:
                    rel_path = os.path.join(root, file).replace("\\", "/")
                    if rel_path not in [zi.filename for zi in zf.infolist()]:
                        has_changes = True
                        break
            
            if not has_changes:
                for root, _, files in os.walk(config.TEMPLATES_DIR):
                    for file in files:
                        rel_path = os.path.join(root, file).replace("\\", "/")
                        if rel_path not in [zi.filename for zi in zf.infolist()]:
                            has_changes = True
                            break
        
        if has_changes:
            # Backup changes to a timestamped zip
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{current_project}_{current_version}_backup_{timestamp}.zip"
            backup_path = os.path.join(PROJECTS_DIR, current_project, backup_name)
            
            with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
                if os.path.exists(config.SCRIPTS_DIR):
                    for root, _, files in os.walk(config.SCRIPTS_DIR):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(config.SCRIPTS_DIR))
                            zf.write(file_path, arcname)
                
                if os.path.exists(config.TEMPLATES_DIR):
                    for root, _, files in os.walk(config.TEMPLATES_DIR):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(config.TEMPLATES_DIR))
                            zf.write(file_path, arcname)
            
            print(f"Uncommitted changes found. Backed up to '{backup_name}'.")
            return backup_name
    
    except Exception as e:
        print(f"Error checking for uncommitted changes: {e}")
    
    return None

def switch_version(version_name: str) -> bool:
    """Switch to a specific version within the current project.
    
    Args:
        version_name (str): Version name
        
    Returns:
        bool: Success or failure
    """
    current_project, _ = get_current_project()
    if not current_project:
        print("No active project.")
        return False
    
    return switch_project(current_project, version_name)

def export_version(project_name: str, version_name: str, output_path: str) -> bool:
    """Export a version to a standalone zip file.
    
    Args:
        project_name (str): Project name
        version_name (str): Version name
        output_path (str): Output path for the zip file
        
    Returns:
        bool: Success or failure
    """
    # Validate project exists
    metadata = get_project_metadata(project_name)
    if not metadata:
        print(f"Project '{project_name}' does not exist.")
        return False
    
    # Validate version exists
    version_info = None
    for version in metadata["versions"]:
        if version["name"] == version_name:
            version_info = version
            break
    
    if not version_info:
        print(f"Version '{version_name}' does not exist for project '{project_name}'.")
        return False
    
    try:
        # Copy version zip to output path
        version_path = os.path.join(PROJECTS_DIR, project_name, version_info["filename"])
        shutil.copy2(version_path, output_path)
        
        print(f"Version '{version_name}' of project '{project_name}' exported to '{output_path}'.")
        return True
    except Exception as e:
        print(f"Error exporting version: {e}")
        return False

def describe_project(project_name: str = "") -> bool:
    """Show details of a project.
    
    Args:
        project_name (str, optional): Project name (defaults to current project)
        
    Returns:
        bool: Success or failure
    """
    if not project_name:
        project_name, current_version = get_current_project()
        if not project_name:
            print("No active project.")
            return False
    
    metadata = get_project_metadata(project_name)
    if not metadata:
        print(f"Project '{project_name}' does not exist.")
        return False
    
    # Print project details
    print(f"\nProject: {metadata['name']}")
    print(f"Description: {metadata.get('description', '')}")
    print(f"Created: {metadata.get('created', 'Unknown')}")
    print(f"Active Version: {metadata.get('active_version', 'None')}")
    
    # Print versions
    print("\nVersions:")
    if not metadata["versions"]:
        print("  No versions")
    else:
        for version in metadata["versions"]:
            active = " (active)" if version["name"] == metadata.get("active_version") else ""
            print(f"  {version['name']}{active}: {version.get('description', '')}")
            print(f"    Created: {version.get('timestamp', 'Unknown')}")
    
    return True

def list_versions(project_name: str = "") -> List[Dict[str, Any]]:
    """List all versions for a project.
    
    Args:
        project_name (str, optional): Project name (defaults to current project)
        
    Returns:
        List[Dict[str, Any]]: List of version metadata
    """
    if not project_name:
        project_name, _ = get_current_project()
        if not project_name:
            print("No active project.")
            return []
    
    metadata = get_project_metadata(project_name)
    if not metadata:
        print(f"Project '{project_name}' does not exist.")
        return []
    
    return metadata.get("versions", [])