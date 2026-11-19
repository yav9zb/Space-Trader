"""Resizing the window (dragging it, zooming it, macOS fullscreen) must
re-lay-out the whole game without re-creating the window."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from src import display
from src.settings import DisplayMode, Settings


class Clock:
    def get_time(self): return 16
    def tick(self, *a): return 16
    def get_fps(self): return 60.0


@pytest.fixture
def engine():
    from src.engine.game_engine import GameEngine
    from src.states.game_state import GameStates

    game = GameEngine()
    game.clock = Clock()
    game.create_new_universe(seed=4)
    game.change_state(GameStates.PLAYING)
    return game


def resize_window(game, size):
    """What happens when the user drags the window: pygame resizes the surface
    in place and posts an event."""
    pygame.display.set_mode(size, pygame.RESIZABLE)
    game._on_window_resized()


def test_resizing_relays_out_the_hud_radar_camera_map_and_stars(engine):
    from src.states.game_state import GameStates
    resize_window(engine, (1600, 900))

    assert engine.WINDOW_SIZE == (1600, 900)
    assert engine.minimap.screen_width == 1600 and engine.minimap.rect.right <= 1600
    assert (engine.camera.width, engine.camera.height) == (1600, 900)
    assert engine.starfield.screen_width == 1600 and engine.starfield.screen_height == 900
    playing = engine.states[GameStates.PLAYING]
    assert playing.enhanced_hud.screen_width == 1600
    assert playing.large_map.screen_width == 1600
    assert len(engine.starfield.stars) > 100                                 # more stars for more room


def test_the_new_size_is_remembered_in_windowed_mode_only(engine):
    engine.settings.display_mode = DisplayMode.WINDOWED
    resize_window(engine, (1500, 880))
    assert (engine.settings.window_width, engine.settings.window_height) == (1500, 880)

    engine.settings.display_mode = DisplayMode.FULLSCREEN
    resize_window(engine, (1400, 800))
    assert (engine.settings.window_width, engine.settings.window_height) == (1500, 880)    # windowed choice kept
    engine.settings.display_mode = DisplayMode.WINDOWED


def test_repeated_resize_events_for_the_same_size_do_no_work(engine, monkeypatch):
    resize_window(engine, (1300, 800))
    calls = []
    monkeypatch.setattr(engine, "_relayout", lambda: calls.append(1))
    engine._on_window_resized()
    engine._on_window_resized()
    assert calls == []


def test_resize_events_are_handled_by_the_event_loop_without_recreating_the_window(engine, monkeypatch):
    created = []
    real = pygame.display.set_mode
    monkeypatch.setattr(pygame.display, "set_mode", lambda *a, **k: created.append(a) or real(*a, **k))
    pygame.display.set_mode((1250, 780), pygame.RESIZABLE)
    created.clear()
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.WINDOWSIZECHANGED, x=1250, y=780))
    engine.handle_events()
    assert engine.WINDOW_SIZE == (1250, 780)
    assert created == []                                                     # no set_mode on a resize


@pytest.mark.parametrize("size", [(1024, 640), (1280, 800), (1512, 945), (1920, 1080), (2560, 1440), (3440, 1440)])
def test_a_resized_hud_still_has_no_overlaps_at_any_size(engine, size):
    from src.states.game_state import GameStates
    resize_window(engine, size)
    surface = pygame.Surface(size)
    hud = engine.states[GameStates.PLAYING].enhanced_hud
    hud.update(0.016, engine)
    hud.render(surface, engine)
    areas = {a["name"]: pygame.Rect(a["x"], a["y"], a["width"], a["height"]) for a in hud.ui_layout.reserved_areas}
    names = list(areas)
    for i, a in enumerate(names):
        assert pygame.Rect(0, 0, *size).contains(areas[a]) or a == "mission_tracker" and size[1] < 700, (size, a)
        for b in names[i + 1:]:
            assert not areas[a].colliderect(areas[b]), (size, a, b)
    assert not areas.get("mission_tracker", pygame.Rect(0, 0, 0, 0)).colliderect(engine.minimap.rect)


# --- creating the window -------------------------------------------------------------------

def make(monkeypatch, desktop, mac=True):
    monkeypatch.setattr(display, "desktop_size", lambda index=0: desktop)
    monkeypatch.setattr(display, "is_macos", lambda: mac)
    return Settings()


def test_the_windowed_size_is_clamped_to_the_screen_when_the_window_is_created(monkeypatch):
    settings = make(monkeypatch, (1512, 982))
    settings.window_width, settings.window_height = 3000, 2000
    surface = settings.apply_display_settings(None)
    usable = display.usable_area((1512, 982), mac=True)
    assert surface.get_size() == usable and (settings.window_width, settings.window_height) == usable


def test_a_tiny_saved_size_is_raised_to_the_minimum(monkeypatch):
    settings = make(monkeypatch, (2560, 1440))
    settings.window_width, settings.window_height = 300, 200
    assert settings.apply_display_settings(None).get_size() == display.MIN_SIZE


@pytest.mark.parametrize("mode", [DisplayMode.FULLSCREEN, DisplayMode.BORDERLESS])
def test_on_a_mac_fullscreen_fills_the_usable_screen_and_keeps_the_windowed_size(monkeypatch, mode):
    settings = make(monkeypatch, (1728, 1117))
    settings.window_width, settings.window_height = 1280, 800
    settings.display_mode = mode
    surface = settings.apply_display_settings(None)
    assert surface.get_size() == display.usable_area((1728, 1117), mac=True)
    assert (settings.window_width, settings.window_height) == (1280, 800)      # windowed preference untouched


def test_the_resolution_menu_never_offers_a_size_that_does_not_fit(monkeypatch):
    for desktop in ((1470, 956), (1512, 982), (2560, 1440), (3440, 1440)):
        settings = make(monkeypatch, desktop)
        usable = display.usable_area(desktop, mac=True)
        assert all(w <= usable[0] and h <= usable[1] for w, h in settings.available_resolutions), desktop


def test_creating_the_window_twice_and_pumping_events_does_not_crash(monkeypatch):
    """Setting a minimum size through pygame._sdl2's Window wrapper left a
    dangling window handle: the next set_mode followed by an event pump killed
    the process with a bus error. A crash cannot be caught, so this simply has
    to keep running."""
    settings = make(monkeypatch, (1728, 1117))
    for _ in range(3):
        settings.apply_display_settings(None)
        pygame.event.pump()
        pygame.event.get()
    settings.display_mode = DisplayMode.FULLSCREEN
    settings.apply_display_settings(None)
    pygame.event.get()
    settings.display_mode = DisplayMode.WINDOWED
