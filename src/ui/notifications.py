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

    def render(self, screen: pygame.Surface):
        if not self.items:
            return
        if self._font is None:
            self._font = pygame.font.Font(None, 28)
        width = screen.get_width()
        y = 70
        for text, left, color in self.items:
            surface = self._font.render(text, True, color)
            if left < FADE_TIME:
                surface.set_alpha(int(255 * max(0.0, left / FADE_TIME)))
            back = pygame.Surface((surface.get_width() + 24, surface.get_height() + 10), pygame.SRCALPHA)
            back.fill((0, 0, 0, 150))
            x = (width - back.get_width()) // 2
            screen.blit(back, (x, y))
            screen.blit(surface, (x + 12, y + 5))
            y += back.get_height() + 6


notifications = Notifications()
