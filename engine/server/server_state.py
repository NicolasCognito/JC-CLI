# engine/server/server_state.py
"""Server state management module"""
import os
import json
import socket
import threading
import subprocess
import platform
from . import config

def get_local_ip_addresses():
    """Get all local IP addresses of this machine including virtual ones like ZeroTier
    
    Returns:
        list: List of IP addresses
    """
    local_ips = set()  # Use a set to avoid duplicates
    
    try:
        # Method 1: Try hostname resolution which can detect virtual IPs
        hostname = socket.gethostname()
        try:
            # This approach can find virtual network adapters
            ip_addresses = socket.gethostbyname_ex(hostname)[2]
            for ip in ip_addresses:
                if not ip.startswith('127.') and ':' not in ip:
                    local_ips.add(ip)
        except socket.gaierror:
            pass
            
        # Method 2: Try connecting to an external server to determine primary route
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # This doesn't actually create a connection
            s.connect(('8.8.8.8', 1))
            local_ip = s.getsockname()[0]
            if not local_ip.startswith('127.'):
                local_ips.add(local_ip)
        except Exception:
            pass
        finally:
            s.close()
        
        # Method 3: For systems where ZeroTier IPs still aren't detected,
        # try to get all network interfaces using platform-specific commands
        system = platform.system()
        if system == "Windows":
            try:
                # Use ipconfig on Windows
                output = subprocess.check_output("ipconfig", shell=True).decode('utf-8')
                for line in output.split('\n'):
                    if "IPv4 Address" in line:
                        ip = line.split(':')[-1].strip()
                        if ip and not ip.startswith('127.'):
                            local_ips.add(ip)
            except Exception:
                pass
        elif system in ["Linux", "Darwin"]:  # Linux or macOS
            try:
                # Use ifconfig on Linux/Mac
                cmd = "ifconfig" if system == "Darwin" else "ip addr"
                output = subprocess.check_output(cmd, shell=True).decode('utf-8')
                import re
                # Simple regex to extract IPv4 addresses
                pattern = r'inet (?:addr:)?(\d+\.\d+\.\d+\.\d+)'
                ips = re.findall(pattern, output)
                for ip in ips:
                    if not ip.startswith('127.'):
                        local_ips.add(ip)
            except Exception:
                pass
                
    except Exception as e:
        print(f"Warning: Could not determine all local IP addresses: {e}")
    
    return list(local_ips)  # Convert set back to list

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