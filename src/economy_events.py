"""Timed market events that change prices or close trade in a region.

A region is the same 4x4-sector block factions use. Events appear every few
minutes of play near the player, last ten minutes, and are announced as
"Market news" on screen and in the Logbook. Markets read the effect through
StationMarket (see trading/market.py), so the trading screen needs no
special cases.
"""

import random
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

from .factions import (
    FACTION_REGION_SECTORS, FACTION_PIRATE, FACTION_TRADE_GUILD,
    get_controlling_faction, get_station_faction,
)
from .trading.commodity import commodity_registry

EVENT_DURATION = 600.0
FIRST_EVENT_DELAY = 120.0
EVENT_INTERVAL = (300.0, 480.0)
RETRY_DELAY = 60.0
MAX_ACTIVE = 3
BLACK_MARKET_PREMIUM = 1.6

RAID_MULTIPLIER = 1.3
SHORTAGE_MULTIPLIER = 1.7


def region_of(position) -> Tuple[int, int]:
    return (int(position.x // 1000) // FACTION_REGION_SECTORS,
            int(position.y // 1000) // FACTION_REGION_SECTORS)


@dataclass
class EconomyEvent:
    kind: str                       # "raid", "shortage" or "embargo"
    region: Tuple[int, int]
    commodity_id: Optional[str]     # None = every commodity
    multiplier: float
    embargo: bool
    ends_at: float
    headline: str

    def applies_to(self, region, commodity_id) -> bool:
        return (tuple(self.region) == tuple(region)
                and (self.commodity_id is None or self.commodity_id == commodity_id))


class EconomyEvents:
    def __init__(self):
        self.world_seed = None
        self.reset()

    def reset(self):
        self.events: List[EconomyEvent] = []
        self.next_event_at: Optional[float] = None

    # What markets ask -----------------------------------------------------------

    def effect_for(self, station, commodity_id: str):
        """(price multiplier, embargoed) for a commodity at a station."""
        multiplier, embargoed = 1.0, False
        region = region_of(station.position)
        for event in self.events:
            if event.applies_to(region, commodity_id):
                multiplier *= event.multiplier
                embargoed = embargoed or event.embargo

        if self.world_seed is not None:
            from .smuggling import is_contraband
            if (is_contraband(commodity_id)
                    and get_station_faction(station, self.world_seed) == FACTION_PIRATE):
                multiplier *= BLACK_MARKET_PREMIUM
        return multiplier, embargoed

    # Spawning ---------------------------------------------------------------------

    def update(self, game_engine):
        now = game_engine.play_time
        self.events = [e for e in self.events if e.ends_at > now]
        if self.next_event_at is None or now < self.next_event_at - 3600:
            self.next_event_at = now + FIRST_EVENT_DELAY      # first call, or a load rewound time
            return
        if now < self.next_event_at:
            return
        if len(self.events) < MAX_ACTIVE and self._spawn(game_engine, now):
            self.next_event_at = now + random.uniform(*EVENT_INTERVAL)
        else:
            self.next_event_at = now + RETRY_DELAY

    def _spawn(self, game_engine, now) -> bool:
        stations_by_region: Dict[Tuple[int, int], list] = {}
        for station in game_engine.universe.stations:
            stations_by_region.setdefault(region_of(station.position), []).append(station)

        px, py = region_of(game_engine.ship.position)
        nearby = [r for r in stations_by_region if abs(r[0] - px) <= 2 and abs(r[1] - py) <= 2]
        if not nearby:
            return False

        kinds = ["raid", "shortage", "embargo"]
        weights = [0.4, 0.4, 0.2]
        kind = random.choices(kinds, weights)[0]
        if kind == "embargo":
            guild_regions = [r for r in nearby if self._region_faction(r) == FACTION_TRADE_GUILD]
            if not guild_regions:
                kind = "shortage"
            else:
                nearby = guild_regions

        region = random.choice(nearby)
        station = random.choice(stations_by_region[region])
        commodities = commodity_registry.get_all_commodities()
        commodity = random.choice(commodities)

        if kind == "raid":
            event = EconomyEvent("raid", region, None, RAID_MULTIPLIER, False, now + EVENT_DURATION,
                                 f"Pirate raids near {station.name} push prices up 30%")
        elif kind == "shortage":
            event = EconomyEvent("shortage", region, commodity.id, SHORTAGE_MULTIPLIER, False,
                                 now + EVENT_DURATION,
                                 f"Shortage of {commodity.name} near {station.name}: prices up 70%")
        else:
            event = EconomyEvent("embargo", region, commodity.id, 1.0, True, now + EVENT_DURATION,
                                 f"Trade Guild embargoes {commodity.name} near {station.name}")
        self.events.append(event)

        from .ui.notifications import notifications
        notifications.push(f"Market news: {event.headline}", duration=7.0, color=(150, 200, 255))
        return True

    def _region_faction(self, region) -> Optional[str]:
        if self.world_seed is None:
            return None
        cx = region[0] * FACTION_REGION_SECTORS + FACTION_REGION_SECTORS // 2
        cy = region[1] * FACTION_REGION_SECTORS + FACTION_REGION_SECTORS // 2
        return get_controlling_faction(cx, cy, self.world_seed)

    # Persistence ------------------------------------------------------------------

    def to_dict(self) -> Dict:
        return {
            "events": [dict(asdict(e), region=list(e.region)) for e in self.events],
            "next_event_at": self.next_event_at,
        }

    def from_dict(self, data: Dict):
        self.reset()
        if not data:
            return
        for raw in data.get("events", []):
            raw = dict(raw)
            raw["region"] = tuple(raw["region"])
            self.events.append(EconomyEvent(**raw))
        self.next_event_at = data.get("next_event_at")


economy_events = EconomyEvents()
