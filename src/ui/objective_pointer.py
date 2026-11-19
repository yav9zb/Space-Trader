"""A small arrow around the ship pointing at the current mission objective,
with its name and distance. The target comes from the active missions'
destination (a station name or a "Sector (x, y)" label); the geometry is plain
functions so it can be tested without a screen.
"""

import math
import re
from typing import List, Optional, Tuple

import pygame
from pygame import Vector2

RING_RADIUS = 95            # pixels from the ship to the arrow
HIDE_WITHIN = 450           # world units: close enough to see, no arrow needed
COLOR = (255, 215, 120)

_SECTOR = re.compile(r"Sector \((-?\d+), (-?\d+)\)")


def sector_center(x: int, y: int) -> Vector2:
    """World position of the middle of a sector as the HUD labels it (y is
    shown inverted)."""
    return Vector2(x * 1000 + 500, -(y * 1000 + 500))


def target_position(destination: Optional[str], stations) -> Optional[Vector2]:
    """Where a mission destination is: a station by name, or a sector's middle."""
    if not destination:
        return None
    match = _SECTOR.fullmatch(destination)
    if match:
        return sector_center(int(match.group(1)), int(match.group(2)))
    for station in stations:
        if station.name == destination:
            return Vector2(station.position)
    return None


def all_objectives(game_engine) -> List[Tuple[str, Vector2]]:
    """Every active mission objective that has a place, story missions first.
    Used to mark them on the large map."""
    stations = game_engine.universe.stations
    missions = list(game_engine.mission_manager.active_missions)
    missions.sort(key=lambda m: 0 if getattr(m, "story_id", None) else 1)
    found = []
    for mission in missions:
        destination = getattr(mission, "destination_station_id", None)
        position = target_position(destination, stations)
        if position is not None and all(label != destination for label, _ in found):
            found.append((destination, position))
    return found


def edge_point(center: Vector2, target: Vector2, rect: pygame.Rect) -> Vector2:
    """Where the line from center toward target leaves rect (or the target
    itself if it is inside). center must be inside rect."""
    delta = target - center
    scale = 1.0
    for d, c, low, high in ((delta.x, center.x, rect.left, rect.right),
                            (delta.y, center.y, rect.top, rect.bottom)):
        if d > 0:
            scale = min(scale, (high - c) / d)
        elif d < 0:
            scale = min(scale, (low - c) / d)
    return center + delta * max(0.0, scale)


def current_objective(game_engine) -> Optional[Tuple[str, Vector2]]:
    """(label, world position) of the objective to point at: the first active
    story mission with somewhere to go, else the first other mission."""
    stations = game_engine.universe.stations
    missions = list(game_engine.mission_manager.active_missions)
    missions.sort(key=lambda m: 0 if getattr(m, "story_id", None) else 1)
    for mission in missions:
        destination = getattr(mission, "destination_station_id", None)
        position = target_position(destination, stations)
        if position is not None:
            return destination, position
    return None


def pointer_points(ship_screen: Vector2, direction: Vector2, size: int = 11) -> List[Vector2]:
    """Triangle pointing along direction, sitting on the ring around the ship."""
    forward = direction.normalize()
    side = Vector2(-forward.y, forward.x)
    centre = ship_screen + forward * RING_RADIUS
    return [centre + forward * size,
            centre - forward * size * 0.6 + side * size * 0.7,
            centre - forward * size * 0.6 - side * size * 0.7]


def distance_text(distance: float) -> str:
    return f"{int(distance):,}m"


def draw(surface: pygame.Surface, game_engine, font: pygame.font.Font):
    """Draw the pointer for the current objective, if there is one that is
    not already close."""
    objective = current_objective(game_engine)
    if objective is None:
        return
    label, target = objective
    ship = game_engine.ship
    offset = target - ship.position
    if offset.length() <= HIDE_WITHIN:
        return

    # Not camera.world_to_screen: it wraps at the universe size, which is wrong
    # for a target many sectors away
    ship_screen = ship.position - Vector2(game_engine.camera.get_offset())
    points = pointer_points(ship_screen, offset)
    pygame.draw.polygon(surface, COLOR, points)
    pygame.draw.polygon(surface, (60, 50, 20), points, 1)

    text = font.render(f"{label}  {distance_text(offset.length())}", True, COLOR)
    forward = offset.normalize()
    anchor = ship_screen + forward * (RING_RADIUS + 22)
    rect = text.get_rect(center=(int(anchor.x), int(anchor.y)))
    rect.clamp_ip(surface.get_rect().inflate(-10, -10))
    back = pygame.Surface((rect.width + 10, rect.height + 4), pygame.SRCALPHA)
    back.fill((0, 0, 0, 130))
    surface.blit(back, (rect.x - 5, rect.y - 2))
    surface.blit(text, rect)
