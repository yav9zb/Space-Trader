#!/usr/bin/env python3
"""Comprehensive test for advanced debris physics system."""

import sys
import os
import math

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from entities.debris import Debris, DebrisType, DebrisPhysics
from systems.debris_field_manager import DebrisFieldManager, SpatialGrid
from pygame import Vector2
import pygame

def test_debris_types():
    """Test different debris types and their properties."""
    print("Testing debris types...")
    
    # Test metal debris
    metal = Debris(100, 100, DebrisType.METAL)
    assert metal.debris_type == DebrisType.METAL
    assert metal.mass > 0
    assert metal.magnetic == True
    assert metal.restitution == 0.6
    print("✓ Metal debris properties correct")
    
    # Test ice debris
    ice = Debris(200, 200, DebrisType.ICE)
    assert ice.debris_type == DebrisType.ICE
    assert hasattr(ice, 'sublimation_rate')
    assert ice.magnetic == False
    assert ice.mass < metal.mass  # Ice should be lighter
    print("✓ Ice debris properties correct")
    
    # Test ship part debris
    ship_part = Debris(300, 300, DebrisType.SHIP_PART)
    assert ship_part.debris_type == DebrisType.SHIP_PART
    assert hasattr(ship_part, 'salvage_value')
    assert ship_part.magnetic == True
    print("✓ Ship part debris properties correct")
    
    # Test asteroid chunk
    asteroid = Debris(400, 400, DebrisType.ASTEROID_CHUNK)
    assert asteroid.debris_type == DebrisType.ASTEROID_CHUNK
    assert asteroid.mass > metal.mass  # Asteroid should be heaviest
    assert asteroid.magnetic == False
    print("✓ Asteroid chunk debris properties correct")
    
    print("✓ All debris types test passed")

def test_debris_physics():
    """Test debris physics calculations."""
    print("\nTesting debris physics...")
    
    # Create two debris pieces
    debris1 = Debris(100, 100, DebrisType.METAL)
    debris2 = Debris(200, 200, DebrisType.ASTEROID_CHUNK)
    
    # Test gravity calculation
    gravity_force = DebrisPhysics.calculate_gravity(debris1, debris2)
    assert isinstance(gravity_force, Vector2)
    print("✓ Gravity calculation works")
    
    # Test collision response
    # Move debris closer for collision and set velocities moving towards each other
    debris1.position = Vector2(100, 100)
    debris2.position = Vector2(110, 100)  # To the right of debris1
    debris1.velocity = Vector2(-10, 0)    # Moving left towards debris2
    debris2.velocity = Vector2(10, 0)     # Moving right towards debris1
    
    DebrisPhysics.calculate_collision_response(debris1, debris2)
    
    # Velocities should change after collision (objects should bounce)
    assert debris1.velocity.x != -10 or debris2.velocity.x != 10
    print("✓ Collision response works")
    
    print("✓ Debris physics tests passed")

def test_debris_update():
    """Test debris update mechanics."""
    print("\nTesting debris update mechanics...")
    
    debris = Debris(100, 100, DebrisType.METAL)
    original_position = Vector2(debris.position)
    original_rotation = debris.rotation
    
    # Update debris
    debris.update(1.0)  # 1 second
    
    # Position should change based on velocity
    if debris.velocity.length() > 0:
        assert debris.position != original_position
    
    # Rotation should change based on angular velocity
    if debris.angular_velocity != 0:
        assert debris.rotation != original_rotation
    
    # Age should increase
    assert debris.age > 0
    
    print("✓ Debris update mechanics work")

def test_debris_collision():
    """Test debris-to-debris collision."""
    print("\nTesting debris-to-debris collision...")
    
    debris1 = Debris(100, 100, DebrisType.METAL)
    debris2 = Debris(110, 110, DebrisType.ICE)
    
    # Set initial velocities
    debris1.velocity = Vector2(10, 0)
    debris2.velocity = Vector2(-10, 0)
    
    # Test collision
    collision_occurred = debris1.collide_with(debris2)
    assert collision_occurred
    
    # Check collision effects
    assert len(debris1.collision_sparks) > 0
    print("✓ Debris collision detection works")
    
    print("✓ Debris collision tests passed")

def test_debris_fragmentation():
    """Test debris fragmentation."""
    print("\nTesting debris fragmentation...")
    
    large_debris = Debris(100, 100, DebrisType.SHIP_PART)
    large_debris.size = 30  # Make it large enough to fragment
    
    # Fragment the debris
    fragments = large_debris.fragment(3)
    
    assert len(fragments) == 3
    assert all(fragment.size < large_debris.size for fragment in fragments)
    assert all(fragment.debris_type == large_debris.debris_type for fragment in fragments)
    print("✓ Debris fragmentation works")
    
    # Test small debris doesn't fragment
    small_debris = Debris(200, 200, DebrisType.ICE)
    small_debris.size = 5
    
    fragments = small_debris.fragment()
    assert len(fragments) == 0
    print("✓ Small debris doesn't fragment")
    
    print("✓ Debris fragmentation tests passed")

def test_spatial_grid():
    """Test spatial grid for collision optimization."""
    print("\nTesting spatial grid...")
    
    grid = SpatialGrid(cell_size=100)
    
    # Add debris to grid
    debris1 = Debris(50, 50, DebrisType.METAL)
    debris2 = Debris(150, 150, DebrisType.ICE)
    debris3 = Debris(250, 250, DebrisType.SHIP_PART)
    
    grid.add_debris(debris1)
    grid.add_debris(debris2)
    grid.add_debris(debris3)
    
    # Test nearby debris search
    nearby = grid.get_nearby_debris(Vector2(100, 100), 100)
    assert debris1 in nearby
    assert debris2 in nearby
    assert debris3 not in nearby
    print("✓ Spatial grid nearby search works")
    
    # Test collision detection
    collisions = grid.get_potential_collisions(debris1)
    assert isinstance(collisions, list)
    print("✓ Spatial grid collision detection works")
    
    print("✓ Spatial grid tests passed")

def test_debris_field_manager():
    """Test debris field manager."""
    print("\nTesting debris field manager...")
    
    manager = DebrisFieldManager()
    
    # Test adding debris
    debris = Debris(100, 100, DebrisType.METAL)
    manager.add_debris(debris)
    
    assert debris in manager.debris_list
    assert manager.stats['total_debris'] == 1
    print("✓ Debris field manager add works")
    
    # Test creating debris field
    center = Vector2(500, 500)
    created_debris = manager.create_debris_field(center, 100, 10)
    
    assert len(created_debris) == 10
    assert all(d in manager.debris_list for d in created_debris)
    print("✓ Debris field creation works")
    
    # Test explosion debris
    explosion_debris = manager.create_explosion_debris(center, 50, 5)
    assert len(explosion_debris) == 5
    print("✓ Explosion debris creation works")
    
    # Test orbital debris
    orbital_debris = manager.create_orbital_debris(center, 200, 8)
    assert len(orbital_debris) == 8
    print("✓ Orbital debris creation works")
    
    # Test update
    initial_count = len(manager.debris_list)
    manager.update(1.0)
    
    # Manager should still have debris
    assert len(manager.debris_list) > 0
    print("✓ Debris field manager update works")
    
    # Test statistics
    stats = manager.get_stats()
    assert 'total_debris' in stats
    assert 'active_debris' in stats
    print("✓ Debris field manager statistics work")
    
    print("✓ Debris field manager tests passed")

def test_debris_visual_effects():
    """Test debris visual effects."""
    print("\nTesting debris visual effects...")
    
    debris = Debris(100, 100, DebrisType.METAL)
    
    # Set high velocity to generate particle trail (needs to be > 10)
    debris.velocity = Vector2(50, 0)
    print(f"Velocity before update: {debris.velocity}, length: {debris.velocity.length()}")
    
    # Update to generate effects (use small delta_time to keep particles alive)
    debris.update(0.1)
    
    print(f"Velocity after update: {debris.velocity}, length: {debris.velocity.length()}")
    print(f"Particle trail length: {len(debris.particle_trail)}")
    
    # Should have particle trail (velocity of 49 should be > 10)
    if len(debris.particle_trail) == 0:
        print(f"No particle trail created! Velocity: {debris.velocity.length()}")
    assert len(debris.particle_trail) > 0
    print("✓ Particle trail generation works")
    
    # Create collision sparks
    other_debris = Debris(110, 110, DebrisType.ICE)
    debris.collide_with(other_debris)
    
    # Should have collision sparks
    assert len(debris.collision_sparks) > 0
    print("✓ Collision spark generation works")
    
    print("✓ Debris visual effects tests passed")

def test_debris_lifecycle():
    """Test debris lifecycle management."""
    print("\nTesting debris lifecycle...")
    
    debris = Debris(100, 100, DebrisType.ICE)
    
    # Test initial state
    assert not debris.is_expired()
    assert debris.age == 0
    
    # Age the debris
    debris.age = debris.lifetime + 1
    assert debris.is_expired()
    print("✓ Debris expiration works")
    
    # Test ice sublimation
    ice_debris = Debris(200, 200, DebrisType.ICE)
    original_size = ice_debris.size
    
    # Simulate sublimation
    for _ in range(100):
        ice_debris.update(1.0)
    
    # Size should decrease due to sublimation
    assert ice_debris.size < original_size
    print("✓ Ice sublimation works")
    
    print("✓ Debris lifecycle tests passed")

def test_performance_features():
    """Test performance optimization features."""
    print("\nTesting performance features...")
    
    manager = DebrisFieldManager()
    
    # Create many debris to test performance limits
    for i in range(600):  # Exceed max_debris_count
        debris = Debris(i * 10, i * 10, DebrisType.METAL)
        manager.add_debris(debris)
    
    # Manager should limit debris count
    assert len(manager.debris_list) <= manager.max_debris_count
    print("✓ Performance limiting works")
    
    # Test spatial grid performance
    grid = SpatialGrid()
    for i in range(100):
        debris = Debris(i * 5, i * 5, DebrisType.METAL)
        grid.add_debris(debris)
    
    # Grid should have organized debris
    assert len(grid.grid) > 0
    print("✓ Spatial grid organization works")
    
    print("✓ Performance features tests passed")

def main():
    """Run all advanced debris physics tests."""
    print("Testing advanced debris physics system...")
    
    # Initialize pygame (required for Vector2)
    pygame.init()
    
    try:
        test_debris_types()
        test_debris_physics()
        test_debris_update()
        test_debris_collision()
        test_debris_fragmentation()
        test_spatial_grid()
        test_debris_field_manager()
        test_debris_visual_effects()
        test_debris_lifecycle()
        test_performance_features()
        
        print("\n✅ All advanced debris physics tests passed!")
        print("\nAdvanced Debris Physics Features:")
        print("- 4 distinct debris types with unique properties")
        print("- Realistic physics with gravity, collisions, and momentum")
        print("- Particle trails and collision spark effects")
        print("- Debris fragmentation and aggregation")
        print("- Spatial grid optimization for performance")
        print("- Debris field generation (sparse, dense, battle, orbital)")
        print("- Advanced collision detection and response")
        print("- Lifecycle management with expiration and sublimation")
        print("- Performance optimization with limits and culling")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        pygame.quit()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)