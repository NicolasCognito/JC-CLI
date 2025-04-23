# engine/server/client_handling.py
"""Client handling module"""
import json
from engine.core import config
from engine.server import command_processing

def handle_client(server, client_socket, addr):
    """Handle messages from a client
    
    Args:
        server (dict): Server state
        client_socket (socket): Client socket
        addr (tuple): Client address
    """
    try:
        while True:
            data = client_socket.recv(config.BUFFER_SIZE)
            if not data:
                break
                
            # Process command
            try:
                # Parse the command JSON
                command_json = json.loads(data.decode('utf-8'))
                command_processing.process_command(server, command_json)
            except json.JSONDecodeError as e:
                print(f"Error decoding command from {addr}: {e}")
            except Exception as e:
                print(f"Error processing command from {addr}: {e}")
                
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        if client_socket in server['clients']:
            server['clients'].remove(client_socket)
        client_socket.close()
        print(f"Connection closed: {addr}")