"""Deterministic faction control over the sector grid. Sectors are the same
1000-unit grid already used for chunk generation and shown as "Sector: (x, y)"
in the Navigation HUD - this just answers "who controls it," computed on
demand from the world seed rather than stored anywhere.
"""

import random
import zlib

FACTION_TRADE_GUILD = "Trade Guild"
FACTION_INDEPENDENT = "Independent"
FACTION_PIRATE = "Pirate Territory"

# Sectors are grouped into NxN blocks so territory reads as a contiguous
# region on the map rather than flickering faction-by-faction between
# adjacent sectors.
FACTION_REGION_SECTORS = 4

_FACTION_WEIGHTS = [
    (FACTION_TRADE_GUILD, 35),
    (FACTION_INDEPENDENT, 40),
    (FACTION_PIRATE, 25),
]

# Sectors within this many chunks of the origin are always Independent, so
# the starting area is never pirate territory - mirrors the start_distance
# guard universe.py already uses to keep bandit encounters away from spawn.
SAFE_ZONE_SECTORS = 2

FACTION_TRADER_SPAWN_MULTIPLIER = {
    FACTION_TRADE_GUILD: 2.5,
    FACTION_INDEPENDENT: 1.0,
    FACTION_PIRATE: 0.2,
}

FACTION_BANDIT_SPAWN_MULTIPLIER = {
    FACTION_TRADE_GUILD: 0.5,
    FACTION_INDEPENDENT: 1.0,
    FACTION_PIRATE: 1.6,
}


# Regions whose control has been changed by the story or the player. Kept in
# StoryState (so it saves and loads) and mirrored here so the many callers of
# get_controlling_faction need no extra argument.
_region_overrides = {}


def set_region_override(region, faction: str):
    _region_overrides[tuple(region)] = faction


def clear_region_overrides():
    _region_overrides.clear()


def region_of_sector(chunk_x: int, chunk_y: int):
    return (chunk_x // FACTION_REGION_SECTORS, chunk_y // FACTION_REGION_SECTORS)


def get_controlling_faction(chunk_x: int, chunk_y: int, world_seed) -> str:
    """Deterministically map a sector to its controlling faction. Uses a
    local Random instance (not the global `random` module) since this is
    called far more often than generation itself - e.g. every HUD frame -
    and must not disturb the global RNG stream chunk generation relies on.
    """
    if abs(chunk_x) <= SAFE_ZONE_SECTORS and abs(chunk_y) <= SAFE_ZONE_SECTORS:
        return FACTION_INDEPENDENT

    region_x = chunk_x // FACTION_REGION_SECTORS
    region_y = chunk_y // FACTION_REGION_SECTORS
    if (region_x, region_y) in _region_overrides:
        return _region_overrides[(region_x, region_y)]
    seed_string = f"{world_seed}_faction_{region_x}_{region_y}"
    seed = zlib.crc32(seed_string.encode()) & 0x7FFFFFFF

    rng = random.Random(seed)
    names = [name for name, _ in _FACTION_WEIGHTS]
    weights = [weight for _, weight in _FACTION_WEIGHTS]
    return rng.choices(names, weights=weights, k=1)[0]


def get_station_faction(station, world_seed) -> str:
    """Which faction controls the sector a station sits in. Uses the same
    raw (non-inverted) chunk coordinates universe.py uses for generation -
    the y-inversion in the Navigation HUD is a display-only concern.
    """
    chunk_x = int(station.position.x // 1000)
    chunk_y = int(station.position.y // 1000)
    return get_controlling_faction(chunk_x, chunk_y, world_seed)


def get_faction_price_multiplier(standing: int) -> float:
    """Price multiplier from standing with the faction controlling a
    station's sector - allied factions discount, hostile ones charge a
    markup. Stacks with (multiplies against) the existing station-type
    discount in upgrade_system.py rather than replacing it.
    """
    if standing >= 60:
        return 0.90
    if standing >= 25:
        return 0.95
    if standing <= -60:
        return 1.25
    if standing <= -25:
        return 1.10
    return 1.0


# Standing at or below this makes a faction hostile: its patrols attack you
# and, for factions that police their stations, docking is refused.
HOSTILE_STANDING = -60

# Independent stations always welcome you, so a hostile player always has a
# safe place to trade and earn their way back.
DOCKING_REFUSING_FACTIONS = (FACTION_TRADE_GUILD, FACTION_PIRATE)


def is_hostile(standing: int) -> bool:
    return standing <= HOSTILE_STANDING


def docking_refusal(faction: str, standing: int):
    """Message explaining why a station of this faction won't let you dock,
    or None if docking is allowed."""
    if faction in DOCKING_REFUSING_FACTIONS and is_hostile(standing):
        return f"{faction} has barred you from its stations"
    return None
