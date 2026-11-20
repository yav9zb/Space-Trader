"""Hauling goods between the ship and a base."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

from src.base_building.base_entity import ModuleType, PlayerBase
from src.base_building.transfer import commodity_name, deposit, depositable, withdraw
from src.entities.ship import Ship
from src.trading.commodity import commodity_registry


@pytest.fixture
def pair():
    ship = Ship(0, 0)
    base = PlayerBase(0, 0)
    base.add_module(ModuleType.STORAGE, 4, 0, free=True)
    base.modules[(4, 0)].is_constructed = True
    return ship, base


def test_depositing_moves_goods_from_the_hold_to_the_base(pair):
    ship, base = pair
    ship.cargo_hold.add_cargo("metal_ore", 6)
    assert deposit(ship, base, "metal_ore", 4) == 4
    assert ship.cargo_hold.get_quantity("metal_ore") == 2
    assert base.get_resource_amount("metal_ore") == 4


def test_you_cannot_deposit_more_than_you_carry_or_the_base_can_hold(pair):
    ship, base = pair
    ship.cargo_hold.add_cargo("metal_ore", 2)
    assert deposit(ship, base, "metal_ore", 50) == 2
    base.stored_resources.clear()
    ship.cargo_hold.add_cargo("metal_ore", 8)
    fits = base.free_capacity // commodity_registry.get_commodity("metal_ore").volume
    base.add_resource("metal_ore", fits - 1)
    assert deposit(ship, base, "metal_ore", 8) == 1
    assert ship.cargo_hold.get_quantity("metal_ore") == 7
    assert deposit(ship, base, "metal_ore", 1) == 0


def test_mission_cargo_stays_with_the_ship(pair):
    ship, base = pair
    ship.cargo_hold.add_mission_cargo("electronics", 3, "m1")
    ship.cargo_hold.add_cargo("electronics", 2)
    assert depositable(ship) == {"electronics": 2}
    assert deposit(ship, base, "electronics", 10) == 2
    assert ship.cargo_hold.get_quantity("electronics") == 3
    assert ship.cargo_hold.get_mission_quantity("electronics") == 3


def test_withdrawing_moves_goods_from_the_base_to_the_hold_within_its_capacity(pair):
    ship, base = pair
    base.add_resource("metal_ore", 30)
    volume = commodity_registry.get_commodity("metal_ore").volume
    room = ship.cargo_hold.get_available_capacity() // volume
    assert withdraw(ship, base, "metal_ore", 100) == room < 30
    assert ship.cargo_hold.get_quantity("metal_ore") == room
    assert base.get_resource_amount("metal_ore") == 30 - room
    assert withdraw(ship, base, "metal_ore", 1) == 0              # the hold is full


def test_withdrawing_what_the_base_does_not_have_does_nothing(pair):
    ship, base = pair
    assert withdraw(ship, base, "metal_ore", 3) == 0
    assert withdraw(ship, base, "unobtainium", 3) == 0
    assert deposit(ship, base, "unobtainium", 3) == 0


def test_names(pair):
    assert commodity_name("metal_ore") == "Metal Ore"
    assert commodity_name("???") == "???"
