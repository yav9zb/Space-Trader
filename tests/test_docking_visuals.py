import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest
from pygame import Vector2

from src.ui import docking_visuals as dv
from src.ui import gfx


@pytest.fixture(autouse=True)
def pygame_ready():
    pygame.display.init()
    pygame.font.init()
    gfx.clear_caches()
    yield


def screen(w=300, h=300):
    s = pygame.Surface((w, h))
    s.fill((0, 0, 0))
    return s


def lit(surface, threshold=30):
    return sum(1 for x in range(surface.get_width()) for y in range(surface.get_height())
               if sum(surface.get_at((x, y))[:3]) > threshold)


def test_the_zone_colour_tells_you_whether_you_can_dock():
    assert dv.zone_status(50, 100, 10, 50) == (dv.CAN_DOCK, "ready")
    assert dv.zone_status(50, 100, 80, 50) == (dv.TOO_FAST, "too fast")
    assert dv.zone_status(150, 100, 10, 50) == (dv.TOO_FAR, "far")
    assert dv.zone_status(100, 100, 50, 50)[1] == "ready"                  # exactly on the limits still counts


def ring_coverage(surface, radius, center=(150, 150)):
    """Fraction of the ring's circumference (sampled by angle) that has paint."""
    import math
    hits = 0
    for degree in range(360):
        a = math.radians(degree)
        painted = any(
            sum(surface.get_at((int(center[0] + math.cos(a) * r), int(center[1] + math.sin(a) * r)))[:3]) > 60
            for r in (radius - 1, radius, radius + 1))
        hits += painted
    return hits / 360


def test_a_dashed_ring_has_gaps_and_turns_with_the_spin():
    a, b = screen(), screen()
    dv.dashed_ring(a, (150, 150), 100, (255, 255, 255), 0)
    dv.dashed_ring(b, (150, 150), 100, (255, 255, 255), 9)
    assert 0.4 < ring_coverage(a, 100) < 0.8                              # dashes with gaps, not a solid ring
    assert pygame.image.tostring(a, "RGB") != pygame.image.tostring(b, "RGB")   # and they turn

    solid = screen()
    dv.dashed_ring(solid, (150, 150), 100, (255, 255, 255), 0, dash_degrees=360, gap_degrees=0)
    assert ring_coverage(solid, 100) > 0.95


def test_tiny_rings_are_skipped_rather_than_crashing():
    s = screen()
    dv.dashed_ring(s, (50, 50), 2, (255, 255, 255), 0)
    dv.draw_progress_arc(s, (50, 50), 3, 0.5, (0, 255, 0))
    assert lit(s) == 0


def test_beam_pulses_move_along_the_beam_and_stay_on_it():
    start, end = Vector2(0, 0), Vector2(100, 0)
    early = dv.beam_points(start, end, 0.0)
    later = dv.beam_points(start, end, 0.2)
    assert len(early) == 7
    assert all(0 <= p.x <= 100 and p.y == 0 for p in early + later)
    assert sorted(p.x for p in early) != sorted(p.x for p in later)         # they travel


def test_the_tractor_beam_draws_between_the_ports_and_not_when_they_coincide():
    s = screen()
    dv.draw_tractor_beam(s, (50, 150), (250, 150), 0.3, 0.0)
    between = sum(1 for x in range(60, 240) for y in range(120, 180) if sum(s.get_at((x, y))[:3]) > 30)
    outside = sum(1 for x in range(0, 30) for y in range(0, 300) if sum(s.get_at((x, y))[:3]) > 30)
    assert between > 60 and outside == 0
    pulses = sum(1 for x in range(300) for y in range(300) if s.get_at((x, y))[:3] == (235, 245, 255))
    assert pulses >= 7 * 5                                                 # seven pulses, each a bright dot

    empty = screen()
    dv.draw_tractor_beam(empty, (100, 100), (101, 100), 0.5, 0.0)
    assert lit(empty) == 0


def test_undocking_sends_the_pulses_the_other_way():
    forward, backward = screen(), screen()
    dv.draw_tractor_beam(forward, (50, 150), (250, 150), 0.3, 0.13)
    dv.draw_tractor_beam(backward, (50, 150), (250, 150), 0.3, 0.13, reverse=True)
    assert pygame.image.tostring(forward, "RGB") != pygame.image.tostring(backward, "RGB")


def test_the_beam_narrows_as_docking_progresses():
    def width_of(progress):
        s = screen()
        dv.draw_tractor_beam(s, (50, 150), (250, 150), progress, 0.0)
        rows = [y for y in range(300) if sum(s.get_at((100, y))[:3]) > 20]
        return (max(rows) - min(rows)) if rows else 0

    assert width_of(0.0) > width_of(1.0)


def test_the_progress_arc_grows_with_progress_and_is_empty_at_zero():
    amounts = []
    for fraction in (0.0, 0.25, 0.5, 1.0):
        s = screen()
        dv.draw_progress_arc(s, (150, 150), 80, fraction, (0, 255, 0))
        amounts.append(lit(s))
    assert amounts[0] == 0 and amounts[0] < amounts[1] < amounts[2] < amounts[3]


def test_the_zone_draws_a_glowing_ring_that_is_fainter_when_far():
    near, far = screen(), screen()
    dv.draw_zone(near, (150, 150), 90, dv.CAN_DOCK, 0.0, emphasis=1.0)
    dv.draw_zone(far, (150, 150), 90, dv.TOO_FAR, 0.0, emphasis=0.5)
    assert lit(near) > lit(far) > 0


def test_the_playing_state_draws_the_docking_visuals_without_error_in_every_phase():
    """Runs the real engine's docking overlay through every docking state."""
    from src.engine.game_engine import GameEngine
    from src.docking.docking_manager import DockingState
    from src.states.game_state import GameStates

    class Clock:
        def get_time(self): return 16
        def tick(self, *a): return 16
        def get_fps(self): return 60.0

    engine = GameEngine()
    engine.clock = Clock()
    engine.create_new_universe(seed=4)
    engine.change_state(GameStates.PLAYING)
    station = engine.universe.stations[0]
    manager = engine.docking_manager
    engine.ship.position = station.position + Vector2(-station.size - 40, 0)
    for state in (DockingState.FREE_FLIGHT, DockingState.APPROACHING, DockingState.DOCKING,
                  DockingState.DOCKED, DockingState.UNDOCKING):
        manager.target_station = station
        manager.docking_state = state
        manager.docking_timer = 0.7
        engine.states[GameStates.PLAYING].render(engine.screen)
