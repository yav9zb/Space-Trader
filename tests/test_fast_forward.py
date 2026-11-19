"""The debug-save tool: jumping to an act must leave exactly the state the
earlier play would have, which is proved by finishing the campaign from there
with the same conversations and events the full playthrough uses."""

import pytest

from src.story.fast_forward import STAGES, PATHS, fast_forward
from src.story.story_state import story_state
from tests.test_campaign_playthrough import (
    Campaign, PATHS as CHOICES, act1, act2, act3, act4, signal, prologue,
)

FINAL = "Open the Signal to every faction."


def run_from(stage, c, choice):
    """Play whatever the campaign still has to offer from the start of `stage`."""
    if stage == "act1":
        act1(c)
    if stage in ("act1", "act2"):
        act2(c)
    if stage in ("act1", "act2", "act3"):
        act3(c, choice)
    if stage != "finale":
        act4(c, FINAL)
    else:
        signal(c, FINAL)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("stage", STAGES)
def test_the_campaign_can_be_finished_from_every_jump_point(stage, path):
    c = Campaign()
    fast_forward(c.engine, stage, path)
    run_from(stage, c, CHOICES[path][0])

    assert story_state.has_flag("campaign_complete")
    assert c.engine.victory == 1
    assert len(story_state.completed_story_missions) == 16


def test_each_stage_has_its_chapter_rank_and_the_right_missions_done():
    expected = {
        "act1": ("act_1", 3, 20), "act2": ("act_2", 6, 45), "act3": ("act_3", 10, 85),
        "act4": ("act_4", 13, 100), "finale": ("act_4", 14, 120),
    }
    for stage, (chapter, completed, reputation) in expected.items():
        c = Campaign()
        done = fast_forward(c.engine, stage, "join")
        assert story_state.chapter == chapter, stage
        assert len(done) == completed == len(story_state.completed_story_missions), stage
        assert c.engine.mission_manager.reputation == reputation, stage


def test_only_the_contacts_of_finished_acts_have_been_met():
    c = Campaign()
    fast_forward(c.engine, "act2", "join")
    assert story_state.has_flag("met_rourke") and story_state.has_flag("met_kestrel")
    assert not story_state.has_flag("met_archivist")           # act 2's own contact is still to meet


def test_the_choice_is_left_to_the_player_at_the_start_of_act_three():
    c = Campaign()
    fast_forward(c.engine, "act3", "expose")
    assert not story_state.has_flag("path_chosen")
    assert story_state.region_overrides == {}


def test_later_stages_carry_the_path_with_its_standing_and_borders():
    for path, flag in (("expose", "path_expose"), ("join", "path_join"), ("independent", "path_independent")):
        c = Campaign()
        fast_forward(c.engine, "act4", path)
        assert story_state.has_flag(flag)
        assert story_state.region_overrides, path


def test_the_finale_stage_has_the_signal_mission_ready():
    c = Campaign()
    fast_forward(c.engine, "finale", "independent")
    assert "act4_2" in story_state.active_story_missions
    assert c.mission("act4_2").destination_station_id.startswith("Sector (")


def test_bad_arguments_are_rejected():
    c = Campaign()
    with pytest.raises(ValueError):
        fast_forward(c.engine, "act9", "join")
    with pytest.raises(ValueError):
        fast_forward(c.engine, "act2", "conquer")


def test_the_ledger_has_every_entry_up_to_the_stage():
    c = Campaign()
    fast_forward(c.engine, "act4", "join")
    assert {"ledger_cover", "ledger_entry_1", "ledger_entry_5", "ledger_entry_9",
            "ledger_entry_10"} <= set(story_state.ledger_entries)
    assert "ledger_entry_11" not in story_state.ledger_entries        # found in Act 4 itself


def test_the_debug_save_script_writes_a_save_the_real_game_can_load(tmp_path):
    """End to end: the script's save loads into a real engine, in the right
    chapter, with the right conversation options and the contacts placed."""
    import importlib.util
    import os

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    spec = importlib.util.spec_from_file_location(
        "make_debug_save", os.path.join(os.path.dirname(__file__), "..", "scripts", "make_debug_save.py"))
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)

    name = script.make_save("act4", "join", seed=77, save_dir=str(tmp_path))
    assert (tmp_path / f"{name}.json").exists()

    from src.engine.game_engine import GameEngine
    from src.save_system import SaveSystem
    from src.story.dialogue import DialogueSession
    from src.story.dialogue_data import NODES

    engine = GameEngine()
    assert SaveSystem(str(tmp_path)).load_game(name, engine)

    assert engine.story_state.chapter == "act_4"
    assert engine.story_state.has_flag("path_join")
    assert engine.mission_manager.reputation == 100
    assert engine.story_state.npc_stations.get("okoye")
    offered = [c.text for c in DialogueSession(NODES, "okoye_return", engine).visible_choices()]
    assert "What did the decoded page say?" in offered
