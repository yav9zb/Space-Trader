import pytest
from src.entities.ship import Ship
from pygame import Vector2

def test_ship_initialization():
    ship = Ship(400, 300)
    assert ship.position == Vector2(400, 300)
    assert ship.velocity == Vector2(0, 0)
    assert ship.rotation == 0

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