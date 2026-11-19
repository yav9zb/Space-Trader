"""The Retina path: a point-sized surface for the game, scaled onto a pixel
surface with the HUD, radar and notifications drawn on top at full resolution.
A fake high-density window stands in for the real one so this runs anywhere."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest
from pygame import Vector2

from src import hidpi
from src.ui.hud import panel_kit
from src.ui.ui_theme import UIElementType


class FakeWindow:
    """What pygame.Window(..., allow_high_dpi=True) gives on a 2x display."""
    RATIO = 2

    def __init__(self, title, size, resizable=True):
        self.title, self._size, self.resizable = title, tuple(size), resizable
        self._surface = None
        self.flips = 0
        self.position = (0, 0)

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = tuple(value)

    def get_surface(self):
        want = (self._size[0] * self.RATIO, self._size[1] * self.RATIO)
        if self._surface is None or self._surface.get_size() != want:
            self._surface = pygame.Surface(want)
        return self._surface

    def flip(self):
        self.flips += 1

    def set_icon(self, icon):
        pass


@pytest.fixture
def retina(monkeypatch):
    hidpi.reset()
    monkeypatch.setattr(hidpi, "wanted", lambda: True)
    monkeypatch.setattr(hidpi, "make_window", lambda title, size, resizable=True: FakeWindow(title, size, resizable))
    yield
    hidpi.reset()


class Clock:
    def get_time(self): return 16
    def tick(self, *a): return 16
    def get_fps(self): return 60.0


@pytest.fixture
def engine(retina):
    from src.engine.game_engine import GameEngine
    from src.states.game_state import GameStates

    game = GameEngine()
    game.clock = Clock()
    game.create_new_universe(seed=4)
    game.change_state(GameStates.PLAYING)
    return game


# --- the presenter -------------------------------------------------------------------------

def test_the_presenter_scales_the_frame_draws_layers_at_full_resolution_and_shows_it():
    window = FakeWindow("t", (400, 300))
    presenter = hidpi.Presenter(window)
    frame = presenter.sync()
    assert frame.get_size() == (400, 300)
    frame.fill((0, 80, 0))
    seen = []

    def layer(pixels, ratio):
        seen.append((pixels.get_size(), ratio))
        pygame.draw.rect(pixels, (255, 0, 0), (0, 0, 20, 20))

    presenter.queue(layer)
    presenter.present()

    pixels = window.get_surface()
    assert seen == [((800, 600), 2.0)]
    assert pixels.get_at((400, 300))[:3] == (0, 80, 0)                      # the frame, scaled up
    assert pixels.get_at((10, 10))[:3] == (255, 0, 0)                       # the layer, in real pixels
    assert window.flips == 1 and presenter.layers == []                     # shown, and layers are one-shot


def test_the_pause_veil_goes_over_the_frame_and_layers_but_under_the_top_layers():
    window = FakeWindow("t", (200, 200))
    presenter = hidpi.Presenter(window)
    presenter.sync().fill((200, 200, 200))
    presenter.queue(lambda p, r: pygame.draw.rect(p, (200, 200, 200), (0, 0, 40, 40)))
    presenter.queue(lambda p, r: pygame.draw.rect(p, (255, 255, 255), (100, 100, 20, 20)), on_top=True)
    presenter.veil_alpha = 128
    presenter.present()

    pixels = window.get_surface()
    assert pixels.get_at((300, 300))[0] < 130                               # the frame is dimmed
    assert pixels.get_at((10, 10))[0] < 130                                 # and so is a layer under the veil
    assert pixels.get_at((110, 110))[:3] == (255, 255, 255)                 # the top layer is not
    assert presenter.veil_alpha == 0                                        # one-shot


def test_resizing_the_window_gives_a_new_point_surface_and_pixel_surface():
    window = FakeWindow("t", (400, 300))
    presenter = hidpi.Presenter(window)
    first = presenter.sync()
    window.size = (500, 320)
    second = presenter.sync()
    assert second.get_size() == (500, 320) and second is not first
    assert window.get_surface().get_size() == (1000, 640) and presenter.ratio == 2.0


def test_it_is_only_wanted_on_a_real_high_density_display(monkeypatch):
    hidpi.reset()
    assert hidpi.wanted() is False                                          # the headless driver
    monkeypatch.setenv("SPACETRADER_HIDPI", "0")
    assert hidpi.wanted() is False                                          # switched off


def test_if_the_high_density_window_cannot_be_made_the_standard_display_is_used(monkeypatch):
    from src.settings import Settings

    hidpi.reset()
    monkeypatch.setattr(hidpi, "wanted", lambda: True)

    def boom(*args, **kwargs):
        raise RuntimeError("no high-dpi here")
    monkeypatch.setattr(hidpi, "make_window", boom)
    surface = Settings().apply_display_settings(None)
    assert surface is not None and hidpi.get_presenter() is None
    pygame.display.get_surface()                                            # a normal pygame display exists
    hidpi.reset()


# --- the engine on the Retina path ---------------------------------------------------------------

def test_the_engine_draws_into_a_point_surface_and_presents_at_full_resolution(engine):
    from src.states.game_state import GameStates

    presenter = engine.presenter
    assert presenter is not None
    assert engine.screen is presenter.point_surface
    assert engine.screen.get_size() == presenter.points == engine.WINDOW_SIZE

    engine.render()
    pixels = presenter.pixel_surface
    assert pixels.get_size() == (engine.WINDOW_SIZE[0] * 2, engine.WINDOW_SIZE[1] * 2)
    assert presenter.window.flips == 1


def test_the_hud_is_drawn_at_full_resolution_not_scaled_up(engine):
    """The panels must appear on the pixel surface at twice the point layout,
    and must not also be on the point surface (where they would be blurred)."""
    from src.states.game_state import GameStates

    playing = engine.states[GameStates.PLAYING]
    engine.update()
    engine.render()
    pixels = engine.presenter.pixel_surface
    sharp_rects = {a["name"]: pygame.Rect(a["x"], a["y"], a["width"], a["height"])
                   for a in playing._sharp_hud.ui_layout.reserved_areas}
    assert {"ship_status", "navigation"} <= set(sharp_rects)

    # point-resolution layout of the same panels, for comparison
    point_hud = playing.enhanced_hud
    point_hud.update(0.016, engine)
    point_rects = {name: rect for _, name, rect in point_hud._left_column(engine)}
    for name in ("ship_status", "navigation"):
        sharp, point = sharp_rects[name], point_rects[name]
        assert abs(sharp.width - 2 * point.width) <= 0.2 * 2 * point.width, name         # about double
        assert abs(sharp.height - 2 * point.height) <= 0.2 * 2 * point.height, name

    panel = sharp_rects["ship_status"]
    assert sum(pixels.get_at((panel.x + 14, panel.y + 14))[:3]) > 0            # panel chrome is there


def test_the_point_surface_does_not_carry_the_panels(engine):
    """With the sharp layer on, flight must not draw the (blurry) panels too."""
    from src.states.game_state import GameStates

    engine.update()
    engine.render()
    playing = engine.states[GameStates.PLAYING]
    assert playing.enhanced_hud.ui_layout.reserved_areas == []              # render_panels never ran on this HUD


def test_notifications_are_drawn_sharp_only(engine):
    from src.ui.notifications import notifications

    notifications.clear()
    notifications.push("Hello there", duration=5.0)
    engine.fade_remaining = 0.0                     # a screen change's fade-in would dim it
    engine.update()
    engine.render()
    pixels = engine.presenter.pixel_surface
    w = pixels.get_width()
    lit = sum(1 for x in range(w // 2 - 200, w // 2 + 200) for y in range(120, 220)
              if sum(pixels.get_at((x, y))[:3]) > 300)
    assert lit > 30
    notifications.clear()


def test_resizing_rebuilds_the_surfaces_and_the_sharp_layout(engine):
    from src.states.game_state import GameStates

    engine.render()
    window = engine.presenter.window
    window.size = (1500, 900)
    engine._on_window_resized()
    assert engine.WINDOW_SIZE == (1500, 900) and engine.screen.get_size() == (1500, 900)
    engine.update()
    engine.render()
    assert engine.presenter.pixel_surface.get_size() == (3000, 1800)
    assert engine.states[GameStates.PLAYING]._sharp_key == ((3000, 1800), 2.0)


@pytest.mark.parametrize("size", [(1024, 640), (1280, 800), (1512, 945), (2560, 1440)])
def test_the_sharp_panels_never_overlap_or_leave_the_window(engine, size):
    from src.states.game_state import GameStates

    window = engine.presenter.window
    window.size = size
    engine._on_window_resized()
    engine.update()
    engine.render()
    playing = engine.states[GameStates.PLAYING]
    hud = playing._sharp_hud
    pixels_rect = pygame.Rect(0, 0, size[0] * 2, size[1] * 2)
    areas = {a["name"]: pygame.Rect(a["x"], a["y"], a["width"], a["height"]) for a in hud.ui_layout.reserved_areas}
    for name, rect in areas.items():
        assert pixels_rect.contains(rect) or (name == "mission_tracker" and size[1] < 700), (size, name)
    names = list(areas)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            assert not areas[a].colliderect(areas[b]), (size, a, b)
    radar = playing._sharp_radar.rect
    assert not areas["mission_tracker"].colliderect(radar) if "mission_tracker" in areas else True


def test_pausing_dims_the_sharp_frame_and_the_menu_works_with_point_mouse_coordinates(engine, monkeypatch):
    from src.states.game_state import GameStates
    from src.ui import screen_scaler as ss

    engine.update()
    engine.render()
    playing_px = engine.presenter.pixel_surface.copy()

    engine.change_state(GameStates.PAUSED)
    engine.render()
    paused_px = engine.presenter.pixel_surface
    probe = (engine.presenter.pixel_surface.get_width() - 40, engine.presenter.pixel_surface.get_height() - 40)
    assert sum(paused_px.get_at(probe)[:3]) <= sum(playing_px.get_at(probe)[:3])

    pause = engine.states[GameStates.PAUSED]
    scale = ss.scale_for(engine.WINDOW_SIZE)
    rect = pause.option_rects[4]                                            # Main Menu, in pixels
    ratio = engine.presenter.ratio
    window_pos = (int(rect.centerx / ratio), int(rect.centery / ratio))     # points, as the mouse reports
    monkeypatch.setattr(ss, "_real_get_pos", lambda: window_pos)
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=window_pos, button=1))
    engine.handle_events()
    assert engine.current_state == GameStates.MAIN_MENU


def test_menus_still_render_through_the_presenter(engine):
    from src.states.game_state import GameStates

    for state in (GameStates.MAIN_MENU, GameStates.SETTINGS, GameStates.LOGBOOK):
        engine.change_state(state)
        engine.render()
    assert engine.presenter.window.flips >= 3


# --- the pieces at full resolution -------------------------------------------------------------------

def metrics(ratio):
    pygame.font.init()
    return panel_kit.make_metrics(1.0, ratio)


def test_a_panel_at_twice_the_ratio_is_about_twice_as_big_and_still_fits_inside_its_rectangle():
    def build(ratio):
        m = metrics(ratio)
        panel = panel_kit.Panel("SHIP STATUS", UIElementType.SHIP_STATUS, (150, 175, 255), m, round(220 * ratio))
        panel.stat("Credits", "12,345", icon="credits")
        panel.bar("hull", "HULL", "50/100", 0.5, panel_kit.GREEN)
        panel.chip("READY", panel_kit.GREEN, label="BOOST")
        panel.grid([("LASER", "50", 0.5, panel_kit.BLUE)] * 4)
        panel.entry("Mission title", "1h 2m", "-> Station", "(3, -2)", 0.4)
        return panel

    one, two = build(1.0), build(2.0)
    assert 1.75 < two.height() / one.height() < 2.3

    surface = pygame.Surface((600, 800))
    surface.fill((255, 0, 255))
    rect = two.draw(surface, 60, 40)
    assert rect.width == 440
    for x in range(0, 600, 3):
        for y in range(0, 800, 3):
            if not rect.inflate(6, 6).collidepoint(x, y):
                assert surface.get_at((x, y))[:3] == (255, 0, 255), (x, y)


def test_the_radar_at_twice_the_ratio_is_about_twice_as_big_with_matching_markers():
    from src.ui.minimap import Minimap, COLORS

    small, big = Minimap(1200, 750), Minimap(2400, 1500, ratio=2.0)
    assert 1.8 < big.map_size / small.map_size < 2.2

    ship = type("S", (), {"position": Vector2(0, 0), "rotation": 0})()
    surfaces = []
    for radar in (small, big):
        s = pygame.Surface(radar.screen_width and (radar.screen_width, radar.screen_height), pygame.SRCALPHA)
        radar.draw(s, ship, [], [], [("hostile", Vector2(800, 0))])
        surfaces.append(s)
    count = lambda s: sum(1 for x in range(s.get_width()) for y in range(s.get_height())
                          if s.get_at((x, y))[:3] == COLORS["hostile"])
    assert 3 < count(surfaces[1]) / max(1, count(surfaces[0])) < 5.5          # a marker has about 4x the pixels


def test_notifications_scale_with_the_ratio():
    from src.ui.notifications import Notifications

    def lit(ratio):
        n = Notifications()
        n.push("Hello world", duration=5.0)
        s = pygame.Surface((int(600 * ratio), int(300 * ratio)))
        n.render(s, ratio)
        return sum(1 for x in range(s.get_width()) for y in range(s.get_height()) if sum(s.get_at((x, y))[:3]) > 300)

    assert 3.0 < lit(2.0) / lit(1.0) < 5.0
