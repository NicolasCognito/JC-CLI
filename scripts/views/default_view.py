NAME = "default"

#!/usr/bin/env python3
"""
Default text view for JC‑CLI.
Pure functions only; no file watchers or side‑effects beyond stdout.
"""
import os

def _print_header(username: str):
    print("=" * 60)
    print(f"JC‑CLI DEFAULT VIEW  –  Player: {username}")
    print("=" * 60)


def render(world: dict, ctx: dict):
    """Render the world snapshot once (called by ViewManager)."""
    username = ctx.get("username", "?")
    _print_header(username)

    print(f"\nCounter: {world.get('counter', 0)}")

    if "entities" in world:
        print("\nEntities:")
        for eid, ent in world["entities"].items():
            print(f"- {eid}: {ent.get('name', '?')}")

    if "players" in world and username in world["players"]:
        player = world["players"][username]
        print("\nYour status:")
        for k, v in player.items():
            if k != "secrets":
                print(f"- {k}: {v}")

    print()  # blank line at bottom

# ------------------------------------------------------------
# Optional input hook
# ------------------------------------------------------------

def handle_input(line: str, ctx: dict) -> bool:
    """Return True if input was consumed by the view."""
    lower = line.lower()
    if lower == "refresh":
        # the manager will re-render right after this returns
        return True
    if lower == "clear":
        os.system('cls' if os.name == 'nt' else 'clear')
        return True
    if lower == "help":
        print("\nView‑local commands:")
        print("  refresh       – redraw immediately")
        print("  clear         – clear the terminal")
        print("  help          – this help text")
        print("  view <name>   – switch to another discovered view\n")
        return True
    return False