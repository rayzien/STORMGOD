"""
image_renderer.py — Premium glassmorphic card renderer for STORM GOD.
Features: gradient backgrounds, premium fonts, rayzien/stormgod GitHub watermark,
and specialized help card generation.
"""
import os
import hashlib
import requests as http_requests
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
FONTS_DIR = os.path.join(BASE_DIR, "fonts")

# Ensure fonts directory exists
os.makedirs(FONTS_DIR, exist_ok=True)

# ── Color Palette ──
TEXT_WHITE = (240, 240, 245, 255)
TEXT_SILVER = (200, 200, 210, 255)
TEXT_MUTED = (100, 100, 115, 255)
ACCENT_CYAN = (0, 200, 255, 255)
ACCENT_PURPLE = (150, 80, 255, 255)
ACCENT_GOLD = (255, 200, 80, 255)
ACCENT_GREEN = (80, 220, 140, 255)
ACCENT_RED = (255, 80, 100, 255)
BG_DARK = (8, 8, 14, 255)
BG_CARD = (14, 14, 22, 220)
BG_HEADER = (20, 18, 32, 240)
GITHUB_BADGE_BG = (25, 25, 40, 200)

# Category colors for help card
CATEGORY_COLORS = {
    "core": ACCENT_CYAN,
    "farm": ACCENT_GREEN,
    "music": ACCENT_PURPLE,
    "utility": ACCENT_GOLD,
    "sticker": (255, 140, 80, 255),
    "emoji": (255, 100, 200, 255),
    "prompts": TEXT_SILVER,
    "premium": ACCENT_GOLD,
}


def _download_font(url, filename):
    """Download a font file if not already cached."""
    filepath = os.path.join(FONTS_DIR, filename)
    if os.path.exists(filepath):
        return filepath
    try:
        r = http_requests.get(url, timeout=15)
        if r.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(r.content)
            return filepath
    except Exception as e:
        print(f"[STORMGOD] Font download failed ({filename}): {e}")
    return None


def _load_fonts():
    """Load premium fonts with fallback chain."""
    # Try downloading Inter and JetBrains Mono from Google Fonts CDN
    font_urls = {
        "Inter-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf",
        "JetBrainsMono-Regular.ttf": "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Regular.ttf",
    }
    
    # Try to download fonts (non-blocking, uses cache)
    for fname, url in font_urls.items():
        _download_font(url, fname)
    
    # Font loading priority
    title_candidates = [
        os.path.join(FONTS_DIR, "Inter-Bold.ttf"),
        "arialbd.ttf", "segoeui.ttf", "consolab.ttf"
    ]
    body_candidates = [
        os.path.join(FONTS_DIR, "JetBrainsMono-Regular.ttf"),
        "consolas.ttf", "lucon.ttf", "cour.ttf", "arial.ttf"
    ]
    
    font_title = None
    font_body = None
    font_small = None
    font_header = None
    
    # Load title font
    for f_path in title_candidates:
        try:
            font_header = ImageFont.truetype(f_path, 28)
            font_title = ImageFont.truetype(f_path, 20)
            break
        except (OSError, IOError):
            continue
    
    # Load body font
    for f_path in body_candidates:
        try:
            font_body = ImageFont.truetype(f_path, 14)
            font_small = ImageFont.truetype(f_path, 11)
            break
        except (OSError, IOError):
            continue
    
    # Ultimate fallback
    if not font_title:
        font_header = ImageFont.load_default()
        font_title = ImageFont.load_default()
    if not font_body:
        font_body = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    return font_header, font_title, font_body, font_small


def _draw_gradient_bg(img, colors=None):
    """Draw a vertical gradient background."""
    if colors is None:
        colors = [(8, 8, 14), (15, 10, 30), (8, 8, 14)]
    
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    num_segments = len(colors) - 1
    segment_height = h / num_segments
    
    for seg in range(num_segments):
        c1 = colors[seg]
        c2 = colors[seg + 1]
        y_start = int(seg * segment_height)
        y_end = int((seg + 1) * segment_height)
        
        for y in range(y_start, min(y_end, h)):
            ratio = (y - y_start) / max(1, segment_height)
            r = int(c1[0] + (c2[0] - c1[0]) * ratio)
            g = int(c1[1] + (c2[1] - c1[1]) * ratio)
            b = int(c1[2] + (c2[2] - c1[2]) * ratio)
            draw.line([(0, y), (w, y)], fill=(r, g, b, 255))


def _draw_github_watermark(draw, x, y, font_small):
    """Draw the rayzien/stormgod GitHub badge watermark."""
    badge_text = "github.com/rayzien/stormgod"
    text_w = draw.textlength(badge_text, font=font_small)
    
    # Badge background
    pad_x, pad_y = 10, 4
    draw.rounded_rectangle(
        [x - pad_x, y - pad_y, x + text_w + pad_x, y + 14 + pad_y],
        radius=8,
        fill=GITHUB_BADGE_BG,
        outline=(60, 60, 80, 180),
        width=1
    )
    draw.text((x, y), badge_text, fill=TEXT_MUTED, font=font_small)


def generate_glass_card(title, lines, output_filename="response.png"):
    """
    Renders a premium STORM GOD styled card response with dynamic height.
    """
    font_header, font_title, font_body, font_small = _load_fonts()
    
    # Dimensions
    width = 780
    card_pad = 24
    header_h = 70
    line_height = 26
    content_height = header_h + 40 + (len(lines) * line_height) + 80
    height = max(380, content_height)
    
    # Create base with gradient
    base_img = Image.new("RGBA", (width, height), BG_DARK)
    _draw_gradient_bg(base_img, [(8, 8, 14), (12, 8, 25), (8, 8, 14)])
    
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Card background
    cx0, cy0 = card_pad, card_pad
    cx1, cy1 = width - card_pad, height - card_pad
    
    draw.rounded_rectangle([cx0, cy0, cx1, cy1], radius=16, fill=BG_CARD)
    
    # Header bar
    draw.rounded_rectangle([cx0 + 8, cy0 + 8, cx1 - 8, cy0 + header_h], radius=10, fill=BG_HEADER)
    
    # Borders (double-line effect)
    draw.rounded_rectangle([cx0 + 3, cy0 + 3, cx1 - 3, cy1 - 3], radius=14, outline=(50, 50, 70, 150), width=1)
    draw.rounded_rectangle([cx0 + 1, cy0 + 1, cx1 - 1, cy1 - 1], radius=15, outline=TEXT_MUTED, width=1)
    
    # Subtle top accent line (cyan glow)
    draw.line([(cx0 + 40, cy0 + 8), (cx1 - 40, cy0 + 8)], fill=(*ACCENT_CYAN[:3], 60), width=1)

    # Logo watermark (translucent)
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            logo_w, logo_h = 200, 200
            logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
            r, g, b, a = logo.split()
            a = a.point(lambda p: int(p * 0.04))
            translucent_logo = Image.merge("RGBA", (r, g, b, a))
            pos_x = cx1 - logo_w - 20
            pos_y = (height - logo_h) // 2
            overlay.paste(translucent_logo, (pos_x, pos_y), translucent_logo)
        except Exception:
            pass

    # Corner logo
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            cw, ch = 32, 32
            corner_logo = logo.resize((cw, ch), Image.Resampling.LANCZOS)
            r2, g2, b2, a2 = corner_logo.split()
            a2 = a2.point(lambda p: int(p * 0.6))
            corner_logo = Image.merge("RGBA", (r2, g2, b2, a2))
            overlay.paste(corner_logo, (cx0 + 18, cy0 + 19), corner_logo)
        except Exception:
            pass

    # Title
    draw.text((cx0 + 60, cy0 + 24), title.upper(), fill=ACCENT_GOLD, font=font_title)
    
    # Status badge
    from utils import read_config
    try:
        conf = read_config()
        if conf.get("catch_enabled", "true") == "true":
            draw.text((cx1 - 240, cy0 + 28), "[STORMGOD ENGINE ACTIVE]", fill=ACCENT_CYAN, font=font_small)
    except Exception:
        pass

    # Body lines
    start_y = cy0 + header_h + 28
    for i, line in enumerate(lines):
        y_pos = start_y + (i * line_height)
        if y_pos > cy1 - 50:
            break
        
        if "═" in line or "─" in line:
            # Separator line
            draw.text((cx0 + 30, y_pos), line, fill=(60, 60, 80, 200), font=font_body)
        elif ":" in line and not line.startswith(" "):
            key, val = line.split(":", 1)
            draw.text((cx0 + 30, y_pos), key + ":", fill=ACCENT_CYAN, font=font_body)
            key_w = draw.textlength(key + ":", font=font_body) + 5
            draw.text((cx0 + 30 + key_w, y_pos), val, fill=TEXT_SILVER, font=font_body)
        else:
            draw.text((cx0 + 30, y_pos), line, fill=TEXT_SILVER, font=font_body)

    # Footer: GitHub watermark badge (right side)
    _draw_github_watermark(draw, cx1 - 240, cy1 - 24, font_small)
    
    # Footer: Developer credit (left side)
    draw.text((cx0 + 22, cy1 - 22), "developed by rayzien", fill=TEXT_MUTED, font=font_small)

    # Blend and save
    final_img = Image.alpha_composite(base_img, overlay)
    output_path = os.path.join(BASE_DIR, output_filename)
    final_img.save(output_path, "PNG")
    return output_path


def generate_help_card(title, lines, output_filename="response.png"):
    """
    Specialized renderer for the help command — wider layout, 
    category icons, and prominent watermark.
    """
    font_header, font_title, font_body, font_small = _load_fonts()
    
    # Help card is wider
    width = 850
    card_pad = 20
    header_h = 80
    line_height = 24
    content_height = header_h + 40 + (len(lines) * line_height) + 90
    height = max(500, content_height)
    
    base_img = Image.new("RGBA", (width, height), BG_DARK)
    _draw_gradient_bg(base_img, [(6, 6, 12), (14, 8, 28), (10, 6, 20), (6, 6, 12)])
    
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    cx0, cy0 = card_pad, card_pad
    cx1, cy1 = width - card_pad, height - card_pad
    
    # Card body
    draw.rounded_rectangle([cx0, cy0, cx1, cy1], radius=16, fill=BG_CARD)
    
    # Header with gradient accent
    draw.rounded_rectangle([cx0 + 6, cy0 + 6, cx1 - 6, cy0 + header_h], radius=12, fill=BG_HEADER)
    
    # Top accent glow line
    for i in range(3):
        alpha = max(10, 40 - i * 12)
        draw.line([(cx0 + 30, cy0 + 6 + i), (cx1 - 30, cy0 + 6 + i)], fill=(*ACCENT_PURPLE[:3], alpha), width=1)
    
    # Borders
    draw.rounded_rectangle([cx0 + 2, cy0 + 2, cx1 - 2, cy1 - 2], radius=15, outline=(50, 50, 70, 130), width=1)
    draw.rounded_rectangle([cx0, cy0, cx1, cy1], radius=16, outline=TEXT_MUTED, width=1)

    # Logo in header
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            cw, ch = 40, 40
            corner_logo = logo.resize((cw, ch), Image.Resampling.LANCZOS)
            r2, g2, b2, a2 = corner_logo.split()
            a2 = a2.point(lambda p: int(p * 0.7))
            corner_logo = Image.merge("RGBA", (r2, g2, b2, a2))
            overlay.paste(corner_logo, (cx0 + 18, cy0 + 20), corner_logo)
        except Exception:
            pass

    # Main title
    draw.text((cx0 + 68, cy0 + 18), "STORM GOD", fill=ACCENT_GOLD, font=font_header)
    draw.text((cx0 + 68, cy0 + 50), "COMMAND CENTER", fill=TEXT_MUTED, font=font_small)
    
    # Version badge
    draw.rounded_rectangle([cx1 - 80, cy0 + 22, cx1 - 16, cy0 + 40], radius=6, fill=(40, 30, 60, 200))
    draw.text((cx1 - 72, cy0 + 24), "v5.0.0", fill=ACCENT_PURPLE, font=font_small)

    # Body lines with category color detection
    start_y = cy0 + header_h + 24
    current_cat_color = TEXT_SILVER
    
    for i, line in enumerate(lines):
        y_pos = start_y + (i * line_height)
        if y_pos > cy1 - 55:
            draw.text((cx0 + 30, y_pos), "... scroll down for more ...", fill=TEXT_MUTED, font=font_small)
            break
        
        if "═" in line:
            # Double separator
            draw.line([(cx0 + 28, y_pos + 10), (cx1 - 28, y_pos + 10)], fill=(50, 50, 70, 150), width=1)
        elif "─" in line:
            draw.line([(cx0 + 28, y_pos + 10), (cx1 - 28, y_pos + 10)], fill=(40, 40, 55, 100), width=1)
        elif any(icon in line for icon in ["◈", "⚡", "♫", "⚙", "🎨", "😎", "❓", "★"]):
            # Category header — detect which category for color
            for cat_key, color in CATEGORY_COLORS.items():
                if COMMANDS_DOC.get(cat_key, {}).get("title", "") in line:
                    current_cat_color = color
                    break
            
            # Draw category header with accent dot
            draw.ellipse([cx0 + 26, y_pos + 4, cx0 + 34, y_pos + 12], fill=current_cat_color)
            draw.text((cx0 + 42, y_pos - 2), line, fill=TEXT_WHITE, font=font_title)
        elif line.startswith("    "):
            # Indented description / command preview
            draw.text((cx0 + 50, y_pos), line, fill=TEXT_MUTED, font=font_body)
        elif ":" in line and not line.strip().startswith("Type") and not line.strip().startswith("github"):
            key, val = line.split(":", 1)
            draw.text((cx0 + 30, y_pos), key + ":", fill=current_cat_color, font=font_body)
            key_w = draw.textlength(key + ":", font=font_body) + 5
            draw.text((cx0 + 30 + key_w, y_pos), val, fill=TEXT_SILVER, font=font_body)
        elif "github.com" in line:
            # Don't draw raw github line — we have the badge
            pass
        else:
            draw.text((cx0 + 30, y_pos), line, fill=TEXT_SILVER, font=font_body)

    # Footer area
    # GitHub watermark badge (prominent, right side)
    _draw_github_watermark(draw, cx1 - 250, cy1 - 26, font_small)
    
    # Developer credit
    draw.text((cx0 + 20, cy1 - 24), "developed by rayzien", fill=TEXT_MUTED, font=font_small)
    
    # Premium nudge
    draw.text((width // 2 - 60, cy1 - 24), "★ GET PREMIUM", fill=ACCENT_GOLD, font=font_small)

    # Blend and save
    final_img = Image.alpha_composite(base_img, overlay)
    output_path = os.path.join(BASE_DIR, output_filename)
    final_img.save(output_path, "PNG")
    return output_path
