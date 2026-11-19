"""Named station contacts. Each NPC lives at one station, chosen when their
chapter begins and then remembered in StoryState so they stay put across
saves. Placement rules (faction, distance from spawn, station type) are data
here; the logic lives in director.py.
"""

from dataclasses import dataclass
from typing import Dict, Tuple

CHAPTER_ORDER = ["prologue", "act_1", "act_2", "act_3", "act_4"]


@dataclass(frozen=True)
class NPC:
    id: str
    name: str
    role: str
    faction: str                 # faction that must control the station's sector
    intro_node: str              # dialogue node for the first conversation
    return_node: str             # dialogue node for later conversations
    station_types: Tuple[str, ...] = ()   # required station types; empty = any
    min_ring: int = 0            # distance from spawn in sectors (Chebyshev)
    max_ring: int = 2
    chapter: str = "prologue"    # first chapter in which they are available


NPCS: Dict[str, NPC] = {
    "hale": NPC(
        id="hale",
        name="Dock Master Hale",
        role="Retired dock master",
        faction="Independent",
        intro_node="hale_intro",
        return_node="hale_return",
        min_ring=0,
        max_ring=1,
        chapter="prologue",
    ),
    "rourke": NPC(
        id="rourke",
        name="Captain Rourke",
        role="Independent freighter captain",
        faction="Independent",
        intro_node="rourke_intro",
        return_node="rourke_return",
        min_ring=2,
        max_ring=4,
        chapter="act_1",
    ),
    "voss": NPC(
        id="voss",
        name="Auditor Voss",
        role="Trade Guild auditor",
        faction="Trade Guild",
        intro_node="voss_intro",
        return_node="voss_return",
        min_ring=3,
        max_ring=6,
        chapter="act_1",
    ),
    "kestrel": NPC(
        id="kestrel",
        name="Kestrel",
        role="Information broker",
        faction="Pirate Territory",
        intro_node="kestrel_intro",
        return_node="kestrel_return",
        min_ring=4,
        max_ring=8,
        chapter="act_1",
    ),
    "archivist": NPC(
        id="archivist",
        name="The Archivist",
        role="Trade Guild records clerk",
        faction="Trade Guild",
        intro_node="archivist_intro",
        return_node="archivist_return",
        station_types=("Research Station",),
        min_ring=5,
        max_ring=9,
        chapter="act_2",
    ),
    "okoye": NPC(
        id="okoye",
        name="Dr. Okoye",
        role="Signals researcher",
        faction="Independent",
        intro_node="okoye_intro",
        return_node="okoye_return",
        station_types=("Research Station",),
        min_ring=6,
        max_ring=9,
        chapter="act_3",
    ),
}


def chapter_index(chapter: str) -> int:
    return CHAPTER_ORDER.index(chapter) if chapter in CHAPTER_ORDER else 0


def is_available(npc: NPC, story_state) -> bool:
    """An NPC appears once the campaign reaches their chapter."""
    return chapter_index(story_state.chapter) >= chapter_index(npc.chapter)
