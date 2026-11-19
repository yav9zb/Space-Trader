"""Dialogue data model and engine. Pure logic over a duck-typed game_engine
(needs .mission_manager, .ship, .story_state), so it unit-tests headlessly and
the UI screen stays a thin wrapper.

Authoring format (see dialogue_data.py): nodes keyed by id, each with a
speaker, text, optional on_enter effects, and a list of choices. A choice may
carry `requires` (all must hold for it to be offered) and `effects` (applied
when picked). A choice with next=None ends the conversation.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..missions.rank_system import RANKS

REQUIREMENT_KEYS = {
    "min_rank", "min_reputation", "min_standing", "flag", "not_flag",
    "story_active", "story_done", "not_story_started",
}

EFFECT_TYPES = {
    "set_flag",
    "clear_flag",
    "adjust_standing",
    "adjust_reputation",
    "give_credits",
    "start_story_mission",
    "add_ledger_entry",
    "set_chapter",
    "bump_counter",
    "show_dialogue",
    "flip_region",
}


@dataclass
class Choice:
    text: str
    next: Optional[str] = None
    requires: Dict[str, Any] = field(default_factory=dict)
    effects: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Node:
    id: str
    speaker: str
    text: str
    choices: List[Choice] = field(default_factory=list)
    on_enter: List[Dict[str, Any]] = field(default_factory=list)


def evaluate_requirements(requires: Dict[str, Any], game_engine) -> bool:
    """True if every requirement in the dict holds."""
    mission_manager = game_engine.mission_manager
    story = game_engine.story_state

    for key, value in requires.items():
        if key == "min_rank":
            if mission_manager.reputation < dict(RANKS)[value]:
                return False
        elif key == "min_reputation":
            if mission_manager.reputation < value:
                return False
        elif key == "min_standing":
            for faction, needed in value.items():
                if mission_manager.faction_standing.get(faction, 0) < needed:
                    return False
        elif key == "flag":
            if not story.has_flag(value):
                return False
        elif key == "not_flag":
            if story.has_flag(value):
                return False
        elif key == "story_active":
            if value not in story.active_story_missions:
                return False
        elif key == "story_done":
            if value not in story.completed_story_missions:
                return False
        elif key == "not_story_started":
            if value in story.active_story_missions or value in story.completed_story_missions:
                return False
        else:
            raise ValueError(f"Unknown requirement: {key}")
    return True


def apply_effects(effects: List[Dict[str, Any]], game_engine):
    """Apply each effect in order."""
    mission_manager = game_engine.mission_manager
    story = game_engine.story_state

    for effect in effects:
        kind = effect["type"]
        if kind == "set_flag":
            story.set_flag(effect["name"], effect.get("value", True))
        elif kind == "clear_flag":
            story.clear_flag(effect["name"])
        elif kind == "adjust_standing":
            faction = effect["faction"]
            current = mission_manager.faction_standing.get(faction, 0)
            mission_manager.faction_standing[faction] = current + effect["amount"]
        elif kind == "adjust_reputation":
            mission_manager.reputation = max(0, mission_manager.reputation + effect["amount"])
        elif kind == "give_credits":
            game_engine.ship.credits += effect["amount"]
        elif kind == "start_story_mission":
            from .story_missions import start_story_mission
            start_story_mission(effect["mission_id"], game_engine)
        elif kind == "bump_counter":
            story.bump(effect["name"])
        elif kind == "show_dialogue":
            game_engine.start_dialogue(effect["node"])
        elif kind == "flip_region":
            from .borders import flip_nearest_region
            flip_nearest_region(game_engine, effect["from"], effect["faction"])
        elif kind == "add_ledger_entry":
            story.add_ledger_entry(effect["id"])
        elif kind == "set_chapter":
            story.chapter = effect["chapter"]
            # New chapter, new contacts
            from .director import ensure_npcs_placed
            ensure_npcs_placed(game_engine)
        else:
            raise ValueError(f"Unknown effect: {kind}")


def format_text(text: str, game_engine) -> str:
    """Fill {station:key} tokens with the station a story waypoint or contact
    was placed at (key is a placement key such as "prologue_2.a")."""
    placed = game_engine.story_state.npc_stations

    def replace(match):
        return placed.get(match.group(1), "a nearby station")

    return re.sub(r"\{station:([^}]+)\}", replace, text)


class DialogueSession:
    """One conversation: tracks the current node, filters choices by their
    requirements, and applies effects as the player moves through."""

    def __init__(self, nodes: Dict[str, Node], start_id: str, game_engine):
        self.nodes = nodes
        self.game_engine = game_engine
        self.current: Optional[Node] = None
        self.finished = False
        self._enter(start_id)

    def _enter(self, node_id: str):
        self.current = self.nodes[node_id]
        apply_effects(self.current.on_enter, self.game_engine)
        self.game_engine.story_state.mark_node_seen(node_id)

    def current_text(self) -> str:
        """The current node's text with station tokens filled in."""
        return format_text(self.current.text, self.game_engine) if self.current else ""

    def visible_choices(self) -> List[Choice]:
        if self.current is None:
            return []
        return [
            choice for choice in self.current.choices
            if evaluate_requirements(choice.requires, self.game_engine)
        ]

    def choose(self, index: int) -> bool:
        """Pick the index-th visible choice. Returns True if the conversation
        continues, False if it ended."""
        choices = self.visible_choices()
        if not (0 <= index < len(choices)):
            raise IndexError("No such choice")
        choice = choices[index]
        apply_effects(choice.effects, self.game_engine)

        if choice.next is None:
            self.finished = True
            self.current = None
            return False
        self._enter(choice.next)
        return True


def is_ascii_safe(text: str) -> bool:
    """Default pygame font can't draw arrows, checkmarks, curly quotes etc."""
    return all(ord(ch) < 128 for ch in text)


def validate_nodes(nodes: Dict[str, Node]) -> List[str]:
    """Return a list of authoring problems (empty if the data is sound)."""
    problems = []
    for node_id, node in nodes.items():
        if node.id != node_id:
            problems.append(f"{node_id}: key does not match node id {node.id}")
        if not is_ascii_safe(node.text) or not is_ascii_safe(node.speaker):
            problems.append(f"{node_id}: non-ASCII text")
        for effect in node.on_enter:
            if effect.get("type") not in EFFECT_TYPES:
                problems.append(f"{node_id}: unknown on_enter effect {effect.get('type')}")
        for i, choice in enumerate(node.choices):
            where = f"{node_id}[{i}]"
            if not is_ascii_safe(choice.text):
                problems.append(f"{where}: non-ASCII choice text")
            if choice.next is not None and choice.next not in nodes:
                problems.append(f"{where}: next '{choice.next}' does not exist")
            for key in choice.requires:
                if key not in REQUIREMENT_KEYS:
                    problems.append(f"{where}: unknown requirement {key}")
            for effect in choice.effects:
                if effect.get("type") not in EFFECT_TYPES:
                    problems.append(f"{where}: unknown effect {effect.get('type')}")
    return problems
