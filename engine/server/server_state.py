# engine/server/server_state.py
"""Server state management module"""
import os
import json
import socket
import threading
from engine.core import config

def get_local_ip_addresses():
    """Get all local IP addresses of this machine
    
    Returns:
        list: List of IP addresses
    """
    local_ips = []
    try:
        # Try connecting to an external server to determine route
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # This doesn't actually create a connection
            s.connect(('8.8.8.8', 1))
            local_ip = s.getsockname()[0]
            local_ips.append(local_ip)
        except Exception:
            pass
        finally:
            s.close()
            
        # If that didn't work, try hostname resolution
        if not local_ips:
            hostname = socket.gethostname()
            ip_list = socket.getaddrinfo(hostname, None)
            
            for ip_info in ip_list:
                ip = ip_info[4][0]
                # Only include IPv4 addresses that aren't localhost
                if not ip.startswith('127.') and ':' not in ip:
                    local_ips.append(ip)
                
    except Exception as e:
        print(f"Warning: Could not determine local IP addresses: {e}")
    
    return local_ips

def initialize(session_dir=None):
    """Initialize server state
    
    Args:
        session_dir (str, optional): Session directory
        
    Returns:
        dict: Server state or None if initialization failed
    """
    try:
        # Set session directory
        session_dir = session_dir or os.getcwd()
        history_path = os.path.join(session_dir, config.HISTORY_FILE)
        
        # Create server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((config.SERVER_HOST, config.SERVER_PORT))
        
        # Initialize history file if it doesn't exist
        if not os.path.exists(history_path):
            with open(history_path, 'w') as f:
                json.dump([], f)
        
        # Get initial sequence number
        sequence_number = get_highest_sequence(history_path)
        
        # Get local IP addresses for display
        local_ips = get_local_ip_addresses()
        
        # Return server state
        return {
            'socket': server_socket,
            'clients': [],
            'lock': threading.Lock(),
            'session_dir': session_dir,
            'history_path': history_path,
            'sequence_number': sequence_number,
            'local_ips': local_ips
        }
    except Exception as e:
        print(f"Error initializing server: {e}")
        return None

def get_highest_sequence(history_path):
    """Get the highest sequence number from history file
    
    Args:
        history_path (str): Path to history file
        
    Returns:
        int: Highest sequence number
    """
    try:
        with open(history_path, 'r') as f:
            history = json.load(f)
        
        if not history:
            return 0
        
        # Find highest sequence number
        highest_seq = max(cmd.get("seq", 0) for cmd in history)
        return highest_seq
        
    except Exception as e:
        print(f"Error reading history file: {e}")
        return 0