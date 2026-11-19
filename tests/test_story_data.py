"""Validates the authored story data as a whole: dialogue graph, NPC roster,
and the lore/flag/ledger references that tie them together."""

from src.story.chapters import STORY_MISSIONS, STAGE_KINDS
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
    for definition in STORY_MISSIONS.values():
        for effect in definition.on_complete:
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
    # Scenes opened automatically by effects (e.g. when a story mission completes)
    frontier += [e["node"] for e in _all_effects() if e["type"] == "show_dialogue"]
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


def test_every_story_mission_is_well_formed():
    from src.missions.rank_system import RANKS
    import re
    for mid, d in STORY_MISSIONS.items():
        assert d.id == mid and d.title and d.description and d.stages
        assert d.giver in NPCS, mid
        for stage in d.stages:
            assert stage.kind in STAGE_KINDS, (mid, stage.kind)
            if stage.kind == "dock_at":
                assert stage.params["waypoint"] in d.waypoints, mid
            if stage.kind == "earn_rank":
                assert stage.params["rank"] in dict(RANKS), mid
            for key in re.findall(r"\{(\w+)\}", stage.text):
                assert key in d.waypoints, (mid, key)
        for key in re.findall(r"\{(\w+)\}", d.description):
            assert key in d.waypoints, (mid, key)
        for wp in d.waypoints.values():
            assert 0 <= wp.min_ring <= wp.max_ring


def test_every_story_mission_can_be_started_by_a_conversation():
    started = {e["mission_id"] for e in _all_effects() if e["type"] == "start_story_mission"}
    assert started == set(STORY_MISSIONS), set(STORY_MISSIONS) ^ started


def test_dialogue_effects_reference_real_missions_and_scenes():
    for effect in _all_effects():
        if effect["type"] == "start_story_mission":
            assert effect["mission_id"] in STORY_MISSIONS
        if effect["type"] == "show_dialogue":
            assert effect["node"] in NODES


def test_station_tokens_refer_to_real_waypoints():
    import re
    valid = {f"{mid}.{key}" for mid, d in STORY_MISSIONS.items() for key in d.waypoints}
    valid |= set(NPCS)                       # a contact's own station
    for node in NODES.values():
        for token in re.findall(r"\{station:([^}]+)\}", node.text):
            assert token in valid, (node.id, token)


def _choices():
    for node in NODES.values():
        for choice in node.choices:
            yield node, choice


def test_story_mission_requirements_point_at_real_missions_and_stages():
    for node, choice in _choices():
        req = choice.requires
        for key in ("story_active", "story_done", "not_story_started"):
            if key in req:
                assert req[key] in STORY_MISSIONS, (node.id, req[key])
        for mission_id in req.get("story_done_all", []):
            assert mission_id in STORY_MISSIONS, (node.id, mission_id)
        if "story_stage" in req:
            mission_id, stage = req["story_stage"]
            assert mission_id in STORY_MISSIONS, (node.id, mission_id)
            assert 0 <= stage < len(STORY_MISSIONS[mission_id].stages), (node.id, req)


def test_every_waiting_counter_stage_is_fed_by_a_conversation():
    """A counter stage named story:x is only ever advanced by a node that
    bumps story:x; otherwise the mission could never finish."""
    bumped = {e["name"] for e in _all_effects() if e["type"] == "bump_counter"}
    for mission_id, definition in STORY_MISSIONS.items():
        for stage in definition.stages:
            if stage.kind == "counter":
                assert stage.params["counter"] in bumped, (mission_id, stage.params["counter"])


def test_every_story_mission_has_a_real_giver_and_something_that_starts_it():
    """The contact named as giver must exist, and some node or an earlier
    mission's completion must start the mission."""
    started = {e["mission_id"] for e in _all_effects() if e["type"] == "start_story_mission"}
    for mission_id, definition in STORY_MISSIONS.items():
        assert definition.giver in NPCS, mission_id
        assert mission_id in started, mission_id


def test_ledger_entries_added_by_missions_and_dialogue_are_all_read_somewhere():
    added = {e["id"] for e in _all_effects() if e["type"] == "add_ledger_entry"}
    assert set(LEDGER_ENTRIES) <= added, set(LEDGER_ENTRIES) - added


def test_every_campaign_chapter_is_entered_by_a_set_chapter_effect():
    entered = {e["chapter"] for e in _all_effects() if e["type"] == "set_chapter"}
    assert set(CHAPTER_ORDER) - {"prologue"} <= entered


def test_the_campaign_has_the_planned_size():
    assert len(STORY_MISSIONS) == 16
    assert len(NPCS) == 6
