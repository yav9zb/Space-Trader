"""The debris simulation was most of a flight frame. These tests pin the
optimised neighbour search and gravity sum to the plain versions they replaced,
so the speed-up cannot change how debris behaves."""

import math
import random

from pygame import Vector2

from src.entities.debris import Debris, DebrisPhysics, DebrisType
from src.systems.debris_field_manager import SpatialGrid


def _field(seed, count=140, spread=700):
    rng = random.Random(seed)
    kinds = [DebrisType.METAL, DebrisType.ICE, DebrisType.SHIP_PART,
             DebrisType.ASTEROID_CHUNK]
    pieces = []
    for _ in range(count):
        d = Debris(rng.uniform(0, spread), rng.uniform(0, spread), rng.choice(kinds))
        d.velocity = Vector2(rng.uniform(-20, 20), rng.uniform(-20, 20))
        pieces.append(d)
    return pieces


def _reference_nearby(grid, position, radius):
    out = []
    cell_radius = int(math.ceil(radius / grid.cell_size))
    cx, cy = grid._get_cell_key(position)
    for xo in range(-cell_radius, cell_radius + 1):
        for yo in range(-cell_radius, cell_radius + 1):
            for d in grid.grid.get((cx + xo, cy + yo), []):
                if (d.position - position).length() <= radius:
                    out.append(d)
    return out


def _reference_update_acceleration(piece, nearby):
    acceleration = Vector2(0, 0)
    for other in nearby:
        if other != piece:
            acceleration += DebrisPhysics.calculate_gravity(piece, other) / piece.mass
    return acceleration


def test_nearby_search_matches_the_plain_version():
    for seed in range(4):
        pieces = _field(seed)
        grid = SpatialGrid()
        for p in pieces:
            grid.add_debris(p)
        for p in pieces[:40]:
            for radius in (30, 90, 300):
                got = grid.get_nearby_debris(p.position, radius)
                want = _reference_nearby(grid, p.position, radius)
                assert [id(x) for x in got] == [id(x) for x in want]


def test_gravity_sum_matches_the_pairwise_calls():
    for seed in range(4):
        pieces = _field(seed)
        for p in pieces[:40]:
            nearby = [o for o in pieces if (o.position - p.position).length() <= 300]
            want = _reference_update_acceleration(p, nearby)
            probe = Debris(p.position.x, p.position.y, p.debris_type)
            probe.size, probe.mass = p.size, p.mass
            probe.position = Vector2(p.position)
            probe.velocity = Vector2(0, 0)
            probe.friction = 1.0
            probe.update(0.0, nearby if p in nearby else nearby + [p])
            assert math.isclose(probe.acceleration.x, want.x, rel_tol=1e-9, abs_tol=1e-9)
            assert math.isclose(probe.acceleration.y, want.y, rel_tol=1e-9, abs_tol=1e-9)


def test_debris_beyond_the_view_is_simulated_a_quarter_as_often():
    from src.systems.debris_field_manager import DebrisFieldManager

    manager = DebrisFieldManager()
    manager.enable_collisions = False
    near = Debris(100, 0, DebrisType.METAL)
    far = Debris(5000, 0, DebrisType.METAL)
    for piece in (near, far):
        piece.velocity = Vector2(0, 0)
        piece.lifetime = 1e9
        manager.add_debris(piece)

    for _ in range(8):
        manager.update(0.1, Vector2(0, 0), near_radius=1000)

    assert math.isclose(near.age, 0.8)
    # Updated on every fourth frame, each time with the time it missed
    assert math.isclose(far.age, 0.8)


def test_the_view_radius_follows_the_window_size(monkeypatch):
    import pygame
    from src.engine.game_engine import GameEngine
    from src.states.game_state import GameStates

    engine = GameEngine()
    engine.create_new_universe(seed=5)
    engine.change_state(GameStates.PLAYING)
    seen = []
    monkeypatch.setattr(engine.universe, "update",
                        lambda dt, focus=None, near_radius=None: seen.append(near_radius))
    engine.update()
    width, height = engine.WINDOW_SIZE
    assert seen and math.isclose(seen[0], math.hypot(width, height) / 2 + 300)
