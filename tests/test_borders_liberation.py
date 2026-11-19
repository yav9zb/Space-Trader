import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import random
from types import SimpleNamespace

import pytest
from pygame import Vector2

from src import factions
from src.combat.combat_manager import combat_manager
from src.entities.bandit import BanditState
from src.entities.patrol import PatrolShip
from src.entities.ship import Ship
from src.entities.station import StationType
from src.factions import (
    get_controlling_faction, FACTION_INDEPENDENT, FACTION_PIRATE, FACTION_TRADE_GUILD,
    FACTION_REGION_SECTORS, SAFE_ZONE_SECTORS,
)
from src.missions.mission_manager import MissionManager
from src.missions.mission_types import Mission, MissionStatus, MissionType
from src.missions.specific_missions import LiberationMission
from src.story import borders
from src.story.dialogue import apply_effects, validate_nodes, Node, Choice
from src.story.story_state import StoryState, story_state
from src.ui.notifications import notifications
from src.universe import Universe

SEED = 777


@pytest.fixture
def world():
    story_state.reset()
    notifications.clear()
    for group in (combat_manager.active_bandits, combat_manager.active_patrols,
                  combat_manager.active_traders, combat_manager.explosions):
        group.clear()
    universe = Universe(seed=SEED)
    universe.generate_universe()
    engine = SimpleNamespace(
        universe=universe, world_seed=SEED, ship=Ship(0, 0),
        mission_manager=MissionManager(), story_state=story_state, play_time=0.0,
    )
    engine.mission_manager._world_seed = SEED
    yield engine
    story_state.reset()
    notifications.clear()
    combat_manager.active_bandits.clear()
    combat_manager.active_patrols.clear()


def pirate_region(seed=SEED):
    half = FACTION_REGION_SECTORS // 2
    for rx in range(-6, 7):
        for ry in range(-6, 7):
            if get_controlling_faction(rx * FACTION_REGION_SECTORS + half,
                                       ry * FACTION_REGION_SECTORS + half, seed) == FACTION_PIRATE:
                return rx, ry
    raise AssertionError("no pirate region")


# --- Overrides ---------------------------------------------------------------------

def sectors_in(region):
    return [(region[0] * FACTION_REGION_SECTORS + dx, region[1] * FACTION_REGION_SECTORS + dy)
            for dx in range(FACTION_REGION_SECTORS) for dy in range(FACTION_REGION_SECTORS)]


def test_an_override_changes_every_sector_in_the_region_and_nothing_else(world):
    region = pirate_region()
    neighbour = (region[0] + 1, region[1])
    before = {s: get_controlling_faction(*s, SEED) for s in sectors_in(neighbour)}

    story_state.set_region_override(region, FACTION_INDEPENDENT)

    assert all(get_controlling_faction(*s, SEED) == FACTION_INDEPENDENT for s in sectors_in(region))
    assert {s: get_controlling_faction(*s, SEED) for s in sectors_in(neighbour)} == before


def test_the_safe_zone_cannot_be_overridden(world):
    story_state.set_region_override((0, 0), FACTION_PIRATE)
    assert get_controlling_faction(0, 0, SEED) == FACTION_INDEPENDENT
    assert get_controlling_faction(SAFE_ZONE_SECTORS, SAFE_ZONE_SECTORS, SEED) == FACTION_INDEPENDENT


def test_overrides_save_load_and_reset(world):
    region = pirate_region()
    story_state.set_region_override(region, FACTION_TRADE_GUILD)
    data = json.loads(json.dumps(story_state.to_dict()))
    assert data["region_overrides"] == {f"{region[0]},{region[1]}": FACTION_TRADE_GUILD}

    story_state.reset()
    assert get_controlling_faction(*sectors_in(region)[0], SEED) == FACTION_PIRATE

    story_state.from_dict(data)
    assert get_controlling_faction(*sectors_in(region)[0], SEED) == FACTION_TRADE_GUILD

    story_state.from_dict({})                       # an older save: no overrides at all
    assert get_controlling_faction(*sectors_in(region)[0], SEED) == FACTION_PIRATE


def test_negative_region_coordinates_work(world):
    story_state.set_region_override((-3, -2), FACTION_TRADE_GUILD)
    cx, cy = -3 * FACTION_REGION_SECTORS + 1, -2 * FACTION_REGION_SECTORS + 2
    assert get_controlling_faction(cx, cy, SEED) == FACTION_TRADE_GUILD


# --- Flipping --------------------------------------------------------------------------

def test_flip_region_announces_and_records_the_change(world):
    region = pirate_region()
    borders.flip_region(region, FACTION_INDEPENDENT)
    assert story_state.count_events("region_flipped") == 1
    assert any("Borders shift" in item[0] and FACTION_INDEPENDENT in item[0] for item in notifications.items)


def test_nearest_region_picks_the_closest_one_of_the_right_faction(world):
    found = borders.nearest_region(Vector2(0, 0), FACTION_PIRATE, SEED)
    assert found is not None
    center = borders.region_center(found)
    assert get_controlling_faction(int(center.x // 1000), int(center.y // 1000), SEED) == FACTION_PIRATE
    for region in [(rx, ry) for rx in range(-6, 7) for ry in range(-6, 7)]:
        c = borders.region_center(region)
        if get_controlling_faction(int(c.x // 1000), int(c.y // 1000), SEED) == FACTION_PIRATE:
            assert (c - Vector2(0, 0)).length() >= (center - Vector2(0, 0)).length() - 1e-6


def test_flip_nearest_region_reports_failure_when_there_is_none(world):
    assert borders.flip_nearest_region(world, FACTION_PIRATE, FACTION_INDEPENDENT) is True
    # Flip every pirate region nearby, then there is nothing left to flip
    for _ in range(200):                            # bounded: a broken flip must fail, not hang
        if not borders.flip_nearest_region(world, FACTION_PIRATE, FACTION_INDEPENDENT):
            break
    else:
        pytest.fail("flip_nearest_region never ran out of regions to flip")
    assert borders.flip_nearest_region(world, FACTION_PIRATE, FACTION_INDEPENDENT) is False


def test_the_flip_region_dialogue_effect(world):
    region_before = borders.nearest_region(world.ship.position, FACTION_PIRATE, SEED)
    apply_effects([{"type": "flip_region", "from": FACTION_PIRATE, "faction": FACTION_TRADE_GUILD}], world)
    center = borders.region_center(region_before)
    assert get_controlling_faction(int(center.x // 1000), int(center.y // 1000), SEED) == FACTION_TRADE_GUILD


def test_flip_region_is_a_valid_authored_effect():
    node = Node("n", "X", "hi", choices=[Choice("go", effects=[
        {"type": "flip_region", "from": FACTION_PIRATE, "faction": FACTION_INDEPENDENT}])])
    assert validate_nodes({"n": node}) == []


# --- Liberation missions ------------------------------------------------------------------

def make_liberation(world):
    region = pirate_region()
    mission = LiberationMission("Base-1", region[0], region[1])
    world.mission_manager.available_missions.append(mission)
    world.mission_manager.reputation = 50
    ok, message = world.mission_manager.accept_mission(mission.id, world.ship, world)
    assert ok, message
    return mission, region


def fleet(mission):
    return [b for b in combat_manager.active_bandits if b.stronghold_id == mission.id]


def test_liberation_spawns_the_whole_fleet_once_at_the_region_center(world):
    mission, region = make_liberation(world)
    mission.on_update(world)
    mission.on_update(world)

    ships = fleet(mission)
    assert len(ships) == mission.fleet_size == 5
    center = borders.region_center(region)
    assert all((s.position - center).length() < 300 for s in ships)
    assert sum(1 for s in ships if s.name == "Warlord") == 1
    assert mission.status == MissionStatus.IN_PROGRESS
    assert mission.mission_type == MissionType.LIBERATION


def test_killing_the_fleet_completes_the_mission_and_frees_the_region(world):
    mission, region = make_liberation(world)
    mission.on_update(world)

    for ship in fleet(mission):
        combat_manager._handle_bandit_destroyed(ship, world.ship)
        if len(story_state.recent_events):
            pass
    assert mission.update_progress(world.ship) is True
    assert mission.status == MissionStatus.COMPLETED

    center = borders.region_center(region)
    assert get_controlling_faction(int(center.x // 1000), int(center.y // 1000), SEED) == FACTION_INDEPENDENT


def test_the_region_does_not_flip_until_the_last_ship_dies(world):
    mission, region = make_liberation(world)
    mission.on_update(world)
    for ship in fleet(mission)[:-1]:
        combat_manager._handle_bandit_destroyed(ship, world.ship)
    assert mission.update_progress(world.ship) is False
    center = borders.region_center(region)
    assert get_controlling_faction(int(center.x // 1000), int(center.y // 1000), SEED) == FACTION_PIRATE
    assert "4/5" in mission.progress_description or "Stronghold ships destroyed" in mission.progress_description


def test_only_the_survivors_are_respawned_after_a_load(world):
    mission, _ = make_liberation(world)
    mission.on_update(world)
    for ship in fleet(mission)[:2]:
        combat_manager._handle_bandit_destroyed(ship, world.ship)
    restored = Mission.from_dict(json.loads(json.dumps(mission.to_dict())))

    combat_manager.active_bandits.clear()               # a load wipes runtime entities
    restored.on_update(world)
    assert len(fleet(restored)) == 3
    restored.on_update(world)
    assert len(fleet(restored)) == 3


def test_patrols_leave_the_stronghold_fleet_to_the_player(world):
    mission, _ = make_liberation(world)
    mission.on_update(world)
    ship = fleet(mission)[0]
    patrol = PatrolShip(ship.position - Vector2(200, 0))
    assert patrol._pick_target(SimpleNamespace(
        mission_manager=world.mission_manager, ship=world.ship)) is None


def test_liberation_missions_are_generated_at_military_bases_in_pirate_regions(world):
    manager = world.mission_manager
    military = world.universe.ensure_station_in_sector(34, 31, StationType.MILITARY)
    made = []
    for seed in range(150):
        random.seed(seed)
        m = manager.generate_station_specific_mission(military, world.universe.stations)
        if m and m.mission_type == MissionType.LIBERATION:
            made.append(m)
    random.seed()
    assert made
    half = FACTION_REGION_SECTORS // 2
    for m in made:
        assert get_controlling_faction(m.region_x * FACTION_REGION_SECTORS + half,
                                       m.region_y * FACTION_REGION_SECTORS + half, SEED) == FACTION_PIRATE
        assert m.requirements.min_reputation == 20


def test_no_liberation_mission_without_a_known_world(world):
    manager = MissionManager()                       # _world_seed unset
    military = world.universe.ensure_station_in_sector(34, 31, StationType.MILITARY)
    assert manager._generate_liberation_mission(military) is None
