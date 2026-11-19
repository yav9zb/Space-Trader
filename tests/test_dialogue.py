from types import SimpleNamespace

import pytest

from src.story.dialogue import (
    Choice, Node, DialogueSession, apply_effects, evaluate_requirements,
    validate_nodes,
)
from src.story.story_state import StoryState


def make_engine(reputation=0, standing=None, credits=0):
    return SimpleNamespace(
        mission_manager=SimpleNamespace(
            reputation=reputation,
            faction_standing=dict(standing or {"Trade Guild": 0, "Independent": 0, "Pirate Territory": 0}),
        ),
        ship=SimpleNamespace(credits=credits),
        story_state=StoryState(),
    )


def test_empty_requirements_always_pass():
    assert evaluate_requirements({}, make_engine())


def test_rank_and_reputation_requirements():
    assert not evaluate_requirements({"min_rank": "Captain"}, make_engine(reputation=79))
    assert evaluate_requirements({"min_rank": "Captain"}, make_engine(reputation=80))
    assert evaluate_requirements({"min_reputation": 10}, make_engine(reputation=10))
    assert not evaluate_requirements({"min_reputation": 10}, make_engine(reputation=9))


def test_standing_requirement_checks_every_faction_listed():
    engine = make_engine(standing={"Trade Guild": 30, "Independent": 0, "Pirate Territory": -10})
    assert evaluate_requirements({"min_standing": {"Trade Guild": 25}}, engine)
    assert not evaluate_requirements({"min_standing": {"Trade Guild": 25, "Pirate Territory": 0}}, engine)


def test_flag_requirements():
    engine = make_engine()
    assert not evaluate_requirements({"flag": "met_hale"}, engine)
    assert evaluate_requirements({"not_flag": "met_hale"}, engine)
    engine.story_state.set_flag("met_hale")
    assert evaluate_requirements({"flag": "met_hale"}, engine)
    assert not evaluate_requirements({"not_flag": "met_hale"}, engine)


def test_unknown_requirement_raises():
    with pytest.raises(ValueError):
        evaluate_requirements({"bogus": 1}, make_engine())


def test_effects_change_game_state():
    engine = make_engine(reputation=5, credits=100)
    apply_effects([
        {"type": "set_flag", "name": "deal_made"},
        {"type": "adjust_standing", "faction": "Trade Guild", "amount": 7},
        {"type": "adjust_reputation", "amount": 10},
        {"type": "give_credits", "amount": 250},
        {"type": "add_ledger_entry", "id": "entry_1"},
        {"type": "set_chapter", "chapter": "act_1"},
        {"type": "bump_counter", "name": "story:test"},
    ], engine)

    assert engine.story_state.has_flag("deal_made")
    assert engine.mission_manager.faction_standing["Trade Guild"] == 7
    assert engine.mission_manager.reputation == 15
    assert engine.ship.credits == 350
    assert engine.story_state.ledger_entries == ["entry_1"]
    assert engine.story_state.chapter == "act_1"
    assert engine.story_state.count_events("story:test") == 1


def test_reputation_effect_never_goes_below_zero():
    engine = make_engine(reputation=3)
    apply_effects([{"type": "adjust_reputation", "amount": -50}], engine)
    assert engine.mission_manager.reputation == 0


def test_show_dialogue_effect_opens_the_conversation():
    engine = make_engine()
    opened = []
    engine.start_dialogue = opened.append
    apply_effects([{"type": "show_dialogue", "node": "cache_found"}], engine)
    assert opened == ["cache_found"]


def test_story_requirements():
    engine = make_engine()
    story = engine.story_state
    assert evaluate_requirements({"not_story_started": "m"}, engine)
    assert not evaluate_requirements({"story_active": "m"}, engine)
    story.active_story_missions.append("m")
    assert evaluate_requirements({"story_active": "m"}, engine)
    assert not evaluate_requirements({"not_story_started": "m"}, engine)
    story.finish_story_mission("m", completed=True)
    assert evaluate_requirements({"story_done": "m"}, engine)
    assert not evaluate_requirements({"not_story_started": "m"}, engine)


def test_station_tokens_are_filled_from_placements():
    engine = make_engine()
    engine.story_state.npc_stations["prologue_2.a"] = "Yard-12"
    node = Node("n", "X", "Meet at {station:prologue_2.a} or {station:nowhere}.")
    session = DialogueSession({"n": node}, "n", engine)
    assert session.current_text() == "Meet at Yard-12 or a nearby station."


def test_unknown_effect_raises():
    with pytest.raises(ValueError):
        apply_effects([{"type": "explode"}], make_engine())


SAMPLE = {
    "start": Node("start", "Hale", "Welcome, captain.", on_enter=[{"type": "set_flag", "name": "met_hale"}], choices=[
        Choice("Ask about the ledger.", next="ledger"),
        Choice("Show your license.", next="license", requires={"min_rank": "Trader"}),
        Choice("Leave.", next=None),
    ]),
    "ledger": Node("ledger", "Hale", "It belonged to a friend.", choices=[
        Choice("Take the job.", next=None, effects=[{"type": "set_flag", "name": "took_job"}]),
    ]),
    "license": Node("license", "Hale", "Impressive.", choices=[Choice("Thanks.", next=None)]),
}


def test_session_filters_choices_by_requirements():
    session = DialogueSession(SAMPLE, "start", make_engine(reputation=0))
    assert [c.text for c in session.visible_choices()] == ["Ask about the ledger.", "Leave."]

    session = DialogueSession(SAMPLE, "start", make_engine(reputation=15))
    assert len(session.visible_choices()) == 3


def test_session_applies_on_enter_and_marks_nodes_seen():
    engine = make_engine()
    DialogueSession(SAMPLE, "start", engine)
    assert engine.story_state.has_flag("met_hale")
    assert engine.story_state.has_seen("start")


def test_session_walks_a_conversation_to_its_end():
    engine = make_engine()
    session = DialogueSession(SAMPLE, "start", engine)
    assert session.choose(0) is True          # -> ledger
    assert session.current.id == "ledger"
    assert session.choose(0) is False         # take the job, ends
    assert session.finished
    assert engine.story_state.has_flag("took_job")


def test_choosing_an_invisible_choice_index_raises():
    session = DialogueSession(SAMPLE, "start", make_engine(reputation=0))
    with pytest.raises(IndexError):
        session.choose(2)  # only two choices are visible at rank 0


def test_validate_accepts_sound_data():
    assert validate_nodes(SAMPLE) == []


def test_validate_reports_authoring_mistakes():
    broken = {
        "a": Node("a", "X", "café", choices=[
            Choice("go", next="missing"),
            Choice("x", next=None, requires={"bogus": 1}, effects=[{"type": "explode"}]),
        ]),
        "wrong_key": Node("b", "X", "ok"),
    }
    problems = " | ".join(validate_nodes(broken))
    assert "non-ASCII" in problems
    assert "'missing' does not exist" in problems
    assert "unknown requirement bogus" in problems
    assert "unknown effect explode" in problems
    assert "does not match node id" in problems
