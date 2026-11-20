"""The service bay: a ship within reach of a base is refuelled and repaired out of the
base's own fuel cells and machinery, and only while a bay works."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest
from pygame import Vector2

from src.base_building import base_entity as be
from src.base_building.base_entity import ModuleType, PlayerBase
from src.base_building.base_manager import BaseManager


class Wallet:
    credits = 10 ** 6


class FakeStats:
    def __init__(self, hull):
        self.hull = hull

    def get_effective_hull_points(self):
        return self.hull


class FakeShip:
    """The parts of the ship the bay touches."""

    def __init__(self, position=(0, 0), fuel=20.0, hull=40.0):
        self.position = Vector2(position)
        self.fuel_capacity = 100.0
        self.current_fuel = fuel
        self.max_hull = 100.0
        self.current_hull = hull

    def get_effective_stats(self):
        return FakeStats(self.max_hull)

    def refuel(self, amount):
        added = min(amount, self.fuel_capacity - self.current_fuel)
        self.current_fuel += added
        return added

    def repair_ship(self, amount=None):
        self.current_hull = self.max_hull if amount is None else min(self.max_hull, self.current_hull + amount)


def powered_base(bays=1, fuel_cells=50, machinery=50):
    base = PlayerBase(0, 0, "Test Base")
    base.add_module(ModuleType.POWER_GENERATOR, 3, 0, free=True)
    for i in range(bays):
        base.add_module(ModuleType.SERVICE_BAY, 3 + i, 3, free=True)
    base.add_module(ModuleType.STORAGE, 4, -3, free=True)
    base.add_module(ModuleType.STORAGE, 5, -3, free=True)
    for _ in range(200):
        base.update(1.0)
    base.add_resource("fuel_cells", fuel_cells)
    base.add_resource("machinery", machinery)
    for _ in range(5):
        base.update(1.0)
    return base


def test_the_service_bay_is_buildable_with_a_cost_and_a_key():
    assert ModuleType.SERVICE_BAY in be.BUILDABLE
    stats = be.BaseModule.MODULE_DEFINITIONS[ModuleType.SERVICE_BAY]
    assert stats.cost_credits > 0 and stats.cost_goods and stats.power_consumption > 0


def test_a_working_bay_refuels_and_repairs_the_ship_from_the_base_goods():
    base = powered_base()
    ship = FakeShip()
    cells, machinery = base.get_resource_amount("fuel_cells"), base.get_resource_amount("machinery")
    for _ in range(10):
        base.serve(ship, 1.0)
    assert ship.current_fuel == pytest.approx(20 + 10 * be.REFUEL_RATE)
    assert ship.current_hull == pytest.approx(40 + 10 * be.HULL_RATE)
    assert base.get_resource_amount("fuel_cells") < cells and base.get_resource_amount("machinery") < machinery


def test_what_it_gives_is_paid_for_in_goods_with_nothing_lost_or_made_up():
    base = powered_base(fuel_cells=3, machinery=0)
    ship = FakeShip(fuel=0.0, hull=100.0)
    for _ in range(100):
        base.serve(ship, 1.0)
    assert ship.current_fuel == pytest.approx(3 * be.FUEL_PER_CELL)       # three cells, no more
    assert base.get_resource_amount("fuel_cells") == 0


def test_a_ship_that_needs_nothing_uses_nothing():
    base = powered_base()
    ship = FakeShip(fuel=100.0, hull=100.0)
    cells = base.get_resource_amount("fuel_cells")
    base.serve(ship, 5.0)
    assert base.get_resource_amount("fuel_cells") == cells and base.service_lack == set()


def test_it_stops_at_full_and_never_overfills():
    base = powered_base()
    ship = FakeShip(fuel=99.0, hull=99.0)
    base.serve(ship, 10.0)
    assert ship.current_fuel == 100.0 and ship.current_hull == 100.0


def test_two_bays_work_twice_as_fast():
    one, two = powered_base(bays=1), powered_base(bays=2)
    a, b = FakeShip(), FakeShip()
    one.serve(a, 1.0)
    two.serve(b, 1.0)
    assert (b.current_fuel - 20) == pytest.approx(2 * (a.current_fuel - 20))


def test_no_bay_or_no_power_means_no_service():
    plain = powered_base(bays=0)
    ship = FakeShip()
    plain.serve(ship, 5.0)
    assert ship.current_fuel == 20.0 and ship.current_hull == 40.0

    dark = PlayerBase(0, 0, "Dark")
    dark.add_module(ModuleType.SERVICE_BAY, 3, 3, free=True)
    dark.add_resource("fuel_cells", 10)
    for _ in range(100):
        dark.update(1.0)
    dark.power_ratio = dark.power_generation / max(1, dark.power_consumption)
    for module in dark.service_bays():
        module.efficiency = 0.2                       # below the least power a bay works on
    dark.serve(ship, 5.0)
    assert ship.current_fuel == 20.0


def test_a_knocked_out_bay_does_not_serve():
    base = powered_base()
    base.service_bays()[0].take_damage(10 ** 6)
    base.update(0.0)
    ship = FakeShip()
    base.serve(ship, 5.0)
    assert ship.current_fuel == 20.0


def test_running_out_of_goods_is_remembered_and_cleared_when_restocked():
    base = powered_base(fuel_cells=0)
    ship = FakeShip()
    base.serve(ship, 1.0)
    assert "fuel_cells" in base.service_lack
    base.add_resource("fuel_cells", 5)
    base.serve(ship, 1.0)
    assert "fuel_cells" not in base.service_lack and ship.current_fuel > 20


def test_the_manager_serves_only_a_ship_within_reach_and_says_when_goods_run_out():
    manager = BaseManager()
    base_id = manager.found_base(Vector2(0, 0), [], Wallet())
    base = manager.get_base(base_id)
    base.add_module(ModuleType.POWER_GENERATOR, 3, 0, free=True)
    base.add_module(ModuleType.SERVICE_BAY, 3, 3, free=True)
    base.stored_resources.clear()
    base.add_resource("fuel_cells", 1)
    for _ in range(200):
        base.update(1.0)

    far = FakeShip(position=(manager.interact_range * 3, 0))
    manager.serve_ship(far, 5.0)
    assert far.current_fuel == 20.0

    near = FakeShip(position=(manager.interact_range * 0.5, 0))
    for _ in range(5):
        manager.serve_ship(near, 1.0)
    assert near.current_fuel > 20
    assert any("no fuel cells" in text for text, _ in manager.events)
    count = sum(1 for text, _ in manager.events if "no fuel cells" in text)
    manager.serve_ship(near, 1.0)
    assert sum(1 for text, _ in manager.events if "no fuel cells" in text) == count      # said once


def test_the_real_ship_is_served_in_the_game_loop(monkeypatch):
    from src.base_building.base_manager import base_manager
    from src.engine.game_engine import GameEngine

    class Clock:
        def get_time(self): return 16
        def tick(self, *a): return 16
        def get_fps(self): return 60.0

    game = GameEngine()
    game.clock = Clock()
    game.create_new_universe(seed=4)
    saved = (dict(base_manager.bases), base_manager.active_base_id, base_manager.next_base_id)
    base_manager.reset()
    try:
        where = Vector2(game.ship.position.x + 40000, game.ship.position.y)
        base_id = base_manager.found_base(where, game.universe.stations, Wallet())
        base = base_manager.get_base(base_id)
        base.add_module(ModuleType.POWER_GENERATOR, 3, 0, free=True)
        base.add_module(ModuleType.SERVICE_BAY, 3, 3, free=True)
        base.add_resource("fuel_cells", 20)
        for _ in range(200):
            base.update(1.0)
        game.ship.position = Vector2(where)
        game.ship.current_fuel = 10.0
        from src.states.game_state import GameStates
        game.change_state(GameStates.PLAYING)
        game.fade_remaining = 0
        playing = game.states[GameStates.PLAYING]
        for _ in range(60):
            game.ship.position = Vector2(where)
            playing.update(1 / 30)
        assert game.ship.current_fuel > 10.0
    finally:
        base_manager.reset()
        base_manager.bases.update(saved[0])
        base_manager.active_base_id, base_manager.next_base_id = saved[1], saved[2]
