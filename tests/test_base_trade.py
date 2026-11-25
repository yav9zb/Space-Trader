"""The trade hub: a base with a working hub buys its own goods for credits, at a
share of the standard price that sags as you sell and heals with time."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest
from pygame import Vector2

from src.base_building import trade
from src.base_building import base_entity as be
from src.base_building.base_entity import BUILDABLE, ModuleType, PlayerBase
from src.base_building.base_manager import BaseManager
from src.trading.commodity import commodity_registry


class Wallet:
    def __init__(self, credits=0):
        self.credits = credits


def hub_base(hubs=1, ore=50):
    base = PlayerBase(0, 0, "Test Base")
    base.add_module(ModuleType.POWER_GENERATOR, 3, 0, free=True)
    base.add_module(ModuleType.STORAGE, 4, -3, free=True)
    base.add_module(ModuleType.STORAGE, 5, -3, free=True)
    for i in range(hubs):
        base.add_module(ModuleType.TRADE_HUB, 3 + 2 * i, 3, free=True)
    for _ in range(200):
        base.update(1.0)
    base.add_resource("metal_ore", ore)
    return base


def price_of(commodity_id):
    return commodity_registry.get_commodity(commodity_id).base_price


def test_the_hub_is_buildable_with_a_cost_and_a_key():
    assert ModuleType.TRADE_HUB in BUILDABLE
    stats = be.BaseModule.MODULE_DEFINITIONS[ModuleType.TRADE_HUB]
    assert stats.cost_credits > 0 and stats.cost_goods and stats.power_consumption > 0


def test_a_working_hub_pays_a_share_of_the_standard_price():
    base = hub_base()
    assert trade.is_open(base)
    assert trade.quote(base, "metal_ore") == int(price_of("metal_ore") * trade.HUB_RATE)
    assert trade.quote(base, "metal_ore") < price_of("metal_ore")            # it never beats a station's standard price


def test_selling_takes_goods_out_of_the_base_and_pays_the_wallet():
    base, wallet = hub_base(), Wallet(100)
    sold, paid = trade.sell(base, wallet, "metal_ore", 3)
    assert sold == 3 and base.get_resource_amount("metal_ore") == 47
    assert wallet.credits == 100 + paid and paid > 0


def test_cannot_sell_more_than_the_base_has_and_unknown_goods_fetch_nothing():
    base, wallet = hub_base(ore=4), Wallet()
    assert trade.sell(base, wallet, "metal_ore", 100)[0] == 4
    assert trade.sell(base, wallet, "metal_ore", 5) == (0, 0) and base.get_resource_amount("metal_ore") == 0
    base.stored_resources["mystery"] = 5
    assert trade.quote(base, "mystery") == 0 and trade.sell(base, wallet, "mystery", 5) == (0, 0)
    assert base.get_resource_amount("mystery") == 5


def test_selling_pushes_the_price_down_within_one_sale_and_never_below_the_floor():
    base, wallet = hub_base(ore=110), Wallet()
    start = trade.quote(base, "metal_ore")
    sold, paid = trade.sell(base, wallet, "metal_ore", 110)
    assert paid < sold * start                                               # later units fetched less
    assert trade.quote(base, "metal_ore") == max(1, int(price_of("metal_ore") * trade.HUB_RATE * (1 - trade.MAX_DROP)))


def test_the_price_heals_with_time():
    base, wallet = hub_base(), Wallet()
    trade.sell(base, wallet, "metal_ore", 30)
    low = trade.quote(base, "metal_ore")
    for _ in range(100):
        base.update(1.0)
    assert trade.quote(base, "metal_ore") > low
    for _ in range(2000):
        base.update(1.0)
    assert trade.quote(base, "metal_ore") == int(price_of("metal_ore") * trade.HUB_RATE)
    assert base.hub_saturation == {}


def test_each_good_has_its_own_price_drop():
    base, wallet = hub_base(), Wallet()
    base.add_resource("electronics", 5)
    trade.sell(base, wallet, "metal_ore", 20)
    assert trade.quote(base, "electronics") == int(price_of("electronics") * trade.HUB_RATE)


def test_no_hub_a_hub_still_building_or_one_knocked_out_buys_nothing():
    plain, wallet = hub_base(hubs=0), Wallet()
    assert not trade.is_open(plain) and trade.quote(plain, "metal_ore") == 0
    assert trade.sell(plain, wallet, "metal_ore", 5) == (0, 0) and wallet.credits == 0

    building = PlayerBase(0, 0, "B")
    building.add_module(ModuleType.TRADE_HUB, 3, 3)
    building.add_resource("metal_ore", 5)
    building.update(1.0)
    assert not trade.is_open(building)

    hit = hub_base()
    hit.working_hubs()[0].take_damage(10 ** 6)
    hit.update(0.0)
    assert not trade.is_open(hit) and trade.sell(hit, wallet, "metal_ore", 5) == (0, 0)


def test_two_hubs_do_not_pay_more_than_one():
    one, two = hub_base(hubs=1), hub_base(hubs=2)
    assert trade.quote(one, "metal_ore") == trade.quote(two, "metal_ore")


def test_the_price_drop_is_saved_and_old_saves_load_without_it():
    manager = BaseManager()
    base_id = manager.found_base(Vector2(0, 0), [], Wallet(10 ** 6))
    base = manager.get_base(base_id)
    base.hub_saturation["metal_ore"] = 0.25
    data = manager.save_bases()
    other = BaseManager()
    assert other.load_bases(data)
    assert other.get_base(base_id).hub_saturation == {"metal_ore": 0.25}
    del data["bases"][base_id]["hub_saturation"]
    assert other.load_bases(data) and other.get_base(base_id).hub_saturation == {}


# --- the screen ---------------------------------------------------------------------------------------------------------

from tests.test_base_screen import engine, open_screen, with_base, key, click, record_text      # noqa: E402,F401


def hub_screen(engine, ore=10):
    base_id, base = with_base(engine)
    base.stored_resources.clear()
    base.add_module(ModuleType.POWER_GENERATOR, 3, -2, free=True)
    base.add_module(ModuleType.TRADE_HUB, 3, 2, free=True)
    base.add_resource("metal_ore", ore)
    for _ in range(200):
        base.update(1.0)
    return base


def test_the_trade_tab_sells_with_the_keys(engine):
    base = hub_screen(engine)
    state = open_screen(engine)
    engine.ship.credits = 0
    state.handle_input(key(pygame.K_t))
    assert state.selected_tab == "trade"
    engine.render()
    price = trade.quote(base, "metal_ore")
    state.handle_input(key(pygame.K_RETURN))
    assert base.get_resource_amount("metal_ore") == 9 and engine.ship.credits == price
    state.handle_input(key(pygame.K_RIGHT, mod=pygame.KMOD_SHIFT))
    assert base.get_resource_amount("metal_ore") == 0 and "Sold" in state.status


def test_the_trade_tab_sells_with_the_buttons(engine):
    base = hub_screen(engine)
    state = open_screen(engine)
    engine.ship.credits = 0
    state.selected_tab = "trade"
    engine.render()
    pygame.event.clear()
    pygame.event.post(click(state.trade_buttons.rects[1].center))
    engine.handle_events()
    assert base.get_resource_amount("metal_ore") == 0 and engine.ship.credits > 0


def test_the_trade_tab_explains_a_base_without_a_hub(engine, monkeypatch):
    base_id, base = with_base(engine)
    base.stored_resources.clear()
    base.add_resource("metal_ore", 5)
    drawn = record_text(monkeypatch)
    state = open_screen(engine)
    state.selected_tab = "trade"
    engine.render()
    assert any("no Trade Hub" in text for text, _ in drawn)
    state.handle_input(key(pygame.K_RETURN))
    assert base.get_resource_amount("metal_ore") == 5


def test_the_trade_tab_lists_what_the_hub_pays(engine, monkeypatch):
    hub_screen(engine)
    drawn = record_text(monkeypatch)
    state = open_screen(engine)
    state.selected_tab = "trade"
    engine.render()
    text = " ".join(t for t, _ in drawn)
    assert "Metal Ore" in text and f"{int(price_of('metal_ore') * trade.HUB_RATE)}" in text
