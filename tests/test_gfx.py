import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import random

import pygame
import pytest
from pygame import Vector2

from src.ui import gfx


@pytest.fixture(autouse=True)
def pygame_ready():
    pygame.display.init()
    pygame.font.init()
    gfx.clear_caches()
    yield
    gfx.clear_caches()


def screen(w=200, h=200):
    surface = pygame.Surface((w, h))
    surface.fill((0, 0, 0))
    return surface


def lit_pixels(surface, threshold=12):
    return sum(1 for x in range(surface.get_width()) for y in range(surface.get_height())
               if sum(surface.get_at((x, y))[:3]) > threshold)


# --- colours -------------------------------------------------------------------------

def test_colour_helpers_stay_in_range_and_move_the_right_way():
    assert gfx.lighten((100, 100, 100), 0.5) == (177, 177, 177)
    assert gfx.darken((100, 200, 50), 0.5) == (50, 100, 25)
    assert gfx.lighten((250, 250, 250), 5) == (255, 255, 255)
    assert gfx.darken((10, 10, 10), 5) == (0, 0, 0)
    assert gfx.mix((0, 0, 0), (200, 100, 50), 0.5) == (100, 50, 25)
    assert gfx.clamp_color((300, -5, 12.7, 99)) == (255, 0, 12)          # alpha dropped, no crash


def test_flicker_stays_between_its_bounds():
    for seed in range(50):
        assert 0.4 <= gfx.flicker(seed, speed=2.0, low=0.4) <= 1.0


# --- glows -------------------------------------------------------------------------------

def test_a_glow_is_bright_in_the_middle_dark_outside_and_adds_to_what_is_there():
    s = screen()
    gfx.draw_glow(s, (100, 100), 40, (255, 100, 50))
    centre, edge, outside = s.get_at((100, 100)), s.get_at((100, 75)), s.get_at((5, 5))
    assert sum(centre[:3]) > sum(edge[:3]) > 0
    assert outside[:3] == (0, 0, 0)

    s.fill((60, 60, 60))
    gfx.draw_glow(s, (100, 100), 40, (255, 100, 50))
    assert s.get_at((100, 100))[0] > 60                                      # added, not replaced
    assert s.get_at((5, 5))[:3] == (60, 60, 60)                              # outside the glow's square
    assert s.get_at((62, 62))[:3] == (60, 60, 60)                            # inside the square, outside the glow: black adds nothing


def test_glows_are_cached_and_the_cache_is_bounded():
    a = gfx.glow_surface(30, (200, 100, 50))
    assert gfx.glow_surface(30, (200, 100, 50)) is a
    for r in range(2, gfx._CACHE_LIMIT + 20):
        gfx.glow_surface(r, (10, 20, 30))
    assert len(gfx._glows) <= gfx._CACHE_LIMIT


def test_tiny_or_zero_strength_glows_draw_nothing():
    s = screen()
    gfx.draw_glow(s, (50, 50), 1, (255, 255, 255))
    gfx.draw_glow(s, (50, 50), 30, (255, 255, 255), strength=0)
    assert lit_pixels(s) == 0


# --- sphere shading -----------------------------------------------------------------------

def test_the_sphere_overlay_is_darker_at_the_lower_right_and_clear_outside_the_disc():
    shade = gfx.sphere_shade(50)
    upper_left = shade.get_at((30, 30)).a
    lower_right = shade.get_at((78, 78)).a
    assert lower_right > upper_left + 40
    assert shade.get_at((1, 1)).a == 0                                       # a corner outside the disc
    assert gfx.sphere_shade(50) is shade                                     # cached


def test_shading_a_planet_darkens_its_far_side_more_than_its_lit_side():
    s = screen()
    pygame.draw.circle(s, (180, 180, 180), (100, 100), 50)
    gfx.draw_shaded_sphere_overlay(s, (100, 100), 50)
    assert sum(s.get_at((75, 75))[:3]) > sum(s.get_at((125, 125))[:3])


# --- edge flash ---------------------------------------------------------------------------

def test_the_edge_flash_tints_the_borders_not_the_middle_and_scales_with_strength():
    s = screen(300, 200)
    gfx.draw_edge_flash(s, (255, 0, 0), 1.0)
    assert s.get_at((1, 100))[0] > 40
    assert s.get_at((150, 100))[:3] == (0, 0, 0)

    strong = s.get_at((1, 100))[0]
    s.fill((0, 0, 0))
    gfx.draw_edge_flash(s, (255, 0, 0), 0.4)
    assert 0 < s.get_at((1, 100))[0] < strong

    s.fill((0, 0, 0))
    gfx.draw_edge_flash(s, (255, 0, 0), 0.0)
    assert lit_pixels(s) == 0


# --- engine flame -------------------------------------------------------------------------

def test_the_flame_trails_behind_the_ship_and_scales_with_power():
    s = screen()
    gfx.draw_engine_flame(s, (100, 100), 0, 16, (200, 80, 20), (255, 230, 160), power=1.0)
    below = sum(1 for y in range(112, 200) for x in range(60, 140) if sum(s.get_at((x, y))[:3]) > 40)
    above = sum(1 for y in range(0, 90) for x in range(60, 140) if sum(s.get_at((x, y))[:3]) > 40)
    assert below > 30 and above == 0

    weak, strong = screen(), screen()
    gfx.draw_engine_flame(weak, (100, 100), 0, 16, (200, 80, 20), (255, 230, 160), power=0.4)
    gfx.draw_engine_flame(strong, (100, 100), 0, 16, (200, 80, 20), (255, 230, 160), power=1.9)
    assert lit_pixels(strong) > lit_pixels(weak)

    off = screen()
    gfx.draw_engine_flame(off, (100, 100), 0, 16, (200, 80, 20), (255, 230, 160), power=0)
    assert lit_pixels(off) == 0


def test_the_flame_follows_the_ships_rotation():
    s = screen()
    gfx.draw_engine_flame(s, (100, 100), 90, 16, (200, 80, 20), (255, 230, 160), power=1.0)
    left = sum(1 for x in range(0, 88) for y in range(60, 140) if sum(s.get_at((x, y))[:3]) > 40)
    right = sum(1 for x in range(112, 200) for y in range(60, 140) if sum(s.get_at((x, y))[:3]) > 40)
    assert left > 30 and right == 0                                          # a ship turned right exhausts left


# --- stations ----------------------------------------------------------------------------

def test_every_station_type_has_its_own_look_and_draws_inside_its_halo():
    from src.entities.station import Station, StationType

    images = {}
    for station_type in StationType:
        station = Station(150, 150, station_type)
        station.rotation_speed = 0
        station.rotation = 0
        station.color = (180, 180, 180)             # same colour and size: only the art may differ
        station.size = 40
        s = screen(300, 300)
        station.draw(s, Vector2(0, 0))
        images[station_type] = pygame.image.tostring(s, "RGB")
        assert lit_pixels(s) > 200

    kinds = list(images)
    for i, a in enumerate(kinds):
        for b in kinds[i + 1:]:
            assert images[a] != images[b], (a, b)


def test_stations_draw_at_any_rotation_without_error():
    from src.entities.station import Station, StationType

    s = screen(300, 300)
    for station_type in StationType:
        station = Station(150, 150, station_type)
        for angle in (0, 33, 90, 181, 359):
            station.rotation = angle
            station.draw(s, Vector2(0, 0))


# --- ship, damage and camera -----------------------------------------------------------------

def test_taking_damage_pulses_and_the_pulse_fades_out():
    from src.entities.ship import Ship

    ship = Ship(0, 0)
    assert ship.damage_pulse == 0
    ship.take_damage(20)
    assert 0.3 < ship.damage_pulse <= 1.0
    before = ship.damage_pulse
    ship.update(0.2)
    assert ship.damage_pulse < before
    for _ in range(40):
        ship.update(0.1)
    assert ship.damage_pulse == 0


def test_a_harder_hit_pulses_harder_and_no_damage_does_not_pulse():
    from src.entities.ship import Ship

    light, heavy = Ship(0, 0), Ship(0, 0)
    light.take_damage(2)
    heavy.take_damage(30)
    assert heavy.damage_pulse > light.damage_pulse
    clean = Ship(0, 0)
    clean.take_damage(0)
    assert clean.damage_pulse == 0


def test_the_camera_shakes_only_while_the_player_is_hurting():
    from src.camera import Camera
    from src.entities.ship import Ship

    camera = Camera(800, 600)
    ship = Ship(1000, 1000)
    camera.follow(ship)
    assert camera.get_offset() == camera.position                            # steady when unhurt

    ship.take_damage(30)
    camera.follow(ship)
    offsets = {tuple(camera.get_offset()) for _ in range(20)}
    assert len(offsets) > 5                                                  # it jolts around
    assert all((Vector2(o) - camera.position).length() <= 7 * 1.5 for o in offsets)   # but only slightly

    ship.damage_pulse = 0
    camera.follow(ship)
    assert camera.get_offset() == camera.position


def test_the_ship_leaves_an_exhaust_trail_only_while_thrusting_and_it_fades():
    from src.entities.ship import Ship

    ship = Ship(0, 0)
    ship.update(0.05)
    assert ship._trail == []
    ship.thrusting = True
    for _ in range(10):
        ship.update(0.05)
    assert 0 < len(ship._trail) <= 24
    ship.thrusting = False
    for _ in range(20):
        ship.update(0.05)
    assert ship._trail == []


# --- starfield ---------------------------------------------------------------------------------

def test_the_starfield_has_three_depth_layers_that_scroll_at_different_speeds():
    from src.entities.starfield import StarField, LAYERS

    random.seed(1)
    field = StarField(300, 800, 600)
    assert {star[3] for star in field.stars} == {0, 1, 2}

    far = next(s for s in field.stars if s[3] == 0)
    near = next(s for s in field.stars if s[3] == 2)
    shift = 100
    moved = lambda star: abs(((star[0] - shift * LAYERS[star[3]][1]) % 800) - star[0])
    assert moved(near) > moved(far) * 3                                      # near stars travel farther


def test_the_starfield_draws_and_stays_on_screen_for_any_camera_position():
    from src.entities.starfield import StarField

    field = StarField(200, 640, 480)
    s = screen(640, 480)
    for camera in (Vector2(0, 0), Vector2(-5000, 9000), Vector2(123456, -98765)):
        field.draw(s, camera)
    assert lit_pixels(s, threshold=60) > 100


# --- explosions --------------------------------------------------------------------------------

def test_an_explosion_throws_sparks_that_move_and_die_out():
    from src.combat.combat_manager import CombatManager

    manager = CombatManager()
    manager._create_explosion(Vector2(100, 100), 40)
    explosion = manager.explosions[0]
    assert len(explosion["sparks"]) == 14
    start = [Vector2(sp[0]) for sp in explosion["sparks"]]

    manager._update_explosions(0.3)
    assert any((sp[0] - st).length() > 5 for sp, st in zip(explosion["sparks"], start))
    manager._update_explosions(0.6)
    assert all(sp[2] < 0.3 for sp in explosion["sparks"])
    manager._update_explosions(0.5)
    assert manager.explosions == []


def test_an_explosion_draws_a_bright_flash_that_fades():
    from src.combat.combat_manager import CombatManager

    manager = CombatManager()
    manager._create_explosion(Vector2(100, 100), 40)
    early = screen()
    manager.draw_combat_effects(early, Vector2(0, 0))
    manager._update_explosions(0.8)
    late = screen()
    manager.draw_combat_effects(late, Vector2(0, 0))
    assert lit_pixels(early) > lit_pixels(late) >= 0


# --- bars and rings -----------------------------------------------------------------------

def test_a_bar_fills_in_proportion_and_is_lit_on_top():
    s = screen(300, 60)
    green = (80, 210, 90)
    gfx.draw_bar(s, (10, 10, 200, 14), 0.5, green)
    filled_mid = s.get_at((60, 17))[:3]
    empty_mid = s.get_at((180, 17))[:3]
    assert filled_mid != empty_mid and abs(filled_mid[1] - green[1]) < 80
    assert s.get_at((60, 12))[1] > s.get_at((60, 20))[1]                    # highlight on the top edge
    assert s.get_at((150, 17))[:3] == s.get_at((190, 17))[:3]               # both beyond half: trough


def test_bars_clamp_and_handle_empty_and_full():
    s = screen(300, 60)
    gfx.draw_bar(s, (10, 10, 200, 14), -3, (255, 0, 0))
    assert s.get_at((100, 17))[:3] == (16, 20, 32)                          # empty: just the trough
    gfx.draw_bar(s, (10, 30, 200, 14), 9, (255, 0, 0))
    assert s.get_at((205, 37))[0] > 100                                      # full: filled to the end


def test_a_ring_glow_is_bright_on_the_ring_and_dark_away_from_it():
    s = screen(300, 300)
    gfx.draw_ring_glow(s, (150, 150), 80, 6, (255, 200, 100))
    on_ring = sum(s.get_at((150 + 80, 150))[:3])
    inside, outside = sum(s.get_at((150, 150))[:3]), sum(s.get_at((150 + 120, 150))[:3])
    assert on_ring > 100 and inside == 0 and outside == 0
    assert gfx.ring_glow(80, 6, (255, 200, 100)) is gfx.ring_glow(80, 6, (255, 200, 100))   # cached


# --- projectiles ------------------------------------------------------------------------------

def _owner(kind):
    from types import SimpleNamespace
    return {
        "player": SimpleNamespace(cargo_hold=object()),
        "patrol": SimpleNamespace(faction="Trade Guild", patrol_center=Vector2(0, 0)),
        "bandit": SimpleNamespace(patrol_center=Vector2(0, 0), bandit_type="fighter"),
    }[kind]


def test_shots_are_coloured_by_who_fired_them_and_bandits_are_not_mistaken_for_patrols():
    from src.combat.weapons import Projectile, WeaponType

    colours = {}
    for kind in ("player", "patrol", "bandit"):
        shot = Projectile(Vector2(0, 0), Vector2(0, -100), 5, _owner(kind), WeaponType.LASER)
        colours[kind] = shot._palette()
    assert len({c[0] for c in colours.values()}) == 3
    outer_bandit = colours["bandit"][0]
    assert outer_bandit[0] > outer_bandit[1] and outer_bandit[0] > outer_bandit[2]     # red
    assert colours["player"][0][2] > colours["player"][0][0]                          # blue-ish
    assert colours["patrol"][0][1] > colours["patrol"][0][0]                          # green-ish


@pytest.mark.parametrize("weapon", ["LASER", "PLASMA", "MISSILE", "RAILGUN"])
def test_every_weapon_draws_a_visible_shot_that_points_along_its_travel(weapon):
    from src.combat.weapons import Projectile, WeaponType

    s = screen(300, 300)
    shot = Projectile(Vector2(150, 150), Vector2(400, 0), 5, _owner("player"), getattr(WeaponType, weapon))
    shot.draw(s, Vector2(0, 0))
    assert lit_pixels(s) > 15
    left = sum(1 for x in range(100, 148) for y in range(130, 170) if sum(s.get_at((x, y))[:3]) > 40)
    right = sum(1 for x in range(153, 200) for y in range(130, 170) if sum(s.get_at((x, y))[:3]) > 40)
    assert left > 0                                                     # a tail behind a rightward shot


# --- asteroids and black holes ---------------------------------------------------------------

def test_every_asteroid_type_draws_and_its_craters_stay_put():
    from src.entities.asteroid import Asteroid, AsteroidType

    for kind in AsteroidType:
        asteroid = Asteroid(Vector2(150, 150), 30, kind)
        s = screen(300, 300)
        asteroid.draw(s, Vector2(0, 0))
        assert lit_pixels(s) > 150
        craters = list(asteroid._craters())
        asteroid.rotation += 77
        asteroid.draw(s, Vector2(0, 0))
        assert asteroid._craters() == craters                           # fixed on the rock, they just turn with it


def test_damaged_asteroids_and_ships_show_a_health_bar():
    from src.entities.asteroid import Asteroid
    from src.entities.bandit import BanditShip, BanditType

    asteroid = Asteroid(Vector2(150, 150), 30)
    s1, s2 = screen(300, 300), screen(300, 300)
    asteroid.draw(s1, Vector2(0, 0))
    asteroid.current_health = asteroid.max_health * 0.4
    asteroid.draw(s2, Vector2(0, 0))
    assert lit_pixels(s2) > lit_pixels(s1)

    bandit = BanditShip(Vector2(150, 150), BanditType.FIGHTER)
    a, b = screen(300, 300), screen(300, 300)
    bandit.draw(a, Vector2(0, 0))
    bandit.current_hull = bandit.max_hull * 0.3
    bandit.draw(b, Vector2(0, 0))
    assert lit_pixels(b) > lit_pixels(a)


def test_a_black_hole_has_a_black_core_ringed_by_light():
    from src.entities.black_hole import BlackHole

    hole = BlackHole(Vector2(300, 300), 60.0)
    s = screen(600, 600)
    hole.draw(s, Vector2(0, 0))
    assert s.get_at((300, 300))[:3] == (0, 0, 0)
    ring = max(sum(s.get_at((300 + r, 300))[:3]) for r in range(int(60 * 0.4), int(60 * 0.9)))
    assert ring > 150
    assert lit_pixels(s) > 3000                                         # a big glow, not a dot


# --- HUD status bars ----------------------------------------------------------------------------------

def test_status_bars_change_colour_as_they_empty():
    from src.ui.hud.enhanced_hud import StatusBar

    def fill_colour(value):
        bar = StatusBar(100, 12, (80, 200, 255))
        bar.value = bar.target_value = value
        s = screen(160, 40)
        bar.draw(s, 10, 10)
        return s.get_at((14, 17))[:3]

    healthy, middling, critical = fill_colour(1.0), fill_colour(0.45), fill_colour(0.2)
    assert healthy != middling != critical
    assert critical[0] > critical[2] and middling[0] > middling[2]       # amber and red, not the bar's blue
    assert healthy[2] > healthy[0]


def test_craters_are_drawn_and_depend_only_on_the_asteroid_not_on_chance():
    from src.entities.asteroid import Asteroid

    a, b = Asteroid(Vector2(150, 150), 30), Asteroid(Vector2(150, 150), 30)
    a.rotation = b.rotation = 20
    b.color = a.color                                                      # colour is random per rock
    b.shape_points = list(a.shape_points)                                    # and so is the outline
    assert a._craters() == b._craters()                                   # seeded by the asteroid itself

    with_craters, without = screen(300, 300), screen(300, 300)
    a.draw(with_craters, Vector2(0, 0))
    b._crater_list = []
    b.draw(without, Vector2(0, 0))
    differing = sum(1 for x in range(100, 200) for y in range(100, 200)
                    if with_craters.get_at((x, y)) != without.get_at((x, y)))
    assert differing > 10


# --- panels ---------------------------------------------------------------------------------

def test_a_panel_is_lighter_at_the_top_translucent_and_rounded():
    panel = gfx.panel_surface(200, 120, (10, 14, 30), 180, 10)
    top, bottom = panel.get_at((100, 2)), panel.get_at((100, 117))
    assert sum(top[:3]) > sum(bottom[:3])                                   # a soft gradient
    assert top.a == bottom.a == 180                                         # same translucency throughout
    assert panel.get_at((0, 0)).a == 0                                      # rounded corner is clear
    assert gfx.panel_surface(200, 120, (10, 14, 30), 180, 10) is panel      # cached


def test_corner_accents_mark_all_four_corners_and_leave_the_middle_alone():
    s = screen(200, 120)
    gfx.draw_corner_accents(s, pygame.Rect(10, 10, 180, 100), (255, 255, 255))
    for corner in ((10, 10), (189, 10), (10, 109), (189, 109)):
        assert sum(s.get_at(corner)[:3]) > 600
    assert s.get_at((100, 60))[:3] == (0, 0, 0)
    assert s.get_at((100, 10))[:3] == (0, 0, 0)                             # the edges between corners stay bare


def test_menu_panels_get_the_gradient_and_corner_brackets():
    from src.ui.menu_style import draw_panel, ACCENT_BLUE

    s = screen(300, 200)
    draw_panel(s, pygame.Rect(20, 20, 260, 160))
    assert sum(s.get_at((150, 25))[:3]) > sum(s.get_at((150, 170))[:3])      # gradient
    assert sum(s.get_at((20, 20))[:3]) > sum(ACCENT_BLUE)                    # a lightened corner bracket

    tiny = screen(100, 60)
    draw_panel(tiny, pygame.Rect(5, 5, 50, 30))                              # too small for brackets: no crash


def test_a_pulsing_glow_reuses_a_few_surfaces_instead_of_building_one_per_frame():
    import math
    screen = pygame.Surface((300, 300))
    gfx.clear_caches()
    built = []
    original = gfx._bounded

    def spy(cache, key, build):
        if key not in cache:
            built.append(key)
        return original(cache, key, build)

    gfx._bounded = spy
    try:
        for frame in range(120):
            pulse = 0.5 + 0.5 * math.sin(frame * 0.2)
            gfx.draw_glow(screen, (150, 150), 30 + 8 * pulse, (200 * pulse, 90, 20), 1.0)
            gfx.draw_ring_glow(screen, (150, 150), 40 + 6 * pulse, 3, (60, 120 * pulse, 200), 1.0)
    finally:
        gfx._bounded = original
    # 240 draws; the colour sweep here is far wider than any real pulse
    assert len(built) < 60


def test_snapping_keeps_a_glow_within_a_few_percent_of_what_was_asked():
    assert gfx.snap_radius(5) == 5
    for r in (16, 23, 37, 64, 150, 400):
        assert abs(gfx.snap_radius(r) - r) <= max(1, r * 0.07)
    assert gfx.snap_color((0, 0, 0)) == (0, 0, 0)
    assert gfx.snap_color((255, 255, 255)) == (255, 255, 255)
    assert all(abs(a - b) <= 4 for a, b in zip(gfx.snap_color((93, 119, 37)), (93, 119, 37)))
