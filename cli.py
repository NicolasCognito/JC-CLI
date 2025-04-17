"""
JC-CLI Command Line Interface: Processes user input
"""
import sys
import threading
import time

class CLI:
    def __init__(self, engine):
        """Initialize CLI"""
        self.engine = engine
        self.running = False
        self.current_player = None
        
        # List of local commands that don't get sent to the engine
        self.local_commands = {
            "help": self._help_command,
            "exit": self._exit_command,
            "quit": self._exit_command,
            "view": self._view_command,
            "clear": self._clear_command,
            "whoami": self._whoami_command
        }
    
    def start(self):
        """Start the CLI input loop"""
        self.running = True
        
        # Start in a separate thread so engine can process commands
        input_thread = threading.Thread(target=self._input_loop)
        input_thread.daemon = True
        input_thread.start()
        
        # Show the initial game state
        self.engine.view.update()
        
        # Block main thread to keep program running
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.running = False
    
    def _input_loop(self):
        """Main input loop for CLI"""
        print("JC-CLI started. Type 'help' for commands.")
        
        while self.running:
            try:
                # Prompt for input
                command = input(f"{self.current_player or 'CLI'}> ").strip()
                
                if not command:
                    continue
                
                # Check if it's a local command
                cmd_parts = command.split()
                if cmd_parts[0] in self.local_commands:
                    # Execute local command
                    self.local_commands[cmd_parts[0]](cmd_parts[1:])
                else:
                    # If no player prefix and current_player is set, add it
                    if (
                        self.current_player and 
                        not any(command.startswith(p) for p in ["plr", "player", "sys"])
                    ):
                        command = f"{self.current_player} {command}"
                    
                    # Send to engine
                    self.engine.process_command(command)
            
            except (EOFError, KeyboardInterrupt):
                # Exit on Ctrl+D or Ctrl+C
                self.running = False
                break
                
            except Exception as e:
                print(f"Error processing command: {e}")
    
    def _help_command(self, args=None):
        """Display help information"""
        print("\nJC-CLI Commands:")
        print("  help               - Show this help")
        print("  exit, quit         - Exit the application")
        print("  view <player_id>   - Set view to a specific player")
        print("  clear              - Clear the screen")
        print("  whoami             - Show current player view")
        print("\nGame Commands (automatically prefixed with current player):")
        print("  mv <src_slot> <dst_slot>    - Move resource between slots")
        print("  use <card_id>               - Use a card")
        print("  endturn                     - End current player's turn")
        print("\nSystem Commands (require 'sys' prefix):")
        print("  sys init <plr1> <plr2> ...  - Initialize game with players")
        print("  sys deck <card1> <card2>... - Set up deck")
        print("  sys draw <plr> <card>       - Draw card for player")
        print("\nNote: Commands can also be prefixed with player ID manually:")
        print("  plr1 mv slot_1 slot_3")
    
    def _exit_command(self, args=None):
        """Exit the application"""
        print("Exiting JC-CLI...")
        self.running = False
        sys.exit(0)
    
    def _view_command(self, args):
        """
        Set view to a specific player
        
        Args:
            args (list): Command arguments
        """
        if not args:
            print("Usage: view <player_id>")
            return
        
        player_id = args[0]
        self.current_player = player_id
        self.engine.view.set_current_player(player_id)
        print(f"View set to {player_id}")
    
    def _clear_command(self, args=None):
        """Clear the screen"""
        # Update view (which clears screen)
        self.engine.view.update()
    
    def _whoami_command(self, args=None):
        """Show current player view"""
        if self.current_player:
            print(f"Current view: {self.current_player}")
        else:
            print("No player view selected. Use 'view <player_id>' to set.")