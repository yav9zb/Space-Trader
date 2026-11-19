"""The fleet, escort and reach_sector stage kinds, driven through throwaway
story missions so they are tested independently of the authored campaign."""

import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from types import SimpleNamespace

import pytest
from pygame import Vector2

from src.combat.combat_manager import combat_manager
from src.entities.ship import Ship
from src.missions.mission_manager import MissionManager
from src.missions.mission_types import Mission, MissionStatus
from src.story import chapters, director
from src.story.chapters import Stage, StoryMissionDef, Waypoint
from src.story.objectives import displayed_sector
from src.story.story_missions import start_story_mission
from src.story.story_state import story_state
from src.universe import Universe

FLEET = StoryMissionDef(
    id="t_fleet", title="Fleet", description="Break the fleet at {a}.", giver="hale",
    waypoints={"a": Waypoint(faction="Independent", min_ring=2, max_ring=4)},
    stages=(Stage("fleet", "Destroy the fleet", {
        "at": "a", "ships": ["boss", "fighter", "fighter"], "boss_name": "Dross"}),),
)
ESCORT = StoryMissionDef(
    id="t_escort", title="Escort", description="Guard the trader to {b}.", giver="hale",
    waypoints={"b": Waypoint(faction="Independent", min_ring=2, max_ring=4)},
    stages=(Stage("escort", "Escort the trader to {b}",
                  {"from": "giver", "to": "b", "ambush": "scout_patrol"}),),
)
SECTOR = StoryMissionDef(
    id="t_sector", title="Far", description="Go far.", giver="hale",
    stages=(Stage("reach_sector", "Reach (12, -9)", {"x": 12, "y": -9, "radius": 1}),),
)


@pytest.fixture
def engine(monkeypatch):
    for definition in (FLEET, ESCORT, SECTOR):
        monkeypatch.setitem(chapters.STORY_MISSIONS, definition.id, definition)
    story_state.reset()
    for group in (combat_manager.active_bandits, combat_manager.active_traders,
                  combat_manager.active_patrols):
        group.clear()
    universe = Universe(seed=4242)
    universe.generate_universe()
    eng = SimpleNamespace(
        universe=universe, world_seed=universe.world_seed, story_state=story_state,
        mission_manager=MissionManager(), ship=Ship(0, 0), play_time=0.0,
        opened=[],
    )
    eng.start_dialogue = eng.opened.append
    director.ensure_npcs_placed(eng)
    yield eng
    story_state.reset()
    for group in (combat_manager.active_bandits, combat_manager.active_traders):
        group.clear()


def mission_for(engine, story_id):
    assert start_story_mission(story_id, engine)
    return next(m for m in engine.mission_manager.active_missions if m.story_id == story_id)


def stronghold(mission):
    key = f"{mission.story_id}:0"
    return [b for b in combat_manager.active_bandits if b.stronghold_id == key]


def tick(engine):
    engine.mission_manager.update(engine)


# --- reach_sector ---------------------------------------------------------------------

def test_displayed_sector_inverts_y_like_the_hud():
    assert displayed_sector(Vector2(12500, -9500)) == (12, 9)
    assert displayed_sector(Vector2(12500, 8500)) == (12, -9)


def test_reach_sector_uses_displayed_coordinates_and_radius(engine):
    mission = mission_for(engine, "t_sector")
    engine.ship.position = Vector2(12500, -9500)        # displays as (12, 9): wrong side
    tick(engine)
    assert mission.status != MissionStatus.COMPLETED

    engine.ship.position = Vector2(13400, 8200)          # displays as (13, -9): within radius 1
    tick(engine)
    assert mission in engine.mission_manager.completed_missions


def test_reach_sector_outside_the_radius_does_not_count(engine):
    mission = mission_for(engine, "t_sector")
    engine.ship.position = Vector2(14500, 8500)          # displays as (14, -9)
    tick(engine)
    assert mission.status != MissionStatus.COMPLETED


# --- fleet ---------------------------------------------------------------------------------

def test_a_fleet_spawns_once_beside_the_waypoint_and_names_its_boss(engine):
    mission = mission_for(engine, "t_fleet")
    tick(engine)
    tick(engine)
    ships = stronghold(mission)
    assert len(ships) == 3
    station = director.find_station_by_name(mission.resolved["a"], engine.universe)
    assert all((s.position - station.position).length() < station.size + 800 for s in ships)
    assert [s.name for s in ships].count("Dross") == 1


def test_destroying_the_fleet_completes_the_mission(engine):
    mission = mission_for(engine, "t_fleet")
    tick(engine)
    for ship in stronghold(mission)[:-1]:
        combat_manager._handle_bandit_destroyed(ship, engine.ship)
    tick(engine)
    assert mission.status != MissionStatus.COMPLETED
    combat_manager._handle_bandit_destroyed(stronghold(mission)[-1], engine.ship)
    tick(engine)
    assert mission in engine.mission_manager.completed_missions
    assert "t_fleet" in story_state.completed_story_missions


def test_only_survivors_return_after_a_load(engine):
    mission = mission_for(engine, "t_fleet")
    tick(engine)
    combat_manager._handle_bandit_destroyed(stronghold(mission)[0], engine.ship)
    restored = Mission.from_dict(json.loads(json.dumps(mission.to_dict())))
    engine.mission_manager.active_missions = [restored]
    combat_manager.active_bandits.clear()
    tick(engine)
    tick(engine)
    assert len(stronghold(restored)) == 2


def test_restarting_a_fleet_mission_ignores_kills_from_the_last_attempt(engine):
    first = mission_for(engine, "t_fleet")
    tick(engine)
    for ship in stronghold(first)[:2]:
        combat_manager._handle_bandit_destroyed(ship, engine.ship)
    engine.mission_manager.abandon_mission(first.id, engine.ship, engine)
    combat_manager.active_bandits.clear()

    second = mission_for(engine, "t_fleet")
    tick(engine)
    assert len(stronghold(second)) == 3
    tick(engine)
    assert second.status != MissionStatus.COMPLETED


# --- escort ------------------------------------------------------------------------------------

def escorted(mission):
    return [t for t in combat_manager.active_traders if t.escort_id == f"{mission.story_id}:0"]


def test_an_escort_trader_starts_at_the_giver_with_one_ambush(engine):
    mission = mission_for(engine, "t_escort")
    tick(engine)
    tick(engine)
    traders = escorted(mission)
    assert len(traders) == 1
    origin = director.find_station_by_name(story_state.npc_stations["hale"], engine.universe)
    assert (traders[0].position - origin.position).length() < origin.size + 100
    assert traders[0].destination_station.name == mission.resolved["b"]
    ambush = len(combat_manager.active_bandits)
    assert ambush >= 2
    tick(engine)
    assert len(combat_manager.active_bandits) == ambush


def test_the_trader_arriving_completes_the_mission(engine):
    mission = mission_for(engine, "t_escort")
    tick(engine)
    escorted(mission)[0].update(0.1, engine)             # not there yet
    tick(engine)
    assert mission.status != MissionStatus.COMPLETED

    trader = escorted(mission)[0]
    trader.position = Vector2(trader.destination_station.position)
    trader.update(0.1, engine)
    tick(engine)
    assert mission in engine.mission_manager.completed_missions


def test_losing_the_trader_fails_the_mission_and_it_can_be_retried(engine):
    mission = mission_for(engine, "t_escort")
    tick(engine)
    escorted(mission)[0].take_damage(10_000)
    tick(engine)
    assert mission in engine.mission_manager.failed_missions
    assert "t_escort" not in story_state.active_story_missions

    again = mission_for(engine, "t_escort")              # startable again, old loss not held against it
    tick(engine)
    assert again.status == MissionStatus.IN_PROGRESS
    assert again not in engine.mission_manager.failed_missions


def test_a_missing_trader_returns_beside_the_player_after_a_load(engine):
    mission = mission_for(engine, "t_escort")
    tick(engine)
    restored = Mission.from_dict(json.loads(json.dumps(mission.to_dict())))
    engine.mission_manager.active_missions = [restored]
    combat_manager.active_traders.clear()
    bandits = len(combat_manager.active_bandits)
    engine.ship.position = Vector2(5000, 5000)
    tick(engine)
    traders = escorted(restored)
    assert len(traders) == 1
    assert (traders[0].position - engine.ship.position).length() < 200
    assert len(combat_manager.active_bandits) == bandits      # the ambush is not repeated
