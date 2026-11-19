import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import random
from types import SimpleNamespace

import pygame
import pytest
from pygame import Vector2

from src.combat.combat_manager import combat_manager
from src.combat.weapons import Projectile, WeaponType
from src.entities.bandit import BanditShip, BanditType
from src.entities.ship import Ship
from src.entities.station import StationType
from src.entities.trader import TraderShip, TraderState
from src.factions import get_controlling_faction, FACTION_PIRATE
from src.missions.mission_manager import MissionManager
from src.missions.mission_types import Mission, MissionStatus, MissionType
from src.missions.specific_missions import EscortMission, BountyMission
from src.story.story_state import story_state
from src.universe import Universe


def clear_combat():
    combat_manager.active_traders.clear()
    combat_manager.active_bandits.clear()
    combat_manager.explosions.clear()


@pytest.fixture
def world():
    story_state.reset()
    clear_combat()
    universe = Universe(seed=808)
    universe.generate_universe()
    a = universe.ensure_station_in_sector(30, 30, StationType.TRADING)
    b = universe.ensure_station_in_sector(33, 30, StationType.MINING)
    engine = SimpleNamespace(
        universe=universe, world_seed=universe.world_seed,
        ship=Ship(a.position.x + 100, a.position.y),
        mission_manager=MissionManager(), story_state=story_state,
    )
    engine.a, engine.b = a, b
    yield engine
    story_state.reset()
    clear_combat()


def roundtrip(mission):
    return Mission.from_dict(json.loads(json.dumps(mission.to_dict())))


def active_escort_traders(mission):
    return [t for t in combat_manager.active_traders if t.escort_id == mission.id]


def start_escort(world):
    mission = EscortMission(world.a.name, world.b.name)
    world.mission_manager.available_missions.append(mission)
    world.mission_manager.reputation = 50
    ok, message = world.mission_manager.accept_mission(mission.id, world.ship, world)
    assert ok, message
    return mission


# --- Escort -----------------------------------------------------------------

def test_escort_spawns_the_trader_and_an_ambush_exactly_once(world):
    mission = start_escort(world)
    mission.on_update(world)

    traders = active_escort_traders(mission)
    assert len(traders) == 1
    assert traders[0].destination_station is world.b
    assert len(combat_manager.active_bandits) >= 2
    assert mission.status == MissionStatus.IN_PROGRESS

    bandits_before = len(combat_manager.active_bandits)
    mission.on_update(world)
    mission.on_update(world)
    assert len(active_escort_traders(mission)) == 1
    assert len(combat_manager.active_bandits) == bandits_before


def test_ambush_sits_beside_the_route_not_on_a_station(world):
    mission = start_escort(world)
    mission.on_update(world)
    midpoint = (world.a.position + world.b.position) / 2
    for bandit in combat_manager.active_bandits:
        assert (bandit.position - midpoint).length() < 700
        assert (bandit.position - world.a.position).length() > 1000


def test_trader_arriving_completes_the_mission(world):
    mission = start_escort(world)
    mission.on_update(world)
    trader = active_escort_traders(mission)[0]
    trader.position = Vector2(world.b.position)
    trader.update(0.1, world)

    assert not trader.alive
    assert mission.update_progress(world.ship) is True
    assert mission.status == MissionStatus.COMPLETED


def test_destroying_the_trader_fails_the_mission(world):
    mission = start_escort(world)
    mission.on_update(world)
    trader = active_escort_traders(mission)[0]
    assert trader.take_damage(1000) is True

    assert mission.update_progress(world.ship) is False
    assert mission.status == MissionStatus.FAILED


def test_escorted_trader_keeps_going_when_hit_instead_of_fleeing(world):
    mission = start_escort(world)
    mission.on_update(world)
    trader = active_escort_traders(mission)[0]
    trader.take_damage(5)
    assert trader.state == TraderState.TRAVELING

    plain = TraderShip(Vector2(0, 0), world.b)
    plain.take_damage(5)
    assert plain.state == TraderState.FLEEING


def test_missing_trader_after_a_load_is_brought_back_without_a_second_ambush(world):
    mission = start_escort(world)
    mission.on_update(world)
    restored = roundtrip(mission)
    assert restored.escort_spawned and restored.ambush_spawned

    clear_combat()                      # a load wipes the runtime entities
    restored.on_update(world)
    traders = [t for t in combat_manager.active_traders if t.escort_id == restored.id]
    assert len(traders) == 1
    assert (traders[0].position - world.ship.position).length() < 200
    assert combat_manager.active_bandits == []


def test_escort_mission_type_and_requirements(world):
    mission = EscortMission(world.a.name, world.b.name)
    assert mission.mission_type == MissionType.ESCORT
    assert mission.requirements.min_reputation == 5
    assert world.b.name in mission.description


# --- Bandit targeting and fire -----------------------------------------------

def test_bandit_prefers_a_nearer_escorted_trader_over_the_player(world):
    bandit = BanditShip(Vector2(0, 0), BanditType.FIGHTER)
    player = SimpleNamespace(position=Vector2(600, 0))
    escorted = TraderShip(Vector2(200, 0), world.b)
    escorted.escort_id = "m1"
    combat_manager.add_trader(escorted)

    assert bandit._select_focus(player) is escorted


def test_bandit_ignores_ordinary_and_distant_traders(world):
    bandit = BanditShip(Vector2(0, 0), BanditType.FIGHTER)
    player = SimpleNamespace(position=Vector2(600, 0))
    ordinary = TraderShip(Vector2(200, 0), world.b)          # not escorted
    far = TraderShip(Vector2(5000, 0), world.b)
    far.escort_id = "m1"
    combat_manager.add_trader(ordinary)
    combat_manager.add_trader(far)

    assert bandit._select_focus(player) is player


def test_bandit_fire_can_destroy_an_escorted_trader(world):
    bandit = BanditShip(Vector2(-3000, 0), BanditType.FIGHTER)
    trader = TraderShip(Vector2(0, 0), world.b)
    trader.escort_id = "m1"
    combat_manager.add_trader(trader)
    bandit.weapon_system.projectiles.append(
        Projectile(trader.position, Vector2(0, 0), 500, bandit, WeaponType.LASER))

    combat_manager._check_bandit_combat(bandit, world.ship, world)

    assert not trader.alive
    assert story_state.count_events("escort_lost:m1") == 1


def test_bandit_fire_does_not_hurt_ordinary_traders(world):
    bandit = BanditShip(Vector2(-3000, 0), BanditType.FIGHTER)
    trader = TraderShip(Vector2(0, 0), world.b)
    combat_manager.add_trader(trader)
    bandit.weapon_system.projectiles.append(
        Projectile(trader.position, Vector2(0, 0), 500, bandit, WeaponType.LASER))

    combat_manager._check_bandit_combat(bandit, world.ship, world)
    assert trader.alive and trader.current_hull == trader.max_hull


# --- Bounty ---------------------------------------------------------------

def make_bounty(world, target_type="heavy"):
    mission = BountyMission("Red Vask", 4, 0, target_type, world.a.name)
    world.mission_manager.available_missions.append(mission)
    world.mission_manager.reputation = 50
    ok, message = world.mission_manager.accept_mission(mission.id, world.ship, world)
    assert ok, message
    return mission


def targets(mission):
    return [b for b in combat_manager.active_bandits if b.bounty_id == mission.id]


def test_bounty_spawns_a_named_target_in_its_sector_once(world):
    mission = make_bounty(world, "boss")
    mission.on_update(world)
    mission.on_update(world)

    found = targets(mission)
    assert len(found) == 1
    assert found[0].name == "Red Vask"
    assert found[0].bandit_type == BanditType.BOSS
    assert int(found[0].position.x // 1000) == 4 and int(found[0].position.y // 1000) == 0


def test_bounty_description_uses_the_hud_sector_convention(world):
    mission = BountyMission("Red Vask", 4, 0, "heavy", world.a.name)
    assert "Sector (4, -1)" in mission.description      # HUD shows int(-y // 1000)


def test_killing_the_target_completes_the_bounty_and_stops_respawns(world):
    mission = make_bounty(world)
    mission.on_update(world)
    target = targets(mission)[0]

    combat_manager._handle_bandit_destroyed(target, world.ship)
    assert mission.update_progress(world.ship) is True
    assert mission.status == MissionStatus.COMPLETED

    clear_combat()
    mission.on_update(world)
    assert targets(mission) == []


def test_missing_target_is_respawned_until_it_is_killed(world):
    mission = make_bounty(world)
    mission.on_update(world)
    restored = roundtrip(mission)
    assert (restored.target_name, restored.sector_x, restored.sector_y) == ("Red Vask", 4, 0)

    clear_combat()                      # a load wipes the runtime entities
    restored.on_update(world)
    assert len(targets(restored)) == 1


def test_named_bandit_draws_without_error():
    pygame.display.init()
    pygame.font.init()
    surface = pygame.Surface((400, 300))
    bandit = BanditShip(Vector2(200, 150), BanditType.BOSS)
    bandit.name = "Red Vask"
    bandit.draw(surface, Vector2(0, 0))


# --- Generation ----------------------------------------------------------------

def generate_many(manager, station, stations, n=60):
    out = []
    for seed in range(n):
        random.seed(seed)
        mission = manager.generate_station_specific_mission(station, stations)
        if mission:
            out.append(mission)
    random.seed()
    return out


def test_new_mission_types_are_offered_where_the_weights_say(world):
    manager = MissionManager()
    manager._world_seed = world.world_seed
    stations = world.universe.stations
    trading = world.a
    military = world.universe.ensure_station_in_sector(34, 31, StationType.MILITARY)

    assert any(m.mission_type == MissionType.ESCORT
               for m in generate_many(manager, trading, stations))
    assert any(m.mission_type == MissionType.BOUNTY
               for m in generate_many(manager, military, stations))
    assert not any(m.mission_type == MissionType.BOUNTY
                   for m in generate_many(manager, trading, stations))


def test_generated_bounties_are_in_pirate_space_when_the_world_is_known(world):
    manager = MissionManager()
    manager._world_seed = world.world_seed
    military = world.universe.ensure_station_in_sector(34, 31, StationType.MILITARY)

    bounties = [m for m in generate_many(manager, military, world.universe.stations, 80)
                if m.mission_type == MissionType.BOUNTY]
    assert bounties
    fallback = {(4, 0), (-4, 0), (0, 4), (0, -4), (5, 5), (-5, -5)}
    for m in bounties:
        in_pirate_space = get_controlling_faction(m.sector_x, m.sector_y, world.world_seed) == FACTION_PIRATE
        assert in_pirate_space or (m.sector_x, m.sector_y) in fallback
        assert max(abs(m.sector_x), abs(m.sector_y)) >= 3
        assert m.target_type in ("heavy", "boss")
