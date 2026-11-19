"""Menu-style screens are laid out on a fixed pixel grid (a title at y=70,
options every 60 pixels, ...), so on a very short window their content runs off
the bottom and on a very large one it shrinks into a corner. Rather than
rewrite each of them, they are drawn at a logical size sized for that layout and
the result is scaled to the window; mouse positions are mapped back.

Flight is not scaled: the world and HUD are drawn at the window's real pixels.
"""

from typing import Optional, Tuple

import pygame

DESIGN_HEIGHT = 800          # the shortest logical height the menu layouts were built for
STEPS = (1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0)

Size = Tuple[int, int]


def scale_for(window: Size) -> float:
    """How much the logical screen is enlarged to fill the window.

    Below DESIGN_HEIGHT the screen is shrunk to fit (a downscale stays crisp).
    Above it the scale grows in steps, as large as keeps the logical height at
    or above DESIGN_HEIGHT, so text is bigger on big windows without ever
    being cut off."""
    height = window[1]
    if height < DESIGN_HEIGHT:
        return max(0.5, height / DESIGN_HEIGHT)
    best = 1.0
    for step in STEPS:
        if height / step >= DESIGN_HEIGHT:
            best = step
    return best


def logical_size(window: Size) -> Size:
    scale = scale_for(window)
    return max(320, round(window[0] / scale)), max(240, round(window[1] / scale))


_real_get_pos = pygame.mouse.get_pos


class ScreenScaler:
    def __init__(self):
        self.scale = 1.0
        self.active = False
        self._surface: Optional[pygame.Surface] = None

    # Mouse -----------------------------------------------------------------------

    def to_logical(self, pos) -> Tuple[int, int]:
        if not self.active or self.scale == 1.0:
            return int(pos[0]), int(pos[1])
        return int(pos[0] / self.scale), int(pos[1] / self.scale)

    def mouse_pos(self) -> Tuple[int, int]:
        return self.to_logical(_real_get_pos())

    def map_event(self, event: pygame.event.Event) -> pygame.event.Event:
        """The event as the screen being drawn should see it: mouse positions
        in logical coordinates."""
        if not self.active or self.scale == 1.0 or "pos" not in event.dict:
            return event
        data = dict(event.dict)
        data["pos"] = self.to_logical(event.pos)
        if "rel" in data:
            data["rel"] = (int(data["rel"][0] / self.scale), int(data["rel"][1] / self.scale))
        return pygame.event.Event(event.type, data)

    # Drawing ------------------------------------------------------------------------

    def render(self, state, screen: pygame.Surface):
        """Draw a state at the logical size and scale it onto screen."""
        window = screen.get_size()
        self.scale = scale_for(window)
        if self.scale == 1.0:
            state.render(screen)
            return
        size = logical_size(window)
        if self._surface is None or self._surface.get_size() != size:
            self._surface = pygame.Surface(size)
        self._surface.fill((0, 0, 0))
        state.render(self._surface)
        if size == window:
            screen.blit(self._surface, (0, 0))
        else:
            pygame.transform.smoothscale(self._surface, window, screen)

    def draw_overlay(self, draw, screen: pygame.Surface, reference: Optional[Size] = None):
        """Draw a menu layer on top of what is already on screen (the pause
        menu over the game). `draw(surface)` paints onto a transparent surface
        of the logical size, which is then scaled and composited onto screen.
        `reference` is the window size in points when screen is a higher-
        resolution surface (Retina), so the layout and mouse mapping, which
        work in points, stay consistent."""
        window = tuple(reference) if reference else screen.get_size()
        self.scale = scale_for(window)
        if self.scale == 1.0 and window == screen.get_size():
            draw(screen)
            return
        size = logical_size(window)
        layer = pygame.Surface(size, pygame.SRCALPHA)
        draw(layer)
        screen.blit(pygame.transform.smoothscale(layer, screen.get_size()), (0, 0))

    def prepare(self, screen: pygame.Surface, active: bool):
        """Called before events, updates and rendering so that mouse mapping
        matches the screen about to be used."""
        self.active = active
        self.scale = scale_for(screen.get_size()) if active else 1.0


scaler = ScreenScaler()


def install():
    """Make pygame.mouse.get_pos() report logical coordinates while a scaled
    screen is active (the screens read the mouse directly in many places)."""
    pygame.mouse.get_pos = scaler.mouse_pos


def uninstall():
    pygame.mouse.get_pos = _real_get_pos
