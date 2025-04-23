# engine/client/client_network.py
"""Client network functions"""
import json
import socket
import time
from engine.core import config

def connect(client):
    """Connect to the server
    
    Args:
        client (dict): Client state
        
    Returns:
        bool: True if connected, False otherwise
    """
    try:
        # Use client-specific server host and port
        print(f"Connecting to server at {client['server_host']}:{client['server_port']}...")
        client['socket'].connect((client['server_host'], client['server_port']))
        return True
    except ConnectionRefusedError:
        print("Connection refused. The server might not be running.")
        return False
    except socket.gaierror:
        print(f"Network error: Address '{client['server_host']}' is invalid or not reachable.")
        return False
    except TimeoutError:
        print("Connection timed out. Check network connectivity and server address.")
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
    except socket.error as e:
        print(f"Network error while sending command: {e}")
        print("You may have been disconnected from the server.")
        return False
    except Exception as e:
        print(f"Error sending command: {e}")
        return False

def process_command(client, ordered_command):
    """Process a single command
    
    Args:
        client (dict): Client state
        ordered_command (dict): Command with sequence number
    """
    try:
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
    except Exception as e:
        print(f"Error processing command: {e}")

def listen_for_broadcasts(client):
    """Listen for broadcasts from the server
    
    Args:
        client (dict): Client state
    """
    try:
        # Buffer for incomplete messages
        buffer = b""
        
        while True:
            try:
                data = client['socket'].recv(config.BUFFER_SIZE)
                if not data:
                    print("\nDisconnected from server")
                    break
                
                # Add to buffer
                buffer += data
                
                try:
                    # Try to parse the buffer as JSON
                    message = json.loads(buffer.decode('utf-8'))
                    buffer = b""  # Clear buffer after successful parse
                    
                    # Check if it's a history batch
                    if isinstance(message, dict) and message.get("type") == "history_batch":
                        print(f"Received history batch with {len(message.get('commands', []))} commands")
                        # Process all commands in the batch
                        for cmd in message.get("commands", []):
                            process_command(client, cmd)
                    else:
                        # It's a regular command
                        process_command(client, message)
                    
                except json.JSONDecodeError:
                    # Incomplete message, wait for more data
                    continue
                
            except json.JSONDecodeError as e:
                print(f"Error decoding message: {e}")
                buffer = b""  # Reset buffer on error
            except socket.error as e:
                print(f"\nNetwork error: {e}")
                print("Disconnected from server.")
                break
                
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