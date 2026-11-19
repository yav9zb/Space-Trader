"""Short on-screen messages for events that have no screen of their own
(calling for backup, a refused docking request). Draws a small stack at the
top center of the flight view; each message fades after a few seconds.
"""

import pygame

DEFAULT_DURATION = 4.0
FADE_TIME = 0.6
MAX_VISIBLE = 4


class Notifications:
    def __init__(self):
        self.items = []     # [text, seconds_left, color]
        self._font = None

    def push(self, text: str, duration: float = DEFAULT_DURATION, color=(255, 220, 80)):
        # Don't stack identical messages
        for item in self.items:
            if item[0] == text:
                item[1] = duration
                return
        self.items.append([text, duration, color])
        del self.items[:-MAX_VISIBLE]

    def update(self, delta_time: float):
        for item in self.items:
            item[1] -= delta_time
        self.items = [item for item in self.items if item[1] > 0]

    def clear(self):
        self.items.clear()

    def render(self, screen: pygame.Surface, ratio: float = 1.0):
        """Draw the stack. `ratio` is pixels per point, for drawing at full
        resolution on a Retina display."""
        if not self.items:
            return
        size = round(28 * ratio)
        if self._font is None or getattr(self, "_font_size", None) != size:
            self._font = pygame.font.Font(None, size)
            self._font_size = size
        width = screen.get_width()
        y = round(70 * ratio)
        pad_x, pad_y, gap = round(12 * ratio), round(5 * ratio), round(6 * ratio)
        for text, left, color in self.items:
            surface = self._font.render(text, True, color)
            if left < FADE_TIME:
                surface.set_alpha(int(255 * max(0.0, left / FADE_TIME)))
            back = pygame.Surface((surface.get_width() + 2 * pad_x, surface.get_height() + 2 * pad_y), pygame.SRCALPHA)
            back.fill((0, 0, 0, 150))
            x = (width - back.get_width()) // 2
            screen.blit(back, (x, y))
            screen.blit(surface, (x + pad_x, y + pad_y))
            y += back.get_height() + gap


notifications = Notifications()
