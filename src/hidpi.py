"""Sharp rendering on high-density (Retina) displays.

pygame-ce can hand out a drawing surface at a display's physical pixels
(`Window(..., allow_high_dpi=True)`): 2400x1500 for a 1200x750-point window on
a Retina Mac. The game's world and menus are laid out in points, so they keep
being drawn into an ordinary point-sized surface; each frame that surface is
scaled onto the pixel surface and the layers that benefit from real pixels
(HUD panels, radar, notifications) are drawn on top at full resolution.

Everything here degrades to "not used": on a standard display, under a
headless driver, with stock pygame, or when disabled, the engine falls back to
the plain `pygame.display.set_mode` path.
"""

import logging
import os
from typing import Callable, List, Optional, Tuple

import pygame

logger = logging.getLogger(__name__)

# A layer is drawn onto the pixel surface: layer(surface, ratio)
Layer = Callable[[pygame.Surface, float], None]

MIN_RATIO = 1.5            # below this the standard path is as good


def wanted() -> bool:
    """Whether to use the high-density path in this environment."""
    if os.environ.get("SPACETRADER_HIDPI") == "0":
        return False
    if not hasattr(pygame, "Window"):
        return False
    try:
        if pygame.display.get_driver() in ("dummy", "offscreen"):
            return False
    except pygame.error:
        return False
    from . import display
    return display.backing_scale() >= MIN_RATIO


def make_window(title: str, size: Tuple[int, int], resizable: bool = True):
    """Create the high-density window. Separate so tests can supply a fake."""
    return pygame.Window(title, size, resizable=resizable, allow_high_dpi=True)


class Presenter:
    """Owns the window, the point-sized surface the game draws into, and the
    layers drawn at full resolution after it is scaled up."""

    def __init__(self, window):
        self.window = window
        self.point_surface: Optional[pygame.Surface] = None
        self.layers: List[Layer] = []          # drawn on the pixel surface after the upscaled frame
        self.veil_alpha = 0                    # a dark veil over frame and layers (the pause screen)
        self.top_layers: List[Layer] = []      # drawn after the veil
        self._veil: Optional[pygame.Surface] = None

    # Geometry ---------------------------------------------------------------------

    @property
    def points(self) -> Tuple[int, int]:
        return tuple(int(v) for v in self.window.size)

    @property
    def pixel_surface(self) -> pygame.Surface:
        return self.window.get_surface()

    @property
    def ratio(self) -> float:
        width = self.points[0]
        return self.pixel_surface.get_width() / width if width else 1.0

    def sync(self) -> pygame.Surface:
        """The point-sized surface for the window's current size, re-created if
        the window has been resized."""
        size = self.points
        if self.point_surface is None or self.point_surface.get_size() != size:
            self.point_surface = pygame.Surface(size)
        return self.point_surface

    # Frame --------------------------------------------------------------------------

    def queue(self, layer: Layer, on_top: bool = False):
        (self.top_layers if on_top else self.layers).append(layer)

    def present(self):
        """Scale the point surface onto the pixel surface, draw the layers, show it."""
        pixels = self.pixel_surface
        frame = self.sync()
        if frame.get_size() == pixels.get_size():
            pixels.blit(frame, (0, 0))
        else:
            pygame.transform.smoothscale(frame, pixels.get_size(), pixels)
        ratio = self.ratio
        for layer in self.layers:
            layer(pixels, ratio)
        if self.veil_alpha:
            if self._veil is None or self._veil.get_size() != pixels.get_size():
                self._veil = pygame.Surface(pixels.get_size())
                self._veil.fill((0, 0, 0))
            self._veil.set_alpha(self.veil_alpha)
            pixels.blit(self._veil, (0, 0))
        for layer in self.top_layers:
            layer(pixels, ratio)
        self.layers.clear()
        self.top_layers.clear()
        self.veil_alpha = 0
        self.window.flip()


_presenter: Optional[Presenter] = None


def get_presenter() -> Optional[Presenter]:
    return _presenter


def configure(title: str, size: Tuple[int, int], resizable: bool = True,
              position: Optional[Tuple[int, int]] = None) -> Optional[pygame.Surface]:
    """Create (or resize) the high-density window and return the point-sized
    surface to draw into, or None if the high-density path cannot be used."""
    global _presenter
    try:
        if _presenter is None:
            _presenter = Presenter(make_window(title, size, resizable))
        else:
            _presenter.window.size = size
        if position is not None:
            _presenter.window.position = position
        return _presenter.sync()
    except Exception:
        logger.exception("High-density window unavailable; using the standard one")
        _presenter = None
        return None


def reset():
    """Forget the presenter (tests, or switching back to the standard path)."""
    global _presenter
    _presenter = None
