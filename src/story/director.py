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


def _matches(npc: NPC, station, game_engine) -> bool:
    if get_station_faction(station, game_engine.world_seed) != npc.faction:
        return False
    if npc.station_types and station.station_type.value not in npc.station_types:
        return False
    return npc.min_ring <= _ring(station, game_engine.universe) <= npc.max_ring


def find_station_by_name(name: str, universe):
    for station in universe.stations:
        if station.name == name:
            return station
    return None


def _pick_sector(npc: NPC, game_engine):
    """Deterministically choose a sector in the NPC's ring and faction. The
    ring widens if none qualifies (factions form 4x4 regions, so a narrow
    ring can occasionally miss a faction entirely)."""
    seed = game_engine.world_seed
    for extra in range(0, 13):
        ring_lo = npc.min_ring
        ring_hi = npc.max_ring + extra
        candidates = []
        for cx in range(-ring_hi, ring_hi + 1):
            for cy in range(-ring_hi, ring_hi + 1):
                if not (ring_lo <= max(abs(cx), abs(cy)) <= ring_hi):
                    continue
                if get_controlling_faction(cx, cy, seed) != npc.faction:
                    continue
                order = zlib.crc32(f"{seed}_{npc.id}_{cx}_{cy}".encode())
                candidates.append((order, cx, cy))
        if candidates:
            _, cx, cy = min(candidates)
            return cx, cy
    return None


def place_npc(npc: NPC, game_engine):
    """Find or create the station for an NPC and remember it. Returns the
    station, or None if no suitable sector could be found."""
    story = game_engine.story_state
    universe = game_engine.universe

    remembered = story.npc_stations.get(npc.id)
    if remembered:
        station = find_station_by_name(remembered, universe)
        if station is not None:
            return station

    candidates = [s for s in universe.stations if _matches(npc, s, game_engine)]
    if candidates:
        station = min(candidates, key=lambda s: (_ring(s, universe), s.name))
    else:
        sector = _pick_sector(npc, game_engine)
        if sector is None:
            return None
        from ..entities.station import StationType
        wanted = StationType(npc.station_types[0]) if npc.station_types else None
        station = universe.ensure_station_in_sector(sector[0], sector[1], wanted)

    story.npc_stations[npc.id] = station.name
    return station


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
