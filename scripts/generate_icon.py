"""Generates the app icon (PNG at multiple sizes, plus .ico and .icns).

Run with: ./venv/bin/python scripts/generate_icon.py

Draws a simple badge matching the game's established look (dark space
background, blue accent from the main menu, the same ship triangle
shape used in gameplay) rather than importing outside art.
"""

import math
import os
import subprocess
import sys

import pygame

pygame.init()

SIZE = 1024
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon")
os.makedirs(OUT_DIR, exist_ok=True)


def draw_icon(size):
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    radius = int(size * 0.48)

    # Background badge: dark space navy, matching the main menu's (2, 2, 16),
    # with a small number of concentric rings (not additive) for a subtle
    # center-to-edge falloff instead of a flat fill.
    base = (4, 6, 22)
    mid = (10, 16, 44)
    ring_steps = 3
    for i in range(ring_steps, 0, -1):
        t = i / ring_steps
        r = int(radius * t)
        color = tuple(int(base[c] + (mid[c] - base[c]) * (1 - t)) for c in range(3))
        pygame.draw.circle(surface, color, (center, center), r)

    # Scattered stars within the badge
    import random
    random.seed(42)
    for _ in range(50):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0, radius * 0.92)
        x = center + math.cos(angle) * dist
        y = center + math.sin(angle) * dist
        star_size = random.choice([1, 1, 1, 2, 2]) * max(1, size // 256)
        brightness = random.randint(140, 230)
        pygame.draw.circle(surface, (brightness, brightness, brightness), (int(x), int(y)), max(1, star_size))

    # Ship silhouette - same isoceles triangle shape as the in-game ship
    ship_scale = radius * 0.56
    points = [
        (center, center - ship_scale),
        (center - ship_scale * 0.6, center + ship_scale * 0.7),
        (center, center + ship_scale * 0.42),
        (center + ship_scale * 0.6, center + ship_scale * 0.7),
    ]
    pygame.draw.polygon(surface, (240, 244, 255), points)
    pygame.draw.polygon(surface, (140, 190, 255), points, max(2, size // 200))

    # Engine glow accent (gold, matching the menu's selection color) - a
    # single soft circle, not additively stacked
    glow_pos = (center, int(center + ship_scale * 0.68))
    pygame.draw.circle(surface, (255, 205, 90), glow_pos, max(2, int(ship_scale * 0.14)))

    # Thin accent ring, matching the main menu's underline color
    pygame.draw.circle(surface, (80, 160, 255), (center, center), int(radius * 0.98), max(3, size // 140))

    return surface


def main():
    master = draw_icon(SIZE)
    master_path = os.path.join(OUT_DIR, "icon_1024.png")
    pygame.image.save(master, master_path)
    print(f"Saved {master_path}")

    sizes = [16, 32, 48, 64, 128, 256, 512, 1024]
    png_paths = {}
    for s in sizes:
        scaled = pygame.transform.smoothscale(master, (s, s))
        path = os.path.join(OUT_DIR, f"icon_{s}.png")
        pygame.image.save(scaled, path)
        png_paths[s] = path
        print(f"Saved {path}")

    # .ico for Windows (multi-resolution, via Pillow)
    try:
        from PIL import Image
        ico_sizes = [16, 32, 48, 64, 128, 256]
        base_img = Image.open(png_paths[256])
        ico_path = os.path.join(OUT_DIR, "icon.ico")
        base_img.save(ico_path, format="ICO", sizes=[(s, s) for s in ico_sizes])
        print(f"Saved {ico_path}")
    except ImportError:
        print("Pillow not available - skipped .ico generation")

    # .icns for macOS (via iconutil, macOS-only)
    if sys.platform == "darwin":
        iconset_dir = os.path.join(OUT_DIR, "icon.iconset")
        os.makedirs(iconset_dir, exist_ok=True)
        mapping = {
            16: "icon_16x16.png", 32: "icon_16x16@2x.png",
            32: "icon_32x32.png",
        }
        # iconutil expects specific filenames per size/scale
        specs = [
            (16, "icon_16x16.png"), (32, "icon_16x16@2x.png"),
            (32, "icon_32x32.png"), (64, "icon_32x32@2x.png"),
            (128, "icon_128x128.png"), (256, "icon_128x128@2x.png"),
            (256, "icon_256x256.png"), (512, "icon_256x256@2x.png"),
            (512, "icon_512x512.png"), (1024, "icon_512x512@2x.png"),
        ]
        for s, name in specs:
            scaled = pygame.transform.smoothscale(master, (s, s))
            pygame.image.save(scaled, os.path.join(iconset_dir, name))

        icns_path = os.path.join(OUT_DIR, "icon.icns")
        result = subprocess.run(
            ["iconutil", "-c", "icns", iconset_dir, "-o", icns_path],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"Saved {icns_path}")
        else:
            print(f"iconutil failed: {result.stderr}")

        import shutil
        shutil.rmtree(iconset_dir)


if __name__ == "__main__":
    main()
