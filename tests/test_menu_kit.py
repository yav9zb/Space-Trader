"""The menu toolkit and the screens built on it: layouts are measured from the
window, so they must fit every window size, at any pixel density, and mouse
positions (in window points) must land on the right rows."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from src.ui import menu_kit as mk

SIZES = [(1024, 640), (1280, 720), (1280, 800), (1470, 956), (1512, 945), (1728, 1117), (2560, 1440), (3440, 1440)]


class Clock:
    def get_time(self): return 16
    def tick(self, *a): return 16
    def get_fps(self): return 60.0


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode="")


def click(pos, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=button)


# --- scale ----------------------------------------------------------------------------

def test_scale_grows_continuously_with_the_window_and_is_bounded():
    previous = 0
    for width in range(900, 4000, 100):
        scale = mk.scale_for((width, int(width * 0.625)))
        assert mk.MIN_SCALE <= scale <= mk.MAX_SCALE
        assert scale >= previous
        previous = scale
    assert mk.scale_for((1280, 800)) == pytest.approx(1.0)


def test_a_wide_short_window_is_limited_by_its_height():
    assert mk.scale_for((3440, 800)) == pytest.approx(1.0)
    assert mk.scale_for((1280, 1600)) == pytest.approx(1.0)


def test_a_retina_surface_has_the_same_layout_in_points_with_twice_the_pixels():
    plain, retina = mk.Ui((1512, 945), 1.0), mk.Ui((3024, 1890), 2.0)
    assert plain.scale == pytest.approx(retina.scale)
    assert retina.px(40) == plain.px(40) * 2
    assert retina.font("body").get_height() >= plain.font("body").get_height() * 1.8
    assert retina.to_px((100, 50)) == (200, 100)


def test_fonts_are_cached_by_pixel_size():
    ui = mk.Ui((1280, 800))
    assert ui.font("body") is ui.font("body")
    assert ui.font("body") is not ui.font("title")


# --- text helpers -----------------------------------------------------------------------

def test_fit_text_shortens_with_an_ellipsis_only_when_needed():
    font = mk.Ui((1280, 800)).font("body")
    assert mk.fit_text("short", font, 500) == "short"
    cut = mk.fit_text("a very long line of text that cannot possibly fit", font, 120)
    assert cut.endswith("...") and font.size(cut)[0] <= 120


def test_scroll_window_keeps_the_selection_visible_and_moves_minimally():
    assert mk.scroll_window(5, 4, 8) == 0                      # everything fits
    assert mk.scroll_window(20, 0, 5, 0) == 0
    assert mk.scroll_window(20, 7, 5, 0) == 3                  # scrolls just enough to show row 7
    assert mk.scroll_window(20, 5, 5, 3) == 3                  # already visible: unchanged
    assert mk.scroll_window(20, 2, 5, 10) == 2
    assert mk.scroll_window(20, 19, 5, 0) == 15
    assert mk.scroll_window(20, 3, 5, 99) == 3                 # a stale offset is clamped


# --- the menu list ----------------------------------------------------------------------

@pytest.mark.parametrize("size", SIZES)
def test_a_menu_list_fits_the_area_it_is_given(size):
    ui = mk.Ui(size)
    area = pygame.Rect(0, int(size[1] * 0.3), size[0], int(size[1] * 0.5))
    menu = mk.MenuList(["One", "Two", "Three", "Four", "Five"])
    box = menu.layout(ui, area)
    assert area.contains(box)
    rects = [menu.rects[i] for i in sorted(menu.rects)]
    assert len(rects) == 5
    assert all(not a.colliderect(b) for a, b in zip(rects, rects[1:]))
    assert all(area.contains(r) for r in rects)


def test_a_cramped_menu_shrinks_its_rows_then_scrolls():
    ui = mk.Ui((1280, 800))
    menu = mk.MenuList([f"Item {i}" for i in range(30)])
    area = pygame.Rect(0, 100, 1280, 400)
    menu.layout(ui, area)
    assert len(menu.rects) < 30
    assert all(area.contains(r) for r in menu.rects.values())
    menu.selected = 29
    menu.layout(ui, area)
    assert 29 in menu.rects and 0 not in menu.rects


def test_keys_move_the_highlight_wrap_and_enter_activates():
    ui = mk.Ui((1280, 800))
    menu = mk.MenuList(["A", "B", "C"])
    menu.layout(ui, pygame.Rect(0, 0, 1280, 800))
    assert menu.handle(key(pygame.K_DOWN), ui, play_sounds=False) is None
    assert menu.selected == 1
    menu.handle(key(pygame.K_UP), ui, play_sounds=False)
    menu.handle(key(pygame.K_UP), ui, play_sounds=False)
    assert menu.selected == 2                                  # wrapped
    assert menu.handle(key(pygame.K_RETURN), ui, play_sounds=False) == 2


@pytest.mark.parametrize("ratio", [1.0, 2.0])
def test_mouse_hover_and_click_use_window_points(ratio):
    ui = mk.Ui((int(1280 * ratio), int(800 * ratio)), ratio)
    menu = mk.MenuList(["A", "B", "C"])
    menu.layout(ui, pygame.Rect(0, 0, ui.width, ui.height))
    target = menu.rects[2]
    point = (target.centerx / ratio, target.centery / ratio)
    menu.handle(pygame.event.Event(pygame.MOUSEMOTION, pos=point, rel=(0, 0), buttons=(0, 0, 0)), ui)
    assert menu.selected == 2
    assert menu.handle(click((int(point[0]), int(point[1]))), ui, play_sounds=False) == 2
    assert menu.handle(click((int(point[0]), int(point[1])), button=3), ui, play_sounds=False) is None
    assert menu.handle(click((2, 2)), ui, play_sounds=False) is None


def test_the_menu_is_drawn_without_leaving_its_rows():
    ui = mk.Ui((1280, 800))
    screen = pygame.Surface((1280, 800))
    menu = mk.MenuList(["Alpha", "Beta"])
    menu.layout(ui, screen.get_rect())
    menu.draw(ui, screen)
    row = menu.rects[0]
    assert any(screen.get_at((x, row.centery))[:3] != (0, 0, 0) for x in range(row.left, row.right))


# --- the migrated screens, in the real engine ---------------------------------------------

@pytest.fixture
def engine():
    from src.engine.game_engine import GameEngine
    game = GameEngine()
    game.clock = Clock()
    return game


@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize("name", ["MAIN_MENU", "GAME_OVER", "PAUSED"])
def test_each_migrated_menu_fits_every_window_size(engine, size, name):
    from src.states.game_state import GameStates

    pygame.display.set_mode(size, pygame.RESIZABLE)
    engine._on_window_resized()
    engine.create_new_universe(seed=4)
    engine.change_state(GameStates.PLAYING)
    engine.change_state(getattr(GameStates, name))
    engine.fade_remaining = 0
    engine.render()
    rects = engine.states[getattr(GameStates, name)].option_rects
    assert rects
    window = pygame.Rect(0, 0, *size)
    assert all(window.contains(r) for r in rects)
    assert all(not a.colliderect(b) for a, b in zip(rects, rects[1:]))


@pytest.mark.parametrize("size", [(1024, 640), (1512, 945), (3440, 1440)])
def test_clicking_each_main_menu_option_chooses_it(engine, size):
    from src.states.game_state import GameStates

    pygame.display.set_mode(size, pygame.RESIZABLE)
    engine._on_window_resized()
    expected = [None, GameStates.LOAD_GAME, GameStates.SETTINGS]
    for index, target in enumerate(expected):
        if target is None:
            continue                                            # New Game builds a universe; covered elsewhere
        engine.change_state(GameStates.MAIN_MENU)
        engine.fade_remaining = 0
        engine.render()
        rect = engine.states[GameStates.MAIN_MENU].option_rects[index]
        pygame.event.clear()
        pygame.event.post(click(rect.center))
        engine.handle_events()
        assert engine.current_state == target


def test_exit_on_the_main_menu_stops_the_game(engine):
    from src.states.game_state import GameStates

    engine.change_state(GameStates.MAIN_MENU)
    engine.render()
    menu = engine.states[GameStates.MAIN_MENU]
    pygame.event.clear()
    pygame.event.post(click(menu.option_rects[3].center))
    engine.handle_events()
    assert engine.running is False
    engine.running = True


def test_game_over_menu_returns_to_the_main_menu_by_keyboard(engine):
    from src.states.game_state import GameStates

    engine.create_new_universe(seed=4)
    engine.change_state(GameStates.GAME_OVER)
    engine.render()
    over = engine.states[GameStates.GAME_OVER]
    over.handle_input(key(pygame.K_RETURN))
    assert engine.current_state == GameStates.MAIN_MENU


def test_escape_resumes_from_the_pause_menu(engine):
    from src.states.game_state import GameStates

    engine.create_new_universe(seed=4)
    engine.change_state(GameStates.PLAYING)
    engine.change_state(GameStates.PAUSED)
    engine.states[GameStates.PAUSED].handle_input(key(pygame.K_ESCAPE))
    assert engine.current_state == GameStates.PLAYING


# --- save and load screens -----------------------------------------------------------------

@pytest.fixture
def saves(engine):
    """A few real saved games, removed afterwards."""
    from src.save_system import save_system

    engine.create_new_universe(seed=4)
    names = [f"Slot {i:02d} with a rather long descriptive name to test fitting" if i == 3 else f"Slot {i:02d}"
             for i in range(14)]
    for name in names:
        assert save_system.save_game(engine, name)
    yield names
    for name in names:
        save_system.delete_save(name)


@pytest.mark.parametrize("size", [(1024, 640), (1512, 945), (3440, 1440)])
def test_the_load_screen_lists_saves_inside_its_panel_and_scrolls(engine, saves, size):
    from src.states.game_state import GameStates

    pygame.display.set_mode(size, pygame.RESIZABLE)
    engine._on_window_resized()
    engine.change_state(GameStates.LOAD_GAME)
    state = engine.states[GameStates.LOAD_GAME]
    state.existing_saves = state.save_system.get_save_list()
    engine.fade_remaining = 0
    engine.render()
    window = pygame.Rect(0, 0, *size)
    assert state.list.rects and all(window.contains(r) for r in state.list.rects.values())
    visible = len(state.list.rects)
    assert visible <= len(saves)
    state.selected_save_index = len(state.existing_saves) - 1
    engine.render()
    assert (len(state.existing_saves) - 1) in state.list.rects
    assert state.list.counter() or visible == len(state.existing_saves)


def test_clicking_a_save_on_the_load_screen_loads_it(engine, saves):
    from src.states.game_state import GameStates

    engine.change_state(GameStates.LOAD_GAME)
    state = engine.states[GameStates.LOAD_GAME]
    state.existing_saves = state.save_system.get_save_list()
    engine.fade_remaining = 0
    engine.render()
    rect = state.list.rects[1]
    wanted = state.existing_saves[1].save_name
    loaded = []
    state.save_system.load_game = lambda name, game: loaded.append(name) or True
    pygame.event.clear()
    pygame.event.post(click(rect.center))
    engine.handle_events()
    assert loaded == [wanted]
    assert engine.current_state == GameStates.PLAYING


def test_delete_still_removes_the_selected_save(engine, saves):
    from src.states.game_state import GameStates

    engine.change_state(GameStates.LOAD_GAME)
    state = engine.states[GameStates.LOAD_GAME]
    state.existing_saves = state.save_system.get_save_list()
    before = len(state.existing_saves)
    state.handle_input(key(pygame.K_DELETE))
    assert len(state.existing_saves) == before - 1


@pytest.mark.parametrize("size", [(1024, 640), (1512, 945), (3440, 1440)])
def test_the_save_screen_fits_and_its_input_box_takes_a_click(engine, saves, size):
    from src.states.game_state import GameStates

    pygame.display.set_mode(size, pygame.RESIZABLE)
    engine._on_window_resized()
    engine.change_state(GameStates.SAVE_GAME)
    state = engine.states[GameStates.SAVE_GAME]
    state.existing_saves = state.save_system.get_save_list()
    state.editing_name = False
    engine.fade_remaining = 0
    engine.render()
    window = pygame.Rect(0, 0, *size)
    assert window.contains(state.input_box)
    assert state.list.rects and all(window.contains(r) for r in state.list.rects.values())
    assert state.input_box.bottom < min(r.top for r in state.list.rects.values())

    pygame.event.clear()
    pygame.event.post(click(state.input_box.center))
    engine.handle_events()
    assert state.editing_name is True

    rect = state.list.rects[2]
    pygame.event.post(click(rect.center))
    engine.handle_events()
    assert state.editing_name is False and state.selected_save_index == 2


def test_typing_a_name_on_the_save_screen_still_works(engine):
    from src.states.game_state import GameStates

    engine.change_state(GameStates.SAVE_GAME)
    state = engine.states[GameStates.SAVE_GAME]
    state.save_name = ""
    for ch in "abc":
        state.handle_input(pygame.event.Event(pygame.KEYDOWN, key=ord(ch), unicode=ch))
    assert state.save_name == "abc"


# --- trading and upgrades ------------------------------------------------------------------

def _shipyard():
    from src.entities.station import Station, StationType
    return Station(300, 300, StationType.SHIPYARD)


def _stock_cargo(engine, station):
    engine.ship.credits = 50000
    for commodity in station.market.get_available_commodities()[:4]:
        engine.ship.cargo_hold.add_cargo(commodity.id, 2)


@pytest.mark.parametrize("size", SIZES)
def test_the_trading_screen_fits_every_window_size(engine, size):
    from src.states.game_state import GameStates

    pygame.display.set_mode(size, pygame.RESIZABLE)
    engine._on_window_resized()
    engine.create_new_universe(seed=4)
    station = engine.universe.stations[0]
    _stock_cargo(engine, station)
    engine.change_state(GameStates.TRADING, station)
    engine.fade_remaining = 0
    engine.render()
    state = engine.states[GameStates.TRADING]
    window = pygame.Rect(0, 0, *size)
    for rects in (state.market_list.rects, state.cargo_list.rects):
        assert rects and all(window.contains(r) for r in rects.values())
    assert all(window.contains(r) for r in state.buttons.rects)
    assert max(r.bottom for r in state.market_list.rects.values()) < min(r.top for r in state.buttons.rects)
    assert not any(a.colliderect(b) for a, b in zip(state.buttons.rects, state.buttons.rects[1:]))


def test_trading_with_the_mouse_selects_buys_and_sells(engine):
    from src.states.game_state import GameStates

    engine.create_new_universe(seed=4)
    station = engine.universe.stations[0]
    engine.ship.credits = 50000
    engine.change_state(GameStates.TRADING, station)
    engine.fade_remaining = 0
    engine.render()
    state = engine.states[GameStates.TRADING]
    assert state.cargo_list.count == 0

    # pick the third market row and buy it with the Buy button
    commodity = state.available_commodities[2]
    pygame.event.clear()
    pygame.event.post(click(state.market_list.rects[2].center))
    engine.handle_events()
    assert state.selected_commodity_index == 2 and state.viewing_cargo is False
    engine.render()
    credits_before = engine.ship.credits
    pygame.event.post(click(state.buttons.rects[0].center))
    engine.handle_events()
    assert engine.ship.credits < credits_before
    assert engine.ship.cargo_hold.get_cargo_items()[0][0].id == commodity.id

    # the cargo row is now clickable; Sell sells it back
    engine.render()
    pygame.event.post(click(state.cargo_list.rects[0].center))
    engine.handle_events()
    assert state.viewing_cargo is True
    engine.render()
    pygame.event.post(click(state.buttons.rects[1].center))
    engine.handle_events()
    assert engine.ship.cargo_hold.get_cargo_items() == []


def test_the_sell_button_is_disabled_on_the_market_side_and_leave_exits(engine):
    from src.states.game_state import GameStates

    engine.create_new_universe(seed=4)
    engine.change_state(GameStates.TRADING, engine.universe.stations[0])
    engine.fade_remaining = 0
    engine.render()
    state = engine.states[GameStates.TRADING]
    assert state.buttons.enabled == [True, False, True, True]
    pygame.event.clear()
    pygame.event.post(click(state.buttons.rects[1].center))                # disabled: nothing happens
    engine.handle_events()
    assert engine.current_state == GameStates.TRADING
    pygame.event.post(click(state.buttons.rects[3].center))
    engine.handle_events()
    assert engine.current_state == GameStates.PLAYING


def test_the_trading_keys_still_work(engine):
    from src.states.game_state import GameStates

    engine.create_new_universe(seed=4)
    engine.change_state(GameStates.TRADING, engine.universe.stations[0])
    state = engine.states[GameStates.TRADING]
    state.handle_input(key(pygame.K_DOWN))
    assert state.selected_commodity_index == 1
    state.handle_input(key(pygame.K_TAB))
    assert state.viewing_cargo is True and state.selected_commodity_index == 0
    state.handle_input(pygame.event.Event(pygame.MOUSEWHEEL, y=-1, x=0))
    state.handle_input(key(pygame.K_ESCAPE))
    assert engine.current_state == GameStates.PLAYING


@pytest.mark.parametrize("size", SIZES)
def test_the_upgrade_screen_fits_every_window_size(engine, size):
    from src.states.game_state import GameStates

    pygame.display.set_mode(size, pygame.RESIZABLE)
    engine._on_window_resized()
    engine.create_new_universe(seed=4)
    engine.ship.credits = 50000
    engine.change_state(GameStates.UPGRADES, _shipyard())
    engine.fade_remaining = 0
    state = engine.states[GameStates.UPGRADES]
    window = pygame.Rect(0, 0, *size)
    for viewing in (True, False):
        state.viewing_categories = viewing
        engine.render()
        assert state.list.rects and all(window.contains(r) for r in state.list.rects.values())
        bar = state.category_buttons if viewing else state.upgrade_buttons
        assert all(window.contains(r) for r in bar.rects)


def test_upgrades_by_mouse_open_a_category_then_buy_an_upgrade(engine):
    from src.states.game_state import GameStates

    engine.create_new_universe(seed=4)
    engine.ship.credits = 50000
    engine.change_state(GameStates.UPGRADES, _shipyard())
    engine.fade_remaining = 0
    engine.render()
    state = engine.states[GameStates.UPGRADES]
    assert state.viewing_categories

    pygame.event.clear()
    pygame.event.post(click(state.list.rects[0].center))                    # a category: opens it
    engine.handle_events()
    assert state.viewing_categories is False
    engine.render()

    credits_before = engine.ship.credits
    pygame.event.post(click(state.upgrade_buttons.rects[0].center))         # Buy
    engine.handle_events()
    assert engine.ship.credits < credits_before

    engine.render()
    pygame.event.post(click(state.upgrade_buttons.rects[1].center))         # Back
    engine.handle_events()
    assert state.viewing_categories is True


# --- settings --------------------------------------------------------------------------------

@pytest.fixture
def settings_screen(engine, monkeypatch):
    """The settings screen with the real settings restored afterwards and no
    window re-creation when display options change."""
    from src.settings import game_settings
    from src.states.game_state import GameStates

    saved = dict(vars(game_settings))
    monkeypatch.setattr(game_settings, "save", lambda *a, **k: None)
    monkeypatch.setattr(engine, "_update_display", lambda: None)
    engine.change_state(GameStates.SETTINGS)
    engine.fade_remaining = 0
    yield engine.states[GameStates.SETTINGS]
    vars(game_settings).update(saved)


def _open(engine, state, page):
    state.page = page
    engine.render()


@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize("page", [None, "camera", "display", "controls", "audio", "difficulty", "dev", "help"])
def test_every_settings_page_fits_every_window_size(engine, settings_screen, size, page):
    pygame.display.set_mode(size, pygame.RESIZABLE)
    engine._on_window_resized()
    window = pygame.Rect(0, 0, *size)
    _open(engine, settings_screen, page)
    rects = (settings_screen.category_menu.rects if page is None else settings_screen.list.rects).values()
    assert rects and all(window.contains(r) for r in rects)
    assert all(not a.colliderect(b) for a, b in zip(list(rects), list(rects)[1:]))


def test_the_category_menu_opens_pages_by_keyboard_and_mouse(engine, settings_screen):
    state = settings_screen
    engine.render()
    pygame.event.clear()
    pygame.event.post(click(state.category_menu.rects[3].center))              # Audio
    engine.handle_events()
    assert state.page == "audio"
    state.handle_input(key(pygame.K_ESCAPE))
    assert state.page is None
    state.selected_category = 1
    state.handle_input(key(pygame.K_RETURN))
    assert state.page == "display"


def test_escape_leaves_settings_to_where_it_was_opened_from(engine, settings_screen):
    from src.states.game_state import GameStates
    settings_screen.previous_state = GameStates.PAUSED
    settings_screen.handle_input(key(pygame.K_ESCAPE))
    assert engine.current_state == GameStates.PAUSED


def test_left_and_right_change_values_on_every_page(engine, settings_screen):
    from src.settings import CameraMode
    from src.difficulty.difficulty_manager import difficulty_manager
    state, s = settings_screen, engine.settings
    original_level = difficulty_manager.current_difficulty

    state.page = "camera"
    s.camera_mode = CameraMode.CENTERED
    state.handle_input(key(pygame.K_RIGHT))
    assert s.camera_mode != CameraMode.CENTERED
    s.camera_mode = CameraMode.SMOOTH
    state.selected["camera"] = 1
    before = s.camera_smoothing
    state.handle_input(key(pygame.K_RIGHT))
    assert s.camera_smoothing == pytest.approx(before + 0.05) or s.camera_smoothing == 1.0
    s.camera_mode = CameraMode.CENTERED
    state.handle_input(key(pygame.K_RIGHT))                                    # smoothing is N/A now
    assert s.camera_smoothing == pytest.approx(min(1.0, before + 0.05))

    state.page, state.selected["audio"] = "audio", 0
    s.master_volume = 0.5
    state.handle_input(key(pygame.K_RIGHT))
    assert s.master_volume == pytest.approx(0.55)
    state.handle_input(key(pygame.K_LEFT))
    state.handle_input(key(pygame.K_LEFT))
    assert s.master_volume == pytest.approx(0.45)

    state.page = "display"
    state.selected["display"] = 2
    s.hud_scale = 1.0
    state.handle_input(key(pygame.K_RIGHT))
    assert s.hud_scale == pytest.approx(1.1)

    state.page = "difficulty"
    state.handle_input(key(pygame.K_RIGHT))
    assert difficulty_manager.current_difficulty != original_level
    difficulty_manager.set_difficulty(original_level)

    state.page = "dev"
    s.dev_view_enabled = False
    state.selected["dev"] = 0
    state.handle_input(key(pygame.K_RETURN))
    assert s.dev_view_enabled is True
    state.selected["dev"] = 1
    shown = s.dev_show_fps
    state.handle_input(key(pygame.K_RETURN))
    assert s.dev_show_fps is (not shown)
    s.dev_view_enabled = False
    state.handle_input(key(pygame.K_RETURN))                                   # disabled while dev view is off
    assert s.dev_show_fps is (not shown)


def test_clicking_a_value_row_changes_it_and_clicking_back_leaves_the_page(engine, settings_screen):
    state, s = settings_screen, engine.settings
    s.master_volume = 0.5
    _open(engine, state, "audio")
    rect = state.list.rects[0]
    pygame.event.clear()
    pygame.event.post(click((rect.right - 10, rect.centery)))                  # right half raises
    engine.handle_events()
    assert s.master_volume == pytest.approx(0.55)
    pygame.event.post(click((rect.left + 10, rect.centery)))                   # left half lowers
    engine.handle_events()
    assert s.master_volume == pytest.approx(0.5)
    engine.render()
    pygame.event.post(click(state.list.rects[3].center))                       # Back
    engine.handle_events()
    assert state.page is None


def test_a_disabled_row_ignores_clicks_and_keys(engine, settings_screen):
    from src.settings import CameraMode
    state, s = settings_screen, engine.settings
    s.camera_mode = CameraMode.CENTERED
    s.camera_deadzone_radius = 100
    state.page, state.selected["camera"] = "camera", 2
    state.handle_input(key(pygame.K_RIGHT))
    assert s.camera_deadzone_radius == 100


def test_the_control_scheme_can_be_cycled_and_the_reference_panel_follows(engine, settings_screen):
    from src.input.control_schemes import control_scheme_manager
    state = settings_screen
    first = control_scheme_manager.get_current_scheme()
    state.page = "controls"
    state.handle_input(key(pygame.K_RIGHT))
    assert control_scheme_manager.get_current_scheme() != first
    engine.render()                                                             # draws the new bindings
    state.handle_input(key(pygame.K_LEFT))
    assert control_scheme_manager.get_current_scheme() == first


def test_up_and_down_move_through_a_pages_rows_and_wrap(engine, settings_screen):
    state = settings_screen
    state.page = "camera"
    state.selected["camera"] = 0
    state.handle_input(key(pygame.K_DOWN))
    assert state.selected["camera"] == 1
    state.handle_input(key(pygame.K_UP))
    state.handle_input(key(pygame.K_UP))
    assert state.selected["camera"] == len(state.rows("camera")) - 1          # wrapped to Back
    state.handle_input(key(pygame.K_RETURN))
    assert state.page is None


# --- mission board -----------------------------------------------------------------------------

@pytest.fixture
def board(engine):
    """A mission board over a fresh mission manager (it is a process-wide
    singleton), put back as it was afterwards."""
    import copy
    from src.states.game_state import GameStates

    manager = engine.mission_manager
    saved = copy.copy(vars(manager))
    engine.create_new_universe(seed=4)
    manager.available_missions, manager.active_missions = [], []
    manager.visited_stations, manager.station_mission_seeds = set(), {}
    manager.reputation = 80
    manager.faction_standing = {name: 80 for name in manager.faction_standing}
    engine.change_state(GameStates.MISSIONS, engine.universe.stations[0])
    engine.fade_remaining = 0
    state = engine.states[GameStates.MISSIONS]
    assert state.available_missions
    yield state
    vars(manager).clear()
    vars(manager).update(saved)


@pytest.mark.parametrize("size", SIZES)
def test_the_mission_board_fits_every_window_size_in_list_and_details(engine, board, size):
    pygame.display.set_mode(size, pygame.RESIZABLE)
    engine._on_window_resized()
    window = pygame.Rect(0, 0, *size)
    for details in (False, True):
        board.viewing_details = details
        engine.render()
        bar = board.detail_buttons if details else board.list_buttons
        assert all(window.contains(r) for r in bar.rects)
        if not details:
            assert board.list.rects and all(window.contains(r) for r in board.list.rects.values())
        assert all(window.contains(r) for r in board.tab_rects.values()) or size[0] < 1100


def test_clicking_the_tabs_switches_between_available_and_active(engine, board):
    engine.render()
    pygame.event.clear()
    pygame.event.post(click(board.tab_rects["active"].center))
    engine.handle_events()
    assert board.current_tab == "active"
    engine.render()
    pygame.event.post(click(board.tab_rects["available"].center))
    engine.handle_events()
    assert board.current_tab == "available"


def test_a_second_click_on_a_mission_opens_its_details_and_accept_works_by_button(engine, board):
    engine.render()
    pygame.event.clear()
    pygame.event.post(click(board.list.rects[1].center))
    engine.handle_events()
    assert board.selected_mission_index == 1 and board.viewing_details is False
    pygame.event.post(click(board.list.rects[1].center))
    engine.handle_events()
    assert board.viewing_details is True

    wanted = board.available_missions[1].id
    engine.render()
    pygame.event.post(click(board.detail_buttons.rects[0].center))             # Accept
    engine.handle_events()
    assert any(m.id == wanted for m in engine.mission_manager.active_missions)
    assert board.current_tab == "active"


def test_abandon_by_button_and_back_to_the_list(engine, board):
    board.handle_input(key(pygame.K_a))                                        # accept the first mission
    assert board.current_tab == "active" and board.active_missions, board.message
    board.viewing_details = True
    engine.render()
    assert board.detail_buttons.enabled == [False, True, True]
    pygame.event.clear()
    pygame.event.post(click(board.detail_buttons.rects[1].center))             # Abandon
    engine.handle_events()
    assert not board.active_missions
    engine.render()
    pygame.event.post(click(board.detail_buttons.rects[2].center))             # Back
    engine.handle_events()
    assert board.viewing_details is False


def test_the_keyboard_still_drives_the_board(engine, board):
    from src.states.game_state import GameStates

    board.handle_input(key(pygame.K_DOWN))
    assert board.selected_mission_index == 1
    board.handle_input(key(pygame.K_TAB))
    assert board.current_tab == "active"
    board.handle_input(key(pygame.K_TAB))
    board.handle_input(key(pygame.K_RETURN))
    assert board.viewing_details
    board.handle_input(key(pygame.K_ESCAPE))
    assert not board.viewing_details
    board.handle_input(key(pygame.K_ESCAPE))
    assert engine.current_state == GameStates.PLAYING


def test_long_mission_text_wraps_inside_the_panel_and_scrolls(engine, board):
    mission = board.available_missions[0]
    mission.description = "A very long briefing that keeps going. " * 40
    pygame.display.set_mode((1024, 640), pygame.RESIZABLE)
    engine._on_window_resized()
    board.viewing_details = True
    engine.render()
    ui = board._ui
    lines = board._detail_lines(ui, mission, 900)
    assert len(lines) > 12
    assert all(ui.font(role).size(text)[0] <= 900 for text, role, _, _ in lines)
    start = board.detail_scroll
    board.handle_input(key(pygame.K_DOWN))
    board.handle_input(key(pygame.K_DOWN))
    engine.render()
    assert board.detail_scroll == start + 2
    for _ in range(200):
        board.handle_input(key(pygame.K_DOWN))
    engine.render()
    last = board.detail_scroll
    engine.render()
    assert board.detail_scroll == last                                         # clamped, not running away
    board.handle_input(key(pygame.K_PAGEUP))
    assert board.detail_scroll < last
