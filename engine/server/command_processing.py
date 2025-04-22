# engine/server/command_processing.py
"""Command processing module"""
import json
import time
import os

def process_command(server, command):
    """Assign sequence number and broadcast to all clients
    
    Args:
        server (dict): Server state
        command (dict): Command data
    """
    with server['lock']:
        # Assign sequence number
        server['sequence_number'] += 1
        
        # Create ordered command
        ordered_command = {
            "seq": server['sequence_number'],
            "timestamp": time.time(),
            "command": command
        }
        
        # Broadcast to all clients
        broadcast(server, ordered_command)
        
        # Append to history file
        append_to_history(server, ordered_command)
        
        # Print command info
        username = command.get("username", "unknown")
        cmd_text = command.get("text", "")
        print(f"[{server['sequence_number']}] {username}: {cmd_text}")

def send_history(server, client_socket):
    """Send command history to a new client
    
    Args:
        server (dict): Server state
        client_socket (socket): Client socket
    """
    try:
        if os.path.exists(server['history_path']):
            with open(server['history_path'], 'r') as f:
                history = json.load(f)
            
            print(f"Sending {len(history)} historical commands to new client")
            
            # Send each command in order
            for cmd in history:
                # Convert to bytes and send
                cmd_bytes = json.dumps(cmd).encode('utf-8')
                client_socket.sendall(cmd_bytes)
                time.sleep(0.05)  # Small delay to prevent flooding
    except Exception as e:
        print(f"Error sending history: {e}")

def append_to_history(server, ordered_command):
    """Append command to history file
    
    Args:
        server (dict): Server state
        ordered_command (dict): Command with sequence number
    """
    try:
        # Read existing history
        if os.path.exists(server['history_path']):
            with open(server['history_path'], 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        # Append new command
        history.append(ordered_command)
        
        # Write back to file
        with open(server['history_path'], 'w') as f:
            json.dump(history, f, indent=2)
            
    except Exception as e:
        print(f"Error appending to history file: {e}")

def broadcast(server, ordered_command):
    """Send the command to all connected clients
    
    Args:
        server (dict): Server state
        ordered_command (dict): Command with sequence number
    """
    message = json.dumps(ordered_command).encode('utf-8')
    
    # List of clients to remove (in case of errors)
    dead_clients = []
    
    for client in server['clients']:
        try:
            client.sendall(message)
        except Exception:
            dead_clients.append(client)
    
    # Remove any clients that failed
    for client in dead_clients:
        if client in server['clients']:
            server['clients'].remove(client)
            client.close()