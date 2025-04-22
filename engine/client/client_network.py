# engine/client/client_network.py
"""Client network functions"""
import json
import socket
from engine.core import config

def connect(client):
    """Connect to the server
    
    Args:
        client (dict): Client state
        
    Returns:
        bool: True if connected, False otherwise
    """
    try:
        client['socket'].connect((config.SERVER_HOST, config.SERVER_PORT))
        return True
    except ConnectionRefusedError:
        return False
    except Exception as e:
        print(f"Connection error: {e}")
        return False

def disconnect(client):
    """Disconnect from the server
    
    Args:
        client (dict): Client state
    """
    try:
        client['socket'].close()
    except Exception:
        pass

def send_command(client, command_text):
    """Send command to the server
    
    Args:
        client (dict): Client state
        command_text (str): Command text to send
        
    Returns:
        bool: True if sent, False otherwise
    """
    try:
        # Create command with username
        command = {
            "username": client['username'],
            "text": command_text
        }
        # Send as JSON
        client['socket'].sendall(json.dumps(command).encode('utf-8'))
        return True
    except Exception as e:
        print(f"Error sending command: {e}")
        return False

def listen_for_broadcasts(client):
    """Listen for broadcasts from the server
    
    Args:
        client (dict): Client state
    """
    try:
        while True:
            data = client['socket'].recv(config.BUFFER_SIZE)
            if not data:
                print("Disconnected from server")
                break
            
            try:
                # Parse the ordered command
                ordered_command = json.loads(data.decode('utf-8'))
                
                # Append to commands file
                append_command(client, ordered_command)
                
                # Display for user
                seq = ordered_command["seq"]
                username = ordered_command["command"]["username"]
                cmd_text = ordered_command["command"]["text"]
                
                # Highlight own messages
                if username == client['username']:
                    print(f"[{seq}] You: {cmd_text}")
                else:
                    print(f"[{seq}] {username}: {cmd_text}")
                
            except json.JSONDecodeError as e:
                print(f"Error decoding message: {e}")
    except Exception as e:
        print(f"Error while listening for broadcasts: {e}")

def append_command(client, ordered_command):
    """Append the received command to the commands file
    
    Args:
        client (dict): Client state
        ordered_command (dict): Command with sequence number
    """
    try:
        # Read existing commands
        with open(client['commands_path'], 'r') as f:
            commands = json.load(f)
        
        # Append new command
        commands.append(ordered_command)
        
        # Write back to file
        with open(client['commands_path'], 'w') as f:
            json.dump(commands, f, indent=2)
            
    except Exception as e:
        print(f"Error appending to commands file: {e}")