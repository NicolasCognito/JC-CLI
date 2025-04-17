"""
JC-CLI Lua Bridge: Interface between Python and Lua
"""
import lupa
from lupa import LuaRuntime
import json

class LuaBridge:
    def __init__(self):
        """Initialize Lua runtime environment"""
        # Create Lua runtime
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        
        # Load helper functions
        self._load_helpers()
    
    def _load_helpers(self):
        """Load Lua helper utilities"""
        # Create Python-to-Lua JSON bridge
        self.lua.globals()["py_json"] = {
            "encode": lambda obj: json.dumps(obj),
            "decode": lambda str: json.loads(str)
        }
        
        # Load basic utilities
        self.lua.execute('''
            -- Helper functions for Lua scripts
            function print_debug(...)
                local result = ""
                for i, v in ipairs({...}) do
                    result = result .. tostring(v) .. "\\t"
                end
                py.callback(result)
            end
            
            -- JSON handling using Python's json module
            json = {}
            json.encode = py_json.encode
            json.decode = py_json.decode
            
            -- Expose completion signal function
            function complete()
                py.command_complete()
            end
        ''')
    
    def execute_command(self, parsed_command):
        """
        Execute a command using the appropriate Lua script
        
        Args:
            parsed_command (dict): Parsed command with script_path
            
        Returns:
            bool: Success status
        """
        if not parsed_command or "script_path" not in parsed_command:
            return False
        
        script_path = parsed_command["script_path"]
        if not script_path:
            return False
        
        # Set up callback for debug printing
        self.lua.globals()["py"] = {
            "callback": lambda msg: print(f"Lua: {msg}"),
            "command_complete": self._command_complete_callback
        }
        
        # Create command context
        self.lua.globals()["command"] = {
            "player": parsed_command["player"],
            "action": parsed_command["action"],
            "params": parsed_command["params"],
            "raw": parsed_command["raw_command"]
        }
        
        # Track completion state
        self.command_completed = False
        
        try:
            # Open and execute the Lua script
            with open(script_path, "r") as f:
                script_content = f.read()
                self.lua.execute(script_content)
                
            # Wait for completion signal
            # In a real implementation, this would use proper synchronization
            # This is a simplified approach
            timeout_counter = 0
            while not self.command_completed and timeout_counter < 100:
                # Wait a bit for Lua to complete
                # In a real implementation, use proper signaling
                import time
                time.sleep(0.01)
                timeout_counter += 1
            
            return self.command_completed
            
        except Exception as e:
            print(f"Error executing Lua script: {e}")
            return False
    
    def _command_complete_callback(self):
        """Callback when Lua signals command completion"""
        self.command_completed = True