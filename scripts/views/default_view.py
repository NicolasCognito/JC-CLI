#!/usr/bin/env python3
NAME = "chess_pil"

from io import BytesIO
import os
from PIL import Image, ImageDraw, ImageFont
from rich.console import Console
from rich.image import Image as RichImage
from rich.panel import Panel
from rich.text import Text

console = Console()

# board drawing constants
S = 64  # pixel size per square
LIGHT, DARK = (240,217,181), (181,136, 99)
FONT = ImageFont.truetype("DejaVuSans.ttf", 48)
PIECES = {
    "WK":"♔","WQ":"♕","WR":"♖","WB":"♗","WN":"♘","WP":"♙",
    "BK":"♚","BQ":"♛","BR":"♜","BB":"♝","BN":"♞","BP":"♟","":""
}

def make_board(world):
    img = Image.new("RGB", (8*S, 8*S), LIGHT)
    draw = ImageDraw.Draw(img)
    board = world["board"]
    for r in range(8):
        for c in range(8):
            color = LIGHT if (r+c)%2==0 else DARK
            x, y = c*S, (7-r)*S
            draw.rectangle([x,y,x+S,y+S], fill=color)
            piece = board[r][c]
            glyph = PIECES.get(piece, "")
            if glyph:
                w,h = draw.textsize(glyph, font=FONT)
                fill = "black" if piece.startswith("B") else "white"
                draw.text(
                    (x+(S-w)/2, y+(S-h)/2),
                    glyph, font=FONT, fill=fill
                )
    return img

def render(world, context):
    # --- 1) clear happens in view.py before this is called ---
    # --- 2) build our PIL board ---
    img = make_board(world)

    # --- 3) print it via RichImage (auto ANSI‐block conversion) ---
    console.print(RichImage.from_pil(img, width=32))

    # --- 4) then print the rest exactly as you used to ---
    white_cap = " ".join(world["captured_pieces"]["white"]) or "None"
    black_cap = " ".join(world["captured_pieces"]["black"]) or "None"
    console.print(Panel(f"White has: {white_cap}\nBlack has: {black_cap}", title="Captured"))

    moves = world["move_history"][-5:]
    history = "\n".join(f"{i+1}. {m}" for i,m in enumerate(moves)) or "None"
    console.print(Panel(history, title="Last Moves"))

    cmds = """\
move <from> <to>    – move a piece
castle kingside     – castle kingside
view chess          – redraw board
"""
    console.print(Panel(cmds, title="Commands", border_style="cyan"))
