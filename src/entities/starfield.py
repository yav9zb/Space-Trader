import math
import random

import pygame

# Layers from far to near: (share of the stars, parallax factor, radius, brightness range)
LAYERS = (
    (0.55, 0.04, 1, (70, 140)),
    (0.33, 0.10, 1, (120, 210)),
    (0.12, 0.22, 2, (190, 255)),
)

# Most stars are white; a few are warm or cool, which is what makes a
# starfield look real
TINTS = (
    (1.0, 1.0, 1.0), (1.0, 1.0, 1.0), (1.0, 1.0, 1.0), (1.0, 1.0, 1.0),
    (0.75, 0.85, 1.0), (0.75, 0.85, 1.0),            # blue-white
    (1.0, 0.9, 0.7), (1.0, 0.78, 0.6),               # yellow, orange
)


class StarField:
    """Parallax starfield: three depth layers that scroll at different speeds,
    tinted stars, and a gentle twinkle on the nearer ones."""

    def __init__(self, num_stars, screen_width, screen_height):
        self.stars = []     # [x, y, brightness, layer, tint, twinkle phase]
        for layer, (share, _, _, (low, high)) in enumerate(LAYERS):
            for _ in range(max(1, int(num_stars * share))):
                self.stars.append([
                    random.randint(0, screen_width),
                    random.randint(0, screen_height),
                    random.randint(low, high),
                    layer,
                    random.choice(TINTS),
                    random.uniform(0, math.tau),
                ])

        self.screen_width = screen_width
        self.screen_height = screen_height

    def draw(self, screen, camera_offset):
        """Draw stars; nearer layers move faster than distant ones."""
        now = pygame.time.get_ticks() / 1000.0
        width, height = self.screen_width, self.screen_height
        for x, y, brightness, layer, tint, phase in self.stars:
            _, parallax, radius, _ = LAYERS[layer]
            px = int((x - camera_offset.x * parallax) % width)
            py = int((y - camera_offset.y * parallax) % height)

            level = brightness
            if layer > 0:
                level = brightness * (0.82 + 0.18 * math.sin(now * (1.2 + layer) + phase))
            color = (int(level * tint[0]), int(level * tint[1]), int(level * tint[2]))
            if radius == 1:
                screen.set_at((px, py), color)
            else:
                pygame.draw.circle(screen, color, (px, py), radius)
                # a faint cross makes the brightest stars sparkle
                dim = (color[0] // 3, color[1] // 3, color[2] // 3)
                for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
                    qx, qy = px + dx, py + dy
                    if 0 <= qx < screen.get_width() and 0 <= qy < screen.get_height():
                        screen.set_at((qx, qy), dim)
