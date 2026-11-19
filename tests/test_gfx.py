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
