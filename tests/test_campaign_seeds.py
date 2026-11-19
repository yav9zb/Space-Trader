"""The campaign must work in any universe, not just the seeds the other tests
use: every contact has to find a station in the right faction's space, and
every mission has to resolve all its waypoints."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from types import SimpleNamespace

import pytest

from src.entities.ship import Ship
from src.factions import get_station_faction
from src.missions.mission_manager import MissionManager
from src.story import director
from src.story.chapters import STORY_MISSIONS
from src.story.npcs import NPCS
from src.story.story_missions import create_story_mission
from src.story.story_state import story_state
from src.universe import Universe

SEEDS = [1, 7, 42, 99, 123, 555, 1234, 2024, 31337, 65535, 77777, 90210, 123456, 424242,
         987654, 1000003, 2222222, 5555555, 8675309, 1322708771]


def engine_for(seed):
    story_state.reset()
    universe = Universe(seed=seed)
    universe.generate_universe()
    return SimpleNamespace(
        universe=universe, world_seed=universe.world_seed, story_state=story_state,
        mission_manager=MissionManager(), ship=Ship(0, 0), opened=[])


@pytest.fixture(autouse=True)
def clean():
    yield
    story_state.reset()


@pytest.mark.parametrize("seed", SEEDS)
def test_every_contact_is_placed_in_the_right_faction_on_its_own_station(seed):
    engine = engine_for(seed)
    story_state.chapter = "act_4"                     # everyone is available
    director.ensure_npcs_placed(engine)

    names = []
    for npc in NPCS.values():
        name = story_state.npc_stations.get(npc.id)
        assert name, f"seed {seed}: {npc.id} was not placed"
        station = director.find_station_by_name(name, engine.universe)
        assert station is not None
        assert get_station_faction(station, engine.world_seed) == npc.faction, (seed, npc.id)
        if npc.station_types:
            assert station.station_type.value in npc.station_types, (seed, npc.id)
        names.append(name)
    assert len(set(names)) == len(names), f"seed {seed}: two contacts share a station"


@pytest.mark.parametrize("seed", SEEDS)
def test_every_mission_resolves_its_waypoints_to_distinct_real_stations(seed):
    engine = engine_for(seed)
    story_state.chapter = "act_4"
    director.ensure_npcs_placed(engine)

    for mission_id, definition in STORY_MISSIONS.items():
        mission = create_story_mission(mission_id, engine)
        assert mission is not None, f"seed {seed}: {mission_id} could not be set up"
        for key, spec in definition.waypoints.items():
            station = director.find_station_by_name(mission.resolved[key], engine.universe)
            assert station is not None
            assert get_station_faction(station, engine.world_seed) == spec.faction, (seed, mission_id, key)

    # Contacts and waypoints never share a station
    placed = list(story_state.npc_stations.values())
    assert len(set(placed)) == len(placed), f"seed {seed}: a station was claimed twice"
