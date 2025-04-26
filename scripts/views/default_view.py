#!/usr/bin/env python3
"""
VIEW MODULE: chess_rich
Renders a Pillow chessboard as a PNG using piece images from the images directory,
displays it inline via imgcat, prints CLI panels with Rich, and saves the image for debugging.
"""

NAME = "chess_rich"

import os
import io
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont  # pip install pillow
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
try:
    from imgcat import imgcat                  # pip install imgcat
    HAS_IMGCAT = True
except ImportError:
    HAS_IMGCAT = False

# Board rendering settings
SQUARE_SIZE = 64
LIGHT_COLOR = (240, 217, 181)
DARK_COLOR  = (181, 136,  99)

# Piece image mapping (filenames in the images directory)
PIECE_IMAGES = {
    "WK": "w_king.png",
    "WQ": "w_queen.png",
    "WR": "w_rook.png",
    "WB": "w_bishop.png",
    "WN": "w_knight.png",
    "WP": "w_pawn.png",
    "BK": "b_king.png",
    "BQ": "b_queen.png",
    "BR": "b_rook.png",
    "BB": "b_bishop.png",
    "BN": "b_knight.png",
    "BP": "b_pawn.png"
}

# Unicode chess piece mapping (fallback)
PIECES = {
    "WK":"♔","WQ":"♕","WR":"♖","WB":"♗","WN":"♘","WP":"♙",
    "BK":"♚","BQ":"♛","BR":"♜","BB":"♝","BN":"♞","BP":"♟","": ""
}

def load_piece_images():
    """Load all piece images from the images directory"""
    images_dir = Path(__file__).parent / "images"
    piece_images = {}
    
    for piece_code, filename in PIECE_IMAGES.items():
        image_path = images_dir / filename
        try:
            if image_path.exists():
                # Load and resize the image to fit the square size
                img = Image.open(image_path).convert("RGBA")
                img = img.resize((SQUARE_SIZE - 10, SQUARE_SIZE - 10), Image.LANCZOS)
                piece_images[piece_code] = img
        except Exception as e:
            print(f"Failed to load piece image {filename}: {e}", file=sys.stderr)
    
    return piece_images

def make_board_image(world):
    """Generate a PIL.Image of the chess board using piece images."""
    board = world.get("board")
    
    # Handle empty or missing board by creating default setup
    if not board:
        board = [["" for _ in range(8)] for _ in range(8)]
        # Set up initial position - fixed to have black at top, white at bottom
        board[0] = ["BR", "BN", "BB", "BQ", "BK", "BB", "BN", "BR"]  # Black back row
        board[1] = ["BP" for _ in range(8)]                         # Black pawns
        board[6] = ["WP" for _ in range(8)]                         # White pawns
        board[7] = ["WR", "WN", "WB", "WQ", "WK", "WB", "WN", "WR"]  # White back row
    
    # Create image with space for coordinates
    img_width = 8 * SQUARE_SIZE + 40  # Extra space for rank labels
    img_height = 8 * SQUARE_SIZE + 40  # Extra space for file labels
    img = Image.new("RGB", (img_width, img_height), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    
    # Draw board background
    board_margin = 20  # Margin for coordinates
    draw.rectangle(
        [board_margin, board_margin, 
         board_margin + 8 * SQUARE_SIZE, 
         board_margin + 8 * SQUARE_SIZE], 
        fill=(220, 220, 220)
    )
    
    # Try to load a font for coordinates
    try:
        font_paths = [
            os.path.expanduser("~/.fonts/DejaVuSans.ttf"),
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]
        font = None
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, 14)
                break
        if not font:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    
    # Load piece images
    piece_images = load_piece_images()
    
    # Draw the board squares - keep the same orientation with black at top, white at bottom
    for r in range(8):
        for c in range(8):
            x0 = board_margin + c * SQUARE_SIZE
            y0 = board_margin + r * SQUARE_SIZE  # Changed: now r=0 is top row (black's side)
            color = LIGHT_COLOR if (r + c) % 2 == 0 else DARK_COLOR
            draw.rectangle([x0, y0, x0 + SQUARE_SIZE, y0 + SQUARE_SIZE], fill=color)
            
            # Draw piece - access board in correct orientation
            piece = board[r][c] if r < len(board) and c < len(board[r]) else ""
            if piece and piece in piece_images:
                # Place the piece image centered on the square
                piece_img = piece_images[piece]
                offset_x = (SQUARE_SIZE - piece_img.width) // 2
                offset_y = (SQUARE_SIZE - piece_img.height) // 2
                # Create a temporary image for the piece on this square
                square_img = Image.new("RGBA", (SQUARE_SIZE, SQUARE_SIZE), (0, 0, 0, 0))
                square_img.paste(piece_img, (offset_x, offset_y), piece_img)
                # Paste the piece onto the board
                img.paste(square_img, (x0, y0), square_img)
            elif piece:
                # Fallback to Unicode if image not found
                glyph = PIECES.get(piece, "")
                try:
                    w, h = draw.textsize(glyph, font=font)
                except AttributeError:
                    try:
                        w, h = font.getbbox(glyph)[2:]
                    except Exception:
                        w, h = SQUARE_SIZE//2, SQUARE_SIZE//2
                
                x = x0 + (SQUARE_SIZE - w) / 2
                y = y0 + (SQUARE_SIZE - h) / 2
                fill = (0, 0, 0) if piece.startswith("B") else (255, 255, 255)
                draw.text((x, y), glyph, font=font, fill=fill)
    
    # Draw coordinates - adapted for the correct orientation
    for c in range(8):
        # Draw file labels (a-h)
        file_label = chr(ord('a') + c)
        x = board_margin + c * SQUARE_SIZE + SQUARE_SIZE // 2
        y = board_margin + 8 * SQUARE_SIZE + 10
        draw.text((x, y), file_label, font=font, fill=(0, 0, 0))
    
    for r in range(8):
        # Draw rank labels (1-8) - adjusted for orientation
        rank_label = str(r + 1)  # Changed: rank 1 is now at the bottom (white's side)
        x = 5
        y = board_margin + (7 - r) * SQUARE_SIZE + SQUARE_SIZE // 2  # Changed to count from bottom
        draw.text((x, y), rank_label, font=font, fill=(0, 0, 0))
    
    return img

def render(world, context):
    """Main render function called by the view manager"""
    console = Console()

    # Build board image
    img = make_board_image(world)

    # Try to display inline image with imgcat
    if HAS_IMGCAT:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        try:
            imgcat(buf.getvalue())
        except Exception as e:
            console.print(f"[red]Failed to render image via imgcat: {e}[/]")

def handle_input(cmd, ctx):
    """Handle view-specific input"""
    if cmd.lower() == "help":
        console = Console()
        return True
    return False  # Let other commands pass through