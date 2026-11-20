"""The base screen (B in flight), built on the menu kit: it must fit every window
size, offer to found a base with the reasons when it cannot, build with clicks,
move goods between the hold and the base, and keep the mouse mapped onto the
base."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest
from pygame import Vector2

from src.base_building.base_entity import BUILDABLE, BaseModule, ModuleType
from src.base_building.base_manager import base_manager
from src.ui import menu_kit as mk

SIZES = [(1024, 640), (1280, 720), (1280, 800), (1512, 945), (2560, 1440), (3440, 1440)]
TABS = ["build", "storage", "production"]


class Clock:
    def get_time(self): return 16
    def tick(self, *a): return 16
    def get_fps(self): return 60.0


def key(k, mod=0):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode="", mod=mod)


def click(pos, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=button)


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


def open_screen(engine, size=(1280, 800), previous="PLAYING"):
    from src.states.game_state import GameStates

    pygame.display.set_mode(size, pygame.RESIZABLE)
    engine._on_window_resized()
    engine.change_state(getattr(GameStates, previous))
    engine.change_state(GameStates.BASE_CONSTRUCTION)
    engine.fade_remaining = 0
    return engine.states[GameStates.BASE_CONSTRUCTION]


def put_ship_in_open_space(engine):
    engine.ship.position = Vector2(engine.ship.position.x + 40000, engine.ship.position.y + 40000)


def with_base(engine):
    """A base right next to the ship, and the screen open on it."""
    put_ship_in_open_space(engine)
    engine.ship.credits = 100000
    base_id = base_manager.found_base(engine.ship.position, engine.universe.stations, engine.ship)
    engine.ship.credits = 100000
    base = base_manager.get_base(base_id)
    engine.ship.position = Vector2(base.position) + Vector2(-300, 0)
    return base_id, base


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


# --- founding -----------------------------------------------------------------------------------------------

def test_away_from_a_base_the_screen_offers_to_found_one(engine, monkeypatch):
    drawn = record_text(monkeypatch)
    put_ship_in_open_space(engine)
    state = open_screen(engine)
    assert state.base_id is None
    engine.render()
    assert any("Founding one costs" in text for text, _ in drawn)
    assert state.tab_rects == []


def test_it_says_why_a_base_cannot_be_founded_here(engine, monkeypatch):
    drawn = record_text(monkeypatch)
    engine.ship.credits = 10
    state = open_screen(engine)                       # at the start: next to a station, and poor
    engine.render()
    texts = " ".join(text for text, _ in drawn)
    assert "Too close to a station" in texts
    assert state.found_buttons.enabled[0] is False


def test_founding_with_enter_charges_you_and_opens_the_new_base(engine):
    put_ship_in_open_space(engine)
    engine.ship.credits = base_manager.founding_cost + 250
    state = open_screen(engine)
    engine.render()
    assert state.found_buttons.enabled[0] is True
    state.handle_input(key(pygame.K_RETURN))
    assert state.base_id and engine.ship.credits == 250
    assert base_manager.get_base(state.base_id).position == engine.ship.position
    assert state.construction_system.is_construction_active
    assert state.selected_tab == "build"
    engine.render()


def test_founding_by_clicking_the_button_and_cancel_leaves(engine):
    from src.states.game_state import GameStates

    put_ship_in_open_space(engine)
    engine.ship.credits = 10 ** 6
    state = open_screen(engine)
    engine.render()
    pygame.event.clear()
    pygame.event.post(click(state.found_buttons.rects[0].center))
    engine.handle_events()
    assert state.base_id is not None

    put_ship_in_open_space(engine)
    engine.ship.position += Vector2(30000, 0)
    other = open_screen(engine)
    engine.render()
    pygame.event.clear()
    pygame.event.post(click(other.found_buttons.rects[1].center))
    engine.handle_events()
    assert engine.current_state == GameStates.PLAYING
    assert len(base_manager.bases) == 1


def test_a_disabled_found_button_does_nothing(engine):
    engine.ship.credits = 10
    state = open_screen(engine)
    engine.render()
    pygame.event.clear()
    pygame.event.post(click(state.found_buttons.rects[0].center))
    engine.handle_events()
    state.handle_input(key(pygame.K_RETURN))
    assert base_manager.bases == {} and engine.ship.credits == 10


# --- layout -------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("size", SIZES)
def test_the_found_screen_fits_every_window(engine, size, monkeypatch):
    drawn = record_text(monkeypatch)
    put_ship_in_open_space(engine)
    open_screen(engine, size)
    engine.render()
    window = pygame.Rect(0, 0, *size)
    assert drawn and all(window.contains(rect) for _, rect in drawn)


def busy_base(engine):
    """A base with modules in every state, so every panel has something to show."""
    base_id, base = with_base(engine)
    base.add_resource("metal_ore", 6)
    base.add_resource("electronics", 8)
    base.add_resource("machinery", 4)
    for module_type, spot in ((ModuleType.POWER_GENERATOR, (3, -2)), (ModuleType.MINING_FACILITY, (3, 0)),
                              (ModuleType.REFINERY, (-5, 0)), (ModuleType.FACTORY, (-5, 3))):
        base.add_module(module_type, *spot, free=True)
    for _ in range(100):
        base.update(1.0)
    return base_id, base


@pytest.mark.parametrize("tab", TABS)
@pytest.mark.parametrize("size", SIZES)
def test_every_tab_fits_every_window(engine, size, tab, monkeypatch):
    busy_base(engine)
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
def test_the_help_overlay_fits_every_window(engine, size, monkeypatch):
    busy_base(engine)
    drawn = record_text(monkeypatch)
    state = open_screen(engine, size)
    state.show_help = True
    engine.render()
    window = pygame.Rect(0, 0, *size)
    assert not state.help_overflows
    assert all(window.contains(rect) for _, rect in drawn)


def test_the_base_is_drawn_behind_the_panels(engine):
    busy_base(engine)
    state = open_screen(engine, (1280, 800))
    state.show_base_info = False
    engine.render()
    centre = pygame.Rect(0, 0, 200, 200)
    centre.center = (640, 400)
    colours = {tuple(engine.screen.get_at((x, y))[:3]) for x in range(centre.left, centre.right, 4)
               for y in range(centre.top, centre.bottom, 4)}
    assert len(colours) > 3


# --- building --------------------------------------------------------------------------------------------------------

def aim_at_cell(state, engine, monkeypatch, gx, gy, size=1):
    """Put the mouse over a grid cell (for a module `size` wide) and return where to click."""
    base = state._base()
    zoom = state.zoom_level
    world = base.position + Vector2((gx + size / 2) * base.grid_size, (gy + size / 2) * base.grid_size)
    view = Vector2(engine.screen.get_size())
    point = (world - state._camera_offset()) * zoom
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (int(point.x), int(point.y)))
    state.update(0.0)
    return (int(point.x), int(point.y))


def test_clicking_a_module_in_the_list_chooses_it_and_the_digit_keys_too(engine):
    busy_base(engine)
    state = open_screen(engine)
    engine.render()
    for index in (2, 4, 1):
        pygame.event.clear()
        pygame.event.post(click(state.module_list.rects[index].center))
        engine.handle_events()
        assert state.construction_system.selected_module_type == BUILDABLE[index]
    state.handle_input(key(pygame.K_4))
    assert state.construction_system.selected_module_type == BUILDABLE[3]


def test_clicking_the_grid_builds_the_chosen_module_and_charges_for_it(engine, monkeypatch):
    base_id, base = with_base(engine)
    state = open_screen(engine)
    state.show_base_info = False
    engine.render()
    state.handle_input(key(pygame.K_1))                       # a power generator
    before = engine.ship.credits
    point = aim_at_cell(state, engine, monkeypatch, -6, -3)
    state.handle_input(click(point))
    assert base.modules[(-6, -3)].module_type == ModuleType.POWER_GENERATOR
    assert engine.ship.credits == before - BaseModule.MODULE_DEFINITIONS[ModuleType.POWER_GENERATOR].cost_credits
    assert "Building" in state.status


def test_a_click_on_the_grid_that_cannot_build_says_why(engine, monkeypatch):
    base_id, base = with_base(engine)
    engine.ship.credits = 0
    state = open_screen(engine)
    state.show_base_info = False
    engine.render()
    point = aim_at_cell(state, engine, monkeypatch, -6, -3)
    state.handle_input(click(point))
    assert (-6, -3) not in base.modules
    assert "missing" in state.status.lower() and "credits" in state.status.lower()


def test_a_click_over_a_panel_never_builds(engine, monkeypatch):
    base_id, base = with_base(engine)
    state = open_screen(engine)
    engine.render()
    before = dict(base.modules)
    panel = state.panel_rects[-1]
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: panel.center)
    state.update(0.0)
    state.handle_input(click(panel.center))
    assert base.modules == before


def test_remove_mode_takes_a_module_down_and_refunds_half(engine, monkeypatch):
    base_id, base = with_base(engine)
    base.add_module(ModuleType.POWER_GENERATOR, -6, -3, free=True)
    state = open_screen(engine)
    state.show_base_info = False
    engine.render()
    state.handle_input(key(pygame.K_r))
    before = engine.ship.credits
    point = aim_at_cell(state, engine, monkeypatch, -6, -3)
    state.handle_input(click(point))
    assert (-6, -3) not in base.modules
    assert engine.ship.credits == before + BaseModule.MODULE_DEFINITIONS[ModuleType.POWER_GENERATOR].cost_credits // 2


# --- storage ------------------------------------------------------------------------------------------------------------

def test_the_storage_tab_moves_goods_with_keys(engine):
    base_id, base = with_base(engine)
    engine.ship.cargo_hold.add_cargo("electronics", 5)
    state = open_screen(engine)
    state.selected_tab = "storage"
    engine.render()
    rows = state.storage_rows()
    index = [r[0] for r in rows].index("electronics")
    state.storage_list.selected = index
    state.handle_input(key(pygame.K_RIGHT))
    assert base.get_resource_amount("electronics") == 1 and engine.ship.cargo_hold.get_quantity("electronics") == 4
    state.handle_input(key(pygame.K_RIGHT, pygame.KMOD_SHIFT))
    assert base.get_resource_amount("electronics") == 5 and engine.ship.cargo_hold.get_quantity("electronics") == 0
    state.handle_input(key(pygame.K_LEFT))
    assert base.get_resource_amount("electronics") == 4
    state.handle_input(key(pygame.K_LEFT, pygame.KMOD_SHIFT))
    assert base.get_resource_amount("electronics") == 0 and engine.ship.cargo_hold.get_quantity("electronics") == 5


def test_the_storage_buttons_work_by_click(engine):
    base_id, base = with_base(engine)
    engine.ship.cargo_hold.add_cargo("electronics", 5)
    state = open_screen(engine)
    state.selected_tab = "storage"
    engine.render()
    state.storage_list.selected = [r[0] for r in state.storage_rows()].index("electronics")
    engine.render()
    for button, expected in ((0, 1), (1, 5)):                 # Deposit, Deposit all
        pygame.event.clear()
        pygame.event.post(click(state.storage_buttons.rects[button].center))
        engine.handle_events()
        assert base.get_resource_amount("electronics") == expected
    engine.render()
    for button, expected in ((2, 4), (3, 0)):                 # Withdraw, Withdraw all
        pygame.event.clear()
        pygame.event.post(click(state.storage_buttons.rects[button].center))
        engine.handle_events()
        assert base.get_resource_amount("electronics") == expected


def test_the_storage_tab_says_when_nothing_moved(engine):
    base_id, base = with_base(engine)
    state = open_screen(engine)
    state.selected_tab = "storage"
    engine.render()
    state.storage_list.selected = [r[0] for r in state.storage_rows()].index("metal_ore")
    state.handle_input(key(pygame.K_RIGHT))                   # the hold has none
    assert "Nothing" in state.status


def test_mission_cargo_cannot_be_deposited_from_the_screen(engine):
    base_id, base = with_base(engine)
    engine.ship.cargo_hold.add_mission_cargo("electronics", 3, "m1")
    state = open_screen(engine)
    state.selected_tab = "storage"
    engine.render()
    assert "electronics" not in [r[0] for r in state.storage_rows() if r[1]]
    assert state.move_goods(1, everything=True) == 0


# --- production and the rest -----------------------------------------------------------------------------------------------

def test_the_production_tab_reports_each_module(engine, monkeypatch):
    busy_base(engine)
    drawn = record_text(monkeypatch)
    state = open_screen(engine)
    state.selected_tab = "production"
    engine.render()
    text = " ".join(t for t, _ in drawn)
    assert "Mining Facility" in text and "Refinery" in text and "Factory" in text


def test_the_base_keeps_working_while_the_screen_is_open(engine):
    base_id, base = with_base(engine)
    base.add_module(ModuleType.POWER_GENERATOR, 4, -3, free=True)
    state = open_screen(engine)
    for _ in range(100):
        state.update(1.0)
    assert base.modules[(4, -3)].is_constructed


def test_q_w_e_switch_tabs_and_tabs_take_clicks(engine):
    base_id, base = with_base(engine)
    state = open_screen(engine)
    engine.render()
    for k, tab in ((pygame.K_w, "storage"), (pygame.K_e, "production"), (pygame.K_q, "build")):
        state.handle_input(key(k))
        assert state.selected_tab == tab
    for index, tab in enumerate(TABS):
        pygame.event.clear()
        pygame.event.post(click(state.tab_rects[index].center))
        engine.handle_events()
        assert state.selected_tab == tab


def test_a_click_on_a_tab_builds_nothing(engine):
    base_id, base = with_base(engine)
    state = open_screen(engine)
    engine.render()
    before = dict(base.modules)
    pygame.event.clear()
    pygame.event.post(click(state.tab_rects[0].center))
    engine.handle_events()
    assert base.modules == before


def test_escape_closes_help_first_then_leaves_in_one_press(engine):
    from src.states.game_state import GameStates

    with_base(engine)
    state = open_screen(engine)
    state.handle_input(key(pygame.K_F1))
    assert state.show_help
    state.handle_input(key(pygame.K_ESCAPE))
    assert not state.show_help and engine.current_state == GameStates.BASE_CONSTRUCTION
    state.handle_input(key(pygame.K_ESCAPE))
    assert engine.current_state == GameStates.PLAYING
    assert not state.construction_system.is_construction_active


def test_the_wheel_zooms_within_limits(engine):
    with_base(engine)
    state = open_screen(engine)
    for _ in range(40):
        state.handle_input(pygame.event.Event(pygame.MOUSEWHEEL, y=1))
    assert state.zoom_level == state.max_zoom
    for _ in range(80):
        state.handle_input(pygame.event.Event(pygame.MOUSEWHEEL, y=-1))
    assert state.zoom_level == state.min_zoom


@pytest.mark.parametrize("zoom", [0.5, 1.0, 2.0])
def test_the_mouse_is_mapped_onto_the_base_at_any_zoom(engine, monkeypatch, zoom):
    base_id, base = with_base(engine)
    state = open_screen(engine, (1280, 800))
    state.zoom_level = zoom
    engine.render()
    centre = state.view_center
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (centre.x, centre.y))
    state._update_mouse_world_position()
    assert state.mouse_world_pos.distance_to(base.position) < 1.0
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (centre.x + base.grid_size * zoom, centre.y))
    state._update_mouse_world_position()
    assert state.mouse_world_pos.x == pytest.approx(base.position.x + base.grid_size, abs=1.0)


@pytest.mark.parametrize("size", SIZES)
def test_the_base_sits_in_the_space_between_the_panels(engine, size):
    with_base(engine)
    state = open_screen(engine, size)
    engine.render()
    ratio = state._ui.ratio
    centre_px = state.view_center * ratio
    left_panel, right_panel = state.panel_rects[0], state.panel_rects[-1]
    assert left_panel.right < centre_px.x < right_panel.left
    state.show_base_info = False
    engine.render()
    assert state.view_center.x * ratio < right_panel.left


def test_the_screen_opens_on_the_base_in_reach_not_a_far_one(engine):
    base_id, base = with_base(engine)
    far_id = base_manager.found_base(base.position + Vector2(9000, 0), [], type("W", (), {"credits": 10 ** 6})())
    state = open_screen(engine)
    assert state.base_id == base_id and far_id != base_id
