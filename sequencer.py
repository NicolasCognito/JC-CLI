#!/usr/bin/env python3
"""
JC-CLI Sequencer - Event-Based Version
Watches commands.json file using a file system watcher and executes
unprocessed commands in sequence order without continuous polling.
"""
import json
import os
import subprocess
import sys
import argparse
import shlex
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class CommandFileHandler(FileSystemEventHandler):
    """Handles file system events for the commands.json file"""
    
    def __init__(self, sequencer):
        self.sequencer = sequencer
        self.last_processed_time = time.time()
        # Debounce window to avoid multiple events for a single file write
        self.debounce_window = 0.1  

    def on_modified(self, event):
        """Called when commands.json is modified"""
        if not event.is_directory and os.path.basename(event.src_path) == "commands.json":
            # Debounce to avoid processing the same change multiple times
            current_time = time.time()
            if current_time - self.last_processed_time > self.debounce_window:
                self.last_processed_time = current_time
                # Process next command in a separate thread to keep watcher responsive
                threading.Thread(target=self.sequencer.process_next_command).start()

class EventBasedSequencer:
    """Event-based implementation of the JC-CLI sequencer"""
    
    def __init__(self, client_dir=None):
        """Initialize the sequencer
        
        Args:
            client_dir (str, optional): Directory for client data
        """
        # Set up paths
        self.client_dir = client_dir or os.getcwd()
        self.data_dir = os.path.join(self.client_dir, "data")
        self.commands_file = os.path.join(self.data_dir, "commands.json")
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize commands file if it doesn't exist
        if not os.path.exists(self.commands_file):
            with open(self.commands_file, 'w') as f:
                json.dump([], f)
        
        # Orchestrator path (same directory as this script)
        self.orchestrator_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "orchestrator.py"
        )
        
        # Processing lock to avoid race conditions
        self.processing_lock = threading.Lock()
        
        # Observer for file system events
        self.observer = Observer()
        self.event_handler = CommandFileHandler(self)
        
        print(f"Event-based sequencer initialized. Client dir: {self.client_dir}")
        
    def start(self):
        """Start the file system observer"""
        self.observer.schedule(self.event_handler, self.data_dir, recursive=False)
        self.observer.start()
        print(f"Watching for changes in {self.commands_file}")
        
        # Process any commands that might already be in the file
        self.process_next_command()
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
            
    def stop(self):
        """Stop the file system observer"""
        print("Stopping sequencer...")
        self.observer.stop()
        self.observer.join()
        print("Sequencer stopped.")
            
    def process_next_command(self):
        """Process the next unprocessed command in sequence"""
        # Use a lock to prevent concurrent processing
        if not self.processing_lock.acquire(blocking=False):
            return
            
        try:
            # Read commands
            with open(self.commands_file, 'r') as f:
                commands = json.load(f)
            
            # Find next unprocessed command in sequence
            next_cmd = None
            next_index = None
            
            # Find the last processed command sequence number
            last_seq = 0
            for cmd in commands:
                if cmd.get("processed", False):
                    last_seq = max(last_seq, cmd.get("seq", 0))
            
            # Look for the next command in sequence
            next_seq = last_seq + 1
            for i, cmd in enumerate(commands):
                if cmd.get("seq") == next_seq and not cmd.get("processed", False):
                    next_cmd = cmd
                    next_index = i
                    break
            
            # Process command if found
            if next_cmd:
                # Mark as processed immediately
                commands[next_index]["processed"] = True
                with open(self.commands_file, 'w') as f:
                    json.dump(commands, f, indent=2)
                
                # Get command text and username
                cmd_text = next_cmd['command']['text']
                username = next_cmd['command']['username']
                
                # Parse command to get the actual command and args
                cmd_parts = shlex.split(cmd_text)
                cmd_name = cmd_parts[0] if cmd_parts else ""
                cmd_args = cmd_parts[1:] if len(cmd_parts) > 1 else []
                
                # Log command execution BEFORE running it
                print(f"[Command:{next_seq}] Processing '{cmd_name}' from {username}")
                if cmd_args:
                    print(f"[Command:{next_seq}] Args: {cmd_args}")
                
                # Execute the command
                result = subprocess.run(
                    [sys.executable, self.orchestrator_path, cmd_text, username],
                    cwd=self.client_dir
                )
                
                if result.returncode != 0:
                    print(f"[Command:{next_seq}] '{cmd_name}' failed with code {result.returncode}")
                
                # Process next command if available (recursive chain, but each in its own thread)
                # This ensures commands are processed in sequence without waiting for polling
                self.process_next_command()
        except Exception as e:
            print(f"Error processing command: {e}")
        finally:
            self.processing_lock.release()

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="JC-CLI Event-Based Sequencer")
    parser.add_argument("--dir", help="Client directory to use", default=None)
    args = parser.parse_args()
    
    # Create and start sequencer
    sequencer = EventBasedSequencer(client_dir=args.dir)
    sequencer.start()

if __name__ == "__main__":
    main()