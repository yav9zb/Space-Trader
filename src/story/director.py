"""Places story contacts in the world and decides which conversation to open.

Contacts are placed when their chapter begins (and on game start / load, to
catch anything not yet placed) and the chosen station name is stored in
StoryState, so they stay at the same station for the rest of the campaign.
"""

import zlib
from typing import Optional

from ..factions import get_station_faction, get_controlling_faction
from .npcs import NPCS, NPC, is_available


def _ring(station, universe) -> int:
    cx = int(station.position.x // universe.sector_size)
    cy = int(station.position.y // universe.sector_size)
    return max(abs(cx), abs(cy))


def _matches(spec, station, game_engine) -> bool:
    """spec is anything with faction, station_types, min_ring and max_ring
    (an NPC or a mission Waypoint)."""
    if get_station_faction(station, game_engine.world_seed) != spec.faction:
        return False
    if spec.station_types and station.station_type.value not in spec.station_types:
        return False
    return spec.min_ring <= _ring(station, game_engine.universe) <= spec.max_ring


def find_station_by_name(name: str, universe):
    for station in universe.stations:
        if station.name == name:
            return station
    return None


def _pick_sector(key: str, spec, game_engine, excluded=()):
    """Deterministically choose a sector in the NPC's ring and faction. The
    ring widens if none qualifies (factions form 4x4 regions, so a narrow
    ring can occasionally miss a faction entirely)."""
    seed = game_engine.world_seed
    for extra in range(0, 13):
        ring_lo = spec.min_ring
        ring_hi = spec.max_ring + extra
        candidates = []
        for cx in range(-ring_hi, ring_hi + 1):
            for cy in range(-ring_hi, ring_hi + 1):
                if not (ring_lo <= max(abs(cx), abs(cy)) <= ring_hi):
                    continue
                if (cx, cy) in excluded or get_controlling_faction(cx, cy, seed) != spec.faction:
                    continue
                order = zlib.crc32(f"{seed}_{key}_{cx}_{cy}".encode())
                candidates.append((order, cx, cy))
        if candidates:
            _, cx, cy = min(candidates)
            return cx, cy
    return None


def place_story_station(key: str, spec, game_engine):
    """Find or create a station satisfying spec and remember it under key.
    Stations already claimed by another story key are skipped, so two
    contacts (or a contact and a waypoint) never share a station. Returns the
    station, or None if no suitable sector could be found."""
    story = game_engine.story_state
    universe = game_engine.universe

    remembered = story.npc_stations.get(key)
    if remembered:
        station = find_station_by_name(remembered, universe)
        if station is not None:
            return station

    taken = {name for k, name in story.npc_stations.items() if k != key}
    candidates = [
        s for s in universe.stations
        if s.name not in taken and _matches(spec, s, game_engine)
    ]
    if candidates:
        station = min(candidates, key=lambda s: (_ring(s, universe), s.name))
    else:
        from ..entities.station import StationType
        wanted = StationType(spec.station_types[0]) if spec.station_types else None
        excluded = set()
        station = None
        for _ in range(30):
            sector = _pick_sector(key, spec, game_engine, excluded)
            if sector is None:
                return None
            candidate = universe.ensure_station_in_sector(sector[0], sector[1], wanted)
            if candidate.name not in taken:
                station = candidate
                break
            excluded.add(sector)   # that sector's station belongs to another story key
        if station is None:
            return None

    story.npc_stations[key] = station.name
    return station


def place_npc(npc: NPC, game_engine):
    return place_story_station(npc.id, npc, game_engine)


def ensure_npcs_placed(game_engine):
    """Place every currently available NPC that has no station yet. Safe to
    call repeatedly; tolerates engines without a universe (unit tests)."""
    if not hasattr(game_engine, "universe") or game_engine.universe is None:
        return
    for npc in NPCS.values():
        if is_available(npc, game_engine.story_state):
            place_npc(npc, game_engine)


def get_contact_at(station, game_engine) -> Optional[NPC]:
    """The NPC (if any) waiting at this station."""
    story = game_engine.story_state
    for npc in NPCS.values():
        if is_available(npc, story) and story.npc_stations.get(npc.id) == station.name:
            return npc
    return None


def start_node_for(npc: NPC, story_state) -> str:
    return npc.return_node if story_state.has_seen(npc.intro_node) else npc.intro_node


def start_contact_dialogue(npc: NPC, game_engine):
    game_engine.start_dialogue(start_node_for(npc, game_engine.story_state))
