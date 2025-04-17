"""
JC-CLI Thin Server: Minimal server for command indexing and distribution
"""
import socket
import threading
import json
import time

class ThinServer:
    def __init__(self, engine, port=8080):
        """Initialize thin server"""
        self.engine = engine
        self.port = port
        self.clients = []
        self.next_index = 0
        self.socket = None
        self.running = False
        
        # Load next index from history.json
        self._load_next_index()
    
    def _load_next_index(self):
        """Load next index from history"""
        try:
            with open("history.json", "r") as f:
                history = json.load(f)
            
            # Find highest index
            highest_index = -1
            for turn in history.get("history", {}).get("turns", []):
                for action in turn.get("actions", []):
                    highest_index = max(highest_index, action.get("index", -1))
                for post in turn.get("postprocessing", []):
                    highest_index = max(highest_index, post.get("index", -1))
            
            # Next index is one higher
            self.next_index = highest_index + 1
            
        except (FileNotFoundError, json.JSONDecodeError):
            # Start from 0 if no history
            self.next_index = 0
    
    def start(self):
        """Start the server in a separate thread"""
        if self.running:
            return
        
        self.running = True
        server_thread = threading.Thread(target=self._run_server)
        server_thread.daemon = True  # Allow program to exit even if thread is running
        server_thread.start()
    
    def _run_server(self):
        """Run the server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(("0.0.0.0", self.port))
            self.socket.listen(5)
            
            print(f"Server running on port {self.port}")
            
            while self.running:
                try:
                    client_socket, addr = self.socket.accept()
                    print(f"New connection from {addr}")
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    print(f"Error accepting connection: {e}")
                    time.sleep(0.1)
            
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            if self.socket:
                self.socket.close()
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
    
    def handle_client(self, client_socket, addr):
        """
        Handle a client connection
        
        Args:
            client_socket: Socket for client communication
            addr: Client address
        """
        try:
            # Add to client list
            self.clients.append(client_socket)
            
            # Receive and process commands
            while self.running:
                try:
                    # Receive command
                    data = client_socket.recv(4096)
                    if not data:
                        break  # Client disconnected
                    
                    # Decode command
                    command_text = data.decode("utf-8").strip()
                    
                    # Process and broadcast
                    self.receive_command(command_text, client_socket)
                    
                except Exception as e:
                    print(f"Error handling client {addr}: {e}")
                    break
                    
        except Exception as e:
            print(f"Client handling error: {e}")
        finally:
            # Remove from client list and close
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            
            try:
                client_socket.close()
            except:
                pass
            
            print(f"Connection closed: {addr}")
    
    def receive_command(self, command_text, source_client=None):
        """
        Process a command from a client
        
        Args:
            command_text (str): Command text
            source_client: Socket of source client
        """
        if not command_text:
            return
        
        # Assign index
        indexed_command = self.assign_index(command_text)
        
        # Broadcast to all clients
        self.broadcast_command(indexed_command, source_client)
        
        # Process locally
        self.engine.command_sequencer.add_command(indexed_command)
    
    def assign_index(self, command_text):
        """
        Assign sequential index to command
        
        Args:
            command_text (str): Command text
            
        Returns:
            dict: Indexed command
        """
        # Extract player from command
        parts = command_text.strip().split()
        player = parts[0] if parts else "sys"
        
        # Create indexed command
        indexed_command = {
            "index": self.next_index,
            "player": player,
            "command": command_text,
            "applied": False
        }
        
        # Increment index for next command
        self.next_index += 1
        
        return indexed_command
    
    def broadcast_command(self, indexed_command, exclude_client=None):
        """
        Broadcast command to all clients
        
        Args:
            indexed_command (dict): Command to broadcast
            exclude_client: Client to exclude (usually source)
        """
        # Encode command
        command_json = json.dumps(indexed_command)
        command_bytes = command_json.encode("utf-8")
        
        # Broadcast to all clients except sender
        for client in self.clients:
            if client != exclude_client:
                try:
                    client.sendall(command_bytes)
                except Exception as e:
                    print(f"Error sending to client: {e}")
                    # Will be removed on next receive attempt