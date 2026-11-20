"""Docking settings: auto-docking can be turned off (then the dock key does it),
and the speed limit for docking can be made stricter or more forgiving. Both
are saved, applied to the docking manager, and changed from Settings."""

import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest
from pygame import Vector2

from src.docking.docking_manager import DOCKING_SPEEDS, DockingManager
from src.docking.docking_state import DockingResult, DockingState
from src.entities.ship import Ship
from src.entities.station import Station, StationType
from src.settings import Settings


class Clock:
    def get_time(self): return 16
    def tick(self, *a): return 16
    def get_fps(self): return 60.0


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode="")


def near_station(speed):
    station = Station(1000, 1000, StationType.TRADING)
    ship = Ship(0, 0)
    ship.position = Vector2(1000 - (station.size + ship.size + 5), 1000)
    ship.velocity = Vector2(speed, 0)
    return ship, station


# --- the settings ---------------------------------------------------------------------------

def test_defaults_keep_the_old_behaviour():
    s = Settings()
    assert s.auto_dock is True and s.docking_speed == "standard"
    manager = DockingManager()
    manager.apply_settings(s)
    assert manager.auto_dock_enabled is True and manager.max_docking_speed == 50.0


def test_the_settings_are_saved_and_loaded(tmp_path):
    path = str(tmp_path / "settings.json")
    s = Settings()
    s.auto_dock, s.docking_speed = False, "relaxed"
    s.save(path)
    assert json.load(open(path))["auto_dock"] is False
    loaded = Settings()
    loaded.load(path)
    assert loaded.auto_dock is False and loaded.docking_speed == "relaxed"


def test_an_old_settings_file_and_a_bad_value_fall_back_to_the_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"hud_scale": 1.2}))
    s = Settings()
    s.load(str(path))
    assert s.auto_dock is True and s.docking_speed == "standard"
    path.write_text(json.dumps({"auto_dock": "yes please", "docking_speed": "warp"}))
    s = Settings()
    s.load(str(path))
    assert s.auto_dock is True and s.docking_speed == "standard"


def test_speed_levels_are_ordered():
    assert DOCKING_SPEEDS["careful"] < DOCKING_SPEEDS["standard"] < DOCKING_SPEEDS["relaxed"]


# --- docking behaviour ----------------------------------------------------------------------

def test_with_auto_docking_off_a_ship_in_range_waits_for_the_key():
    from src.input.control_schemes import control_scheme_manager

    ship, station = near_station(10)
    manager = DockingManager()
    s = Settings()
    s.auto_dock = False
    manager.apply_settings(s)
    manager.update(ship, [station], 0.016)
    manager.update(ship, [station], 0.016)
    assert manager.docking_state == DockingState.APPROACHING
    # The prompt names the key that is really bound, not a made-up one
    assert control_scheme_manager.get_key_name("dock") in manager.get_status_message()
    assert manager.attempt_manual_docking(ship, [station]) == DockingResult.SUCCESS
    assert manager.docking_state == DockingState.DOCKING


def test_with_auto_docking_on_the_same_approach_docks_by_itself():
    ship, station = near_station(10)
    manager = DockingManager()
    manager.apply_settings(Settings())
    manager.update(ship, [station], 0.016)
    manager.update(ship, [station], 0.016)
    assert manager.docking_state == DockingState.DOCKING


@pytest.mark.parametrize("level,speed,allowed", [
    ("careful", 40, False), ("careful", 25, True),
    ("standard", 40, True), ("standard", 60, False),
    ("relaxed", 70, True), ("relaxed", 90, False),
])
def test_the_speed_limit_follows_the_setting(level, speed, allowed):
    ship, station = near_station(speed)
    manager = DockingManager()
    s = Settings()
    s.docking_speed = level
    manager.apply_settings(s)
    can, reason = manager._can_dock(ship, station)
    assert can is allowed
    if not allowed:
        assert reason == DockingResult.TOO_FAST


# --- the Settings screen and the engine -------------------------------------------------------

@pytest.fixture
def engine():
    from src.engine.game_engine import GameEngine
    game = GameEngine()
    game.clock = Clock()
    saved = (game.settings.auto_dock, game.settings.docking_speed)
    game.settings.save = lambda *a, **k: None            # never write the real settings file
    yield game
    game.settings.auto_dock, game.settings.docking_speed = saved


def open_docking_page(engine):
    from src.states.game_state import GameStates
    from src.states.settings_state import CATEGORY_PAGES

    engine.change_state(GameStates.SETTINGS)
    state = engine.states[GameStates.SETTINGS]
    state.page = "docking"
    state.list.set_count(len(state.rows("docking")))
    engine.fade_remaining = 0
    return state


def test_docking_is_a_settings_category():
    import src.states.game_state  # noqa: F401  (the settings module is loaded through it)
    from src.states.settings_state import CATEGORY_PAGES, PAGE_TITLES, PAGE_HINTS
    assert CATEGORY_PAGES["Docking"] == "docking"
    assert "docking" in PAGE_TITLES and "docking" in PAGE_HINTS


def test_the_docking_page_has_both_rows_and_the_manager_follows_changes(engine):
    state = open_docking_page(engine)
    rows = {row.id: row for row in state.rows("docking")}
    assert set(rows) >= {"auto_dock", "docking_speed", "back"}
    assert rows["auto_dock"].value == "ON" and rows["docking_speed"].value.lower().startswith("standard")

    state._change(rows["auto_dock"], 1)
    assert engine.settings.auto_dock is False and engine.docking_manager.auto_dock_enabled is False
    state._change(rows["docking_speed"], 1)
    assert engine.settings.docking_speed == "relaxed" and engine.docking_manager.max_docking_speed == 80.0
    state._change(rows["docking_speed"], -1)
    state._change(rows["docking_speed"], -1)
    assert engine.settings.docking_speed == "careful" and engine.docking_manager.max_docking_speed == 30.0
    state._change(rows["docking_speed"], -1)                      # wraps round
    assert engine.settings.docking_speed == "relaxed"


def test_the_page_renders_and_takes_clicks(engine):
    from src.states.game_state import GameStates

    state = open_docking_page(engine)
    engine.render()
    first = state.list.rects[0]
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=first.center, button=1))
    engine.handle_events()
    assert engine.settings.auto_dock is False                      # a toggle flips on a click


def test_the_engine_applies_saved_settings_when_it_starts():
    from src.engine.game_engine import GameEngine
    from src.settings import game_settings

    before = (game_settings.auto_dock, game_settings.docking_speed)
    game_settings.auto_dock, game_settings.docking_speed = False, "careful"
    try:
        game = GameEngine()
        assert game.docking_manager.auto_dock_enabled is False
        assert game.docking_manager.max_docking_speed == 30.0
    finally:
        game_settings.auto_dock, game_settings.docking_speed = before
