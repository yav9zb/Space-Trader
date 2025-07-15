import pytest
from src.entities.ship import Ship
from src.entities.station import Station
from pygame import Vector2
import math

def test_ship_initialization():
    ship = Ship(400, 300)
    assert ship.position == Vector2(400, 300)
    assert ship.velocity == Vector2(0, 0)
    assert ship.rotation == 0
    assert ship.heading == Vector2(0, -1)  # Points upward initially
    assert ship.acceleration == Vector2(0, 0)

def test_ship_movement():
    ship = Ship(400, 300)
    ship.velocity = Vector2(100, 0)
    ship.update(0.1)  # 0.1 seconds
    assert ship.position.x > 400  # Ship should move right

def test_ship_speed_limit():
    ship = Ship(400, 300)
    ship.velocity = Vector2(1000, 0)  # Try to exceed MAX_SPEED
    ship.update(0.1)
    assert ship.velocity.length() <= ship.MAX_SPEED

def test_ship_constants():
    ship = Ship(0, 0)
    assert ship.THRUST_FORCE == 300
    assert ship.DRAG_COEFFICIENT == 0.99
    assert ship.MAX_SPEED == 400
    assert ship.ROTATION_SPEED == 180
    assert ship.COLLISION_BUFFER == 5

def test_ship_characteristics():
    ship = Ship(0, 0)
    assert ship.size == 15
    assert ship.mass == 1.0
    assert len(ship.points) == 3  # Triangle shape

def test_ship_rotation():
    ship = Ship(0, 0)
    initial_rotation = ship.rotation
    
    # Test rotation changes heading
    ship.rotation = 90
    angle_rad = math.radians(ship.rotation - 90)
    expected_heading = Vector2(math.cos(angle_rad), math.sin(angle_rad))
    
    # Update heading manually (as done in handle_input)
    ship.heading = expected_heading
    
    assert ship.heading.x == pytest.approx(expected_heading.x, rel=1e-5)
    assert ship.heading.y == pytest.approx(expected_heading.y, rel=1e-5)

def test_ship_thrust():
    ship = Ship(0, 0)
    ship.thrusting = True
    ship.heading = Vector2(1, 0)  # Point right
    ship.acceleration = ship.heading * ship.THRUST_FORCE
    
    assert ship.acceleration.x == ship.THRUST_FORCE
    assert ship.acceleration.y == 0

def test_ship_drag():
    ship = Ship(0, 0)
    ship.velocity = Vector2(100, 0)
    initial_speed = ship.velocity.length()
    
    ship.update(0.1)
    
    # Velocity should be reduced by drag
    assert ship.velocity.length() < initial_speed

def test_ship_screen_wrapping():
    ship = Ship(850, 650)  # Outside screen bounds
    ship.update(0.1)
    
    # Should wrap around screen
    assert 0 <= ship.position.x <= 800
    assert 0 <= ship.position.y <= 600

def test_ship_collision_detection():
    ship = Ship(100, 100)
    station = Station(120, 120)  # Close to ship
    
    # Should detect collision
    collision = ship.check_collision_detailed(station)
    assert isinstance(collision, bool)

def test_ship_docking():
    ship = Ship(100, 100)
    ship.velocity = Vector2(10, 0)  # Slow velocity
    station = Station(110, 110)  # Close station
    
    can_dock, distance = ship.check_docking(station)
    assert isinstance(can_dock, bool)
    assert isinstance(distance, float)
    assert distance > 0

def test_ship_docking_speed_requirement():
    ship = Ship(100, 100)
    ship.velocity = Vector2(100, 0)  # Fast velocity
    station = Station(110, 110)  # Close station
    
    can_dock, distance = ship.check_docking(station)
    assert not can_dock  # Should not be able to dock at high speed