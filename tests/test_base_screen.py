"""The base construction screen (B in flight), built on the menu kit: it must
fit every window size, say plainly when there is no base, keep clicks on its
tabs from building anything, and keep the mouse mapped onto the base."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest
from pygame import Vector2

from src.base_building.base_manager import base_manager
from src.ui import menu_kit as mk

SIZES = [(1024, 640), (1280, 720), (1280, 800), (1512, 945), (2560, 1440), (3440, 1440)]
TABS = ["construction", "production", "management"]


class Clock:
    def get_time(self): return 16
    def tick(self, *a): return 16
    def get_fps(self): return 60.0


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode="")


def click(pos, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=button)


@pytest.fixture
def engine():
    from src.engine.game_engine import GameEngine
    game = GameEngine()
    game.clock = Clock()
    game.create_new_universe(seed=4)
    return game


@pytest.fixture
def bases():
    """The base manager is shared: start every test with none, and put it back."""
    saved = (dict(base_manager.bases), base_manager.active_base_id)
    base_manager.bases.clear()
    base_manager.active_base_id = None
    yield base_manager
    base_manager.bases.clear()
    base_manager.bases.update(saved[0])
    base_manager.active_base_id = saved[1]


def open_screen(engine, size=(1280, 800), previous="PLAYING"):
    from src.states.game_state import GameStates

    pygame.display.set_mode(size, pygame.RESIZABLE)
    engine._on_window_resized()
    engine.change_state(getattr(GameStates, previous))
    engine.change_state(GameStates.BASE_CONSTRUCTION)
    engine.fade_remaining = 0
    return engine.states[GameStates.BASE_CONSTRUCTION]


def record_text(monkeypatch):
    """Every rectangle the kit's text helper draws, to check they stay on screen."""
    drawn = []
    original = mk.Ui.text

    def spy(self, screen, text, *args, **kwargs):
        rect = original(self, screen, text, *args, **kwargs)
        drawn.append((text, rect))
        return rect

    monkeypatch.setattr(mk.Ui, "text", spy)
    return drawn


# --- which base -----------------------------------------------------------------------------

def test_with_no_base_the_screen_says_so(engine, bases, monkeypatch):
    drawn = record_text(monkeypatch)
    state = open_screen(engine)
    assert state.base_id is None
    engine.render()
    assert any("No base to build on" in text for text, _ in drawn)
    assert state.tab_rects == []
    # It must not promise a way to get a base that the game does not have
    assert not any("claim" in text.lower() and "start" in text.lower() for text, _ in drawn)


def test_it_works_on_the_active_base_then_the_nearest_then_any(engine, bases):
    far = bases.create_base(Vector2(50000, 50000), "Far")
    near = bases.create_base(Vector2(engine.ship.position.x + 800, engine.ship.position.y), "Near")
    bases.active_base_id = None
    assert open_screen(engine).base_id == near
    bases.set_active_base(far)
    assert open_screen(engine).base_id == far


# --- layout ---------------------------------------------------------------------------------

@pytest.mark.parametrize("size", SIZES)
def test_the_empty_screen_fits_every_window(engine, bases, size, monkeypatch):
    drawn = record_text(monkeypatch)
    open_screen(engine, size)
    engine.render()
    window = pygame.Rect(0, 0, *size)
    assert drawn and all(window.contains(rect) for _, rect in drawn)


@pytest.mark.parametrize("tab", TABS)
@pytest.mark.parametrize("size", SIZES)
def test_every_tab_fits_every_window(engine, bases, size, tab, monkeypatch):
    bases.create_base(Vector2(engine.ship.position.x + 100, engine.ship.position.y), "Alpha")
    drawn = record_text(monkeypatch)
    state = open_screen(engine, size)
    state.selected_tab = tab
    engine.render()
    window = pygame.Rect(0, 0, *size)
    assert drawn
    assert all(window.contains(rect) for _, rect in drawn), [t for t, r in drawn if not window.contains(r)]
    assert not state.panel_overflows
    assert len(state.tab_rects) == 3 and all(window.contains(r) for r in state.tab_rects)


@pytest.mark.parametrize("size", SIZES)
def test_the_help_overlay_fits_every_window(engine, bases, size, monkeypatch):
    bases.create_base(Vector2(engine.ship.position.x + 100, engine.ship.position.y), "Alpha")
    drawn = record_text(monkeypatch)
    state = open_screen(engine, size)
    state.show_help = True
    engine.render()
    window = pygame.Rect(0, 0, *size)
    assert not state.help_overflows
    assert all(window.contains(rect) for _, rect in drawn)
    assert any("Base construction help" in text for text, _ in drawn)


def test_the_base_is_drawn_behind_the_panels(engine, bases):
    bases.create_base(Vector2(engine.ship.position.x + 100, engine.ship.position.y), "Alpha")
    state = open_screen(engine, (1280, 800))
    state.show_base_info = False
    engine.render()
    centre = pygame.Rect(0, 0, 200, 200)
    centre.center = (640, 400)
    colours = {tuple(engine.screen.get_at((x, y))[:3]) for x in range(centre.left, centre.right, 4)
               for y in range(centre.top, centre.bottom, 4)}
    assert len(colours) > 3                      # the grid and the base, not an empty field


# --- input ----------------------------------------------------------------------------------

def test_clicking_a_tab_selects_it_and_builds_nothing(engine, bases):
    base_id = bases.create_base(Vector2(engine.ship.position.x + 100, engine.ship.position.y), "Alpha")
    state = open_screen(engine, (1280, 800))
    engine.render()
    modules_before = dict(bases.get_base(base_id).modules)
    for index, tab in enumerate(TABS):
        pygame.event.clear()
        pygame.event.post(click(state.tab_rects[index].center))
        engine.handle_events()
        assert state.selected_tab == tab
    assert bases.get_base(base_id).modules == modules_before


def test_q_w_e_switch_tabs(engine, bases):
    bases.create_base(Vector2(engine.ship.position.x + 100, engine.ship.position.y), "Alpha")
    state = open_screen(engine)
    for k, tab in ((pygame.K_w, "production"), (pygame.K_e, "management"), (pygame.K_q, "construction")):
        state.handle_input(key(k))
        assert state.selected_tab == tab


def test_escape_closes_help_first_then_leaves_in_one_press(engine, bases):
    from src.states.game_state import GameStates

    bases.create_base(Vector2(engine.ship.position.x + 100, engine.ship.position.y), "Alpha")
    state = open_screen(engine)
    state.handle_input(key(pygame.K_F1))
    assert state.show_help
    state.handle_input(key(pygame.K_ESCAPE))
    assert not state.show_help and engine.current_state == GameStates.BASE_CONSTRUCTION
    state.handle_input(key(pygame.K_ESCAPE))
    assert engine.current_state == GameStates.PLAYING
    assert not state.construction_system.is_construction_active


def test_escape_leaves_when_there_is_no_base(engine, bases):
    from src.states.game_state import GameStates

    state = open_screen(engine)
    state.handle_input(key(pygame.K_ESCAPE))
    assert engine.current_state == GameStates.PLAYING


def test_the_b_key_in_flight_opens_the_screen(engine, bases):
    from src.input.control_schemes import control_scheme_manager
    from src.states.game_state import GameStates

    engine.change_state(GameStates.PLAYING)
    engine.states[GameStates.PLAYING].handle_input(key(control_scheme_manager.get_key("base_construction")))
    assert engine.current_state == GameStates.BASE_CONSTRUCTION
    engine.render()


def test_the_wheel_zooms_within_limits(engine, bases):
    state = open_screen(engine)
    for _ in range(40):
        state.handle_input(pygame.event.Event(pygame.MOUSEWHEEL, y=1))
    assert state.zoom_level == state.max_zoom
    for _ in range(80):
        state.handle_input(pygame.event.Event(pygame.MOUSEWHEEL, y=-1))
    assert state.zoom_level == state.min_zoom


@pytest.mark.parametrize("zoom", [0.5, 1.0, 2.0])
def test_the_mouse_is_mapped_onto_the_base_at_any_zoom(engine, bases, monkeypatch, zoom):
    base_id = bases.create_base(Vector2(3000, 2000), "Alpha")
    state = open_screen(engine, (1280, 800))
    state.zoom_level = zoom
    width, height = engine.screen.get_size()
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (width // 2, height // 2))
    state._update_mouse_world_position()
    base = bases.get_base(base_id)
    assert state.mouse_world_pos.distance_to(base.position) < 1.0
    # A point one grid cell right of the middle is one cell right of the base, whatever the zoom
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (width // 2 + base.grid_size * zoom, height // 2))
    state._update_mouse_world_position()
    assert state.mouse_world_pos.x == pytest.approx(base.position.x + base.grid_size, abs=1.0)


def test_update_runs_with_and_without_a_base(engine, bases):
    state = open_screen(engine)
    state.update(0.016)
    bases.create_base(Vector2(engine.ship.position.x + 100, engine.ship.position.y), "Alpha")
    state = open_screen(engine)
    state.update(0.016)
