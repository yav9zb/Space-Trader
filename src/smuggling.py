"""Contraband and Trade Guild cargo inspections.

Military and munitions goods are contraband in Guild space. Docking at a
Guild-controlled station while carrying any risks an inspection: the cargo is
seized, a fine is charged, standing with the Guild drops, and a mission that
was carrying the goods fails. A favored player is inspected less often and a
trusted one is waved through. Pirate markets pay a premium for the same
goods (see economy_events.effect_for), which is what makes the risk worth
taking.
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .factions import FACTION_TRADE_GUILD, get_station_faction
from .trading.commodity import CommodityCategory, commodity_registry

INSPECTION_CHANCE = 0.6
FAVORED_STANDING = 25
FAVORED_CHANCE = 0.3
TRUSTED_STANDING = 60           # inspectors look the other way
FINE_RATE = 0.5                 # of the goods' base value
STANDING_PENALTY = 8


def is_contraband(commodity_id: str) -> bool:
    try:
        return commodity_registry.get_commodity(commodity_id).category == CommodityCategory.MILITARY
    except KeyError:
        return False


def contraband_in_hold(cargo_hold) -> Dict[str, int]:
    return {cid: qty for cid, qty in cargo_hold.items.items() if qty > 0 and is_contraband(cid)}


def inspection_chance(guild_standing: int) -> float:
    if guild_standing >= TRUSTED_STANDING:
        return 0.0
    if guild_standing >= FAVORED_STANDING:
        return FAVORED_CHANCE
    return INSPECTION_CHANCE


@dataclass
class InspectionResult:
    seized: Dict[str, int]
    fine: int
    failed_mission_ids: List[str] = field(default_factory=list)

    def message(self) -> str:
        units = sum(self.seized.values())
        text = f"Guild inspectors seized {units} units of contraband"
        if self.fine:
            text += f" and fined you {self.fine} credits"
        if self.failed_mission_ids:
            text += " - a mission's cargo was lost"
        return text


def inspect(ship, station, game_engine, rng: Optional[random.Random] = None) -> Optional[InspectionResult]:
    """Run a Guild inspection if this station is Guild-controlled and the
    player is carrying contraband. None if nothing happens (including when
    the player slips through)."""
    if get_station_faction(station, game_engine.world_seed) != FACTION_TRADE_GUILD:
        return None
    seized = contraband_in_hold(ship.cargo_hold)
    if not seized:
        return None

    manager = game_engine.mission_manager
    standing = manager.faction_standing.get(FACTION_TRADE_GUILD, 0)
    roll = (rng or random).random()
    if roll >= inspection_chance(standing):
        return None

    value = sum(commodity_registry.get_commodity(cid).base_price * qty for cid, qty in seized.items())
    fine = min(ship.credits, int(value * FINE_RATE))
    ship.credits -= fine

    hold = ship.cargo_hold
    failed = []
    for mission_id, cargo in list(hold.mission_items.items()):
        if any(cid in seized for cid in cargo):
            failed.append(mission_id)
            for cid in list(cargo):
                if cid in seized:
                    del cargo[cid]
            if not cargo:
                del hold.mission_items[mission_id]
    for cid in seized:
        hold.items.pop(cid, None)

    manager.faction_standing[FACTION_TRADE_GUILD] = standing - STANDING_PENALTY
    for mission in manager.active_missions:
        if mission.id in failed:
            from .missions.mission_types import MissionStatus
            mission.status = MissionStatus.FAILED
            mission.progress_description = "The cargo was seized by Guild inspectors"

    game_engine.story_state.record_event("contraband_seized", station=station.name)
    return InspectionResult(seized, fine, failed)
