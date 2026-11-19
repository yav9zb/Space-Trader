"""Builds the Logbook's pages as plain (kind, text) lines, kept separate from
the screen so the content is testable without pygame. Kinds: "heading",
"body", "dim", "gap".
"""

from typing import Dict, List, Tuple

from ..factions import (
    get_controlling_faction, FACTION_TRADE_GUILD, FACTION_INDEPENDENT, FACTION_PIRATE,
)
from ..economy_events import economy_events
from .director import find_station_by_name
from .chapters import STORY_MISSIONS
from .lore import (
    CHAPTERS, LEDGER_ENTRIES, FACTION_BLURBS, PROLOGUE_DONE_SUMMARY, ACT_DONE_SUMMARIES,
)
from .npcs import NPCS, is_available

TABS = ["Story", "Contacts", "Factions"]

Line = Tuple[str, str]


def _story_page(game) -> List[Line]:
    story = game.story_state
    title, summary = CHAPTERS.get(story.chapter, CHAPTERS["prologue"])
    if story.chapter == "prologue" and story.has_flag("prologue_complete"):
        summary = PROLOGUE_DONE_SUMMARY
    # Once a chapter's missions are all done, say what comes next
    chapter_missions = {
        "act_1": ["act1_1", "act1_2", "act1_3"],
        "act_2": ["act2_1", "act2_2", "act2_3", "act2_4"],
    }.get(story.chapter)
    if chapter_missions and all(m in story.completed_story_missions for m in chapter_missions):
        summary = ACT_DONE_SUMMARIES[story.chapter]
    lines: List[Line] = [("heading", title), ("body", summary), ("gap", "")]

    lines.append(("heading", "Story missions"))
    active = [m for m in getattr(game.mission_manager, "active_missions", [])
              if getattr(m, "story_id", None)]
    for mission in active:
        lines.append(("body", mission.title))
        lines.append(("dim", f"Now: {mission.progress_description}"))
    for mission_id in story.completed_story_missions:
        definition = STORY_MISSIONS.get(mission_id)
        if definition:
            lines.append(("dim", f"Completed: {definition.title}"))
    if not active and not story.completed_story_missions:
        lines.append(("dim", "None yet."))
    lines.append(("gap", ""))

    lines.append(("heading", "Ledger entries"))
    if story.ledger_entries:
        for entry_id in story.ledger_entries:
            entry_title, entry_text = LEDGER_ENTRIES.get(entry_id, (entry_id, ""))
            lines.append(("body", entry_title))
            lines.append(("dim", entry_text))
            lines.append(("gap", ""))
    else:
        lines.append(("dim", "Nothing yet. Talk to the people you meet at stations."))
    return lines


def _contacts_page(game) -> List[Line]:
    story = game.story_state
    lines: List[Line] = []
    for npc in NPCS.values():
        if not (is_available(npc, story) and story.has_seen(npc.intro_node)):
            continue
        lines.append(("heading", f"{npc.name} - {npc.role}"))
        lines.append(("body", f"Faction: {npc.faction}"))
        station = find_station_by_name(story.npc_stations.get(npc.id, ""), game.universe)
        if station is not None:
            sector_x = int(station.position.x // 1000)
            sector_y = int(-station.position.y // 1000)
            lines.append(("body", f"Last known: {station.name}, Sector ({sector_x}, {sector_y})"))
        lines.append(("gap", ""))
    if not lines:
        lines.append(("dim", "You have not met anyone yet. Dock at a station and look "
                             "for a contact."))
    return lines


def _factions_page(game) -> List[Line]:
    standing = game.mission_manager.faction_standing
    ship = game.ship
    here = get_controlling_faction(
        int(ship.position.x // 1000), int(ship.position.y // 1000), game.world_seed)

    lines: List[Line] = [("body", f"You are currently in {here} space."), ("gap", "")]
    for faction in (FACTION_TRADE_GUILD, FACTION_INDEPENDENT, FACTION_PIRATE):
        lines.append(("heading", f"{faction}: {standing.get(faction, 0):+d}"))
        lines.append(("dim", FACTION_BLURBS[faction]))
        lines.append(("gap", ""))

    lines.append(("heading", "Market news"))
    now = getattr(game, "play_time", 0)
    if economy_events.events:
        for event in economy_events.events:
            minutes = max(1, int((event.ends_at - now) // 60))
            lines.append(("body", event.headline))
            lines.append(("dim", f"About {minutes} more minutes"))
    else:
        lines.append(("dim", "Nothing unusual."))
    return lines


def build_pages(game) -> Dict[str, List[Line]]:
    return {
        "Story": _story_page(game),
        "Contacts": _contacts_page(game),
        "Factions": _factions_page(game),
    }
