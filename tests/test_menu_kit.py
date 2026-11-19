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
