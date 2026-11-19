"""Authored story missions, as data. A mission is a list of stages; each
stage has a kind (see objectives.py) and parameters. Station names are not
authored - missions declare waypoints (a faction, a distance band, optionally
a station type) and the director picks or creates matching stations when the
mission starts. Text may use {key} for a waypoint's station name.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple

STAGE_KINDS = {"counter", "dock_at", "destroy_bandits", "reach_sector", "earn_rank"}


@dataclass(frozen=True)
class Waypoint:
    faction: str
    station_types: Tuple[str, ...] = ()
    min_ring: int = 0
    max_ring: int = 3


@dataclass(frozen=True)
class Stage:
    kind: str
    text: str
    params: Dict = field(default_factory=dict)


@dataclass(frozen=True)
class StoryMissionDef:
    id: str
    title: str
    description: str
    giver: str                                   # NPC id, for the origin station
    stages: Tuple[Stage, ...]
    waypoints: Dict[str, Waypoint] = field(default_factory=dict)
    reward_credits: int = 0
    reputation_bonus: int = 0
    on_complete: Tuple[Dict, ...] = ()


STORY_MISSIONS: Dict[str, StoryMissionDef] = {}


def _add(definition: StoryMissionDef):
    STORY_MISSIONS[definition.id] = definition


# --- Prologue: A Dead Man's Ship ---------------------------------------------

_add(StoryMissionDef(
    id="prologue_1",
    title="Honest Work",
    description=(
        "Hale will not point you at the ledger until you have a name in the "
        "trade. Earn a trader's license through contracts and trading, then "
        "show it to him."
    ),
    giver="hale",
    stages=(
        Stage("earn_rank", "Earn a trader's license (Trader rank)", {"rank": "Trader"}),
        Stage("counter", "Show your license to Dock Master Hale",
              {"counter": "story:hale_license_shown"}),
    ),
    reward_credits=200,
    reputation_bonus=2,
))

_add(StoryMissionDef(
    id="prologue_2",
    title="The First Entry",
    description=(
        "Hale has worked out where the first ledger entry points: a berth at "
        "{a}. If Jessup Vane left anything behind, it will be there."
    ),
    giver="hale",
    waypoints={"a": Waypoint(faction="Independent", min_ring=2, max_ring=4)},
    stages=(
        Stage("dock_at", "Dock at {a} and look for Vane's berth", {"waypoint": "a"}),
    ),
    reward_credits=300,
    reputation_bonus=4,
    on_complete=(
        {"type": "add_ledger_entry", "id": "ledger_entry_1"},
        {"type": "set_flag", "name": "prologue_entry_found"},
        {"type": "show_dialogue", "node": "cache_found"},
    ),
))

_add(StoryMissionDef(
    id="prologue_3",
    title="The Courier",
    description=(
        "Vane's locker held a second page: a courier named Reyes is waiting "
        "at {b}. Reach {b} before the trail goes cold."
    ),
    giver="hale",
    waypoints={"b": Waypoint(faction="Independent", min_ring=3, max_ring=6)},
    stages=(
        Stage("dock_at", "Dock at {b} and meet the courier", {"waypoint": "b"}),
    ),
    reward_credits=600,
    reputation_bonus=6,
    on_complete=(
        {"type": "add_ledger_entry", "id": "ledger_entry_2"},
        {"type": "set_flag", "name": "prologue_complete"},
        {"type": "adjust_standing", "faction": "Independent", "amount": 5},
        {"type": "show_dialogue", "node": "courier_meeting"},
    ),
))
