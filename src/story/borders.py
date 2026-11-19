"""Changing who controls a region: the helper the story, dialogue and
liberation missions all go through.
"""

from typing import Optional, Tuple

from pygame import Vector2

from ..factions import (
    FACTION_REGION_SECTORS, get_controlling_faction, region_of_sector,
)
from .story_state import story_state

SEARCH_RADIUS = 6   # regions


def region_center(region: Tuple[int, int]) -> Vector2:
    """World position of the middle of a region."""
    half = FACTION_REGION_SECTORS * 1000 / 2
    return Vector2(region[0] * FACTION_REGION_SECTORS * 1000 + half,
                   region[1] * FACTION_REGION_SECTORS * 1000 + half)


def describe_region(region: Tuple[int, int]) -> str:
    """The region as the player sees it: the sector at its middle, using the
    same convention as the Navigation HUD."""
    center = region_center(region)
    return f"the region around Sector ({int(center.x // 1000)}, {int(-center.y // 1000)})"


def flip_region(region: Tuple[int, int], faction: str):
    """Hand a region to a faction and say so on screen."""
    story_state.set_region_override(region, faction)
    story_state.record_event("region_flipped", region=list(region), faction=faction)

    from ..ui.notifications import notifications
    notifications.push(f"Borders shift: {describe_region(region)} is now {faction} space",
                       duration=7.0, color=(150, 200, 255))


def nearest_region(position: Vector2, faction: str, world_seed) -> Optional[Tuple[int, int]]:
    """The region controlled by faction whose middle is closest to position."""
    here = region_of_sector(int(position.x // 1000), int(position.y // 1000))
    best, best_distance = None, None
    for rx in range(here[0] - SEARCH_RADIUS, here[0] + SEARCH_RADIUS + 1):
        for ry in range(here[1] - SEARCH_RADIUS, here[1] + SEARCH_RADIUS + 1):
            center = region_center((rx, ry))
            sector = (int(center.x // 1000), int(center.y // 1000))
            if get_controlling_faction(sector[0], sector[1], world_seed) != faction:
                continue
            distance = (center - position).length()
            if best_distance is None or distance < best_distance:
                best, best_distance = (rx, ry), distance
    return best


def flip_nearest_region(game_engine, from_faction: str, to_faction: str) -> bool:
    region = nearest_region(game_engine.ship.position, from_faction, game_engine.world_seed)
    if region is None:
        return False
    flip_region(region, to_faction)
    return True
