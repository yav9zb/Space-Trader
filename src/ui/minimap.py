"""The local radar: a circular minimap centred on the ship, north up.

Stations, planets, hazards, ships and mission objectives each have their own
marker; objectives beyond the radar's range are pinned to its rim with an arrow.
Nothing is labelled on the map itself (names would overprint each other); the
range is written in a caption under it.
"""

import math
from typing import Iterable, List, Optional, Tuple

import pygame
from pygame import Vector2

try:
    from .ui_layout import UILayout, Anchor
    from .ui_theme import ui_theme
    from . import gfx, fonts
except ImportError:         # run as a plain script
    from ui_layout import UILayout, Anchor
    from ui_theme import ui_theme
    import gfx, fonts

RIM = (95, 150, 225)
BACKGROUND = (6, 12, 34)
GRID = (30, 52, 96)

# kind -> colour
COLORS = {
    "station": (235, 235, 240),
    "planet": (110, 130, 255),
    "hostile": (255, 80, 70),
    "patrol": (90, 190, 255),
    "trader": (170, 200, 170),
    "hazard_radioactive": (90, 240, 110),
    "hazard_explosive": (255, 150, 60),
    "hazard": (95, 100, 120),
    "blackhole": (170, 100, 255),
    "objective": (255, 215, 120),
}

Contact = Tuple[str, Vector2]       # (kind, world position)


def gather_contacts(game_engine, view_radius: float) -> List[Contact]:
    """The ships, hazards and objectives the radar should show, from the live game."""
    from ..combat.combat_manager import combat_manager
    from ..entities.asteroid import AsteroidType
    from ..entities.bandit import BanditState
    from . import objective_pointer

    here = game_engine.ship.position
    reach = view_radius * 1.05
    contacts: List[Contact] = []

    def near(position):
        return (position - here).length_squared() <= reach * reach

    for bandit in combat_manager.active_bandits:
        if bandit.state != BanditState.DISABLED and near(bandit.position):
            contacts.append(("hostile", Vector2(bandit.position)))
    for patrol in combat_manager.active_patrols:
        if near(patrol.position):
            contacts.append(("patrol", Vector2(patrol.position)))
    for trader in combat_manager.active_traders:
        if near(trader.position):
            contacts.append(("trader", Vector2(trader.position)))
    for asteroid in combat_manager.active_asteroids:
        if not near(asteroid.position):
            continue
        kind = {AsteroidType.RADIOACTIVE: "hazard_radioactive",
                AsteroidType.EXPLOSIVE: "hazard_explosive"}.get(asteroid.asteroid_type, "hazard")
        contacts.append((kind, Vector2(asteroid.position)))
    for hole in combat_manager.active_black_holes:
        if near(hole.position):
            contacts.append(("blackhole", Vector2(hole.position)))
    for _, position in objective_pointer.all_objectives(game_engine):
        contacts.append(("objective", Vector2(position)))
    return contacts


class Minimap:
    def __init__(self, screen_width, screen_height, map_size=150, ratio: float = 1.0):
        self.ratio = ratio           # pixels per point when drawing at full resolution
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.base_size = map_size
        self.view_radius = 2000
        self.ui_layout = UILayout(screen_width, screen_height)
        ui_theme.update_scale(self.ui_layout.font_scale)
        self._layout()

    # Geometry ---------------------------------------------------------------------

    def _layout(self):
        """Everything that depends on the window size."""
        # About a fifth of the window's short side, within sensible bounds
        short_side = min(self.screen_width, self.screen_height)
        self.map_size = round(max(110, min(280, int(short_side / self.ratio * 0.22))) * self.ratio)
        point_scale = UILayout(round(self.screen_width / self.ratio), round(self.screen_height / self.ratio)).font_scale
        self.caption_font = fonts.exact(round(max(11, round(12 * max(0.9, point_scale))) * self.ratio))
        self.caption_height = self.caption_font.get_height() + round(6 * self.ratio)
        self.total_height = self.map_size + self.caption_height
        map_x, map_y = self.ui_layout.get_position(Anchor.TOP_RIGHT, self.map_size, self.total_height, 0, round(60 * self.ratio))
        self.position = Vector2(map_x, map_y)
        self.center = Vector2(self.map_size / 2, self.map_size / 2)
        self.radius = self.map_size / 2 - 4 * self.ratio
        self.scale = self.radius / self.view_radius
        self.surface = pygame.Surface((self.map_size, self.total_height), pygame.SRCALPHA)
        self._backdrop = None

    @property
    def rect(self) -> pygame.Rect:
        """Everything the minimap occupies on screen, caption included."""
        return pygame.Rect(int(self.position.x), int(self.position.y), self.map_size, self.total_height)

    def world_to_local_map_coords(self, world_pos, ship_pos):
        relative = world_pos - ship_pos
        return Vector2(self.center.x + relative.x * self.scale, self.center.y + relative.y * self.scale)

    def _is_in_minimap(self, pos) -> bool:
        return (pos - self.center).length() <= self.radius

    # Drawing -----------------------------------------------------------------------

    def _backdrop_surface(self) -> pygame.Surface:
        """The static part: a dark disc with range rings, crosshair and rim."""
        if self._backdrop is None:
            size = self.map_size
            surface = pygame.Surface((size, size), pygame.SRCALPHA)
            c = (int(self.center.x), int(self.center.y))
            r = int(self.radius)
            for i in range(r, 0, -1):               # a gentle glow toward the middle
                t = 1 - i / r
                pygame.draw.circle(surface, (*gfx.mix((4, 8, 24), (14, 30, 66), t), 215), c, i)
            k = self.ratio
            thin, thick = max(1, round(k)), max(2, round(2 * k))
            for fraction in (1 / 3, 2 / 3):
                pygame.draw.circle(surface, GRID, c, int(r * fraction), thin)
            pygame.draw.line(surface, GRID, (c[0] - r, c[1]), (c[0] + r, c[1]), thin)
            pygame.draw.line(surface, GRID, (c[0], c[1] - r), (c[0], c[1] + r), thin)
            pygame.draw.circle(surface, RIM, c, r, thick)
            for angle in range(0, 360, 45):          # rim ticks
                a = math.radians(angle)
                inner = r - round((6 if angle % 90 == 0 else 3) * k)
                pygame.draw.line(surface, RIM, (c[0] + math.cos(a) * inner, c[1] + math.sin(a) * inner),
                                 (c[0] + math.cos(a) * r, c[1] + math.sin(a) * r), thin)
            self._backdrop = surface
        return self._backdrop

    def _marker(self, kind: str, at: Vector2, scale_hint: float = 1.0):
        k = self.ratio
        color = COLORS.get(kind, (200, 200, 200))
        x, y = int(at.x), int(at.y)
        surface = self.surface
        n = lambda v: max(1, round(v * k))             # a size in points, in pixels
        edge = max(1, round(k))
        if kind == "station":
            half = n(3)
            pygame.draw.rect(surface, color, (x - half, y - half, 2 * half + 1, 2 * half + 1))
            pygame.draw.rect(surface, gfx.darken(color, 0.55), (x - half, y - half, 2 * half + 1, 2 * half + 1), edge)
        elif kind == "planet":
            radius = max(n(3), int(n(4) * scale_hint))
            pygame.draw.circle(surface, color, (x, y), radius)
            pygame.draw.circle(surface, gfx.lighten(color, 0.4), (x, y), radius, edge)
        elif kind in ("hostile", "patrol"):
            pts = [(x, y - n(5)), (x - n(4), y + n(4)), (x + n(4), y + n(4))]
            pygame.draw.polygon(surface, color, pts)
            pygame.draw.polygon(surface, gfx.darken(color, 0.5), pts, edge)
        elif kind == "trader":
            pygame.draw.circle(surface, color, (x, y), n(2))
        elif kind == "blackhole":
            pygame.draw.circle(surface, (0, 0, 0), (x, y), n(4))
            pygame.draw.circle(surface, color, (x, y), n(5), edge)
        elif kind == "objective":
            pts = [(x, y - n(6)), (x + n(6), y), (x, y + n(6)), (x - n(6), y)]
            gfx.draw_glow(surface, (x, y), n(11), color, 0.9)
            pygame.draw.polygon(surface, color, pts)
            pygame.draw.polygon(surface, (60, 45, 15), pts, edge)
        else:                                       # hazards
            pygame.draw.circle(surface, color, (x, y), n(2) if kind != "hazard" else n(1))

    # Marker order: things you need to see last, so nothing important is hidden
    ORDER = ["hazard", "planet", "hazard_radioactive", "hazard_explosive", "blackhole", "station",
             "trader", "patrol", "hostile", "objective"]

    def draw(self, screen, ship, stations, planets, contacts: Optional[Iterable[Contact]] = None):
        surface = self.surface
        surface.fill((0, 0, 0, 0))
        surface.blit(self._backdrop_surface(), (0, 0))
        ship_pos = ship.position
        r2 = self.radius * self.radius
        c = Vector2(self.center)

        items: List[Tuple[str, Vector2, float]] = []
        for planet in planets:
            at = self.world_to_local_map_coords(planet.position, ship_pos)
            if (at - c).length_squared() <= r2:
                items.append(("planet", at, 1.0 + planet.size / 120.0))
        for station in stations:
            at = self.world_to_local_map_coords(station.position, ship_pos)
            if (at - c).length_squared() <= r2:
                items.append(("station", at, 1.0))
        edge: List[Vector2] = []
        for kind, world in (contacts or []):
            at = self.world_to_local_map_coords(world, ship_pos)
            if (at - c).length_squared() <= r2:
                items.append((kind, at, 1.0))
            elif kind == "objective":
                edge.append(at)
        items.sort(key=lambda item: self.ORDER.index(item[0]) if item[0] in self.ORDER else 0)
        for kind, at, hint in items:
            self._marker(kind, at, hint)

        # Objectives out of range: an arrow on the rim pointing outward
        for at in edge:
            direction = (at - c)
            if direction.length_squared() == 0:
                continue
            direction = direction.normalize()
            tip = c + direction * (self.radius - 1)
            side = Vector2(-direction.y, direction.x)
            base = tip - direction * 9 * self.ratio
            pts = [tip, base + side * 5 * self.ratio, base - side * 5 * self.ratio]
            pygame.draw.polygon(surface, COLORS["objective"], pts)
            pygame.draw.polygon(surface, (60, 45, 15), pts, 1)

        # A faint sweep, for life
        sweep = (pygame.time.get_ticks() / 1000.0 * 70.0) % 360
        for i, fade in enumerate((0.6, 0.35, 0.15)):
            a = math.radians(sweep - i * 8)
            end = c + Vector2(math.cos(a), math.sin(a)) * (self.radius - 2)
            pygame.draw.line(surface, (*gfx.mix((10, 20, 40), (90, 200, 255), fade), 255), c, end, max(1, round(self.ratio)))

        # The ship: a wedge pointing the way it faces
        pts = [Vector2(0, -7), Vector2(-4.5, 5), Vector2(0, 2.5), Vector2(4.5, 5)]
        pts = [c + (p * self.ratio).rotate(ship.rotation) for p in pts]
        gfx.draw_glow(surface, c, round(12 * self.ratio), (60, 255, 120), 0.45)
        pygame.draw.polygon(surface, (90, 255, 130), pts)
        pygame.draw.polygon(surface, (20, 90, 40), pts, 1)

        # Caption under the disc: the range, never on top of the map
        text = f"RANGE {self.view_radius / 1000:g} km"
        label = self.caption_font.render(text, True, (150, 170, 205))
        surface.blit(label, ((self.map_size - label.get_width()) // 2, self.map_size + round(2 * self.ratio)))

        screen.blit(surface, (int(self.position.x), int(self.position.y)))

    def set_view_radius(self, radius):
        self.view_radius = max(500, min(5000, radius))
        self.scale = self.radius / self.view_radius

    def resize(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.ui_layout.resize(screen_width, screen_height)
        ui_theme.update_scale(self.ui_layout.font_scale)
        self._layout()
