import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from src.ui import screen_scaler as ss


class Clock:
    def get_time(self): return 16
    def tick(self, *a): return 16
    def get_fps(self): return 60.0


def test_the_scale_table_for_common_mac_window_heights():
    expected = {
        560: 0.7, 640: 0.8, 720: 0.9, 800: 1.0, 828: 1.0, 945: 1.0, 999: 1.0, 1000: 1.25,
        1080: 1.25, 1117: 1.25, 1200: 1.5, 1329: 1.5, 1440: 1.75, 1800: 2.0, 2160: 2.5, 2880: 3.0,
    }
    for height, scale in expected.items():
        assert ss.scale_for((1920, height)) == pytest.approx(scale), height


def test_the_logical_screen_is_never_shorter_than_the_design_height():
    for height in (480, 640, 799, 800, 900, 1080, 1440, 2160, 2880):
        for width in (1024, 1512, 2560, 3440):
            logical_w, logical_h = ss.logical_size((width, height))
            assert logical_h >= ss.DESIGN_HEIGHT - 1, (width, height)
            assert logical_w >= 320


def test_the_logical_screen_keeps_the_windows_aspect_ratio():
    for window in ((1512, 945), (2560, 1440), (3440, 1440), (1024, 640)):
        w, h = ss.logical_size(window)
        assert abs(w / h - window[0] / window[1]) < 0.01


def test_scale_never_makes_text_smaller_than_the_design_on_a_roomy_window_and_only_shrinks_a_short_one():
    for height in range(800, 3000, 50):
        assert ss.scale_for((2000, height)) >= 1.0
    for height in range(400, 800, 40):
        assert ss.scale_for((2000, height)) < 1.0


def test_mouse_positions_map_back_to_logical_coordinates():
    scaler = ss.ScreenScaler()
    scaler.active, scaler.scale = True, 1.75
    assert scaler.to_logical((1750, 875)) == (1000, 500)
    scaler.active = False
    assert scaler.to_logical((1750, 875)) == (1750, 875)                 # unscaled screens: untouched
    scaler.active, scaler.scale = True, 1.0
    assert scaler.to_logical((33, 44)) == (33, 44)


def test_mouse_events_are_mapped_and_other_events_are_not():
    scaler = ss.ScreenScaler()
    scaler.active, scaler.scale = True, 2.0
    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(400, 300), button=1)
    motion = pygame.event.Event(pygame.MOUSEMOTION, pos=(400, 300), rel=(10, -6), buttons=(0, 0, 0))
    key = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)
    assert scaler.map_event(click).pos == (200, 150) and scaler.map_event(click).button == 1
    assert scaler.map_event(motion).pos == (200, 150) and scaler.map_event(motion).rel == (5, -3)
    assert scaler.map_event(key) is key
    scaler.active = False
    assert scaler.map_event(click) is click


def test_get_pos_reports_logical_coordinates_only_while_a_scaled_screen_is_active(monkeypatch):
    monkeypatch.setattr(ss, "_real_get_pos", lambda: (1000, 600))
    scaler = ss.ScreenScaler()
    scaler.active, scaler.scale = True, 2.0
    assert scaler.mouse_pos() == (500, 300)
    scaler.active = False
    assert scaler.mouse_pos() == (1000, 600)


class Recorder:
    def __init__(self):
        self.seen_size = None

    def render(self, surface):
        self.seen_size = surface.get_size()
        surface.fill((10, 20, 30))
        pygame.draw.rect(surface, (255, 0, 0), (0, 0, 40, 40))


def test_a_scaled_screen_is_drawn_at_the_logical_size_and_fills_the_window():
    scaler = ss.ScreenScaler()
    window = pygame.Surface((2560, 1440))
    state = Recorder()
    scaler.prepare(window, True)
    scaler.render(state, window)

    assert state.seen_size == ss.logical_size((2560, 1440)) == (1463, 823)
    assert window.get_at((2000, 1200))[:3] == (10, 20, 30)               # filled everywhere
    assert window.get_at((20, 20))[0] > 200                              # the logical corner square, scaled up
    assert window.get_at((90, 90))[:3] != (255, 0, 0)                    # and it grew: 40px became about 70


def test_a_window_at_the_design_size_is_drawn_directly_with_no_scaling():
    scaler = ss.ScreenScaler()
    window = pygame.Surface((1200, 850))
    state = Recorder()
    scaler.prepare(window, True)
    scaler.render(state, window)
    assert state.seen_size == (1200, 850)


def test_a_short_window_is_drawn_larger_then_shrunk_so_nothing_is_cut_off():
    scaler = ss.ScreenScaler()
    window = pygame.Surface((1024, 640))
    state = Recorder()
    scaler.prepare(window, True)
    scaler.render(state, window)
    assert state.seen_size == (1280, 800)
    assert all(abs(a - b) <= 4 for a, b in zip(window.get_at((1000, 600))[:3], (10, 20, 30)))   # smoothing


# --- in the real engine ------------------------------------------------------------------

@pytest.fixture
def engine():
    from src.engine.game_engine import GameEngine
    game = GameEngine()
    game.clock = Clock()
    return game


def test_clicking_a_menu_option_works_at_a_large_window_size(engine, monkeypatch):
    from src.states.game_state import GameStates

    pygame.display.set_mode((2560, 1440), pygame.RESIZABLE)
    engine._on_window_resized()
    engine.change_state(GameStates.MAIN_MENU)
    engine.render()
    menu = engine.states[GameStates.MAIN_MENU]
    settings_rect = menu.option_rects[2]                                   # window pixels: nothing is scaled

    pygame.event.clear()
    window_pos = settings_rect.center
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=window_pos, button=1))
    engine.handle_events()
    assert engine.current_state == GameStates.SETTINGS


def test_clicking_the_same_place_on_a_short_window_also_works(engine, monkeypatch):
    from src.states.game_state import GameStates

    pygame.display.set_mode((1024, 640), pygame.RESIZABLE)
    engine._on_window_resized()
    engine.change_state(GameStates.MAIN_MENU)
    engine.render()
    menu = engine.states[GameStates.MAIN_MENU]
    rect = menu.option_rects[1]                                            # Load Game
    pygame.event.clear()
    window_pos = rect.center
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=window_pos, button=1))
    engine.handle_events()
    assert engine.current_state == GameStates.LOAD_GAME


def test_flight_is_never_scaled(engine):
    from src.states.game_state import GameStates

    pygame.display.set_mode((2560, 1440), pygame.RESIZABLE)
    engine._on_window_resized()
    engine.create_new_universe(seed=4)
    engine.change_state(GameStates.PLAYING)
    engine.render()
    assert ss.scaler.active is False and ss.scaler.scale == 1.0
    assert engine.states[GameStates.PLAYING].enhanced_hud.screen_width == 2560   # real window pixels


def test_every_scaled_screen_renders_at_every_mac_window_size(engine):
    from src.states.game_state import GameStates
    from src.engine.game_engine import SCALED_STATES

    engine.create_new_universe(seed=4)
    station = engine.universe.stations[0]
    for size in ((1024, 640), (1280, 720), (1470, 956), (1728, 1117), (2560, 1440), (3440, 1440)):
        pygame.display.set_mode(size, pygame.RESIZABLE)
        engine._on_window_resized()
        for state in SCALED_STATES:
            if state in (GameStates.TRADING, GameStates.UPGRADES, GameStates.MISSIONS):
                engine.change_state(state, station)
            elif state == GameStates.DIALOGUE:
                engine.start_dialogue("hale_intro")
            else:
                engine.change_state(state)
            engine.render()
            assert engine.screen.get_size() == size


@pytest.mark.parametrize("size", [(1024, 640), (1512, 945), (2560, 1440), (3440, 1440)])
def test_the_pause_menu_fits_the_window_and_the_world_behind_it_is_not_scaled(engine, monkeypatch, size):
    from src.states.game_state import GameStates

    pygame.display.set_mode(size, pygame.RESIZABLE)
    engine._on_window_resized()
    engine.create_new_universe(seed=4)
    engine.change_state(GameStates.PLAYING)
    engine.change_state(GameStates.PAUSED)
    engine.render()
    pause = engine.states[GameStates.PAUSED]

    # the HUD behind the menu was laid out for the real window, not the logical one
    assert engine.states[GameStates.PLAYING].enhanced_hud.screen_width == size[0]
    assert len(pause.option_rects) == 5
    assert all(pygame.Rect(0, 0, *size).contains(r) for r in pause.option_rects)

    # clicking "Main Menu" (the last option) at its on-screen position works
    window_pos = pause.option_rects[4].center
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=window_pos, button=1))
    engine.handle_events()
    assert engine.current_state == GameStates.MAIN_MENU


def test_overlay_drawing_composites_a_transparent_layer_over_what_is_underneath():
    scaler = ss.ScreenScaler()
    window = pygame.Surface((2560, 1440))
    window.fill((0, 80, 0))

    def draw(layer):
        pygame.draw.rect(layer, (255, 0, 0), (0, 0, 100, 100))                  # only this square

    scaler.prepare(window, True)
    scaler.draw_overlay(draw, window)
    assert window.get_at((50, 50))[0] > 200                                      # the layer shows
    assert window.get_at((2000, 1200))[:3] == (0, 80, 0)                         # the world shows through elsewhere
