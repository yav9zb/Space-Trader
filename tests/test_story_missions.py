import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from types import SimpleNamespace

import pytest

from src.entities.ship import Ship
from src.factions import get_station_faction
from src.missions.mission_manager import MissionManager
from src.missions.mission_types import Mission, MissionStatus, MissionType
from src.story import director
from src.story.dialogue import DialogueSession, apply_effects
from src.story.dialogue_data import NODES
from src.story.story_missions import StoryMission, start_story_mission
from src.story.story_state import story_state
from src.universe import Universe


@pytest.fixture
def engine():
    story_state.reset()
    universe = Universe(seed=2024)
    universe.generate_universe()
    eng = SimpleNamespace(
        universe=universe, world_seed=universe.world_seed, story_state=story_state,
        mission_manager=MissionManager(), ship=Ship(0, 0), opened=[],
    )
    eng.start_dialogue = eng.opened.append
    director.ensure_npcs_placed(eng)
    yield eng
    story_state.reset()


def active_story(engine, story_id):
    return next(m for m in engine.mission_manager.active_missions
                if getattr(m, "story_id", None) == story_id)


def test_starting_places_waypoint_and_tracks_the_mission(engine):
    assert start_story_mission("prologue_2", engine)
    mission = active_story(engine, "prologue_2")

    assert mission.mission_type == MissionType.STORY
    assert mission.status == MissionStatus.ACCEPTED
    assert story_state.active_story_missions == ["prologue_2"]

    berth = mission.resolved["a"]
    station = director.find_station_by_name(berth, engine.universe)
    assert get_station_faction(station, engine.world_seed) == "Independent"
    assert berth in mission.objectives[0].description
    assert mission.destination_station_id == berth
    # The origin is the giver's station, so faction standing resolves correctly
    assert mission.origin_station_id == story_state.npc_stations["hale"]
    # The waypoint is never the contact's own station
    assert berth != story_state.npc_stations["hale"]


def test_starting_twice_does_not_duplicate(engine):
    assert start_story_mission("prologue_2", engine)
    assert not start_story_mission("prologue_2", engine)
    assert len(engine.mission_manager.active_missions) == 1


def test_dock_stage_ignores_earlier_visits_and_completes_on_a_new_one(engine):
    # Find where the berth will be, visit it BEFORE the mission starts
    start_story_mission("prologue_2", engine)
    mission = active_story(engine, "prologue_2")
    berth = mission.resolved["a"]

    # Rebuild a fresh mission whose baseline is taken after an earlier visit
    engine.mission_manager.active_missions.clear()
    story_state.active_story_missions.clear()
    story_state.bump(f"docked_at:{berth}")
    start_story_mission("prologue_2", engine)
    mission = active_story(engine, "prologue_2")

    assert mission.evaluate(engine.ship, story_state, engine.mission_manager) is False
    story_state.bump(f"docked_at:{berth}")
    assert mission.evaluate(engine.ship, story_state, engine.mission_manager) is True
    assert mission.status == MissionStatus.COMPLETED


def test_prologue_1_needs_rank_then_a_dialogue_turn_in(engine):
    start_story_mission("prologue_1", engine)
    mission = active_story(engine, "prologue_1")
    manager = engine.mission_manager

    assert not mission.evaluate(engine.ship, story_state, manager)
    assert mission.stage_index == 0

    manager.reputation = 15
    assert not mission.evaluate(engine.ship, story_state, manager)
    assert mission.stage_index == 1
    assert mission.status == MissionStatus.IN_PROGRESS

    story_state.bump("story:hale_license_shown")
    assert mission.evaluate(engine.ship, story_state, manager)


def test_completion_pays_out_applies_effects_and_opens_the_scene(engine):
    start_story_mission("prologue_2", engine)
    mission = active_story(engine, "prologue_2")
    credits_before = engine.ship.credits

    mission.stage_index = len(mission.definition.stages)
    mission.status = MissionStatus.COMPLETED
    engine.mission_manager.complete_mission(mission, engine.ship, engine)

    assert engine.ship.credits > credits_before
    assert engine.mission_manager.reputation == 4
    assert "ledger_entry_1" in story_state.ledger_entries
    assert story_state.has_flag("prologue_entry_found")
    assert engine.opened == ["cache_found"]
    assert story_state.completed_story_missions == ["prologue_2"]
    assert story_state.active_story_missions == []


def test_abandoning_makes_the_mission_startable_again(engine):
    start_story_mission("prologue_2", engine)
    mission = active_story(engine, "prologue_2")
    engine.mission_manager.abandon_mission(mission.id, engine.ship, engine)

    assert story_state.active_story_missions == []
    assert story_state.completed_story_missions == []
    assert start_story_mission("prologue_2", engine)


def test_a_story_mission_survives_save_and_load_mid_progress(engine):
    start_story_mission("prologue_1", engine)
    mission = active_story(engine, "prologue_1")
    engine.mission_manager.reputation = 15
    mission.evaluate(engine.ship, story_state, engine.mission_manager)   # now on stage 2

    restored = Mission.from_dict(json.loads(json.dumps(mission.to_dict())))
    assert isinstance(restored, StoryMission)
    assert restored.story_id == "prologue_1"
    assert restored.stage_index == 1
    assert restored.baselines == mission.baselines
    assert restored.description == mission.description

    story_state.bump("story:hale_license_shown")
    assert restored.evaluate(engine.ship, story_state, engine.mission_manager) is True


def test_conversation_hands_out_the_first_mission(engine):
    session = DialogueSession(NODES, "hale_ledger", engine)
    offered = [c.text for c in session.visible_choices()]
    assert "I will earn that license." in offered

    session.choose(offered.index("I will earn that license."))
    assert story_state.active_story_missions == ["prologue_1"]

    again = DialogueSession(NODES, "hale_ledger", engine)
    assert "I will earn that license." not in [c.text for c in again.visible_choices()]


def test_full_prologue_chain_through_conversations_and_missions(engine):
    manager = engine.mission_manager
    ship = engine.ship

    def talk(node, pick):
        session = DialogueSession(NODES, node, engine)
        texts = [c.text for c in session.visible_choices()]
        session.choose(texts.index(pick))

    def finish_active(story_id):
        mission = active_story(engine, story_id)
        mission.evaluate(ship, story_state, manager)
        assert mission.status == MissionStatus.COMPLETED, story_id
        manager.complete_mission(mission, ship, engine)

    talk("hale_ledger", "I will earn that license.")            # prologue_1 starts
    manager.reputation = 15
    active_story(engine, "prologue_1").evaluate(ship, story_state, manager)
    talk("hale_return", "I have earned my trader's license.")   # turn-in, prologue_2 starts
    finish_active("prologue_1")
    assert "prologue_2" in story_state.active_story_missions

    berth = active_story(engine, "prologue_2").resolved["a"]
    story_state.bump(f"docked_at:{berth}")
    finish_active("prologue_2")
    assert story_state.has_flag("prologue_entry_found")

    talk("hale_return", "I found Vane's locker.")               # prologue_3 starts
    courier = active_story(engine, "prologue_3").resolved["b"]
    assert courier != berth
    story_state.bump(f"docked_at:{courier}")
    finish_active("prologue_3")
    assert story_state.has_flag("prologue_complete")
    assert manager.faction_standing["Independent"] >= 5

    talk("hale_return", "I met the courier.")
    assert story_state.has_flag("prologue_epilogue_seen")
    assert story_state.completed_story_missions == ["prologue_1", "prologue_2", "prologue_3"]
    assert story_state.ledger_entries[-2:] == ["ledger_entry_1", "ledger_entry_2"]
