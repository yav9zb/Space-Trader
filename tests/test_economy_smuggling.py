import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import random
from types import SimpleNamespace

import pytest
from pygame import Vector2

from src import smuggling
from src.docking.docking_manager import DockingManager
from src.economy_events import (
    economy_events, EconomyEvent, EconomyEvents, region_of, EVENT_DURATION,
    FIRST_EVENT_DELAY, MAX_ACTIVE, BLACK_MARKET_PREMIUM,
)
from src.entities.ship import Ship
from src.entities.station import StationType
from src.factions import (
    get_controlling_faction, get_station_faction,
    FACTION_TRADE_GUILD, FACTION_INDEPENDENT, FACTION_PIRATE,
)
from src.missions.mission_manager import MissionManager
from src.missions.mission_types import Mission, MissionStatus, MissionType
from src.missions.specific_missions import DeliveryMission, SmugglingRunMission
from src.story.story_state import story_state
from src.trading.commodity import commodity_registry
from src.ui.notifications import notifications
from src.universe import Universe, MARKET_REFRESH_SECONDS


def find_sector(faction, seed, start=5):
    for cx in range(start, 80):
        for cy in range(start, 80):
            if get_controlling_faction(cx, cy, seed) == faction:
                return cx, cy
    raise AssertionError(f"no {faction} sector")


@pytest.fixture
def world():
    story_state.reset()
    notifications.clear()
    universe = Universe(seed=1212)
    universe.generate_universe()
    economy_events.reset()
    economy_events.world_seed = universe.world_seed
    engine = SimpleNamespace(
        universe=universe, world_seed=universe.world_seed, ship=Ship(0, 0),
        mission_manager=MissionManager(), story_state=story_state, play_time=0.0,
    )
    yield engine
    economy_events.reset()
    economy_events.world_seed = None
    story_state.reset()
    notifications.clear()


def station_in(world, faction, station_type=StationType.TRADING, start=5):
    cx, cy = find_sector(faction, world.world_seed, start)
    return world.universe.ensure_station_in_sector(cx, cy, station_type)


# --- Contraband and inspections -----------------------------------------------------

def test_only_military_goods_are_contraband():
    assert smuggling.is_contraband("missiles") and smuggling.is_contraband("laser_cells")
    assert not smuggling.is_contraband("food_rations")
    assert not smuggling.is_contraband("no_such_thing")


def test_inspection_chance_falls_with_guild_standing():
    assert smuggling.inspection_chance(0) == smuggling.INSPECTION_CHANCE
    assert smuggling.inspection_chance(smuggling.FAVORED_STANDING) == smuggling.FAVORED_CHANCE
    assert smuggling.inspection_chance(smuggling.TRUSTED_STANDING) == 0.0
    assert smuggling.inspection_chance(-80) == smuggling.INSPECTION_CHANCE


class Roll:
    def __init__(self, value):
        self.value = value

    def random(self):
        return self.value


def load_ship(world, **cargo):
    for cid, qty in cargo.items():
        assert world.ship.cargo_hold.add_cargo(cid, qty)


def test_guild_inspection_seizes_contraband_fines_and_costs_standing(world):
    guild = station_in(world, FACTION_TRADE_GUILD)
    load_ship(world, missiles=4, food_rations=3)
    world.ship.credits = 1000

    result = smuggling.inspect(world.ship, guild, world, Roll(0.0))

    assert result.seized == {"missiles": 4}
    assert result.fine == int(commodity_registry.get_commodity("missiles").base_price * 4 * smuggling.FINE_RATE)
    assert world.ship.credits == 1000 - result.fine
    assert world.ship.cargo_hold.get_quantity("missiles") == 0
    assert world.ship.cargo_hold.get_quantity("food_rations") == 3       # legal cargo untouched
    assert world.mission_manager.faction_standing[FACTION_TRADE_GUILD] == -smuggling.STANDING_PENALTY
    assert story_state.count_events("contraband_seized") == 1


def test_the_fine_never_exceeds_what_the_player_has(world):
    guild = station_in(world, FACTION_TRADE_GUILD)
    load_ship(world, missiles=10)
    world.ship.credits = 20
    result = smuggling.inspect(world.ship, guild, world, Roll(0.0))
    assert result.fine == 20 and world.ship.credits == 0


def test_slipping_through_keeps_the_cargo(world):
    guild = station_in(world, FACTION_TRADE_GUILD)
    load_ship(world, missiles=4)
    assert smuggling.inspect(world.ship, guild, world, Roll(0.99)) is None
    assert world.ship.cargo_hold.get_quantity("missiles") == 4


def test_a_trusted_player_is_never_inspected(world):
    guild = station_in(world, FACTION_TRADE_GUILD)
    load_ship(world, missiles=4)
    world.mission_manager.faction_standing[FACTION_TRADE_GUILD] = smuggling.TRUSTED_STANDING
    assert smuggling.inspect(world.ship, guild, world, Roll(0.0)) is None


def test_only_guild_stations_inspect_and_only_when_carrying_contraband(world):
    independent = station_in(world, FACTION_INDEPENDENT, start=3)
    guild = station_in(world, FACTION_TRADE_GUILD)
    load_ship(world, missiles=4)
    assert smuggling.inspect(world.ship, independent, world, Roll(0.0)) is None
    world.ship.cargo_hold.remove_cargo("missiles", 4)
    assert smuggling.inspect(world.ship, guild, world, Roll(0.0)) is None


def test_seized_mission_cargo_fails_the_mission(world):
    guild = station_in(world, FACTION_TRADE_GUILD)
    mission = SmugglingRunMission("Alpha", guild.name, "missiles", 5)
    mission.status = MissionStatus.IN_PROGRESS
    mission.pickup_completed = True
    world.mission_manager.active_missions.append(mission)
    assert world.ship.cargo_hold.add_mission_cargo("missiles", 5, mission.id)

    result = smuggling.inspect(world.ship, guild, world, Roll(0.0))

    assert result.failed_mission_ids == [mission.id]
    assert mission.status == MissionStatus.FAILED
    assert world.ship.cargo_hold.mission_items == {}
    assert world.ship.cargo_hold.get_quantity("missiles") == 0


def test_docking_runs_the_inspection_hook(world, monkeypatch):
    import src.ui.onboarding_hints as hints
    monkeypatch.setattr(hints.onboarding_hints, "trigger", lambda *_: None)
    from src.audio.sound_manager import sound_manager
    monkeypatch.setattr(sound_manager, "play", lambda *_: None)

    station = SimpleNamespace(name="Yard-1", size=40, position=Vector2(0, 0))
    manager = DockingManager()
    seen = []
    manager.inspection_hook = seen.append
    manager.target_station = station
    manager._complete_docking(Ship(0, 0))
    assert seen == [station]


# --- Smuggling run missions ---------------------------------------------------------------

def test_smuggling_run_is_a_contraband_delivery_that_pays_more():
    run = SmugglingRunMission("A", "B", "missiles", 6)
    plain = DeliveryMission("A", "B", "missiles", 6)
    assert run.mission_type == MissionType.SMUGGLING
    assert run.reward.credits == int(plain.reward.credits * 2.2)
    assert run.requirements.min_reputation >= 10
    assert "Guild" in run.description


def test_smuggling_run_survives_a_save_and_still_delivers(world):
    run = SmugglingRunMission("Alpha", "Beta", "missiles", 5)
    ship = Ship(0, 0)
    ship.cargo_hold.capacity = 50
    assert run.accept(ship, 50)
    run.update_progress(ship, SimpleNamespace(name="Alpha"))
    assert run.pickup_completed

    restored = Mission.from_dict(json.loads(json.dumps(run.to_dict())))
    assert isinstance(restored, SmugglingRunMission)
    assert restored.update_progress(ship, SimpleNamespace(name="Beta")) is True


def test_smuggling_runs_are_generated_and_prefer_pirate_destinations(world):
    manager = MissionManager()
    manager._world_seed = world.world_seed
    origin = world.universe.ensure_station_in_sector(30, 30, StationType.MINING)
    pirate = station_in(world, FACTION_PIRATE, StationType.MINING)
    stations = world.universe.stations

    made = []
    for seed in range(120):
        random.seed(seed)
        mission = manager.generate_station_specific_mission(origin, stations)
        if mission and mission.mission_type == MissionType.SMUGGLING:
            made.append(mission)
    random.seed()

    assert made
    assert all(smuggling.is_contraband(m.commodity_id) for m in made)
    destinations = {s.name: s for s in stations}
    assert all(get_station_faction(destinations[m.destination_station_id], world.world_seed) == FACTION_PIRATE
               for m in made)


# --- Economy events: effects on markets -----------------------------------------------------

def make_event(region, **kwargs):
    base = dict(kind="shortage", region=region, commodity_id="food_rations", multiplier=1.7,
                embargo=False, ends_at=1e9, headline="h")
    base.update(kwargs)
    return EconomyEvent(**base)


def test_event_scopes_by_region_and_commodity(world):
    station = world.universe.ensure_station_in_sector(30, 30, StationType.TRADING)
    here = region_of(station.position)
    elsewhere = (here[0] + 5, here[1])

    economy_events.events = [make_event(here)]
    assert economy_events.effect_for(station, "food_rations")[0] == 1.7
    assert economy_events.effect_for(station, "metal_ore")[0] == 1.0

    economy_events.events = [make_event(elsewhere)]
    assert economy_events.effect_for(station, "food_rations")[0] == 1.0


def test_raid_hits_every_commodity_and_effects_stack(world):
    station = world.universe.ensure_station_in_sector(30, 30, StationType.TRADING)
    here = region_of(station.position)
    economy_events.events = [make_event(here, kind="raid", commodity_id=None, multiplier=1.3),
                             make_event(here, multiplier=1.7)]
    assert economy_events.effect_for(station, "metal_ore")[0] == pytest.approx(1.3)
    assert economy_events.effect_for(station, "food_rations")[0] == pytest.approx(1.3 * 1.7)


def test_markets_apply_event_prices_and_embargoes(world):
    station = world.universe.ensure_station_in_sector(30, 30, StationType.TRADING)
    here = region_of(station.position)
    market = station.market
    assert market.station is station

    base_buy = market.get_buy_price("food_rations")
    base_sell = market.get_sell_price("food_rations")
    economy_events.events = [make_event(here, multiplier=2.0)]
    assert market.get_buy_price("food_rations") == base_buy * 2
    assert market.get_sell_price("food_rations") == base_sell * 2

    economy_events.events = [make_event(here, multiplier=1.0, embargo=True, kind="embargo")]
    assert not market.can_buy_from_station("food_rations")
    assert not market.can_sell_to_station("food_rations")
    assert "food_rations" not in [c.id for c in market.get_available_commodities()]
    assert market.can_buy_from_station("metal_ore")


def test_pirate_markets_pay_a_premium_for_contraband_only(world):
    pirate = station_in(world, FACTION_PIRATE)
    independent = station_in(world, FACTION_INDEPENDENT, start=3)
    assert economy_events.effect_for(pirate, "missiles")[0] == BLACK_MARKET_PREMIUM
    assert economy_events.effect_for(pirate, "food_rations")[0] == 1.0
    assert economy_events.effect_for(independent, "missiles")[0] == 1.0


def test_loaded_stations_still_know_their_region(world):
    from src.save_system import SaveSystem
    universe = world.universe
    universe.ensure_station_in_sector(30, 30, StationType.TRADING)
    save_system = SaveSystem.__new__(SaveSystem)
    data = json.loads(json.dumps(save_system._save_universe_data(world)))
    save_system._load_universe_data(data, world)
    assert all(s.market.station is s for s in world.universe.stations)


def test_markets_recover_stock_over_time(world):
    station = world.universe.ensure_station_in_sector(30, 30, StationType.TRADING)
    station.market.prices["food_rations"].stock = 10
    world.universe.update(MARKET_REFRESH_SECONDS / 2)
    assert station.market.prices["food_rations"].stock == 10          # not yet
    world.universe.update(MARKET_REFRESH_SECONDS)
    assert station.market.prices["food_rations"].stock > 10


# --- Economy events: spawning and persistence ----------------------------------------------------

def place_player_in_region_with_station(world, faction):
    station = station_in(world, faction)
    world.ship.position = Vector2(station.position)
    return station


def test_events_wait_for_the_first_delay_then_appear_and_are_announced(world):
    place_player_in_region_with_station(world, FACTION_INDEPENDENT)
    random.seed(3)
    world.play_time = 0.0
    economy_events.update(world)
    assert economy_events.events == []
    world.play_time = FIRST_EVENT_DELAY + 1
    economy_events.update(world)
    assert len(economy_events.events) == 1
    assert any("Market news" in item[0] for item in notifications.items)
    random.seed()


def test_events_expire_and_the_active_count_is_capped(world):
    place_player_in_region_with_station(world, FACTION_INDEPENDENT)
    random.seed(5)
    economy_events.events = [make_event((9, 9), ends_at=world.play_time + 10)] * 1
    world.play_time = 20
    economy_events.update(world)
    assert economy_events.events == []

    now = 1000.0
    world.play_time = now
    economy_events.events = [make_event((9, 9), ends_at=now + 500) for _ in range(MAX_ACTIVE)]
    economy_events.next_event_at = now - 1
    economy_events.update(world)
    assert len(economy_events.events) == MAX_ACTIVE
    random.seed()


def test_nothing_spawns_when_no_station_is_near(world):
    world.ship.position = Vector2(999999, 999999)
    economy_events.next_event_at = 0.0
    world.play_time = 100.0
    economy_events.update(world)
    assert economy_events.events == []


def test_embargoes_only_ever_land_in_guild_regions(world):
    world.play_time = 500.0
    guild_station = station_in(world, FACTION_TRADE_GUILD)
    independent_station = station_in(world, FACTION_INDEPENDENT, start=3)

    embargoes = []
    for station in (guild_station, independent_station):
        for seed in range(80):
            economy_events.reset()
            economy_events.next_event_at = 0.0
            world.ship.position = Vector2(station.position)
            random.seed(seed)
            economy_events.update(world)
            embargoes += [e for e in economy_events.events if e.kind == "embargo"]
    random.seed()

    assert embargoes, "embargoes should occur sometimes"
    for event in embargoes:
        assert economy_events._region_faction(event.region) == FACTION_TRADE_GUILD
        assert event.embargo and event.commodity_id


def test_with_no_guild_region_nearby_an_embargo_becomes_a_shortage():
    """Embargoes need a Guild region; with none in reach the roll falls back."""
    events = EconomyEvents()
    events.world_seed = 1212
    kinds = set()
    universe = Universe(seed=1212)
    universe.generate_universe()
    station = universe.ensure_station_in_sector(*find_sector(FACTION_PIRATE, 1212), StationType.MINING)
    engine = SimpleNamespace(universe=SimpleNamespace(stations=[station]),
                             ship=SimpleNamespace(position=Vector2(station.position)), play_time=500.0)
    for seed in range(80):
        events.reset()
        events.next_event_at = 0.0
        random.seed(seed)
        events.update(engine)
        kinds.update(e.kind for e in events.events)
    random.seed()
    assert kinds and "embargo" not in kinds


def test_events_survive_a_json_round_trip_and_old_saves_start_clean():
    economy_events.reset()
    economy_events.events = [make_event((2, -3), ends_at=900.0, kind="embargo", embargo=True, multiplier=1.0)]
    economy_events.next_event_at = 750.0
    data = json.loads(json.dumps(economy_events.to_dict()))

    other = EconomyEvents()
    other.from_dict(data)
    assert other.events == economy_events.events
    assert other.events[0].region == (2, -3)
    assert other.next_event_at == 750.0

    other.from_dict({})
    assert other.events == [] and other.next_event_at is None
    economy_events.reset()
