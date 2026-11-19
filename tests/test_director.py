import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import random
from types import SimpleNamespace

import pytest

from src.entities.station import StationType
from src.factions import get_station_faction, get_controlling_faction
from src.story import director
from src.story.npcs import NPC, NPCS, is_available
from src.story.story_state import StoryState
from src.universe import Universe


def make_engine(seed=4242):
    universe = Universe(seed=seed)
    universe.generate_universe()
    return SimpleNamespace(
        universe=universe, world_seed=universe.world_seed, story_state=StoryState())


PIRATE_BROKER = NPC(
    id="test_broker", name="Test Broker", role="Broker", faction="Pirate Territory",
    intro_node="x", return_node="y", station_types=("Mining Station",),
    min_ring=6, max_ring=9, chapter="act_1",
)


def ring_of(station, universe):
    return max(abs(int(station.position.x // universe.sector_size)),
               abs(int(station.position.y // universe.sector_size)))


def test_hale_is_placed_in_safe_independent_space_and_remembered():
    engine = make_engine()
    director.ensure_npcs_placed(engine)
    name = engine.story_state.npc_stations["hale"]
    station = director.find_station_by_name(name, engine.universe)
    assert station is not None
    assert get_station_faction(station, engine.world_seed) == "Independent"
    assert ring_of(station, engine.universe) <= NPCS["hale"].max_ring


def test_placement_is_idempotent():
    engine = make_engine()
    director.ensure_npcs_placed(engine)
    first = dict(engine.story_state.npc_stations)
    count = len(engine.universe.stations)
    director.ensure_npcs_placed(engine)
    assert engine.story_state.npc_stations == first
    assert len(engine.universe.stations) == count


def test_missing_station_is_created_with_required_type_faction_and_ring():
    engine = make_engine()
    station = director.place_npc(PIRATE_BROKER, engine)
    assert station is not None
    assert station.station_type == StationType.MINING
    assert get_station_faction(station, engine.world_seed) == "Pirate Territory"
    assert PIRATE_BROKER.min_ring <= ring_of(station, engine.universe) <= PIRATE_BROKER.max_ring + 12
    assert station in engine.universe.stations
    assert engine.story_state.npc_stations["test_broker"] == station.name


def test_created_station_position_is_repeatable_for_the_same_seed():
    a = director.place_npc(PIRATE_BROKER, make_engine(seed=99))
    b = director.place_npc(PIRATE_BROKER, make_engine(seed=99))
    assert (a.position.x, a.position.y) == (b.position.x, b.position.y)


def test_ensure_station_in_sector_reuses_existing_and_preserves_rng_state():
    engine = make_engine()
    universe = engine.universe
    existing = universe.stations[0]
    cx = int(existing.position.x // universe.sector_size)
    cy = int(existing.position.y // universe.sector_size)
    assert universe.ensure_station_in_sector(cx, cy) is existing

    random.seed(123)
    before = random.getstate()
    universe.ensure_station_in_sector(40, 40, StationType.RESEARCH)
    assert random.getstate() == before


def test_new_station_lands_inside_the_requested_sector():
    engine = make_engine()
    universe = engine.universe
    station = universe.ensure_station_in_sector(25, -13, StationType.SHIPYARD)
    assert int(station.position.x // universe.sector_size) == 25
    assert int(station.position.y // universe.sector_size) == -13
    assert station.station_type == StationType.SHIPYARD


def test_chunk_generation_does_not_overlap_a_precreated_station():
    engine = make_engine()
    universe = engine.universe
    station = universe.ensure_station_in_sector(30, 30, StationType.TRADING)
    from pygame import Vector2
    universe.generate_chunk_around_position(Vector2(30 * 1000 + 500, 30 * 1000 + 500))
    for planet in universe.planets:
        if int(planet.position.x // 1000) == 30 and int(planet.position.y // 1000) == 30:
            assert (planet.position - station.position).length() >= station.size + planet.size


def test_contact_lookup_and_start_node_selection():
    engine = make_engine()
    director.ensure_npcs_placed(engine)
    hale_station = director.find_station_by_name(engine.story_state.npc_stations["hale"], engine.universe)
    other = engine.universe.ensure_station_in_sector(35, 35, StationType.TRADING)

    assert director.get_contact_at(hale_station, engine).id == "hale"
    assert director.get_contact_at(other, engine) is None

    story = engine.story_state
    assert director.start_node_for(NPCS["hale"], story) == "hale_intro"
    story.mark_node_seen("hale_intro")
    assert director.start_node_for(NPCS["hale"], story) == "hale_return"


def test_npcs_appear_only_when_their_chapter_is_reached():
    story = StoryState()
    assert is_available(NPCS["hale"], story)
    assert not is_available(PIRATE_BROKER, story)       # act_1 contact, prologue story
    story.chapter = "act_2"
    assert is_available(PIRATE_BROKER, story)


def test_ensure_npcs_placed_tolerates_engines_without_a_universe():
    director.ensure_npcs_placed(SimpleNamespace(story_state=StoryState()))
