"""The player's base: the model (modules, power, storage, production), the manager
(founding rules, saving), and the economy they sit in. A base is paid for with
the ship's credits and with goods taken from the base's own storage."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest
from pygame import Vector2

from src.base_building import base_entity as be
from src.base_building.base_entity import BUILDABLE, BaseModule, ModuleType, PlayerBase
from src.base_building.base_manager import BaseManager
from src.trading.commodity import commodity_registry


class Wallet:
    def __init__(self, credits=0):
        self.credits = credits


def built(base, steps=400, dt=1.0):
    for _ in range(steps):
        base.update(dt)


def stocked(base, **goods):
    for name, amount in goods.items():
        assert base.add_resource(name, amount) == amount


@pytest.fixture
def base():
    b = PlayerBase(0, 0, "Test")
    # Plenty of room, so tests about goods are not about capacity
    b.add_module(ModuleType.STORAGE, 3, 0, wallet=Wallet(), free=True)
    b.add_module(ModuleType.STORAGE, 4, 0, wallet=Wallet(), free=True)
    built(b, 60)
    return b


# --- the catalogue -----------------------------------------------------------------------------

def test_every_buildable_module_is_priced_in_real_commodities_and_credits():
    assert BUILDABLE and ModuleType.COMMAND_CENTER not in BUILDABLE
    for module_type in BUILDABLE:
        stats = BaseModule.MODULE_DEFINITIONS[module_type]
        assert stats.cost_credits > 0 and stats.build_time > 0
        for commodity_id, amount in stats.cost_goods.items():
            assert commodity_registry.get_commodity(commodity_id) and amount > 0
        if stats.recipe:
            for commodity_id in list(stats.recipe.inputs) + list(stats.recipe.outputs):
                assert commodity_registry.get_commodity(commodity_id)


def test_the_costs_fit_the_economy_the_player_is_in():
    # A ship starts with 1000 credits and a 20 unit hold: nothing may cost the earth
    for module_type in BUILDABLE:
        stats = BaseModule.MODULE_DEFINITIONS[module_type]
        assert stats.cost_credits <= 8000
        hold_volume = sum(commodity_registry.get_commodity(c).volume * n for c, n in stats.cost_goods.items())
        assert hold_volume <= 60          # a few trips at most


# --- a new base --------------------------------------------------------------------------------

def test_a_new_base_has_a_working_command_center():
    b = PlayerBase(100, 100, "Fresh")
    modules = set(b.modules.values())
    assert [m.module_type for m in modules] == [ModuleType.COMMAND_CENTER]
    core = modules.pop()
    assert core.is_constructed
    b.update(1.0)
    assert b.power_generation >= b.power_consumption > 0      # it runs on its own reactor
    assert b.storage_capacity > 0


def test_the_command_center_cannot_be_removed_or_built_again():
    b = PlayerBase(0, 0)
    assert b.remove_module(0, 0) is False
    assert b.add_module(ModuleType.COMMAND_CENTER, 4, 4, wallet=Wallet(10 ** 6)) is False


# --- paying for a module ---------------------------------------------------------------------------

def test_a_module_costs_credits_from_the_wallet_and_goods_from_storage(base):
    cost = BaseModule.MODULE_DEFINITIONS[ModuleType.POWER_GENERATOR]
    stocked(base, **cost.cost_goods)
    wallet = Wallet(cost.cost_credits + 123)
    assert base.add_module(ModuleType.POWER_GENERATOR, 1, 2, wallet=wallet)
    assert wallet.credits == 123
    for commodity_id in cost.cost_goods:
        assert base.get_resource_amount(commodity_id) == 0


def test_a_module_you_cannot_afford_is_refused_and_takes_nothing(base):
    cost = BaseModule.MODULE_DEFINITIONS[ModuleType.POWER_GENERATOR]
    stocked(base, **cost.cost_goods)
    poor = Wallet(cost.cost_credits - 1)
    assert not base.add_module(ModuleType.POWER_GENERATOR, 1, 2, wallet=poor)
    assert poor.credits == cost.cost_credits - 1
    assert all(base.get_resource_amount(c) == n for c, n in cost.cost_goods.items())

    base.stored_resources.clear()
    rich = Wallet(10 ** 6)
    assert not base.add_module(ModuleType.POWER_GENERATOR, 1, 2, wallet=rich)
    assert rich.credits == 10 ** 6


def test_what_is_missing_is_listed_for_the_screen(base):
    cost = BaseModule.MODULE_DEFINITIONS[ModuleType.POWER_GENERATOR]
    missing = base.shortfall(ModuleType.POWER_GENERATOR, credits=0)
    assert "credits" in missing and set(cost.cost_goods) <= set(missing)
    stocked(base, **cost.cost_goods)
    assert base.shortfall(ModuleType.POWER_GENERATOR, credits=cost.cost_credits) == {}


def test_placement_must_be_on_free_grid_cells(base):
    wallet = Wallet(10 ** 6)
    stocked(base, fuel_cells=20)
    assert not base.add_module(ModuleType.POWER_GENERATOR, 0, 0, wallet=wallet)      # on the command center
    assert not base.add_module(ModuleType.POWER_GENERATOR, 99, 0, wallet=wallet)     # off the grid
    assert base.add_module(ModuleType.POWER_GENERATOR, 1, 2, wallet=wallet)
    assert not base.add_module(ModuleType.POWER_GENERATOR, 1, 2, wallet=wallet)      # taken


def test_removing_a_module_refunds_half(base):
    cost = BaseModule.MODULE_DEFINITIONS[ModuleType.POWER_GENERATOR]
    stocked(base, **cost.cost_goods)
    wallet = Wallet(cost.cost_credits)
    base.add_module(ModuleType.POWER_GENERATOR, 1, 2, wallet=wallet)
    assert base.remove_module(1, 2, wallet=wallet)
    assert wallet.credits == cost.cost_credits // 2
    assert (1, 2) not in base.modules
    for commodity_id, amount in cost.cost_goods.items():
        assert base.get_resource_amount(commodity_id) == amount // 2


# --- construction, power and storage ----------------------------------------------------------------------

def test_a_module_takes_its_build_time_and_only_then_works(base):
    stocked(base, fuel_cells=20)
    base.add_module(ModuleType.POWER_GENERATOR, 1, 2, wallet=Wallet(10 ** 6))
    module = base.modules[(1, 2)]
    base.update(1.0)
    assert not module.is_constructed and 0 < module.construction_progress < 1
    assert base.power_generation == be.CORE_POWER
    built(base, int(module.stats.build_time) + 2)
    assert module.is_constructed
    assert base.power_generation == be.CORE_POWER + module.stats.power_generation


def test_storage_modules_raise_capacity_and_goods_are_limited_by_volume(base):
    capacity = base.storage_capacity
    assert capacity >= 2 * BaseModule.MODULE_DEFINITIONS[ModuleType.STORAGE].storage_capacity
    ore = commodity_registry.get_commodity("metal_ore")
    fits = capacity // ore.volume
    assert base.add_resource("metal_ore", fits + 50) == fits
    assert base.used_capacity == fits * ore.volume
    assert base.add_resource("metal_ore", 1) == 0
    assert base.remove_resource("metal_ore", 10) == 10
    assert base.add_resource("metal_ore", 100) == 10


def test_unknown_goods_are_not_accepted(base):
    assert base.add_resource("unobtainium", 5) == 0


def test_too_little_power_slows_everything_down_in_proportion():
    b = PlayerBase(0, 0)
    stocked_core = b
    b.add_resource("fuel_cells", 0)
    m = BaseModule(ModuleType.MINING_FACILITY, 3, 3)
    m.is_constructed = True
    b.modules[(3, 3)] = m
    b.update(1.0)
    assert 0 < b.power_ratio < 1
    assert m.efficiency == pytest.approx(b.power_ratio)


# --- production -----------------------------------------------------------------------------------------------

def powered_base_with(*module_types, base=None):
    b = base or PlayerBase(0, 0)
    spots = iter([(3, -2), (3, 0), (3, 2), (-5, -2), (-5, 0), (-5, 2), (0, 3), (0, -4)])
    for module_type in module_types:
        gx, gy = next(spots)
        stats = BaseModule.MODULE_DEFINITIONS[module_type]
        module = BaseModule(module_type, gx, gy)
        module.is_constructed = True
        for x in range(gx, gx + stats.size):
            for y in range(gy, gy + stats.size):
                b.modules[(x, y)] = module
    b.add_module(ModuleType.STORAGE, 0, 6, wallet=Wallet(), free=True)
    b.modules[(0, 6)].is_constructed = True
    return b


def test_a_mining_facility_produces_ore_from_nothing():
    b = powered_base_with(ModuleType.POWER_GENERATOR, ModuleType.MINING_FACILITY)
    recipe = BaseModule.MODULE_DEFINITIONS[ModuleType.MINING_FACILITY].recipe
    assert recipe.inputs == {}
    built(b, 200)
    expected = int(200 / recipe.seconds) * recipe.outputs["metal_ore"]
    assert abs(b.get_resource_amount("metal_ore") - expected) <= 1


def test_a_refinery_turns_ore_into_electronics_and_stops_when_it_runs_out():
    b = powered_base_with(ModuleType.POWER_GENERATOR, ModuleType.REFINERY)
    recipe = BaseModule.MODULE_DEFINITIONS[ModuleType.REFINERY].recipe
    stocked(b, metal_ore=2 * recipe.inputs["metal_ore"])
    built(b, 400)
    assert b.get_resource_amount("metal_ore") == 0
    assert b.get_resource_amount("electronics") == 2 * recipe.outputs["electronics"]


def test_a_factory_needs_every_input_and_makes_machinery():
    b = powered_base_with(ModuleType.POWER_GENERATOR, ModuleType.POWER_GENERATOR, ModuleType.FACTORY)
    recipe = BaseModule.MODULE_DEFINITIONS[ModuleType.FACTORY].recipe
    stocked(b, electronics=recipe.inputs["electronics"])           # no ore yet
    built(b, 200)
    assert b.get_resource_amount("machinery") == 0
    stocked(b, metal_ore=recipe.inputs["metal_ore"])
    built(b, 200)
    assert b.get_resource_amount("machinery") == recipe.outputs["machinery"]


def test_production_waits_when_storage_is_full_and_resumes_when_there_is_room():
    b = powered_base_with(ModuleType.POWER_GENERATOR, ModuleType.MINING_FACILITY)
    built(b, 5)
    ore = commodity_registry.get_commodity("metal_ore")
    b.stored_resources.clear()
    b.add_resource("metal_ore", b.storage_capacity // ore.volume)
    full = b.get_resource_amount("metal_ore")
    built(b, 300)
    assert b.get_resource_amount("metal_ore") == full
    report = b.production_report()
    assert any("full" in line["state"].lower() for line in report)
    b.remove_resource("metal_ore", 10)
    built(b, 300)
    assert b.get_resource_amount("metal_ore") > full - 10


def test_a_long_time_step_does_not_lose_cycles():
    a = powered_base_with(ModuleType.POWER_GENERATOR, ModuleType.MINING_FACILITY)
    c = powered_base_with(ModuleType.POWER_GENERATOR, ModuleType.MINING_FACILITY)
    built(a, 600, 1.0)
    built(c, 6, 100.0)
    assert abs(a.get_resource_amount("metal_ore") - c.get_resource_amount("metal_ore")) <= 2


def test_the_production_report_says_what_each_module_is_doing():
    b = powered_base_with(ModuleType.POWER_GENERATOR, ModuleType.REFINERY)
    b.update(1.0)
    lines = b.production_report()
    assert len(lines) == 1 and lines[0]["label"]
    assert "needs" in lines[0]["state"].lower()
    stocked(b, metal_ore=10)
    built(b, 3)
    assert "%" in b.production_report()[0]["state"]


# --- the manager ----------------------------------------------------------------------------------------------

class StationAt:
    def __init__(self, x, y):
        self.position = Vector2(x, y)


@pytest.fixture
def manager():
    return BaseManager()


def test_founding_has_rules_and_says_why_it_cannot(manager):
    stations = [StationAt(0, 0)]
    ok, reasons = manager.can_found(Vector2(5000, 5000), stations, credits=10 ** 6)
    assert ok and reasons == []

    ok, reasons = manager.can_found(Vector2(5000, 5000), stations, credits=10)
    assert not ok and any("credits" in r.lower() for r in reasons)

    ok, reasons = manager.can_found(Vector2(100, 0), stations, credits=10 ** 6)
    assert not ok and any("station" in r.lower() for r in reasons)


def test_founding_charges_the_wallet_places_the_base_and_gives_a_starter_kit(manager):
    wallet = Wallet(manager.founding_cost + 500)
    base_id = manager.found_base(Vector2(5000, 5000), [], wallet)
    assert base_id and wallet.credits == 500
    base = manager.get_base(base_id)
    assert base.position == Vector2(5000, 5000)
    assert manager.active_base_id == base_id
    # enough to build the first generator and storage without a supply run
    for module_type in (ModuleType.POWER_GENERATOR, ModuleType.STORAGE):
        assert not (set(base.shortfall(module_type, credits=10 ** 6)) - {"credits"})


def test_bases_keep_their_distance_and_there_is_a_limit(manager):
    wallet = Wallet(10 ** 7)
    first = manager.found_base(Vector2(5000, 5000), [], wallet)
    credits = wallet.credits
    assert manager.found_base(Vector2(5000 + manager.min_base_distance - 10, 5000), [], wallet) is None
    assert wallet.credits == credits                        # a refusal costs nothing
    for index in range(1, manager.max_bases):
        assert manager.found_base(Vector2(5000 + index * 5000, 5000), [], wallet)
    assert len(manager.bases) == manager.max_bases
    ok, reasons = manager.can_found(Vector2(90000, 90000), [], 10 ** 7)
    assert not ok and any("limit" in r.lower() or "most" in r.lower() for r in reasons)
    assert first in manager.bases


def test_the_nearest_base_in_range(manager):
    wallet = Wallet(10 ** 7)
    near = manager.found_base(Vector2(5000, 5000), [], wallet)
    manager.found_base(Vector2(9000, 5000), [], wallet)
    assert manager.base_in_range(Vector2(5000 + manager.interact_range - 1, 5000))[0] == near
    assert manager.base_in_range(Vector2(5000 + manager.interact_range + 50, 5000)) is None


def test_bases_keep_working_wherever_the_player_is(manager):
    wallet = Wallet(10 ** 7)
    base_id = manager.found_base(Vector2(5000, 5000), [], wallet)
    base = manager.get_base(base_id)
    base.add_module(ModuleType.POWER_GENERATOR, 1, 2, wallet=wallet)
    for _ in range(200):
        manager.update(1.0, Vector2(10 ** 6, 10 ** 6))      # far away
    assert base.modules[(1, 2)].is_constructed


def test_saving_and_loading_keeps_everything(manager):
    wallet = Wallet(10 ** 7)
    base_id = manager.found_base(Vector2(5000, 5000), [], wallet, name="Home")
    base = manager.get_base(base_id)
    base.add_module(ModuleType.POWER_GENERATOR, 1, 2, wallet=wallet)
    base.add_module(ModuleType.STORAGE, 3, 0, wallet=wallet)
    for _ in range(30):
        base.update(1.0)                                    # generator half built
    base.add_resource("metal_ore", 4)
    data = manager.save_bases()

    other = BaseManager()
    assert other.load_bases(data)
    loaded = other.get_base(base_id)
    assert loaded.name == "Home" and loaded.position == Vector2(5000, 5000)
    assert other.active_base_id == base_id
    assert loaded.get_resource_amount("metal_ore") == base.get_resource_amount("metal_ore")
    assert set(m.module_type for m in loaded.modules.values()) == set(m.module_type for m in base.modules.values())
    generator = loaded.modules[(1, 2)]
    assert 0 < generator.construction_progress < 1
    built(loaded, 200)
    assert generator.is_constructed
    # and it can be saved again
    assert other.save_bases()["bases"]


def test_a_mid_cycle_factory_survives_a_save():
    b = powered_base_with(ModuleType.POWER_GENERATOR, ModuleType.POWER_GENERATOR, ModuleType.MINING_FACILITY)
    built(b, 7)                                             # part way through a cycle
    manager = BaseManager()
    manager.bases["base_1"] = b
    other = BaseManager()
    assert other.load_bases(manager.save_bases())
    loaded = other.bases["base_1"]
    mining = next(m for m in set(loaded.modules.values()) if m.module_type == ModuleType.MINING_FACILITY)
    original = next(m for m in set(b.modules.values()) if m.module_type == ModuleType.MINING_FACILITY)
    assert mining.cycle_progress == pytest.approx(original.cycle_progress)


def test_loading_garbage_fails_cleanly_and_reset_empties_the_manager(manager):
    assert manager.load_bases({"bases": {"base_1": {"nope": 1}}}) is False
    manager.found_base(Vector2(5000, 5000), [], Wallet(10 ** 7))
    manager.reset()
    assert manager.bases == {} and manager.active_base_id is None


# --- balance ------------------------------------------------------------------------------------------------------

def _worth(goods):
    return sum(commodity_registry.get_commodity(c).base_price * n for c, n in goods.items())


@pytest.mark.parametrize("module_type", [m for m in BUILDABLE if BaseModule.MODULE_DEFINITIONS[m].recipe])
def test_every_recipe_makes_goods_worth_more_than_it_uses(module_type):
    recipe = BaseModule.MODULE_DEFINITIONS[module_type].recipe
    assert _worth(recipe.outputs) >= _worth(recipe.inputs)


def test_a_mining_facility_earns_its_cost_back_in_a_reasonable_time():
    stats = BaseModule.MODULE_DEFINITIONS[ModuleType.MINING_FACILITY]
    per_minute = _worth(stats.recipe.outputs) * 60 / stats.recipe.seconds
    goods_cost = _worth(stats.cost_goods)
    minutes = (stats.cost_credits + goods_cost) / per_minute
    assert 10 <= minutes <= 40, minutes
