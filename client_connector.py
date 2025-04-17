"""
JC-CLI Client Connector: Connects to thin server for multiplayer games
"""
import socket
import threading
import json
import time

class ClientConnector:
    def __init__(self, engine):
        """Initialize client connector"""
        self.engine = engine
        self.socket = None
        self.connected = False
        self.receive_thread = None
    
    def connect(self, server_address):
        """
        Connect to the server
        
        Args:
            server_address (str): Server address in format "host:port"
            
        Returns:
            bool: Success status
        """
        if self.connected:
            return True
        
        try:
            # Parse address
            host, port = server_address.split(":")
            port = int(port)
            
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            
            # Mark as connected
            self.connected = True
            
            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            print(f"Connected to server: {server_address}")
            return True
            
        except Exception as e:
            print(f"Connection error: {e}")
            self.connected = False
            
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
                
            return False
    
    def disconnect(self):
        """Disconnect from server"""
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
    
    def _receive_loop(self):
        """Continuously receive commands from server"""
        buffer = b""
        
        while self.connected:
            try:
                # Receive data
                data = self.socket.recv(4096)
                if not data:
                    # Connection closed
                    self.disconnect()
                    break
                
                # Add to buffer
                buffer += data
                
                # Process complete JSON objects
                while True:
                    try:
                        # Try to parse as JSON
                        command = json.loads(buffer.decode("utf-8"))
                        
                        # Process command
                        self._process_command(command)
                        
                        # Clear buffer after successful processing
                        buffer = b""
                        break
                    except json.JSONDecodeError:
                        # Incomplete JSON, wait for more data
                        break
                    except Exception as e:
                        print(f"Error processing command: {e}")
                        buffer = b""  # Clear buffer on error
                        break
                
            except Exception as e:
                if self.connected:  # Only show error if we think we're connected
                    print(f"Receive error: {e}")
                    self.disconnect()
                    break
                    
            time.sleep(0.01)  # Prevent CPU spinning
    
    def _process_command(self, command):
        """
        Process a command received from server
        
        Args:
            command (dict): Indexed command from server
        """
        if not isinstance(command, dict) or "index" not in command:
            return
        
        # Add to command sequencer
        self.engine.command_sequencer.add_command(command)
    
    def send_command(self, command_text):
        """
        Send a command to the server
        
        Args:
            command_text (str): Command to send
            
        Returns:
            bool: Success status
        """
        if not self.connected or not self.socket:
            return False
        
        try:
            # Send as raw text - server will assign index
            self.socket.sendall(command_text.encode("utf-8"))
            return True
        except Exception as e:
            print(f"Send error: {e}")
            self.disconnect()
            return False