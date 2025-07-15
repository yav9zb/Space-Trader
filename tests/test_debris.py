import pytest
from src.entities.debris import Debris
from pygame import Vector2

def test_debris_initialization():
    debris = Debris(50, 75)
    assert debris.position == Vector2(50, 75)
    assert isinstance(debris.velocity, Vector2)
    assert 1 <= debris.size <= 3
    assert 0 <= debris.rotation <= 360
    assert debris.color == (100, 100, 100)

def test_debris_velocity_range():
    debris = Debris(0, 0)
    assert -1 <= debris.velocity.x <= 1
    assert -1 <= debris.velocity.y <= 1

def test_debris_rotation_speed():
    debris = Debris(0, 0)
    assert -2 <= debris.rotation_speed <= 2

def test_debris_update():
    debris = Debris(0, 0)
    initial_position = debris.position.copy()
    initial_rotation = debris.rotation
    
    debris.update(0.1)
    
    # Position should change based on velocity
    if debris.velocity.length() > 0:
        assert debris.position != initial_position
    
    # Rotation should change based on rotation speed
    if debris.rotation_speed != 0:
        assert debris.rotation != initial_rotation

def test_debris_movement():
    debris = Debris(100, 100)
    debris.velocity = Vector2(10, 5)
    
    debris.update(0.1)
    
    assert debris.position.x == 101.0  # 100 + 10 * 0.1
    assert debris.position.y == 100.5  # 100 + 5 * 0.1

def test_debris_rotation_update():
    debris = Debris(0, 0)
    debris.rotation = 0
    debris.rotation_speed = 90  # 90 degrees per second
    
    debris.update(0.1)
    
    assert debris.rotation == 9.0  # 0 + 90 * 0.1