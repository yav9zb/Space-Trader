"""Raids in the running game: raiders are real ships that shoot the base, the
turrets shoot them down, the player is told, and none of it needs the player to
be there."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import random

import pygame
import pytest
from pygame import Vector2

from src.base_building import raids
from src.base_building.base_entity import ModuleType
from src.base_building.base_manager import base_manager
from src.combat.combat_manager import combat_manager


class Clock:
    def get_time(self): return 16
    def tick(self, *a): return 16
    def get_fps(self): return 60.0


@pytest.fixture
def engine(monkeypatch):
    from src.engine.game_engine import GameEngine

    # Weapons fire on the pygame clock, which a test does not wait for: use a simulated one
    sim = [0.0]
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: int(sim[0] * 1000))

    game = GameEngine()
    game.clock = Clock()
    game.create_new_universe(seed=4)
    game.sim_time = sim
    saved = (dict(base_manager.bases), base_manager.active_base_id, base_manager.next_base_id)
    base_manager.reset()
    combat_manager.clear_all()
    base_manager.raids.rng = random.Random(1)
    yield game
    base_manager.reset()
    base_manager.bases.update(saved[0])
    base_manager.active_base_id, base_manager.next_base_id = saved[1], saved[2]
    combat_manager.clear_all()


def build_base(engine, turrets, storage=1):
    """A powered base far from everything, with the player parked in range but out of the way."""
    where = Vector2(engine.ship.position.x + 40000, engine.ship.position.y + 40000)
    base_id = base_manager.found_base(where, engine.universe.stations, type("W", (), {"credits": 10 ** 6})())
    base = base_manager.get_base(base_id)
    base.add_module(ModuleType.POWER_GENERATOR, 3, 0, free=True)
    base.add_module(ModuleType.POWER_GENERATOR, 3, 2, free=True)
    for i in range(storage):
        base.add_module(ModuleType.STORAGE, 4 + i, -3, free=True)
    for i in range(turrets):
        base.add_module(ModuleType.TURRET, -4 + i, 3, free=True)
    for _ in range(300):
        base.update(1.0)
    engine.ship.position = where + Vector2(2500, 0)
    engine.camera.position = Vector2(engine.ship.position)
    return base_id, base


def fight(engine, base, seconds=120.0, dt=1 / 30):
    t = 0.0
    while base.under_attack and t < seconds:
        engine.ship.current_hull = 100
        base.update(dt)
        engine.sim_time[0] += dt
        combat_manager.update(dt, engine)
        t += dt
    return t


def test_turrets_shoot_down_raiders_and_the_base_holds(engine):
    base_id, base = build_base(engine, turrets=2)
    credits, defeated = engine.ship.credits, combat_manager.bandits_defeated
    base_manager.raids.launch(base_id, base, engine.ship.position, combat_manager)
    raiders = list(combat_manager.active_bandits)
    assert raiders
    fight(engine, base)
    assert not base.under_attack
    assert all(r.current_hull <= 0 for r in raiders)
    assert base.wrecked_count() == 0
    assert any("drove off" in text for text, _ in base_manager.pop_events())
    # The base did the shooting, not the player: no bounty, no kill on the player's record
    assert engine.ship.credits == credits and combat_manager.bandits_defeated == defeated


def test_raiders_really_shoot_the_base_when_nothing_stops_them(engine):
    base_id, base = build_base(engine, turrets=0)
    base_manager.raids.launch(base_id, base, engine.ship.position, combat_manager)
    for _ in range(45 * 30):
        engine.ship.current_hull = 100
        base.update(1 / 30)
        engine.sim_time[0] += 1 / 30
        combat_manager.update(1 / 30, engine)
    assert any(m.hull < m.stats.max_hull for m in base.unique_modules())
    assert base.under_attack                       # nobody has driven them off


def test_an_undefended_base_is_wrecked_by_a_raid_and_mends_afterwards(engine):
    base_id, base = build_base(engine, turrets=0)
    base_manager.raids.launch(base_id, base, engine.ship.position, combat_manager)
    fight(engine, base, seconds=raids.WITHDRAW_AFTER + 30)
    assert not base.under_attack and combat_manager.active_bandits == []
    assert base.wrecked_count() >= 1
    assert any("raided" in text for text, _ in base_manager.pop_events())
    for _ in range(300):
        base.update(1.0)
    assert base.wrecked_count() == 0 and all(m.hull == m.stats.max_hull for m in base.unique_modules())


def test_turrets_leave_a_bounty_target_alone(engine):
    base_id, base = build_base(engine, turrets=2)
    from src.entities.bandit import BanditShip, BanditType
    target = BanditShip(base.position + Vector2(400, 0), BanditType.SCOUT)
    target.bounty_id = "mark"
    combat_manager.add_bandit(target)
    for _ in range(120):
        base.update(1 / 30)
        engine.sim_time[0] += 1 / 30
        combat_manager.update(1 / 30, engine)
    assert target.current_hull == target.max_hull          # the contract is the player's to collect
    assert all(t.weapon_system.projectiles == [] for t in base.turrets())


def test_a_raid_while_the_player_is_away_is_settled_in_the_game_loop(engine):
    base_id, base = build_base(engine, turrets=0)
    engine.ship.position = base.position + Vector2(50000, 0)
    base.raid_timer = 0.5
    combat_manager.update(1.0, engine)
    assert combat_manager.active_bandits == []
    assert any("while you were away" in text for text, _ in base_manager.events)


def test_the_game_tells_the_player_about_a_raid(engine):
    from src.states.game_state import GameStates
    from src.ui.notifications import notifications

    build_base(engine, turrets=0)
    engine.change_state(GameStates.PLAYING)
    engine.fade_remaining = 0
    playing = engine.states[GameStates.PLAYING]
    base_manager.events.append(("Raiders are attacking Frontier Base 1!", (255, 130, 110)))
    pushed = []
    original = notifications.push
    notifications.push = lambda text, *a, **k: (pushed.append(text), original(text, *a, **k))[1]
    try:
        playing.update(0.016)
    finally:
        notifications.push = original
    assert any("Raiders are attacking" in text for text in pushed)
    assert base_manager.events == []


def test_raiders_show_on_the_radar_as_hostile_contacts(engine):
    from src.ui.minimap import gather_contacts

    base_id, base = build_base(engine, turrets=0)
    base_manager.raids.launch(base_id, base, engine.ship.position, combat_manager)
    contacts = gather_contacts(engine, view_radius=10 ** 6)
    assert sum(1 for kind, _ in contacts if kind == "hostile") >= len(base_manager.raids.live[base_id].bandits)


def test_a_new_game_clears_a_raid_in_progress(engine):
    base_id, base = build_base(engine, turrets=0)
    base_manager.raids.launch(base_id, base, engine.ship.position, combat_manager)
    engine.create_new_universe(seed=5)
    assert base_manager.raids.live == {}
    assert base_manager.bases == {} and base_manager.events == []
