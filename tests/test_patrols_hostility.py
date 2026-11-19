import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from types import SimpleNamespace

import pygame
import pytest
from pygame import Vector2

from src.combat.combat_manager import (
    combat_manager, BACKUP_COUNT, BACKUP_LIFETIME, BACKUP_COOLDOWN,
)
from src.combat.weapons import Projectile, WeaponType
from src.docking.docking_manager import DockingManager
from src.docking.docking_state import DockingResult, DockingState
from src.entities.bandit import BanditShip, BanditType, BanditState
from src.entities.patrol import PatrolShip
from src.entities.ship import Ship
from src.entities.station import StationType
from src.factions import (
    docking_refusal, get_controlling_faction, HOSTILE_STANDING,
    FACTION_TRADE_GUILD, FACTION_INDEPENDENT, FACTION_PIRATE,
)
from src.missions.mission_manager import MissionManager, STANDING_RECOVERY_SECONDS
from src.story.story_state import story_state
from src.ui.notifications import Notifications
from src.universe import Universe


def clear_combat():
    for group in (combat_manager.active_traders, combat_manager.active_bandits,
                  combat_manager.active_patrols, combat_manager.explosions):
        group.clear()
    combat_manager.last_backup_time = -BACKUP_COOLDOWN


@pytest.fixture
def world():
    story_state.reset()
    clear_combat()
    universe = Universe(seed=909)
    universe.generate_universe()
    engine = SimpleNamespace(
        universe=universe, world_seed=universe.world_seed,
        ship=Ship(0, 0), mission_manager=MissionManager(),
        story_state=story_state, play_time=1000.0,
    )
    yield engine
    story_state.reset()
    clear_combat()


# --- Hostility rules --------------------------------------------------------

def test_only_guild_and_pirate_stations_bar_a_hostile_player():
    assert docking_refusal(FACTION_TRADE_GUILD, HOSTILE_STANDING)
    assert docking_refusal(FACTION_PIRATE, HOSTILE_STANDING - 30)
    assert docking_refusal(FACTION_TRADE_GUILD, HOSTILE_STANDING + 1) is None
    assert docking_refusal(FACTION_INDEPENDENT, -500) is None   # always a safe harbor


# --- Docking refusal ----------------------------------------------------------

def make_docking_scene(refusal):
    station = SimpleNamespace(name="Yard-1", size=40, position=Vector2(0, 0))
    ship = Ship(0, 0)
    ship.position = Vector2(50, 0)
    ship.velocity = Vector2(0, 0)
    manager = DockingManager()
    manager.refusal_check = lambda s: refusal
    return manager, ship, station


def test_refused_station_cannot_be_docked_at_even_when_close_and_slow():
    manager, ship, station = make_docking_scene("The Trade Guild has barred you from its stations")
    can_dock, reason = manager._can_dock(ship, station)
    assert (can_dock, reason) == (False, DockingResult.REFUSED)


def test_manual_docking_returns_refused_and_nothing_starts():
    manager, ship, station = make_docking_scene("barred")
    assert manager.attempt_manual_docking(ship, [station]) == DockingResult.REFUSED
    assert manager.docking_state == DockingState.FREE_FLIGHT


def test_approaching_a_refusing_station_shows_the_message_and_does_not_auto_dock():
    manager, ship, station = make_docking_scene("The Trade Guild has barred you from its stations")
    manager.target_station = station
    manager.docking_state = DockingState.APPROACHING
    manager._update_approaching(ship, [station])
    assert manager.docking_state == DockingState.APPROACHING
    assert "barred" in manager.get_status_message()


def test_a_welcome_station_docks_normally():
    manager, ship, station = make_docking_scene(None)
    assert manager._can_dock(ship, station) == (True, DockingResult.SUCCESS)


def test_engine_refusal_follows_standing_with_the_stations_faction(world):
    from src.engine.game_engine import GameEngine
    from src.factions import get_station_faction

    station = world.universe.ensure_station_in_sector(30, 30, StationType.TRADING)
    faction = get_station_faction(station, world.world_seed)
    world.mission_manager.faction_standing[faction] = HOSTILE_STANDING
    expected_barred = faction in (FACTION_TRADE_GUILD, FACTION_PIRATE)
    assert bool(GameEngine._docking_refusal(world, station)) == expected_barred
    world.mission_manager.faction_standing[faction] = 0
    assert GameEngine._docking_refusal(world, station) is None


# --- Notifications -----------------------------------------------------------

def test_notifications_expire_and_dedupe_and_cap():
    n = Notifications()
    n.push("a", duration=1.0)
    n.push("a", duration=1.0)
    assert len(n.items) == 1
    for i in range(10):
        n.push(f"m{i}")
    assert len(n.items) == 4
    n.update(100)
    assert n.items == []


def test_notifications_render_without_error():
    pygame.display.init()
    pygame.font.init()
    n = Notifications()
    n.push("Trade Guild backup is on the way")
    n.update(3.8)                                   # inside the fade window
    n.render(pygame.Surface((800, 600)))


# --- Patrol behavior ------------------------------------------------------------

def make_bandit(position, bounty_id=None, state=None):
    bandit = BanditShip(Vector2(position), BanditType.SCOUT)
    bandit.bounty_id = bounty_id
    if state:
        bandit.state = state
    combat_manager.add_bandit(bandit)
    return bandit


def test_patrol_hunts_the_nearest_visible_bandit(world):
    patrol = PatrolShip(Vector2(0, 0))
    far = make_bandit((800, 0))
    near = make_bandit((300, 0))
    assert patrol._pick_target(world) is near
    near.state = BanditState.DISABLED
    assert patrol._pick_target(world) is far


def test_patrol_leaves_bounty_targets_and_out_of_range_bandits_alone(world):
    patrol = PatrolShip(Vector2(0, 0))
    make_bandit((300, 0), bounty_id="m1")
    make_bandit((5000, 0))
    assert patrol._pick_target(world) is None


def test_patrol_is_friendly_to_the_player_by_default(world):
    patrol = PatrolShip(Vector2(0, 0))
    world.ship.position = Vector2(100, 0)
    assert not patrol.is_hostile_to_player(world.mission_manager)
    assert patrol._pick_target(world) is None


def test_patrol_turns_on_the_player_when_standing_is_hostile(world):
    patrol = PatrolShip(Vector2(0, 0))
    world.ship.position = Vector2(100, 0)
    world.mission_manager.faction_standing[FACTION_TRADE_GUILD] = HOSTILE_STANDING
    assert patrol.is_hostile_to_player(world.mission_manager)
    assert patrol._pick_target(world) is world.ship


def test_hostile_patrol_prefers_whichever_target_is_nearer(world):
    patrol = PatrolShip(Vector2(0, 0))
    world.mission_manager.faction_standing[FACTION_TRADE_GUILD] = HOSTILE_STANDING
    world.ship.position = Vector2(500, 0)
    bandit = make_bandit((200, 0))
    assert patrol._pick_target(world) is bandit


def test_shooting_a_patrol_provokes_it_for_a_while(world):
    patrol = PatrolShip(Vector2(0, 0))
    patrol.take_damage(1, by_player=True)
    assert patrol.is_hostile_to_player(world.mission_manager)
    patrol.update(500.0, SimpleNamespace(
        mission_manager=world.mission_manager, ship=world.ship))
    assert not patrol.is_hostile_to_player(world.mission_manager)


def test_backup_patrols_leave_when_their_time_is_up(world):
    patrol = PatrolShip(Vector2(0, 0), lifetime=2.0)
    patrol.update(1.0, world)
    assert patrol.alive
    patrol.update(1.5, world)
    assert not patrol.alive


def test_patrol_closes_in_on_its_target(world):
    patrol = PatrolShip(Vector2(0, 0))
    bandit = make_bandit((850, 0))
    start = (bandit.position - patrol.position).length()
    for _ in range(60):
        patrol.update(0.05, world)
    assert (bandit.position - patrol.position).length() < start


# --- Patrol fire --------------------------------------------------------------

def patrol_shot(patrol, target, damage=500):
    patrol.weapon_system.projectiles.append(
        Projectile(target.position, Vector2(0, 0), damage, patrol, WeaponType.LASER))


def test_patrol_fire_kills_a_bandit_without_paying_the_player(world):
    patrol = PatrolShip(Vector2(0, 0))
    bandit = make_bandit((300, 0))
    patrol_shot(patrol, bandit)
    credits = world.ship.credits

    combat_manager._check_patrol_combat(patrol, world.ship, world)

    assert bandit.current_hull <= 0
    assert world.ship.credits == credits
    assert story_state.count_events("bandit_destroyed") == 0


def test_patrol_fire_never_touches_a_bounty_target(world):
    patrol = PatrolShip(Vector2(0, 0))
    target = make_bandit((300, 0), bounty_id="m1")
    patrol_shot(patrol, target)
    combat_manager._check_patrol_combat(patrol, world.ship, world)
    assert target.current_hull == target.max_hull


def test_hostile_patrol_fire_hurts_the_player_but_a_friendly_one_does_not(world):
    patrol = PatrolShip(Vector2(0, 0))
    world.ship.position = Vector2(200, 0)
    patrol_shot(patrol, world.ship, damage=30)
    combat_manager._check_patrol_combat(patrol, world.ship, world)
    assert world.ship.current_hull == 100

    world.mission_manager.faction_standing[FACTION_TRADE_GUILD] = HOSTILE_STANDING
    patrol_shot(patrol, world.ship, damage=30)
    combat_manager._check_patrol_combat(patrol, world.ship, world)
    assert world.ship.current_hull < 100


# --- Bandits versus patrols -------------------------------------------------------

def test_bandit_goes_after_a_nearer_patrol_and_its_fire_can_destroy_it(world):
    bandit = BanditShip(Vector2(-3000, 0), BanditType.FIGHTER)
    player = SimpleNamespace(position=Vector2(-3000 + 700, 0))
    patrol = PatrolShip(Vector2(-3000 + 200, 0))
    combat_manager.add_patrol(patrol)
    assert bandit._select_focus(player) is patrol

    patrol.current_hull = 10
    bandit.weapon_system.projectiles.append(
        Projectile(patrol.position, Vector2(0, 0), 500, bandit, WeaponType.LASER))
    far_ship = Ship(9000, 9000)
    combat_manager._check_bandit_combat(bandit, far_ship, world)
    assert not patrol.alive


# --- The player firing on a patrol ----------------------------------------------------

def test_hitting_a_patrol_costs_standing_and_killing_it_costs_much_more(world):
    patrol = PatrolShip(Vector2(400, 0))
    combat_manager.add_patrol(patrol)
    standing = world.mission_manager.faction_standing

    world.ship.weapon_system.projectiles.append(
        Projectile(patrol.position, Vector2(0, 0), 10, world.ship, WeaponType.LASER))
    combat_manager._check_player_weapon_hits(world.ship.weapon_system, world)
    assert standing[FACTION_TRADE_GUILD] == -5
    assert patrol.provoked_time > 0

    world.ship.weapon_system.projectiles.append(
        Projectile(patrol.position, Vector2(0, 0), 500, world.ship, WeaponType.LASER))
    combat_manager._check_player_weapon_hits(world.ship.weapon_system, world)
    assert not patrol.alive
    assert standing[FACTION_TRADE_GUILD] == -30


# --- Calling for backup -------------------------------------------------------------

def test_backup_needs_captain_rank(world):
    world.mission_manager.reputation = 79
    ok, message = combat_manager.call_backup(world)
    assert not ok and "Captain" in message
    assert combat_manager.active_patrols == []


def test_backup_is_refused_by_a_hostile_guild(world):
    world.mission_manager.reputation = 100
    world.mission_manager.faction_standing[FACTION_TRADE_GUILD] = HOSTILE_STANDING
    ok, message = combat_manager.call_backup(world)
    assert not ok and "will not answer" in message


def test_backup_arrives_stays_a_while_and_then_needs_a_cooldown(world):
    world.mission_manager.reputation = 100
    ok, _ = combat_manager.call_backup(world)
    assert ok
    assert len(combat_manager.active_patrols) == BACKUP_COUNT
    for patrol in combat_manager.active_patrols:
        assert patrol.lifetime == BACKUP_LIFETIME
        assert 300 < (patrol.position - world.ship.position).length() < 600

    ok, message = combat_manager.call_backup(world)           # straight away
    assert not ok and "not ready" in message

    world.play_time += BACKUP_COOLDOWN + 1
    ok, _ = combat_manager.call_backup(world)
    assert ok
    assert len(combat_manager.active_patrols) == 2 * BACKUP_COUNT


# --- Standing recovery and kill rewards ----------------------------------------------

def test_negative_standing_cools_off_one_point_per_interval_and_only_toward_zero(world):
    manager = world.mission_manager
    manager.faction_standing.update({FACTION_TRADE_GUILD: -10, FACTION_INDEPENDENT: 7, FACTION_PIRATE: -1})
    manager._recover_standing(world)                           # first call just sets the baseline
    world.play_time += STANDING_RECOVERY_SECONDS * 3 + 1
    manager._recover_standing(world)

    assert manager.faction_standing[FACTION_TRADE_GUILD] == -7
    assert manager.faction_standing[FACTION_INDEPENDENT] == 7     # positive untouched
    assert manager.faction_standing[FACTION_PIRATE] == 0          # stops at zero, not +2


def test_rewinding_play_time_on_a_load_does_not_grant_recovery(world):
    manager = world.mission_manager
    manager.faction_standing[FACTION_TRADE_GUILD] = -20
    manager._recover_standing(world)
    world.play_time -= 900
    manager._recover_standing(world)
    assert manager.faction_standing[FACTION_TRADE_GUILD] == -20


def find_sector(faction, seed):
    for cx in range(5, 60):
        for cy in range(5, 60):
            if get_controlling_faction(cx, cy, seed) == faction:
                return cx, cy
    raise AssertionError(f"no {faction} sector found")


@pytest.mark.parametrize("faction,expected", [
    (FACTION_TRADE_GUILD, 2), (FACTION_INDEPENDENT, 2), (FACTION_PIRATE, 0)])
def test_clearing_bandits_from_a_factions_space_earns_its_goodwill(world, faction, expected):
    cx, cy = find_sector(faction, world.world_seed)
    bandit = BanditShip(Vector2(cx * 1000 + 500, cy * 1000 + 500), BanditType.SCOUT)
    before = world.mission_manager.faction_standing[faction]
    combat_manager._handle_bandit_destroyed(bandit, world.ship, world)
    assert world.mission_manager.faction_standing[faction] - before == expected


def test_a_bandit_kill_without_an_engine_changes_no_standing(world):
    bandit = BanditShip(Vector2(500, 500), BanditType.SCOUT)
    combat_manager._handle_bandit_destroyed(bandit, world.ship)
    assert all(v == 0 for v in world.mission_manager.faction_standing.values())


# --- World generation ------------------------------------------------------------------

def count_patrols_in(universe, faction, chunks=30):
    seed = universe.world_seed
    found = 0
    cx = 5
    while found < chunks and cx < 150:
        for cy in range(5, 150):
            if get_controlling_faction(cx, cy, seed) == faction:
                before = len(combat_manager.active_patrols)
                universe.generate_chunk_around_position(Vector2(cx * 1000 + 500, cy * 1000 + 500))
                found += 1
                yield len(combat_manager.active_patrols) - before
                if found >= chunks:
                    break
        cx += 1


def test_only_trade_guild_space_is_patrolled(world):
    guild = sum(count_patrols_in(world.universe, FACTION_TRADE_GUILD))
    clear_combat()
    pirate = sum(count_patrols_in(world.universe, FACTION_PIRATE))
    independent = sum(count_patrols_in(world.universe, FACTION_INDEPENDENT))
    assert guild > 0
    assert pirate == 0
    assert independent == 0
