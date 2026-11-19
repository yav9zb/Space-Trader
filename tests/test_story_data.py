"""Validates the authored story data as a whole: dialogue graph, NPC roster,
and the lore/flag/ledger references that tie them together."""

from src.story.dialogue import validate_nodes
from src.story.dialogue_data import NODES
from src.story.lore import CHAPTERS, LEDGER_ENTRIES, FACTION_BLURBS
from src.story.npcs import NPCS, CHAPTER_ORDER
from src.factions import FACTION_TRADE_GUILD, FACTION_INDEPENDENT, FACTION_PIRATE


def _all_effects():
    for node in NODES.values():
        for effect in node.on_enter:
            yield effect
        for choice in node.choices:
            for effect in choice.effects:
                yield effect


def test_dialogue_graph_has_no_authoring_errors():
    assert validate_nodes(NODES) == []


def test_every_npc_has_dialogue_and_valid_placement_data():
    valid_factions = {FACTION_TRADE_GUILD, FACTION_INDEPENDENT, FACTION_PIRATE}
    for npc in NPCS.values():
        assert npc.intro_node in NODES, npc.id
        assert npc.return_node in NODES, npc.id
        assert npc.faction in valid_factions, npc.id
        assert npc.chapter in CHAPTER_ORDER, npc.id
        assert 0 <= npc.min_ring <= npc.max_ring, npc.id
        assert npc.id and npc.name and npc.role


def test_every_node_is_reachable_from_an_npc():
    reachable = set()
    frontier = [n for npc in NPCS.values() for n in (npc.intro_node, npc.return_node)]
    while frontier:
        node_id = frontier.pop()
        if node_id in reachable:
            continue
        reachable.add(node_id)
        frontier.extend(c.next for c in NODES[node_id].choices if c.next)
    assert set(NODES) - reachable == set(), "orphan dialogue nodes"


def test_flag_requirements_refer_to_flags_something_sets():
    settable = {e["name"] for e in _all_effects() if e["type"] == "set_flag"}
    for node in NODES.values():
        for choice in node.choices:
            for key in ("flag", "not_flag"):
                if key in choice.requires:
                    assert choice.requires[key] in settable, (node.id, choice.requires[key])


def test_ledger_and_chapter_references_exist():
    for effect in _all_effects():
        if effect["type"] == "add_ledger_entry":
            assert effect["id"] in LEDGER_ENTRIES
        if effect["type"] == "set_chapter":
            assert effect["chapter"] in CHAPTER_ORDER


def test_every_chapter_has_lore_and_every_faction_a_blurb():
    for chapter in CHAPTER_ORDER:
        assert chapter in CHAPTERS
    for faction in (FACTION_TRADE_GUILD, FACTION_INDEPENDENT, FACTION_PIRATE):
        assert faction in FACTION_BLURBS


def test_rank_requirements_use_real_rank_names():
    from src.missions.rank_system import RANKS
    names = {name for name, _ in RANKS}
    for node in NODES.values():
        for choice in node.choices:
            if "min_rank" in choice.requires:
                assert choice.requires["min_rank"] in names
