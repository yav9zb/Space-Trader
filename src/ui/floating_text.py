"""Short-lived text that drifts up from a point in the world and fades: the
"+150 cr" that pops when a pirate pays out."""

import pygame
from pygame import Vector2

LIFETIME = 1.4
RISE = 46.0          # pixels over its life
MAX_ACTIVE = 24


class FloatingTexts:
    def __init__(self):
        self.items = []         # [world position, text, color, age]
        self._font = None

    def add(self, position, text: str, color=(255, 225, 120)):
        self.items.append([Vector2(position), text, color, 0.0])
        del self.items[:-MAX_ACTIVE]

    def update(self, delta_time: float):
        for item in self.items:
            item[3] += delta_time
        self.items = [item for item in self.items if item[3] < LIFETIME]

    def clear(self):
        self.items.clear()

    def draw(self, screen: pygame.Surface, camera_offset: Vector2):
        if not self.items:
            return
        if self._font is None:
            from . import fonts
            self._font = fonts.exact(18)
        for position, text, color, age in self.items:
            t = age / LIFETIME
            at = position - camera_offset - Vector2(0, RISE * t)
            fade = 1.0 - max(0.0, (t - 0.55) / 0.45)            # holds, then fades over the last 45%
            shadow = self._font.render(text, True, (0, 0, 10))
            label = self._font.render(text, True, color)
            for surface in (shadow, label):
                surface.set_alpha(int(255 * fade))
            x = int(at.x - label.get_width() / 2)
            screen.blit(shadow, (x + 1, int(at.y) + 1))
            screen.blit(label, (x, int(at.y)))


floating_texts = FloatingTexts()
