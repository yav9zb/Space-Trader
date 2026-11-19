"""The HUD's panels and radar must never overlap, spill outside their own
borders or run off the window, at any window size the game is likely to see."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest
from pygame import Vector2

from src.ui.hud import panel_kit
from src.ui.hud.enhanced_hud import EnhancedHUD
from src.ui.minimap import Minimap, gather_contacts, COLORS
from src.ui.ui_theme import UIElementType

SIZES = [(700, 500), (924, 668), (1280, 720), (1920, 1080)]
MAGENTA = (255, 0, 255)


class Clock:
    def get_time(self): return 16
    def tick(self, *a): return 16
    def get_fps(self): return 60.0


@pytest.fixture(scope="module")
def game():
    from src.engine.game_engine import GameEngine
    from src.states.game_state import GameStates
    from src.story import director
    from src.story.story_missions import start_story_mission

    engine = GameEngine()
    engine.clock = Clock()
    engine.create_new_universe(seed=4)
    engine.change_state(GameStates.PLAYING)
    engine.story_state.chapter = "act_4"
    director.ensure_npcs_placed(engine)
    for mission in ("act1_2", "act2_2", "act4_2"):
        start_story_mission(mission, engine)
    return engine


def hud_for(game, size):
    hud = EnhancedHUD(*size)
    game.minimap = Minimap(*size)
    hud.update(0.016, game)
    return hud


def rects_overlap(a, b):
    return a.colliderect(b)


# --- the panel toolkit -----------------------------------------------------------------

def metrics():
    pygame.font.init()
    return panel_kit.make_metrics(1.0)


def test_a_panels_height_comes_from_its_content_and_grows_with_each_row():
    m = metrics()
    panel = panel_kit.Panel("TEST", UIElementType.SHIP_STATUS, (150, 175, 255), m, 220)
    empty = panel.height()
    panel.stat("Credits", "1,234")
    one = panel.height()
    panel.bar("hull", "HULL", "50/100", 0.5, panel_kit.GREEN)
    panel.chip("READY", panel_kit.GREEN, label="BOOST")
    panel.grid([("LASER", "50", 0.5, panel_kit.BLUE)] * 4)
    assert empty < one < panel.height()


def test_nothing_is_drawn_outside_a_panels_own_rectangle():
    m = metrics()
    panel = panel_kit.Panel("SHIP STATUS", UIElementType.SHIP_STATUS, (150, 175, 255), m, 200)
    panel.stat("Credits", "123,456,789,012", panel_kit.AMBER, icon="credits")
    panel.bar("hull", "HULL", "1000000/1000000", 0.4, panel_kit.AMBER)
    panel.chip("A VERY LONG STATUS NAME INDEED", panel_kit.GREEN, label="STATUS")
    panel.stat("Nearest", "Extraordinarily-Long-Station-Name-9999", icon="station")
    panel.grid([("MISSILE", "9999", 0.3, panel_kit.RED)] * 4)
    panel.entry("A mission with an extremely long title that cannot possibly fit", "99h 59m",
                "-> A destination with a long name too", "(-12, 34)", 0.5)
    surface = pygame.Surface((400, 600))
    surface.fill(MAGENTA)
    rect = panel.draw(surface, 40, 30)

    assert rect.height == panel.height() and rect.width == 200
    for x in range(surface.get_width()):
        for y in range(surface.get_height()):
            if not rect.inflate(2, 2).collidepoint(x, y):
                assert surface.get_at((x, y))[:3] == MAGENTA, (x, y)


def test_long_text_is_shortened_with_an_ellipsis_to_fit():
    m = metrics()
    text = panel_kit.fit_text(m.body, "A very long station name that will not fit", 90)
    assert text.endswith("...") and m.body.size(text)[0] <= 90
    assert panel_kit.fit_text(m.body, "Short", 90) == "Short"


def test_a_bars_value_text_always_fits_on_the_bar():
    m = metrics()
    for width in (120, 160, 210):
        row = panel_kit.BarRow("hull", "HULL", "1000000/1000000", 0.5, panel_kit.GREEN)
        bar, text = row.layout(m, 0, 0, width)
        assert m.small.size(text)[0] <= bar.width - 6, (width, text)
        assert bar.right <= width
    short = panel_kit.BarRow("hull", "HULL", "50/100", 0.5, panel_kit.GREEN).layout(m, 0, 0, 200)[1]
    assert short == "50/100"


def test_level_colours_go_green_amber_red_as_a_value_falls():
    assert panel_kit.level_color(0.9) == panel_kit.GREEN
    assert panel_kit.level_color(0.4) == panel_kit.AMBER
    assert panel_kit.level_color(0.1) == panel_kit.RED


def test_stacked_panels_keep_a_constant_gap_and_never_touch():
    m = metrics()
    panels = []
    for rows in (2, 6, 4):
        p = panel_kit.Panel("P", UIElementType.NAVIGATION, (1, 2, 3), m, 200)
        for _ in range(rows):
            p.stat("a", "b")
        panels.append(p)
    rects = panel_kit.stack(panels, 10, 10, 12)
    for upper, lower in zip(rects, rects[1:]):
        assert lower.top - upper.bottom == 12
    assert [r.height for r in rects] == [p.height() for p in panels]


# --- the left column, tracker and radar at every window size ------------------------------

@pytest.mark.parametrize("size", SIZES)
def test_the_left_panels_fit_the_window_and_never_overlap(game, size):
    hud = hud_for(game, size)
    column = hud._left_column(game)
    assert len(column) == 2
    rects = [rect for _, _, rect in column]
    screen = pygame.Rect(0, 0, *size)
    for rect in rects:
        assert screen.contains(rect), (size, rect)
    assert not rects_overlap(rects[0], rects[1])
    assert rects[1].top - rects[0].bottom >= 6                               # a visible gap


@pytest.mark.parametrize("size", SIZES)
def test_the_tracker_sits_below_the_radar_and_clear_of_the_left_panels(game, size):
    hud = hud_for(game, size)
    surface = pygame.Surface(size)
    hud.ui_layout.clear_reserved_areas()
    hud._render_left_column(surface, game)
    hud._render_mission_tracker(surface, game)
    areas = {a["name"]: pygame.Rect(a["x"], a["y"], a["width"], a["height"]) for a in hud.ui_layout.reserved_areas}
    tracker, radar = areas["mission_tracker"], game.minimap.rect

    assert not tracker.colliderect(radar)
    assert tracker.top >= radar.bottom
    assert not tracker.colliderect(areas["ship_status"]) and not tracker.colliderect(areas["navigation"])
    assert pygame.Rect(0, 0, *size).contains(tracker) or size[1] < 560        # a tiny window may clip the third mission


@pytest.mark.parametrize("size", SIZES)
def test_the_full_hud_renders_at_every_size_without_error(game, size):
    hud = hud_for(game, size)
    surface = pygame.Surface(size)
    surface.fill((0, 0, 0))
    hud.render(surface, game)
    game.minimap.draw(surface, game.ship, game.universe.stations, game.universe.planets,
                      gather_contacts(game, game.minimap.view_radius))


def test_compact_panels_are_used_only_when_the_full_ones_would_not_fit(game):
    tight = hud_for(game, (700, 500))
    roomy = hud_for(game, (1920, 1080))
    full_height = tight.build_ship_status(game, compact=False).height() + tight.build_navigation(game).height()
    compact_height = tight.build_ship_status(game, compact=True).height() + tight.build_navigation(game, True).height()
    assert compact_height < full_height

    tight_bottom = tight._left_column(game)[-1][2].bottom
    assert tight_bottom <= 500
    roomy_panel = roomy._left_column(game)[0][0]
    assert roomy_panel.height() >= roomy.build_ship_status(game, compact=True).height()
    assert len(roomy_panel.rows) == len(roomy.build_ship_status(game, compact=False).rows)   # full version kept


def test_warnings_show_on_the_bars_when_hull_and_fuel_run_low(game):
    hud = hud_for(game, (924, 668))
    ship = game.ship
    saved = (ship.current_hull, ship.current_fuel)
    try:
        ship.current_hull, ship.current_fuel = 100, 100
        hud.hull_bar.value = hud.hull_bar.target_value = 1.0
        hud.fuel_bar.value = hud.fuel_bar.target_value = 1.0
        healthy = [r for r in hud.build_ship_status(game).rows if isinstance(r, panel_kit.BarRow)]
        hud.hull_bar.value = hud.fuel_bar.value = 0.12
        low = [r for r in hud.build_ship_status(game).rows if isinstance(r, panel_kit.BarRow)]
    finally:
        ship.current_hull, ship.current_fuel = saved
    by_label = lambda rows: {r.label: r.color for r in rows}
    assert by_label(healthy)["HULL"] == panel_kit.GREEN
    assert by_label(low)["HULL"] == panel_kit.RED and by_label(low)["FUEL"] == panel_kit.RED


# --- the radar -----------------------------------------------------------------------------

def radar_surface(size=(924, 668)):
    minimap = Minimap(*size)
    screen = pygame.Surface(size, pygame.SRCALPHA)
    return minimap, screen


def ship_at(x, y, rotation=0):
    from types import SimpleNamespace
    return SimpleNamespace(position=Vector2(x, y), rotation=rotation)


def test_the_radar_stays_inside_its_rectangle_and_is_round():
    minimap, screen = radar_surface()
    screen.fill((0, 0, 0, 0))
    minimap.draw(screen, ship_at(0, 0), [], [], [])
    rect = minimap.rect
    for x in range(screen.get_width()):
        for y in range(screen.get_height()):
            if not rect.collidepoint(x, y):
                assert screen.get_at((x, y)).a == 0, (x, y)
    corner = screen.get_at((rect.left + 1, rect.top + 1))
    centre = screen.get_at((rect.centerx, rect.top + minimap.map_size // 2 + 20))
    assert corner.a == 0 and centre.a > 0                                   # a disc, not a square


def test_every_kind_of_contact_gets_its_own_marker_inside_the_range():
    minimap, screen = radar_surface()
    minimap.set_view_radius(2000)
    seen = {}
    for kind in ("hostile", "patrol", "trader", "hazard_radioactive", "hazard_explosive", "blackhole", "objective"):
        s = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        minimap.draw(s, ship_at(0, 0), [], [], [(kind, Vector2(900, -600))])
        mark = minimap.world_to_local_map_coords(Vector2(900, -600), Vector2(0, 0)) + minimap.position
        seen[kind] = [s.get_at((int(mark.x) + dx, int(mark.y) + dy))[:3] for dx in range(-7, 8) for dy in range(-7, 8)]
    for kind, pixels in seen.items():
        assert any(abs(p[0] - COLORS[kind][0]) + abs(p[1] - COLORS[kind][1]) + abs(p[2] - COLORS[kind][2]) < 40
                   for p in pixels), kind


def test_an_objective_beyond_the_range_is_pinned_to_the_rim_with_an_arrow():
    minimap, screen = radar_surface()
    minimap.set_view_radius(1000)
    near_rim = Vector2(minimap.rect.centerx, minimap.rect.top + minimap.radius + 4)
    blank = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    minimap.draw(blank, ship_at(0, 0), [], [], [])
    pinned = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    minimap.draw(pinned, ship_at(0, 0), [], [], [("objective", Vector2(0, 30000))])      # far below

    gold = COLORS["objective"]
    count = sum(1 for x in range(minimap.rect.left, minimap.rect.right) for y in range(minimap.rect.top, minimap.rect.bottom)
                if pinned.get_at((x, y))[:3] == gold)
    assert count > 8
    assert sum(1 for x in range(minimap.rect.left, minimap.rect.right) for y in range(minimap.rect.top, minimap.rect.bottom)
               if blank.get_at((x, y))[:3] == gold) == 0
    # and the arrow is on the lower rim, in the direction of the objective
    ys = [y for x in range(minimap.rect.left, minimap.rect.right) for y in range(minimap.rect.top, minimap.rect.bottom)
          if pinned.get_at((x, y))[:3] == gold]
    assert min(ys) > minimap.rect.top + minimap.map_size * 0.6


def test_the_radar_arrow_for_the_ship_turns_with_its_heading():
    minimap, _ = radar_surface()
    images = []
    for rotation in (0, 90, 180):
        s = pygame.Surface((924, 668), pygame.SRCALPHA)
        minimap.draw(s, ship_at(0, 0, rotation), [], [], [])
        images.append(pygame.image.tostring(s, "RGBA"))
    assert len(set(images)) == 3


def test_the_range_is_written_in_a_caption_under_the_disc_not_over_it():
    minimap, _ = radar_surface()
    assert minimap.caption_height > 0 and minimap.total_height == minimap.map_size + minimap.caption_height
    assert minimap.rect.height == minimap.total_height


def test_the_radar_resizes_with_the_window():
    minimap = Minimap(700, 500)
    small = minimap.rect
    minimap.resize(1920, 1080)
    assert minimap.map_size >= small.width
    assert minimap.rect.right <= 1920 and minimap.rect.top < 100


def test_live_contacts_come_from_the_game_and_include_objectives(game):
    from src.combat.combat_manager import combat_manager
    from src.entities.bandit import BanditShip, BanditType

    combat_manager.active_bandits.clear()
    combat_manager.add_bandit(BanditShip(game.ship.position + Vector2(400, 0), BanditType.FIGHTER))
    far = BanditShip(game.ship.position + Vector2(50000, 0), BanditType.FIGHTER)
    combat_manager.add_bandit(far)
    kinds = [kind for kind, _ in gather_contacts(game, 2000)]
    assert kinds.count("hostile") == 1                                          # the far one is out of range
    assert "objective" in kinds
    combat_manager.active_bandits.clear()
