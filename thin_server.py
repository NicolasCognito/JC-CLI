#!/usr/bin/env python3
"""
JC-CLI Thin Server - Refactored Version
A minimal coordinator that receives commands, assigns sequence numbers,
and broadcasts them to all connected clients.
"""
import socket
import json
import threading
import argparse
import os
import sys

# Import modules from engine
from engine.core import config
from engine.server import server_state
from engine.server import command_processing
from engine.server import client_handling

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="JC-CLI Thin Server")
    parser.add_argument("--session-dir", help="Session directory to use", default=None)
    args = parser.parse_args()
    
    # Initialize server state
    server = server_state.initialize(args.session_dir)
    if not server:
        return
    
    # Start listening for connections
    listen_for_connections(server)

def listen_for_connections(server):
    """Listen for incoming client connections
    
    Args:
        server (dict): Server state
    """
    server['socket'].listen(5)
    print(f"Server listening on {config.SERVER_HOST}:{config.SERVER_PORT}")
    
    try:
        while True:
            client_socket, addr = server['socket'].accept()
            print(f"New connection from {addr}")
            
            # Start thread to handle client
            client_thread = threading.Thread(
                target=client_handling.handle_client,
                args=(server, client_socket, addr)
            )
            client_thread.daemon = True
            client_thread.start()
            
            server['clients'].append(client_socket)
            
            # Send history to new client
            command_processing.send_history(server, client_socket)
            
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server['socket'].close()

if __name__ == "__main__":
    main()