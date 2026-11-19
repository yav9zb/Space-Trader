import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from types import SimpleNamespace

import pygame
import pytest
from pygame import Vector2

from src.story.objectives import displayed_sector
from src.ui import objective_pointer as op


@pytest.fixture(autouse=True)
def pygame_ready():
    pygame.display.init()
    pygame.font.init()
    yield


def station(name, x, y):
    return SimpleNamespace(name=name, position=Vector2(x, y))


def mission(destination, story=False):
    return SimpleNamespace(destination_station_id=destination, story_id="m" if story else None)


def game(missions, stations, ship_at=(0, 0)):
    return SimpleNamespace(
        universe=SimpleNamespace(stations=stations),
        mission_manager=SimpleNamespace(active_missions=missions),
        ship=SimpleNamespace(position=Vector2(ship_at)),
        camera=SimpleNamespace(get_offset=lambda: Vector2(-400, -300)),
    )


def test_a_station_destination_resolves_to_that_stations_position():
    stations = [station("Alpha-1", 100, 200), station("Beta-2", 5000, -3000)]
    assert op.target_position("Beta-2", stations) == Vector2(5000, -3000)
    assert op.target_position("Nowhere", stations) is None
    assert op.target_position(None, stations) is None
    assert op.target_position("", stations) is None


def test_a_sector_destination_resolves_to_the_middle_of_that_sector_as_the_hud_shows_it():
    for x, y in [(26, -22), (0, 0), (-5, 7), (3, 12)]:
        position = op.target_position(f"Sector ({x}, {y})", [])
        assert displayed_sector(position) == (x, y), (x, y)


def test_a_story_mission_is_pointed_at_before_an_ordinary_one():
    stations = [station("Story-1", 9000, 0), station("Plain-2", 100, 0)]
    objective = op.current_objective(game([mission("Plain-2"), mission("Story-1", story=True)], stations))
    assert objective[0] == "Story-1"


def test_missions_without_a_place_are_skipped_and_no_objective_is_fine():
    stations = [station("Plain-2", 100, 0)]
    assert op.current_objective(game([mission(None, story=True), mission("Plain-2")], stations))[0] == "Plain-2"
    assert op.current_objective(game([mission(None)], stations)) is None
    assert op.current_objective(game([], stations)) is None


def test_the_arrow_sits_on_the_ring_and_points_at_the_target():
    ship_screen = Vector2(500, 400)
    for direction in (Vector2(1, 0), Vector2(0, -1), Vector2(-3, 4), Vector2(2, 5)):
        tip, left, right = op.pointer_points(ship_screen, direction)
        forward = direction.normalize()
        centre = (tip + left + right) / 3
        assert abs((centre - ship_screen).length() - op.RING_RADIUS) < 6
        assert (tip - ship_screen).normalize().dot(forward) > 0.97         # points toward the target
        assert (tip - ship_screen).length() > (left - ship_screen).length()  # tip is the far corner


def test_distances_are_shown_in_the_huds_units():
    assert op.distance_text(450) == "450m"
    assert op.distance_text(12345.6) == "12,345m"


GOLD = op.COLOR


def gold_pixels(surface):
    return sum(1 for x in range(surface.get_width()) for y in range(surface.get_height())
               if surface.get_at((x, y))[:3] == GOLD)


def test_a_far_objective_draws_an_arrow_and_a_near_one_does_not():
    font = pygame.font.Font(None, 22)
    far = game([mission("Far-1", story=True)], [station("Far-1", 7000, 0)])
    surface = pygame.Surface((924, 668))
    op.draw(surface, far, font)
    assert gold_pixels(surface) > 50

    near = game([mission("Near-1", story=True)], [station("Near-1", op.HIDE_WITHIN - 10, 0)])
    surface = pygame.Surface((924, 668))
    op.draw(surface, near, font)
    assert gold_pixels(surface) == 0

    nothing = game([], [])
    surface = pygame.Surface((924, 668))
    op.draw(surface, nothing, font)
    assert gold_pixels(surface) == 0


def test_the_label_stays_on_screen_when_the_target_is_toward_an_edge():
    font = pygame.font.Font(None, 22)
    g = game([mission("Edge-1", story=True)], [station("Edge-1", 50000, 0)], ship_at=(1100, 400))
    g.camera = SimpleNamespace(get_offset=lambda: Vector2(100, 100))        # ship near the right edge
    surface = pygame.Surface((924, 668))
    op.draw(surface, g, font)                                               # must not raise
    assert gold_pixels(surface) > 0


# --- Large map -----------------------------------------------------------------------

RECT = pygame.Rect(50, 50, 700, 500)
CENTER = Vector2(400, 300)


def test_edge_point_is_on_the_rectangle_border_along_the_line_to_the_target():
    for target in (Vector2(5000, 300), Vector2(-5000, 300), Vector2(400, -5000), Vector2(400, 9000),
                   Vector2(3000, 2000), Vector2(-2000, -1500)):
        point = op.edge_point(CENTER, target, RECT)
        on_border = (abs(point.x - RECT.left) < 1e-6 or abs(point.x - RECT.right) < 1e-6
                     or abs(point.y - RECT.top) < 1e-6 or abs(point.y - RECT.bottom) < 1e-6)
        assert on_border, (target, point)
        assert RECT.inflate(2, 2).collidepoint(point.x, point.y)
        assert (point - CENTER).normalize().dot((target - CENTER).normalize()) > 0.999   # same direction


def test_edge_point_leaves_a_target_inside_the_rectangle_alone():
    assert op.edge_point(CENTER, Vector2(500, 350), RECT) == Vector2(500, 350)
    assert op.edge_point(CENTER, CENTER, RECT) == CENTER


def test_all_objectives_lists_each_destination_once_story_first():
    stations = [station("A-1", 1000, 0), station("B-2", 0, 2000)]
    missions = [mission("B-2"), mission("A-1", story=True), mission("A-1"), mission(None, story=True),
                mission("Sector (3, -4)")]
    found = op.all_objectives(game(missions, stations))
    assert [label for label, _ in found] == ["A-1", "B-2", "Sector (3, -4)"]


def map_pixels(objectives, ship_at=(0, 0)):
    from src.ui.large_map import LargeMap
    large = LargeMap(924, 668)
    large.visible = True
    surface = pygame.Surface((924, 668))
    ship = SimpleNamespace(position=Vector2(ship_at), heading=Vector2(0, -1), rotation=0)
    large.draw(surface, ship, [], [], objectives)
    return gold_pixels(surface)


def test_the_large_map_marks_near_and_far_objectives_and_shows_nothing_without_any():
    assert map_pixels([]) == 0
    assert map_pixels([("Near-1", Vector2(800, 300))]) > 20            # a ring on the map
    assert map_pixels([("Far-1", Vector2(40000, -30000))]) > 20        # an arrow at the edge
    assert map_pixels([("Far-1", Vector2(40000, -30000)), ("Far-2", Vector2(-40000, 20000))]) \
        > map_pixels([("Far-1", Vector2(40000, -30000))])
