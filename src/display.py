"""Display sizing for every Mac (and other) screen the game may meet.

All sizes here are in points, the units pygame and macOS windows use: a 14-inch
MacBook Pro reports 1512x982 even though it has 3024x1964 pixels. (pygame 2.6
draws at point resolution and macOS scales the result up on Retina screens.)
The functions are pure, taking the desktop size as an argument, so they can be
tested against every screen without having one.
"""

import platform
from typing import Iterable, List, Optional, Tuple

Size = Tuple[int, int]

MIN_SIZE: Size = (1024, 640)

# Room macOS keeps for itself, in points: the menu bar (taller on notched
# MacBooks), the Dock, and a window's title bar.
MENU_BAR = 40
DOCK = 80
TITLE_BAR = 30

# Common window sizes worth offering, 16:10 (MacBooks, iMac) and 16:9
# (external monitors) plus ultrawide and big-display sizes.
PRESETS: List[Size] = [
    (1024, 640), (1280, 720), (1280, 800), (1366, 768), (1440, 900), (1512, 945),
    (1600, 900), (1680, 1050), (1728, 1080), (1920, 1080), (1920, 1200), (2048, 1280),
    (2240, 1260), (2560, 1440), (2560, 1600), (2880, 1620), (3008, 1692), (3440, 1440),
    (3840, 2160),
]

FALLBACK_DESKTOP: Size = (1920, 1080)


def is_macos() -> bool:
    return platform.system() == "Darwin"


def desktop_size(display_index: int = 0) -> Size:
    """The size of a display in points. Falls back sensibly if pygame cannot say."""
    try:
        import pygame
        pygame.display.init()
        sizes = pygame.display.get_desktop_sizes()
        if sizes:
            width, height = sizes[min(display_index, len(sizes) - 1)]
            if width > 0 and height > 0:
                return int(width), int(height)
        info = pygame.display.Info()
        if info.current_w > 0 and info.current_h > 0:
            return int(info.current_w), int(info.current_h)
    except Exception:
        pass
    return FALLBACK_DESKTOP


def backing_scale(display_index: int = 0) -> float:
    """How many physical pixels there are per point (2.0 on a Retina Mac).
    Informational: the game draws at point resolution."""
    try:
        import pygame
        modes = pygame.display.list_modes(display=display_index)
        if modes and modes != -1:
            widest = max(modes)[0]
            points = desktop_size(display_index)[0]
            ratio = widest / points
            return float(round(ratio)) if ratio >= 1.5 else 1.0
    except Exception:
        pass
    return 1.0


def usable_area(desktop: Size, mac: Optional[bool] = None) -> Size:
    """The largest window content size that fits on screen without covering the
    menu bar or Dock (on a Mac) or being taller than the display."""
    mac = is_macos() if mac is None else mac
    width, height = desktop
    if mac:
        height -= MENU_BAR + DOCK + TITLE_BAR
    else:
        height -= TITLE_BAR + 40                # a taskbar, roughly
        width -= 20
    return max(320, width), max(240, height)


def clamp_size(size: Size, usable: Size) -> Size:
    """Keep a window size within [MIN_SIZE, usable]. If the screen is smaller
    than the minimum, the screen wins."""
    width = min(max(int(size[0]), MIN_SIZE[0]), usable[0])
    height = min(max(int(size[1]), MIN_SIZE[1]), usable[1])
    return width, height


def default_window_size(usable: Size) -> Size:
    """A comfortable first window: about 80-90% of the usable area, 16:10."""
    height = min(usable[1] * 0.9, usable[0] * 0.8 * 10 / 16)
    width = min(usable[0] * 0.9, height * 16 / 10)
    return clamp_size((round(width / 2) * 2, round(height / 2) * 2), usable)


def resolution_options(usable: Size, current: Optional[Size] = None) -> List[Size]:
    """Window sizes for the settings menu: the presets that fit, a "fit the
    screen" size, and the current size, smallest first."""
    options = {p for p in PRESETS if p[0] <= usable[0] and p[1] <= usable[1]}
    options.add(default_window_size(usable))
    options.add(clamp_size(usable, usable))
    if current:
        options.add(clamp_size(current, usable))
    return sorted(options, key=lambda s: (s[0] * s[1], s[0]))


def star_count(size: Size, per_720p: int = 100, maximum: int = 500) -> int:
    """Stars scale with the window so a big display is not a sparse one."""
    return max(per_720p // 2, min(maximum, round(per_720p * size[0] * size[1] / (1280 * 720))))
