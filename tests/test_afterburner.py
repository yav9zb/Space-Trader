"""Tests for afterburner and emergency fuel functionality on Ship."""

import pygame
from src.entities.ship import Ship

pygame.init()


def test_afterburner_initialization():
    """Test that afterburner system initializes correctly."""
    ship = Ship(400, 300)

    assert hasattr(ship, 'afterburner_active')
    assert hasattr(ship, 'afterburner_cooldown')
    assert hasattr(ship, 'afterburner_max_cooldown')
    assert hasattr(ship, 'afterburner_speed_multiplier')
    assert hasattr(ship, 'afterburner_fuel_multiplier')

    assert ship.afterburner_active == False
    assert ship.afterburner_cooldown == 0.0
    assert ship.afterburner_max_cooldown == 3.0
    assert ship.afterburner_speed_multiplier == 2.0
    assert ship.afterburner_fuel_multiplier == 5.0


def test_afterburner_status():
    """Test afterburner status method."""
    ship = Ship(400, 300)

    status = ship.get_afterburner_status()

    assert 'active' in status
    assert 'cooldown' in status
    assert 'max_cooldown' in status
    assert 'ready' in status
    assert 'speed_multiplier' in status
    assert 'fuel_multiplier' in status

    assert status['active'] == False
    assert status['cooldown'] == 0.0
    assert status['ready'] == True


def test_afterburner_cooldown():
    """Test afterburner cooldown system."""
    ship = Ship(400, 300)

    ship.afterburner_active = True
    ship.afterburner_active = False
    ship.afterburner_cooldown = ship.afterburner_max_cooldown

    ship.update(1.0)  # 1 second
    assert ship.afterburner_cooldown == 2.0

    ship.update(2.5)  # 2.5 more seconds
    assert ship.afterburner_cooldown == 0.0


def test_afterburner_fuel_consumption():
    """Test afterburner fuel consumption."""
    ship = Ship(400, 300)

    initial_fuel = ship.current_fuel
    ship.thrusting = True

    ship.update(1.0)  # 1 second
    normal_consumption = initial_fuel - ship.current_fuel

    ship.current_fuel = initial_fuel

    ship.afterburner_active = True
    ship.thrusting = True
    ship.update(1.0)  # 1 second
    afterburner_consumption = initial_fuel - ship.current_fuel

    assert afterburner_consumption > normal_consumption
    assert afterburner_consumption == normal_consumption * ship.afterburner_fuel_multiplier


def test_emergency_fuel_system():
    """Test emergency fuel system functionality."""
    ship = Ship(400, 300)

    ship.current_fuel = 0.0
    ship.emergency_fuel_active = True

    ship.thrusting = True
    thrust_force = ship.get_effective_stats().get_effective_thrust_force()
    thrust_force *= ship.emergency_fuel_speed_multiplier
    ship.acceleration = ship.heading * thrust_force

    assert ship.acceleration.length() > 0

    initial_fuel = ship.current_fuel
    ship.update(1.0)
    assert ship.current_fuel == initial_fuel  # No fuel consumed

    ship.current_fuel = 50.0
    ship.emergency_fuel_active = False
    assert ship.emergency_fuel_active == False


def test_emergency_fuel_status():
    """Test emergency fuel status method."""
    ship = Ship(400, 300)

    status = ship.get_emergency_fuel_status()
    assert status['active'] == False
    assert status['speed_multiplier'] == 0.25

    ship.current_fuel = 0.0
    ship.emergency_fuel_active = True

    status = ship.get_emergency_fuel_status()
    assert status['active'] == True


def test_afterburner_emergency_fuel_interaction():
    """Test that afterburner is disabled during emergency fuel."""
    ship = Ship(400, 300)

    ship.current_fuel = 0.0
    ship.emergency_fuel_active = True

    ship.thrusting = True
    afterburner_input = True

    # Should not activate afterburner during emergency fuel
    assert not (afterburner_input and ship.afterburner_cooldown <= 0 and ship.current_fuel > 0 and not ship.emergency_fuel_active)
