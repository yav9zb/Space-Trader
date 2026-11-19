"""The game's font. pygame's built-in font is what every `pygame.font.Font(None,
size)` call in the codebase gets by default; install() swaps in Exo 2 for
exactly those calls, so one place changes the look of every screen without
editing each call site. Calls that name a font file are left alone.

Exo 2 is wider and taller than the built-in font at the same size, so sizes are
scaled to keep text widths (and so every panel layout) about the same.
Synthetic bold matches the built-in font's weight and reads better on a dark
background than Exo's thin default weight.
"""

import logging
import os

import pygame

from ..paths import get_resource_path

logger = logging.getLogger(__name__)

FONT_FILE = os.path.join("assets", "fonts", "Exo2-Variable.ttf")
SIZE_SCALE = 0.70          # Exo 2 at 70% of the size is close to the built-in font in width, and in height
                           # it avoids crowding the fixed line spacing many panels use

_OriginalFont = pygame.font.Font
_installed = False


def font_path() -> str:
    return get_resource_path(FONT_FILE)


class ThemedFont(_OriginalFont):
    """pygame.font.Font that uses Exo 2 when asked for the default font."""

    def __init__(self, file=None, size=20, *args, **kwargs):
        if file is None and os.path.exists(font_path()):
            super().__init__(font_path(), max(8, round(size * SIZE_SCALE)))
            self.set_bold(True)
        else:
            super().__init__(file, size, *args, **kwargs)


def install() -> bool:
    """Route default-font requests to Exo 2. Safe to call repeatedly; does
    nothing (and the game keeps pygame's font) if the font file is missing."""
    global _installed
    if _installed:
        return True
    if not os.path.exists(font_path()):
        logger.warning("Font file not found, keeping the default font: %s", font_path())
        return False
    pygame.font.Font = ThemedFont
    _installed = True
    return True


def uninstall():
    """Put pygame's own Font back (used by tests)."""
    global _installed
    pygame.font.Font = _OriginalFont
    _installed = False
