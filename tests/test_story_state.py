import json
from pathlib import Path
from types import SimpleNamespace

from src.save_system import SaveSystem
from src.story.story_state import StoryState


def roundtrip(state):
    restored = StoryState()
    restored.from_dict(json.loads(json.dumps(state.to_dict())))
    return restored


def test_fresh_state_defaults():
    state = StoryState()
    assert state.chapter == "prologue"
    assert state.flags == {}
    assert state.count_events("docked") == 0


def test_flag_operations():
    state = StoryState()
    state.set_flag("met_hale")
    state.set_flag("choice", "expose")
    assert state.has_flag("met_hale")
    assert state.get_flag("choice") == "expose"
    assert not state.has_flag("never_set")
    state.clear_flag("met_hale")
    assert not state.has_flag("met_hale")


def test_events_are_counted_and_log_is_bounded():
    state = StoryState()
    for i in range(StoryState.MAX_RECENT_EVENTS + 25):
        state.record_event("bandit_destroyed", n=i)
    assert state.count_events("bandit_destroyed") == StoryState.MAX_RECENT_EVENTS + 25
    assert len(state.recent_events) == StoryState.MAX_RECENT_EVENTS
    # Oldest dropped, sequence numbers keep increasing
    assert state.recent_events[-1]["seq"] == StoryState.MAX_RECENT_EVENTS + 24


def test_ledger_entries_are_unique():
    state = StoryState()
    state.add_ledger_entry("entry_1")
    state.add_ledger_entry("entry_1")
    assert state.ledger_entries == ["entry_1"]


def test_full_roundtrip_through_json():
    state = StoryState()
    state.set_flag("a", 3)
    state.chapter = "act_2"
    state.npc_stations["hale"] = "Outpost-12"
    state.active_story_missions.append("m1")
    state.mark_node_seen("hale_intro")
    state.add_ledger_entry("e1")
    state.record_event("docked", station="X")

    restored = roundtrip(state)
    assert restored.flags == {"a": 3}
    assert restored.chapter == "act_2"
    assert restored.npc_stations == {"hale": "Outpost-12"}
    assert restored.active_story_missions == ["m1"]
    assert restored.has_seen("hale_intro")
    assert restored.ledger_entries == ["e1"]
    assert restored.count_events("docked") == 1
    # Sequence numbering continues rather than restarting
    restored.record_event("docked")
    assert restored.recent_events[-1]["seq"] == 1


def test_loading_empty_data_resets_to_fresh_campaign():
    state = StoryState()
    state.set_flag("leftover")
    state.chapter = "act_3"
    state.from_dict({})
    assert state.flags == {}
    assert state.chapter == "prologue"


def test_save_system_includes_story_and_old_saves_reset_it():
    save_system = SaveSystem.__new__(SaveSystem)  # skip __init__ (touches disk)
    engine = SimpleNamespace(story_state=StoryState())
    engine.story_state.set_flag("in_progress")

    data = save_system._save_story_data(engine)
    assert data["flags"] == {"in_progress": True}

    engine.story_state.set_flag("leftover_from_other_save")
    save_system._load_story_data({}, engine)  # a save from before the campaign
    assert engine.story_state.flags == {}

    save_system._load_story_data(data, engine)
    assert engine.story_state.has_flag("in_progress")


def test_story_package_text_is_ascii_only():
    """The default pygame font can't draw non-ASCII glyphs."""
    story_dir = Path(__file__).resolve().parent.parent / "src" / "story"
    for path in story_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        bad = sorted({ch for ch in text if ord(ch) > 127})
        assert not bad, f"{path.name} has non-ASCII characters: {bad}"
