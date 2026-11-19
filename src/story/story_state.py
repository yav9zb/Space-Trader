"""Persistent campaign state: flags, chapter, NPC placements, ledger entries
and a record of notable events. Everything here is plain JSON data, so story
progress saves and loads like any other system, and objectives can be
evaluated purely from this state rather than from live subclass attributes.
"""

from typing import Any, Dict, List

from .. import factions


class StoryState:
    MAX_RECENT_EVENTS = 200

    def __init__(self):
        self.reset()

    def reset(self):
        self.flags: Dict[str, Any] = {}
        self.chapter = "prologue"
        self.active_story_missions: List[str] = []
        self.completed_story_missions: List[str] = []
        self.npc_stations: Dict[str, str] = {}
        self.seen_nodes = set()
        self.ledger_entries: List[str] = []
        self.event_counts: Dict[str, int] = {}
        self.recent_events: List[Dict[str, Any]] = []
        self.region_overrides: Dict[str, str] = {}      # "rx,ry" -> faction
        self._next_seq = 0
        factions.clear_region_overrides()

    # Borders ---------------------------------------------------------------

    def set_region_override(self, region, faction: str):
        """Change who controls a 4x4-sector region. Applies to the HUD, markets,
        patrols and anything generated from now on; chunks already generated
        keep the entities they already have."""
        self.region_overrides[f"{region[0]},{region[1]}"] = faction
        factions.set_region_override(region, faction)

    # Flags -----------------------------------------------------------------

    def set_flag(self, name: str, value: Any = True):
        self.flags[name] = value

    def clear_flag(self, name: str):
        self.flags.pop(name, None)

    def get_flag(self, name: str, default: Any = None) -> Any:
        return self.flags.get(name, default)

    def has_flag(self, name: str) -> bool:
        return bool(self.flags.get(name))

    # Events ----------------------------------------------------------------

    def record_event(self, name: str, **data):
        """Count an event and keep a bounded log of recent ones. Cheap enough
        to call from combat/docking code paths."""
        self.event_counts[name] = self.event_counts.get(name, 0) + 1
        self.recent_events.append({"name": name, "seq": self._next_seq, "data": data})
        self._next_seq += 1
        if len(self.recent_events) > self.MAX_RECENT_EVENTS:
            del self.recent_events[: len(self.recent_events) - self.MAX_RECENT_EVENTS]

    def count_events(self, name: str) -> int:
        return self.event_counts.get(name, 0)

    def bump(self, counter: str, amount: int = 1):
        """Increment a named counter without logging an event. Used for
        fine-grained counters such as "docked_at:<station>" that objectives
        measure against a baseline."""
        self.event_counts[counter] = self.event_counts.get(counter, 0) + amount

    def finish_story_mission(self, mission_id: str, completed: bool):
        """A story mission ended: completed ones are recorded, abandoned or
        failed ones simply become startable again."""
        if mission_id in self.active_story_missions:
            self.active_story_missions.remove(mission_id)
        if completed and mission_id not in self.completed_story_missions:
            self.completed_story_missions.append(mission_id)

    # Dialogue / ledger / missions --------------------------------------------

    def mark_node_seen(self, node_id: str):
        self.seen_nodes.add(node_id)

    def has_seen(self, node_id: str) -> bool:
        return node_id in self.seen_nodes

    def add_ledger_entry(self, entry_id: str):
        if entry_id not in self.ledger_entries:
            self.ledger_entries.append(entry_id)

    # Persistence -------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flags": dict(self.flags),
            "chapter": self.chapter,
            "active_story_missions": list(self.active_story_missions),
            "completed_story_missions": list(self.completed_story_missions),
            "npc_stations": dict(self.npc_stations),
            "seen_nodes": sorted(self.seen_nodes),
            "ledger_entries": list(self.ledger_entries),
            "event_counts": dict(self.event_counts),
            "recent_events": list(self.recent_events),
            "region_overrides": dict(self.region_overrides),
            "next_seq": self._next_seq,
        }

    def from_dict(self, data: Dict[str, Any]):
        """Restore state. An empty/missing dict (a save from before the
        story existed) resets to a fresh campaign."""
        self.reset()
        if not data:
            return
        self.flags = dict(data.get("flags", {}))
        self.chapter = data.get("chapter", "prologue")
        self.active_story_missions = list(data.get("active_story_missions", []))
        self.completed_story_missions = list(data.get("completed_story_missions", []))
        self.npc_stations = dict(data.get("npc_stations", {}))
        self.seen_nodes = set(data.get("seen_nodes", []))
        self.ledger_entries = list(data.get("ledger_entries", []))
        self.event_counts = dict(data.get("event_counts", {}))
        self.recent_events = list(data.get("recent_events", []))
        for key, faction in data.get("region_overrides", {}).items():
            rx, ry = (int(part) for part in key.split(","))
            self.set_region_override((rx, ry), faction)
        self._next_seq = data.get("next_seq", len(self.recent_events))

        # Saves from before the acts existed finished the prologue with the
        # chapter still "prologue" and Hale's old epilogue already seen, so
        # nothing would ever start Act 1 for them.
        if self.chapter == "prologue" and self.has_flag("prologue_epilogue_seen"):
            self.chapter = "act_1"


# Global story state, like mission_manager
story_state = StoryState()
