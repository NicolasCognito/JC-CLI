#!/usr/bin/env python3
"""
JC-CLI Thin Server - Network-Enabled Version
A minimal coordinator that receives commands, assigns sequence numbers,
and broadcasts them to all connected clients over a local network.
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
    
    # Print network information
    print(f"\n===== JC-CLI SERVER NETWORK INFORMATION =====")
    print(f"Server listening on port {config.SERVER_PORT}")
    print("\nClients can connect using any of these addresses:")
    
    if server['local_ips']:
        for ip in server['local_ips']:
            print(f"* {ip}:{config.SERVER_PORT}")
    else:
        print(f"* localhost:{config.SERVER_PORT} (this machine only)")
        
    print("\nTo connect a remote client, use:")
    print(f"python jc-cli.py join-session {os.path.basename(server['session_dir'])} <client-name> <SERVER_IP>")
    print("===============================================\n")
    
    # Start listening for connections
    listen_for_connections(server)

def listen_for_connections(server):
    """Listen for incoming client connections
    
    Args:
        server (dict): Server state
    """
    server['socket'].listen(5)
    
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