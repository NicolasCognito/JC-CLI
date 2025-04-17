"""
JC-CLI View: Displays game state to console
"""
import json
import os

class View:
    def __init__(self):
        """Initialize view"""
        self.current_player = None
    
    def update(self):
        """Update view based on current game state"""
        # Load game state from main.json
        try:
            with open("main.json", "r") as f:
                game_state = json.load(f)
            
            # Clear console
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Display game state
            self._display_game_state(game_state)
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading game state: {e}")
    
    def _display_game_state(self, game_state):
        """
        Display game state to console
        
        Args:
            game_state (dict): Full game state from main.json
        """
        game = game_state.get("game", {})
        
        # Display turn information
        print("=" * 50)
        print(f"JC-CLI Game - Turn {game.get('turn', 0)}")
        print("=" * 50)
        
        # Display world state
        world = game.get("state", {}).get("world", {})
        print("\nWorld State:")
        print(f"  Deck: {len(world.get('deck', []))} cards")
        for key, value in world.items():
            if key != "deck":
                print(f"  {key}: {value}")
        
        # Display players
        players = game.get("state", {}).get("players", {})
        print("\nPlayers:")
        for player_id, player in players.items():
            print(f"\n  {player_id}:")
            print(f"    Points: {player.get('points', 0)}")
            
            # Show hand
            hand = player.get("hand", {}).get("cards", [])
            print(f"    Hand: {', '.join(hand) if hand else 'Empty'}")
            
            # Show inventory
            inventory_slots = player.get("inventory", {}).get("slots", [])
            print(f"    Inventory Slots: {len(inventory_slots)}/{player.get('inventory', {}).get('max_slots', 0)}")
            
            # Display each inventory slot if viewing current player
            if player_id == self.current_player:
                self._display_player_inventory(game, player_id)
        
        # Display card details for current player
        if self.current_player and self.current_player in players:
            self._display_player_cards(game, self.current_player)
        
        print("\n" + "=" * 50)
    
    def _display_player_inventory(self, game, player_id):
        """
        Display player inventory details
        
        Args:
            game (dict): Game state
            player_id (str): Player to display
        """
        # Get player inventory slots
        player = game.get("state", {}).get("players", {}).get(player_id, {})
        inventory_slots = player.get("inventory", {}).get("slots", [])
        
        # Get instances references
        instances = game.get("registers", {}).get("instances", {})
        slots = instances.get("slots", {})
        resources = instances.get("resources", {})
        
        # Get templates for display names
        templates = game.get("registers", {}).get("templates", {}).get("resources", {})
        
        print("\n    Inventory Contents:")
        for slot_id in inventory_slots:
            slot = slots.get(slot_id, {})
            resource_id = slot.get("resource")
            
            if resource_id:
                resource = resources.get(resource_id, {})
                template_id = resource.get("template", "")
                template = templates.get(template_id, {})
                
                name = template.get("name", template_id)
                properties = resource.get("properties", {})
                
                # Format properties as string
                prop_str = ", ".join([f"{k}: {v}" for k, v in properties.items()])
                
                print(f"      {slot_id}: {name} {f'({prop_str})' if prop_str else ''}")
            else:
                print(f"      {slot_id}: Empty")
    
    def _display_player_cards(self, game, player_id):
        """
        Display player card details
        
        Args:
            game (dict): Game state
            player_id (str): Player to display
        """
        # Get player cards
        player = game.get("state", {}).get("players", {}).get(player_id, {})
        hand = player.get("hand", {}).get("cards", [])
        
        if not hand:
            return
        
        # Get instances references
        instances = game.get("registers", {}).get("instances", {})
        cards = instances.get("cards", {})
        slots = instances.get("slots", {})
        resources = instances.get("resources", {})
        
        # Get templates
        card_templates = game.get("registers", {}).get("templates", {}).get("cards", {})
        resource_templates = game.get("registers", {}).get("templates", {}).get("resources", {})
        
        print("\n    Cards:")
        for card_id in hand:
            card = cards.get(card_id, {})
            template_id = card.get("template", "")
            template = card_templates.get(template_id, {})
            
            name = template.get("name", template_id)
            card_slots = card.get("slots", [])
            recipes = template.get("recipes", [])
            
            print(f"      {card_id}: {name}")
            print(f"        Recipes: {', '.join(recipes)}")
            print(f"        Slots:")
            
            for slot_id in card_slots:
                slot = slots.get(slot_id, {})
                resource_id = slot.get("resource")
                
                if resource_id:
                    resource = resources.get(resource_id, {})
                    res_template_id = resource.get("template", "")
                    res_template = resource_templates.get(res_template_id, {})
                    
                    name = res_template.get("name", res_template_id)
                    properties = resource.get("properties", {})
                    
                    # Format properties as string
                    prop_str = ", ".join([f"{k}: {v}" for k, v in properties.items()])
                    
                    print(f"          {slot_id}: {name} {f'({prop_str})' if prop_str else ''}")
                else:
                    print(f"          {slot_id}: Empty")
    
    def set_current_player(self, player_id):
        """
        Set current player view
        
        Args:
            player_id (str): Player to focus on
        """
        self.current_player = player_id
        self.update()