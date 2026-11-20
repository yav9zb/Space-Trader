"""A base in the running game: it exists in the world, keeps working while the
player flies, is saved with the game, is cleared by a new game, shows on the
radar, and B opens it (or offers to found one)."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import json

import pygame
import pytest
from pygame import Vector2

from src.base_building.base_entity import ModuleType
from src.base_building.base_manager import base_manager


class Clock:
    def get_time(self): return 16
    def tick(self, *a): return 16
    def get_fps(self): return 60.0


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode="")


@pytest.fixture
def engine():
    from src.engine.game_engine import GameEngine
    game = GameEngine()
    game.clock = Clock()
    game.create_new_universe(seed=4)
    saved = (dict(base_manager.bases), base_manager.active_base_id, base_manager.next_base_id)
    base_manager.reset()
    yield game
    base_manager.bases.clear()
    base_manager.bases.update(saved[0])
    base_manager.active_base_id, base_manager.next_base_id = saved[1], saved[2]


def far_from_stations(engine):
    """A point well clear of every station."""
    return Vector2(engine.ship.position.x + 40000, engine.ship.position.y + 40000)


def found(engine, offset=(0, 0)):
    wallet = type("W", (), {"credits": 10 ** 6})()
    where = far_from_stations(engine) + Vector2(offset)
    return base_manager.found_base(where, engine.universe.stations, wallet)


# --- a new game and saving --------------------------------------------------------------------------

def test_a_new_game_has_no_bases(engine):
    found(engine)
    assert base_manager.bases
    engine.create_new_universe(seed=5)
    assert base_manager.bases == {} and base_manager.active_base_id is None


def test_bases_are_saved_and_loaded_with_the_game(engine):
    from src.save_system import SaveSystem

    base_id = found(engine)
    base = base_manager.get_base(base_id)
    base.add_resource("metal_ore", 5)
    ore = base.get_resource_amount("metal_ore")
    save_system = SaveSystem.__new__(SaveSystem)
    data = json.loads(json.dumps(save_system._collect_save_data(engine)))
    assert data["bases"]["bases"][base_id]["stored_resources"]["metal_ore"] == ore

    base_manager.reset()
    save_system._apply_save_data(data, engine)
    assert base_manager.get_base(base_id).get_resource_amount("metal_ore") == ore


def test_loading_an_old_save_without_bases_clears_the_bases(engine):
    from src.save_system import SaveSystem

    found(engine)
    save_system = SaveSystem.__new__(SaveSystem)
    data = json.loads(json.dumps(save_system._collect_save_data(engine)))
    del data["bases"]
    save_system._apply_save_data(data, engine)
    assert base_manager.bases == {}


# --- in flight -----------------------------------------------------------------------------------------

def test_a_base_builds_while_the_player_flies(engine):
    from src.states.game_state import GameStates

    base_id = found(engine)
    base = base_manager.get_base(base_id)
    wallet = engine.ship
    engine.ship.credits = 10 ** 6
    base.add_module(ModuleType.POWER_GENERATOR, 1, 2, wallet=wallet)
    engine.change_state(GameStates.PLAYING)
    engine.fade_remaining = 0
    playing = engine.states[GameStates.PLAYING]
    for _ in range(200):
        playing.update(0.5)
    assert base.modules[(1, 2)].is_constructed


def test_a_base_in_view_is_drawn_in_flight(engine):
    from src.states.game_state import GameStates

    base_id = found(engine)
    base = base_manager.get_base(base_id)
    engine.ship.position = Vector2(base.position) + Vector2(150, 0)
    engine.change_state(GameStates.PLAYING)
    engine.fade_remaining = 0
    # The camera wraps the universe, so a teleported ship needs it moved along too
    engine.camera.position = Vector2(engine.ship.position) - Vector2(engine.camera.width / 2, engine.camera.height / 2)
    engine.camera.follow(engine.ship, 1.0)
    engine.update()
    engine.render()
    # The command center is blue; it should be on screen near the middle
    window = engine.screen.get_rect()
    found_blue = any(
        (lambda c: c[2] > 200 and c[0] < 140)(engine.screen.get_at((x, y)))
        for x in range(window.centerx - 300, window.centerx + 300, 3)
        for y in range(window.centery - 300, window.centery + 300, 3))
    assert found_blue


def test_the_radar_shows_bases(engine):
    from src.ui.minimap import gather_contacts

    base_id = found(engine)
    base = base_manager.get_base(base_id)
    engine.ship.position = Vector2(base.position) + Vector2(300, 0)
    kinds = [kind for kind, _ in gather_contacts(engine, 2000)]
    assert "base" in kinds
    engine.ship.position = Vector2(base.position) + Vector2(50000, 0)
    assert "base" not in [kind for kind, _ in gather_contacts(engine, 2000)]


def test_coming_within_range_of_a_base_says_so_once(engine):
    from src.states.game_state import GameStates
    from src.ui.notifications import notifications

    base_id = found(engine)
    base = base_manager.get_base(base_id)
    engine.change_state(GameStates.PLAYING)
    engine.fade_remaining = 0
    playing = engine.states[GameStates.PLAYING]
    engine.ship.position = Vector2(base.position) + Vector2(5000, 0)
    notifications.clear() if hasattr(notifications, "clear") else None
    playing.update(0.016)
    before = len(getattr(notifications, "items", getattr(notifications, "_items", [])))
    engine.ship.position = Vector2(base.position) + Vector2(100, 0)
    playing.update(0.016)
    playing.update(0.016)
    after = len(getattr(notifications, "items", getattr(notifications, "_items", [])))
    assert after == before + 1


# --- the B key ----------------------------------------------------------------------------------------------

def test_b_near_a_base_opens_that_base(engine):
    from src.input.control_schemes import control_scheme_manager
    from src.states.game_state import GameStates

    base_id = found(engine)
    base = base_manager.get_base(base_id)
    engine.ship.position = Vector2(base.position) + Vector2(200, 0)
    engine.change_state(GameStates.PLAYING)
    engine.states[GameStates.PLAYING].handle_input(key(control_scheme_manager.get_key("base_construction")))
    assert engine.current_state == GameStates.BASE_CONSTRUCTION
    assert engine.states[GameStates.BASE_CONSTRUCTION].base_id == base_id


def test_b_away_from_any_base_offers_to_found_one(engine):
    from src.input.control_schemes import control_scheme_manager
    from src.states.game_state import GameStates

    found(engine)
    engine.ship.position = far_from_stations(engine) + Vector2(20000, 0)
    engine.change_state(GameStates.PLAYING)
    engine.states[GameStates.PLAYING].handle_input(key(control_scheme_manager.get_key("base_construction")))
    state = engine.states[GameStates.BASE_CONSTRUCTION]
    assert state.base_id is None
