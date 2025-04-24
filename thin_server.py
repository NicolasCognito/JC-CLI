#!/usr/bin/env python3
"""
JC-CLI Thin Server – updated for paged-history protocol
"""

import argparse, os, sys, threading, socket
from .   import config
from engine.server import server_state, client_handling, command_processing

# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(description="JC-CLI Thin Server")
    parser.add_argument("--session-dir", help="Session directory", default=None)
    args = parser.parse_args()

    server = server_state.initialize(args.session_dir)
    if not server:
        return

    print("\n===== JC-CLI SERVER NETWORK INFORMATION =====")
    print(f"Server listening on port {config.SERVER_PORT}")
    for ip in (server["local_ips"] or ["localhost"]):
        print(f"* {ip}:{config.SERVER_PORT}")
    print("=============================================\n")

    listen_for_connections(server)

# --------------------------------------------------------------------------- #
def listen_for_connections(server):
    """Accept clients and push snapshot + history-meta header."""
    server["socket"].listen(5)

    try:
        while True:
            client_sock, addr = server["socket"].accept()
            print(f"New connection from {addr}")

            # 1) push client code snapshot
            command_processing.send_snapshot(server, client_sock)
            # 2) push only history metadata (page count / highest_seq)
            command_processing.send_history_meta(server, client_sock)

            # hand the socket to a dedicated receive thread
            t = threading.Thread(
                target=client_handling.handle_client,
                args=(server, client_sock, addr),
                daemon=True,
            )
            t.start()
            server["clients"].append(client_sock)

    except KeyboardInterrupt:
        print("\nShutting down server.")
    finally:
        server["socket"].close()

# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
