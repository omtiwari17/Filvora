"""
Comprehensive Asset Generator for Filvora:
Generates all favicons, device app icons, splash assets, OpenGraph cards, and configurations.
"""
import os
import shutil
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ICONS_DIR = os.path.join("static", "icons")
IMG_DIR = os.path.join("static", "img")
os.makedirs(ICONS_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

def lerp_color(c1, c2, t):
    """Linear interpolate between RGB tuples."""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

def create_svg_favicon():
    """Generates standard and high-DPI vector SVG favicon."""
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <!-- Background Gradient -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0a0e1a"/>
      <stop offset="100%" stop-color="#030712"/>
    </linearGradient>
    <!-- Ambient Radial Glow -->
    <radialGradient id="ambientGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#e50914" stop-opacity="0.38"/>
      <stop offset="100%" stop-color="#e50914" stop-opacity="0"/>
    </radialGradient>
    <!-- Vertical Stem Gradient -->
    <linearGradient id="stemGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#f43f5e"/>
      <stop offset="100%" stop-color="#e50914"/>
    </linearGradient>
    <!-- Top Beam Gradient -->
    <linearGradient id="topBeamGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#f43f5e"/>
      <stop offset="60%" stop-color="#f59e0b"/>
      <stop offset="100%" stop-color="#fbbf24"/>
    </linearGradient>
    <!-- Middle Play Beam Gradient -->
    <linearGradient id="midBeamGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#f43f5e"/>
      <stop offset="100%" stop-color="#f59e0b"/>
    </linearGradient>
    <!-- Cinema Drop Shadow -->
    <filter id="fShadow" x="-20%" y="-20%" width="150%" height="150%">
      <feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="#000000" flood-opacity="0.75"/>
    </filter>
  </defs>

  <!-- Dark Cinema Squircle Container -->
  <rect x="20" y="20" width="472" height="472" rx="108" fill="url(#bgGrad)" stroke="#ffffff" stroke-opacity="0.12" stroke-width="4"/>
  <!-- Ambient Center Glow -->
  <circle cx="256" cy="256" r="215" fill="url(#ambientGlow)"/>

  <!-- The Filvora "F" Mark -->
  <g filter="url(#fShadow)">
    <!-- Vertical Stem -->
    <rect x="120" y="110" width="82" height="292" rx="28" fill="url(#stemGrad)"/>
    <!-- Top Horizontal Beam -->
    <rect x="160" y="110" width="220" height="74" rx="28" fill="url(#topBeamGrad)"/>
    <!-- Middle Horizontal Play Arrow -->
    <path d="M 160 236 L 290 236 L 332 268 L 290 300 L 160 300 Z" fill="url(#midBeamGrad)"/>
  </g>
</svg>'''
    path = os.path.join(ICONS_DIR, "favicon.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Generated {path}")

def create_safari_pinned_tab_svg():
    """Generates monochrome vector SVG silhouette for Safari pinned tabs."""
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <!-- Monochrome Silhouette of Filvora F Mark for Safari Pinned Tab -->
  <g fill="#000000">
    <!-- Vertical Stem -->
    <rect x="120" y="110" width="82" height="292" rx="28"/>
    <!-- Top Horizontal Beam -->
    <rect x="160" y="110" width="220" height="74" rx="28"/>
    <!-- Middle Horizontal Play Arrow -->
    <path d="M 160 236 L 290 236 L 332 268 L 290 300 L 160 300 Z"/>
  </g>
</svg>'''
    path = os.path.join(ICONS_DIR, "safari-pinned-tab.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Generated {path}")

def create_master_raster(size=1024, is_maskable=False):
    """
    Renders high-res master bitmap for supersampled downscaling.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Background
    if is_maskable:
        # Maskable icon requires 100% full-bleed background
        draw.rectangle((0, 0, size, size), fill=(5, 8, 17, 255))
    else:
        # App icon squircle with subtle border
        pad = int(size * 0.04)
        rad = int(size * 0.22)
        draw.rounded_rectangle((pad, pad, size - pad, size - pad), radius=rad, fill=(5, 8, 17, 255))
        draw.rounded_rectangle((pad, pad, size - pad, size - pad), radius=rad, outline=(255, 255, 255, 28), width=int(size * 0.008))

    # 2. Ambient radial crimson glow
    glow_size = int(size * 0.82)
    glow_img = Image.new("RGBA", (glow_size, glow_size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    g_center = glow_size / 2
    max_r = int(glow_size / 2)
    for r in range(max_r, 0, -4):
        alpha = int(45 * (1 - r / max_r) ** 1.8)
        glow_draw.ellipse(
            (g_center - r, g_center - r, g_center + r, g_center + r),
            fill=(229, 9, 20, alpha)
        )
    glow_pos = (int((size - glow_size) / 2), int((size - glow_size) / 2))
    img.alpha_composite(glow_img, glow_pos)

    # 3. Filvora "F" Mark
    # Scale factors: maskable is scaled down to 0.65 to fit safely within the 80% circle
    scale = (size / 512.0) * (0.70 if is_maskable else 0.88)
    
    # Calculate offset to center the mark
    # Base bounds at 512: x from 120 to 380 (width 260, center 250), y from 110 to 402 (height 292, center 256)
    orig_cx, orig_cy = 250.0, 256.0
    dest_cx, dest_cy = size / 2.0, size / 2.0

    def tx(x):
        return dest_cx + (x - orig_cx) * scale

    def ty(y):
        return dest_cy + (y - orig_cy) * scale

    f_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Colors
    c_crimson = (229, 9, 20)      # #e50914 (Brand Red)
    c_rose = (244, 63, 94)        # #f43f5e (Vivid Rose)
    c_amber = (245, 158, 11)      # #f59e0b (Cinema Amber)
    c_gold = (251, 191, 36)       # #fbbf24 (Radiant Gold)

    # A. Vertical Stem: x=120, y=110, w=82, h=292, rx=28
    stem_x0 = int(tx(120))
    stem_y0 = int(ty(110))
    stem_w = int(82 * scale)
    stem_h = int(292 * scale)
    stem_rx = int(28 * scale)

    stem_strip = Image.new("RGBA", (stem_w, stem_h), (0, 0, 0, 0))
    for y in range(stem_h):
        t = y / max(1, stem_h)
        col = lerp_color(c_rose, c_crimson, t)
        for x in range(stem_w):
            stem_strip.putpixel((x, y), (*col, 255))
    stem_mask = Image.new("L", (stem_w, stem_h), 0)
    ImageDraw.Draw(stem_mask).rounded_rectangle((0, 0, stem_w - 1, stem_h - 1), radius=stem_rx, fill=255)
    f_layer.paste(stem_strip, (stem_x0, stem_y0), stem_mask)

    # B. Top Horizontal Beam: x=160, y=110, w=220, h=74, rx=28
    top_x0 = int(tx(160))
    top_y0 = int(ty(110))
    top_w = int(220 * scale)
    top_h = int(74 * scale)
    top_rx = int(28 * scale)

    top_strip = Image.new("RGBA", (top_w, top_h), (0, 0, 0, 0))
    for x in range(top_w):
        t = x / max(1, top_w)
        col = lerp_color(c_rose, c_gold, t)
        for y in range(top_h):
            top_strip.putpixel((x, y), (*col, 255))
    top_mask = Image.new("L", (top_w, top_h), 0)
    ImageDraw.Draw(top_mask).rounded_rectangle((0, 0, top_w - 1, top_h - 1), radius=top_rx, fill=255)
    f_layer.paste(top_strip, (top_x0, top_y0), top_mask)

    # C. Middle Horizontal Play Arrow: x=160, y=236, w=172, h=64
    # Polygon: (160,236) -> (290,236) -> (332,268) -> (290,300) -> (160,300)
    mid_x0 = int(tx(160))
    mid_y0 = int(ty(236))
    mid_w = int(172 * scale)
    mid_h = int(64 * scale)

    mid_strip = Image.new("RGBA", (mid_w, mid_h), (0, 0, 0, 0))
    for x in range(mid_w):
        t = x / max(1, mid_w)
        col = lerp_color(c_rose, c_amber, t)
        for y in range(mid_h):
            mid_strip.putpixel((x, y), (*col, 255))
    mid_mask = Image.new("L", (mid_w, mid_h), 0)
    mid_draw = ImageDraw.Draw(mid_mask)
    tip_cut = int(42 * scale)
    pts = [
        (0, 0),
        (mid_w - tip_cut, 0),
        (mid_w - 1, mid_h // 2),
        (mid_w - tip_cut, mid_h - 1),
        (0, mid_h - 1)
    ]
    mid_draw.polygon(pts, fill=255)
    f_layer.paste(mid_strip, (mid_x0, mid_y0), mid_mask)

    # 4. Drop Shadow beneath the F
    shadow = f_layer.split()[3].filter(ImageFilter.GaussianBlur(radius=int(size * 0.03)))
    shadow_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_img.paste((0, 0, 0, 180), (0, int(size * 0.018)), mask=shadow)

    img.alpha_composite(shadow_img)
    img.alpha_composite(f_layer)

    return img

def create_og_image():
    """Generates 1200x630 OpenGraph / Twitter rich social preview card."""
    w, h = 1200, 630
    img = Image.new("RGBA", (w, h), (3, 7, 18, 255)) # #030712
    draw = ImageDraw.Draw(img)

    # Background ambient lighting: crimson glow on left, gold glow on right
    left_glow = Image.new("RGBA", (700, 700), (0, 0, 0, 0))
    ImageDraw.Draw(left_glow).ellipse((0, 0, 699, 699), fill=(229, 9, 20, 50))
    left_glow = left_glow.filter(ImageFilter.GaussianBlur(radius=100))
    img.alpha_composite(left_glow, (-100, -50))

    right_glow = Image.new("RGBA", (600, 600), (0, 0, 0, 0))
    ImageDraw.Draw(right_glow).ellipse((0, 0, 599, 599), fill=(245, 158, 11, 28))
    right_glow = right_glow.filter(ImageFilter.GaussianBlur(radius=120))
    img.alpha_composite(right_glow, (750, 80))

    # Outer decorative subtle border
    draw.rounded_rectangle((24, 24, w - 24, h - 24), radius=28, outline=(255, 255, 255, 20), width=2)

    # Paste high-res logo mark on left
    logo = create_master_raster(size=380, is_maskable=False)
    img.alpha_composite(logo, (90, int((h - 380) / 2)))

    # Brand Title: FILVORA
    # Try system fonts, fall back to clean PIL default
    font_title = None
    font_sub = None
    font_pill = None
    for fn in ["segui_black.ttf", "arialbd.ttf", "calibrib.ttf", "tahoma.ttf"]:
        try:
            font_title = ImageFont.truetype(fn, 78)
            font_sub = ImageFont.truetype(fn, 24)
            font_pill = ImageFont.truetype(fn, 16)
            break
        except Exception:
            pass

    text_x = 510
    draw.text((text_x, 175), "FILVORA", fill=(255, 255, 255, 255), font=font_title)
    
    # Version badge next to title
    v_box = (text_x + 360, 195, text_x + 440, 235)
    draw.rounded_rectangle(v_box, radius=8, fill=(229, 9, 20, 240), outline=(255, 255, 255, 60), width=1)
    if font_sub:
        draw.text((text_x + 372, 203), "v2.5", fill=(255, 255, 255, 255), font=font_sub)

    # Subtitle / Tagline
    if font_sub:
        draw.text((text_x, 275), "Next-Gen Cinematic Streaming Platform", fill=(243, 244, 246, 230), font=font_sub)
        draw.text((text_x, 315), "Instant 4K Movies & Series • Multi-Server Failover • Zero Ads", fill=(156, 163, 175, 220), font=font_pill)

    # Feature Badges
    pills = ["⚡ Multi-Server", "🎬 4K HDR", "📱 Multi-Device PWA", "🛡️ Profile Isolation"]
    px = text_x
    py = 390
    for p in pills:
        pw = len(p) * 11 + 24
        draw.rounded_rectangle((px, py, px + pw, py + 36), radius=18, fill=(17, 24, 39, 220), outline=(75, 85, 99, 140), width=1)
        if font_pill:
            draw.text((px + 12, py + 9), p, fill=(209, 213, 219, 255), font=font_pill)
        px += pw + 16

    path = os.path.join(ICONS_DIR, "og-image.png")
    img.save(path, format="PNG", optimize=True)
    print(f"Generated {path}")

def create_browserconfig_xml():
    """Generates Windows 10/11 Start Tile browserconfig.xml."""
    xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
    <msapplication>
        <tile>
            <square150x150logo src="/static/icons/mstile-150x150.png"/>
            <square310x310logo src="/static/icons/mstile-310x310.png"/>
            <TileColor>#030712</TileColor>
        </tile>
    </msapplication>
</browserconfig>'''
    path = os.path.join(ICONS_DIR, "browserconfig.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    print(f"Generated {path}")

def build_all_assets():
    print("--- 1. Generating SVG Assets ---")
    create_svg_favicon()
    create_safari_pinned_tab_svg()
    create_browserconfig_xml()

    print("--- 2. Generating Master 1024x1024 Bitmaps ---")
    master_icon = create_master_raster(size=1024, is_maskable=False)
    master_maskable = create_master_raster(size=1024, is_maskable=True)

    print("--- 3. Downscaling Device App Icons & Favicons ---")
    sizes_regular = {
        "icon-512.png": 512,
        "icon-192.png": 192,
        "apple-touch-icon.png": 180,
        "apple-touch-icon-152x152.png": 152,
        "apple-touch-icon-120x120.png": 120,
        "mstile-150x150.png": 150,
        "mstile-310x310.png": 310,
        "favicon-48x48.png": 48,
        "favicon-32x32.png": 32,
        "favicon-16x16.png": 16,
    }

    for name, sz in sizes_regular.items():
        resized = master_icon.resize((sz, sz), Image.Resampling.LANCZOS)
        path = os.path.join(ICONS_DIR, name)
        resized.save(path, format="PNG", optimize=True)
        print(f"  [OK] Generated {name} ({sz}x{sz})")

    sizes_maskable = {
        "icon-512-maskable.png": 512,
        "icon-192-maskable.png": 192,
    }

    for name, sz in sizes_maskable.items():
        resized = master_maskable.resize((sz, sz), Image.Resampling.LANCZOS)
        path = os.path.join(ICONS_DIR, name)
        resized.save(path, format="PNG", optimize=True)
        print(f"  [OK] Generated {name} ({sz}x{sz} maskable)")

    print("--- 4. Assembling Multi-Resolution favicon.ico ---")
    ico_path = os.path.join(ICONS_DIR, "favicon.ico")
    master_icon.save(
        ico_path,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64)]
    )
    print(f"  [OK] Generated {ico_path} (16, 32, 48, 64 px layers)")

    print("--- 5. Generating Social Share Preview (og-image.png) ---")
    create_og_image()

    print("--- 6. Syncing Legacy & Root Mirrors ---")
    # Copy to static/img/ for backward compatibility
    for fname in ["icon-192.png", "icon-512.png", "favicon.ico"]:
        src = os.path.join(ICONS_DIR, fname)
        dst = os.path.join(IMG_DIR, fname)
        shutil.copy2(src, dst)
        print(f"  [OK] Mirrored {src} -> {dst}")

    # Copy favicon.ico to static/ root
    shutil.copy2(ico_path, os.path.join("static", "favicon.ico"))
    print("  [OK] Mirrored favicon.ico -> static/favicon.ico")

if __name__ == "__main__":
    build_all_assets()
    print("\nAll Filvora icons and assets successfully generated!")
