# engine/client/sequencer_control.py
"""Sequencer process management"""
import subprocess
import sys
import os
from engine.core import config

def start_sequencer(client):
    """Start the sequencer as a separate process
    
    Args:
        client (dict): Client state
        
    Returns:
        bool: True if started, False otherwise
    """
    try:
        # Prepare sequencer command with client directory
        sequencer_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "sequencer.py"
        )
        
        sequencer_cmd = [
            sys.executable, 
            sequencer_path, 
            "--dir", client['client_dir']
        ]
        
        print(f"Starting sequencer: {' '.join(sequencer_cmd)}")
        
        # Start sequencer process
        client['sequencer_process'] = subprocess.Popen(sequencer_cmd)
        
        return True
    except Exception as e:
        print(f"Error starting sequencer: {e}")
        return False

def cleanup(client):
    """Clean up resources when exiting
    
    Args:
        client (dict): Client state
    """
    if client.get('sequencer_process'):
        print("Terminating sequencer process...")
        try:
            client['sequencer_process'].terminate()
            client['sequencer_process'].wait(timeout=2)
        except:
            # Force kill if termination fails
            try:
                client['sequencer_process'].kill()
            except:
                pass