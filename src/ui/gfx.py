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


def snap_radius(radius) -> int:
    """Round a size to a nearby step (finer when small), so an effect whose
    size drifts every frame uses a handful of cached surfaces instead of
    building a new one each frame."""
    radius = int(radius)
    if radius < 16:
        return radius
    step = 1 + radius // 16
    return int(round(radius / step)) * step


def snap_color(color):
    """Round each channel to the nearest multiple of 8 (0 and 255 stay put)."""
    return tuple(255 if c >= 252 else int(c / 8 + 0.5) * 8 for c in clamp_color(color))


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
    radius = snap_radius(radius)
    surface = glow_surface(radius, snap_color(tuple(c * min(1.0, strength) for c in color[:3])))
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
_rings = {}
_panels = {}


def panel_surface(width: int, height: int, background, alpha: int, radius: int) -> pygame.Surface:
    """A translucent panel with a soft vertical gradient (a little lighter at
    the top) and rounded corners. Cached by size, so panels cost one blit."""
    width, height, alpha, radius = max(2, int(width)), max(2, int(height)), int(alpha), int(radius)
    background = clamp_color(background)

    def build():
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        top = lighten(background, 0.16)
        for y in range(height):
            t = min(1.0, y / max(1, height * 0.55))
            surface.fill((*mix(top, background, t), alpha), (0, y, width, 1))
        mask = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, width, height), border_radius=radius)
        surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        return surface

    return _bounded(_panels, (width, height, background, alpha, radius), build)


def draw_corner_accents(screen: pygame.Surface, rect, color, length: int = 10, thickness: int = 2):
    """Short bright brackets on a panel's four corners."""
    rect = pygame.Rect(rect)
    length = max(4, min(length, rect.width // 3, rect.height // 3))
    x0, y0, x1, y1 = rect.left, rect.top, rect.right - 1, rect.bottom - 1
    for (cx, cy, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        pygame.draw.line(screen, color, (cx, cy), (cx + dx * length, cy), thickness)
        pygame.draw.line(screen, color, (cx, cy), (cx, cy + dy * length), thickness)


def ring_glow(radius: int, width: int, color) -> pygame.Surface:
    """A soft glowing ring (bright at `radius`, fading on both sides), black
    elsewhere, for additive blitting. Used for accretion disks and shockwaves."""
    radius, width = max(3, int(radius)), max(1, int(width))
    color = clamp_color(color)

    def build():
        reach = radius + width * 2
        size = reach * 2
        surface = pygame.Surface((size, size))
        surface.fill((0, 0, 0))
        steps = width * 4
        for i in range(steps + 1):
            offset = (i / steps - 0.5) * 2 * width * 2          # -2w .. +2w around the ring
            level = max(0.0, 1.0 - abs(offset) / (width * 2)) ** 2
            r = int(radius + offset)
            if r > 0 and level > 0:
                pygame.draw.circle(surface, tuple(int(c * level) for c in color), (reach, reach), r, 2)
        return surface

    return _bounded(_rings, (radius, width, color), build)


def draw_ring_glow(screen: pygame.Surface, pos, radius, width, color, strength: float = 1.0):
    radius = int(radius)
    if radius < 3 or strength <= 0:
        return
    radius = snap_radius(radius)
    color = snap_color(tuple(c * min(1.0, strength) for c in color[:3]))
    surface = ring_glow(radius, width, color)
    half = surface.get_width() // 2
    screen.blit(surface, (int(pos[0]) - half, int(pos[1]) - half), special_flags=pygame.BLEND_RGB_ADD)


def draw_bar(screen: pygame.Surface, rect, fraction: float, color,
             background=(16, 20, 32), border=(110, 125, 150)):
    """A status bar: dark trough, a fill with a lighter top edge so it has
    some volume, and a thin border."""
    rect = pygame.Rect(rect)
    fraction = max(0.0, min(1.0, fraction))
    radius = max(1, rect.height // 3)
    pygame.draw.rect(screen, background, rect, border_radius=radius)
    fill_width = int(rect.width * fraction)
    if fill_width > 1:
        fill = pygame.Rect(rect.x, rect.y, fill_width, rect.height)
        pygame.draw.rect(screen, color, fill, border_radius=radius)
        highlight = pygame.Rect(rect.x + 1, rect.y + 1, max(0, fill_width - 2), max(1, rect.height // 3))
        pygame.draw.rect(screen, lighten(color, 0.45), highlight, border_radius=radius)
    pygame.draw.rect(screen, border, rect, 1, border_radius=radius)


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
    _rings.clear()
    _panels.clear()
