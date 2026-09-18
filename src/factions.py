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
