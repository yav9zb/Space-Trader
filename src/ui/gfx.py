"""Small drawing helpers shared by the entities: soft glows, shaded spheres
and colour utilities. Everything expensive is built once and cached, so the
per-frame cost of an effect is a single blit.
"""

import math

import pygame

_CACHE_LIMIT = 300
_glows = {}
_shades = {}


def clamp_color(color):
    return tuple(max(0, min(255, int(c))) for c in tuple(color)[:3])


def lighten(color, amount):
    """Move a colour toward white (amount 0..1)."""
    return clamp_color(c + (255 - c) * amount for c in color)


def darken(color, amount):
    """Move a colour toward black (amount 0..1)."""
    return clamp_color(c * (1 - amount) for c in color)


def mix(a, b, t):
    return clamp_color(x + (y - x) * t for x, y in zip(a, b))


def _bounded(cache, key, build):
    surface = cache.get(key)
    if surface is None:
        if len(cache) >= _CACHE_LIMIT:
            cache.clear()
        surface = cache[key] = build()
    return surface


def glow_surface(radius: int, color) -> pygame.Surface:
    """A soft round glow, bright in the middle and fading to black. Meant to
    be added to the screen (BLEND_RGB_ADD), so black costs nothing."""
    radius = max(2, int(radius))
    color = clamp_color(color)

    def build():
        size = radius * 2
        surface = pygame.Surface((size, size))
        surface.fill((0, 0, 0))
        steps = max(6, min(radius, 40))
        for i in range(steps):
            t = i / (steps - 1)                     # 0 outside .. 1 centre
            level = t * t * 0.9
            r = max(1, int(radius * (1 - t * 0.97)))
            pygame.draw.circle(surface, tuple(int(c * level) for c in color), (radius, radius), r)
        return surface

    return _bounded(_glows, (radius, color), build)


def draw_glow(screen: pygame.Surface, pos, radius, color, strength: float = 1.0):
    """Add a soft glow centred on pos."""
    radius = int(radius)
    if radius < 2 or strength <= 0:
        return
    surface = glow_surface(radius, tuple(c * min(1.0, strength) for c in color[:3]))
    screen.blit(surface, (int(pos[0]) - radius, int(pos[1]) - radius), special_flags=pygame.BLEND_RGB_ADD)


def sphere_shade(radius: int) -> pygame.Surface:
    """A transparent overlay that darkens the lower right of a disc so a flat
    circle reads as a lit sphere: light from the upper left, soft terminator,
    slightly dark limb."""
    radius = max(3, int(radius))

    def build():
        size = radius * 2
        shade = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(shade, (0, 0, 12, 175), (radius, radius), radius)

        light = pygame.Surface((size, size), pygame.SRCALPHA)
        steps = 40
        for i in range(steps):
            t = i / (steps - 1)
            r = max(2, int(radius * (1.45 - 1.15 * t)))
            offset = radius * (0.12 + 0.30 * t)
            pygame.draw.circle(light, (255, 255, 255, int(190 * t) + 10),
                               (int(radius - offset), int(radius - offset)), r)
        shade.blit(light, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        # Keep the overlay inside the disc
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (radius, radius), radius)
        shade.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        return shade

    return _bounded(_shades, radius, build)


def draw_shaded_sphere_overlay(screen: pygame.Surface, pos, radius):
    radius = int(radius)
    if radius < 3:
        return
    screen.blit(sphere_shade(radius), (int(pos[0]) - radius, int(pos[1]) - radius))


def flicker(seed: float, speed: float = 1.0, low: float = 0.75) -> float:
    """A cheap steady-looking flicker between low and 1.0 based on the clock."""
    t = pygame.time.get_ticks() / 1000.0 * speed + seed
    return low + (1 - low) * (0.5 + 0.5 * math.sin(t * 17.0) * math.sin(t * 5.3 + 1.7))


def draw_engine_flame(screen: pygame.Surface, pos, rotation: float, size: float,
                      outer_color, inner_color, power: float = 1.0, seed: float = 0.0,
                      offset: float = 0.5):
    """A flickering exhaust flame behind a ship that points "up" at rotation 0.
    power scales its length (1.0 is a normal burn)."""
    from pygame import Vector2
    if power <= 0.02:
        return
    jitter = flicker(seed, speed=3.0, low=0.7)
    length = power * jitter

    def polygon(length_scale, width_scale):
        local = [
            Vector2(0, size * offset),
            Vector2(-size * width_scale, size * (offset + length_scale)),
            Vector2(0, size * (offset + length_scale * 1.35)),
            Vector2(size * width_scale, size * (offset + length_scale)),
        ]
        return [p.rotate(rotation) + Vector2(pos) for p in local]

    exhaust = Vector2(0, size * (offset + 0.6 * length)).rotate(rotation) + Vector2(pos)
    draw_glow(screen, exhaust, size * (1.3 + 0.9 * length), outer_color, 0.55)
    pygame.draw.polygon(screen, outer_color, polygon(1.25 * length, 0.5))
    pygame.draw.polygon(screen, inner_color, polygon(0.7 * length, 0.28))


_vignettes = {}


def draw_edge_flash(screen: pygame.Surface, color, strength: float):
    """Tint the edges of the screen, for a hit or a warning. Strength 0..1."""
    if strength <= 0.02:
        return
    width, height = screen.get_size()
    color = clamp_color(color)

    def build():
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        depth = max(20, min(width, height) // 6)
        for i in range(depth):
            alpha = int(150 * (1 - i / depth) ** 2)
            pygame.draw.rect(surface, (*color, alpha), (i, i, width - 2 * i, height - 2 * i), 1)
        return surface

    vignette = _bounded(_vignettes, (width, height, color), build)
    vignette.set_alpha(int(255 * min(1.0, strength)))
    screen.blit(vignette, (0, 0))


def clear_caches():
    _glows.clear()
    _shades.clear()
    _vignettes.clear()
