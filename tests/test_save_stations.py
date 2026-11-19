import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from types import SimpleNamespace

from src.entities.station import StationType
from src.save_system import SaveSystem
from src.universe import Universe


def snapshot(station):
    return (station.station_type, tuple(station.color), len(station.shape_points), station.size)


def test_stations_keep_their_look_through_save_and_load():
    """Loading rebuilt stations with the right type and name but a random
    color and shape, because those were derived from a random type at
    construction and never recomputed."""
    universe = Universe(seed=31337)
    universe.generate_universe()
    for i, station_type in enumerate(StationType):
        universe.ensure_station_in_sector(30 + i, 30, station_type)
    engine = SimpleNamespace(universe=universe, world_seed=universe.world_seed)

    before = {s.name: snapshot(s) for s in universe.stations}
    assert len({v[0] for v in before.values()}) == len(StationType)  # every type covered

    save_system = SaveSystem.__new__(SaveSystem)  # skip __init__ (touches disk)
    data = json.loads(json.dumps(save_system._save_universe_data(engine)))
    save_system._load_universe_data(data, engine)

    after = {s.name: snapshot(s) for s in engine.universe.stations}
    assert after == before


def test_loaded_station_type_is_the_entity_enum():
    """Station code compares against entities.station.StationType; the market
    module has a separate enum with the same values."""
    universe = Universe(seed=5)
    universe.generate_universe()
    universe.ensure_station_in_sector(31, 31, StationType.SHIPYARD)
    engine = SimpleNamespace(universe=universe, world_seed=universe.world_seed)

    save_system = SaveSystem.__new__(SaveSystem)
    data = json.loads(json.dumps(save_system._save_universe_data(engine)))
    save_system._load_universe_data(data, engine)

    assert all(isinstance(s.station_type, StationType) for s in engine.universe.stations)
