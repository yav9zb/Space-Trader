import pytest
from src.entities.debris import Debris, DebrisType
from pygame import Vector2

def test_debris_initialization():
    debris = Debris(50, 75, DebrisType.METAL)
    assert debris.position == Vector2(50, 75)
    assert isinstance(debris.velocity, Vector2)
    assert 8 <= debris.size <= 25  # METAL size range
    assert 0 <= debris.rotation <= 360
    assert debris.color == (120, 120, 130)  # METAL color

def test_debris_velocity_range():
    debris = Debris(0, 0)
    assert -20 <= debris.velocity.x <= 20
    assert -20 <= debris.velocity.y <= 20

def test_debris_angular_velocity_range():
    debris = Debris(0, 0)
    assert -30 <= debris.angular_velocity <= 30

def test_debris_update():
    debris = Debris(0, 0)
    initial_position = debris.position.copy()
    initial_rotation = debris.rotation
    initial_age = debris.age

    debris.update(0.1)

    assert debris.age == pytest.approx(initial_age + 0.1)

    # Position should change based on velocity
    if debris.velocity.length() > 0:
        assert debris.position != initial_position

    # Rotation should change based on angular velocity
    if debris.angular_velocity != 0:
        assert debris.rotation != initial_rotation

def test_debris_movement():
    debris = Debris(100, 100, DebrisType.METAL)
    debris.velocity = Vector2(10, 5)

    debris.update(0.1)

    # Space friction is applied before integrating position
    expected_velocity = Vector2(10, 5) * debris.friction
    expected_position = Vector2(100, 100) + expected_velocity * 0.1

    assert debris.position.x == pytest.approx(expected_position.x)
    assert debris.position.y == pytest.approx(expected_position.y)

def test_debris_rotation_update():
    debris = Debris(0, 0)
    debris.rotation = 0
    debris.angular_velocity = 90  # degrees per second

    debris.update(0.1)

    # Angular velocity decays slightly (x0.999) before being integrated
    expected_rotation = (90 * 0.999) * 0.1
    assert debris.rotation == pytest.approx(expected_rotation)
