"""Comprehensive tests for the advanced debris physics system."""

import pygame
from src.entities.debris import Debris, DebrisType, DebrisPhysics
from src.systems.debris_field_manager import DebrisFieldManager, SpatialGrid
from pygame import Vector2

pygame.init()


def test_debris_types():
    """Test different debris types and their properties."""
    metal = Debris(100, 100, DebrisType.METAL)
    assert metal.debris_type == DebrisType.METAL
    assert metal.mass > 0
    assert metal.magnetic == True
    assert metal.restitution == 0.6

    ice = Debris(200, 200, DebrisType.ICE)
    assert ice.debris_type == DebrisType.ICE
    assert hasattr(ice, 'sublimation_rate')
    assert ice.magnetic == False
    assert ice.mass < metal.mass  # Ice should be lighter

    ship_part = Debris(300, 300, DebrisType.SHIP_PART)
    assert ship_part.debris_type == DebrisType.SHIP_PART
    assert hasattr(ship_part, 'salvage_value')
    assert ship_part.magnetic == True

    asteroid = Debris(400, 400, DebrisType.ASTEROID_CHUNK)
    assert asteroid.debris_type == DebrisType.ASTEROID_CHUNK
    assert asteroid.mass > metal.mass  # Asteroid should be heaviest
    assert asteroid.magnetic == False


def test_debris_physics():
    """Test debris physics calculations."""
    debris1 = Debris(100, 100, DebrisType.METAL)
    debris2 = Debris(200, 200, DebrisType.ASTEROID_CHUNK)

    gravity_force = DebrisPhysics.calculate_gravity(debris1, debris2)
    assert isinstance(gravity_force, Vector2)

    # Move debris closer and set velocities moving towards each other
    debris1.position = Vector2(100, 100)
    debris2.position = Vector2(110, 100)
    debris1.velocity = Vector2(-10, 0)
    debris2.velocity = Vector2(10, 0)

    DebrisPhysics.calculate_collision_response(debris1, debris2)

    # Velocities should change after collision (objects should bounce)
    assert debris1.velocity.x != -10 or debris2.velocity.x != 10


def test_debris_update():
    """Test debris update mechanics."""
    debris = Debris(100, 100, DebrisType.METAL)
    original_position = Vector2(debris.position)
    original_rotation = debris.rotation

    debris.update(1.0)

    if debris.velocity.length() > 0:
        assert debris.position != original_position

    if debris.angular_velocity != 0:
        assert debris.rotation != original_rotation

    assert debris.age > 0


def test_debris_collision():
    """Test debris-to-debris collision."""
    debris1 = Debris(100, 100, DebrisType.METAL)
    debris2 = Debris(110, 110, DebrisType.ICE)

    debris1.velocity = Vector2(10, 0)
    debris2.velocity = Vector2(-10, 0)

    collision_occurred = debris1.collide_with(debris2)
    assert collision_occurred
    assert len(debris1.collision_sparks) > 0


def test_debris_fragmentation():
    """Test debris fragmentation."""
    large_debris = Debris(100, 100, DebrisType.SHIP_PART)
    large_debris.size = 30  # Make it large enough to fragment

    fragments = large_debris.fragment(3)

    assert len(fragments) == 3
    assert all(fragment.size < large_debris.size for fragment in fragments)
    assert all(fragment.debris_type == large_debris.debris_type for fragment in fragments)

    # Small debris shouldn't fragment
    small_debris = Debris(200, 200, DebrisType.ICE)
    small_debris.size = 5

    fragments = small_debris.fragment()
    assert len(fragments) == 0


def test_spatial_grid():
    """Test spatial grid for collision optimization."""
    grid = SpatialGrid(cell_size=100)

    debris1 = Debris(50, 50, DebrisType.METAL)
    debris2 = Debris(150, 150, DebrisType.ICE)
    debris3 = Debris(250, 250, DebrisType.SHIP_PART)

    grid.add_debris(debris1)
    grid.add_debris(debris2)
    grid.add_debris(debris3)

    nearby = grid.get_nearby_debris(Vector2(100, 100), 100)
    assert debris1 in nearby
    assert debris2 in nearby
    assert debris3 not in nearby

    collisions = grid.get_potential_collisions(debris1)
    assert isinstance(collisions, list)


def test_debris_field_manager():
    """Test debris field manager."""
    manager = DebrisFieldManager()

    debris = Debris(100, 100, DebrisType.METAL)
    manager.add_debris(debris)

    assert debris in manager.debris_list
    assert manager.stats['total_debris'] == 1

    center = Vector2(500, 500)
    created_debris = manager.create_debris_field(center, 100, 10)
    assert len(created_debris) == 10
    assert all(d in manager.debris_list for d in created_debris)

    explosion_debris = manager.create_explosion_debris(center, 50, 5)
    assert len(explosion_debris) == 5

    orbital_debris = manager.create_orbital_debris(center, 200, 8)
    assert len(orbital_debris) == 8

    manager.update(1.0)
    assert len(manager.debris_list) > 0

    stats = manager.get_stats()
    assert 'total_debris' in stats
    assert 'active_debris' in stats


def test_debris_visual_effects():
    """Test debris visual effects."""
    debris = Debris(100, 100, DebrisType.METAL)

    # High velocity (> 10) generates a particle trail
    debris.velocity = Vector2(50, 0)
    debris.update(0.1)

    assert len(debris.particle_trail) > 0

    other_debris = Debris(110, 110, DebrisType.ICE)
    debris.collide_with(other_debris)

    assert len(debris.collision_sparks) > 0


def test_debris_lifecycle():
    """Test debris lifecycle management."""
    debris = Debris(100, 100, DebrisType.ICE)

    assert not debris.is_expired()
    assert debris.age == 0

    debris.age = debris.lifetime + 1
    assert debris.is_expired()

    ice_debris = Debris(200, 200, DebrisType.ICE)
    original_size = ice_debris.size

    for _ in range(100):
        ice_debris.update(1.0)

    assert ice_debris.size < original_size  # Sublimation shrinks ice


def test_performance_features():
    """Test performance optimization features."""
    manager = DebrisFieldManager()

    # Create more debris than max_debris_count to test the cap
    for i in range(600):
        debris = Debris(i * 10, i * 10, DebrisType.METAL)
        manager.add_debris(debris)

    assert len(manager.debris_list) <= manager.max_debris_count

    grid = SpatialGrid()
    for i in range(100):
        debris = Debris(i * 5, i * 5, DebrisType.METAL)
        grid.add_debris(debris)

    assert len(grid.grid) > 0
