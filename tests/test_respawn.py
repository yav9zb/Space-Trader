"""Tests for respawn fuel, ammo, and system reset functionality."""

import pygame
from src.entities.ship import Ship
from src.systems.respawn_system import RespawnSystem

pygame.init()


class MockUniverse:
    """Mock universe for testing."""
    def __init__(self):
        self.stations = []


class MockGameEngine:
    """Mock game engine for testing."""
    def __init__(self):
        self.ship = Ship(400, 300)
        self.universe = MockUniverse()


def test_respawn_fuel_reset():
    """Test that fuel is reset to full on respawn."""
    game_engine = MockGameEngine()
    respawn_system = RespawnSystem()

    game_engine.ship.current_fuel = 10.0

    respawn_system._reset_ship_to_safe_state(game_engine)

    assert game_engine.ship.current_fuel == game_engine.ship.fuel_capacity


def test_respawn_ammo_reset():
    """Test that ammo is reset to starting amounts on respawn."""
    game_engine = MockGameEngine()
    respawn_system = RespawnSystem()

    game_engine.ship.ammo_storage = {
        "laser_cells": 5,
        "plasma_cartridges": 2,
        "missiles": 1,
        "railgun_slugs": 3
    }

    respawn_system._reset_ship_to_safe_state(game_engine)

    expected_ammo = {
        "laser_cells": 50,
        "plasma_cartridges": 25,
        "missiles": 10,
        "railgun_slugs": 30
    }

    assert game_engine.ship.ammo_storage == expected_ammo


def test_respawn_emergency_fuel_reset():
    """Test that emergency fuel system is reset on respawn."""
    game_engine = MockGameEngine()
    respawn_system = RespawnSystem()

    game_engine.ship.emergency_fuel_active = True

    respawn_system._reset_ship_to_safe_state(game_engine)

    assert game_engine.ship.emergency_fuel_active == False


def test_respawn_afterburner_reset():
    """Test that afterburner system is reset on respawn."""
    game_engine = MockGameEngine()
    respawn_system = RespawnSystem()

    game_engine.ship.afterburner_active = True
    game_engine.ship.afterburner_cooldown = 2.0

    respawn_system._reset_ship_to_safe_state(game_engine)

    assert game_engine.ship.afterburner_active == False
    assert game_engine.ship.afterburner_cooldown == 0.0


def test_complete_respawn_reset():
    """Test that all systems are properly reset on respawn."""
    game_engine = MockGameEngine()
    respawn_system = RespawnSystem()

    game_engine.ship.current_fuel = 5.0
    game_engine.ship.current_hull = 25.0
    game_engine.ship.credits = 5000
    game_engine.ship.emergency_fuel_active = True
    game_engine.ship.afterburner_active = True
    game_engine.ship.afterburner_cooldown = 1.5

    respawn_system._reset_ship_to_safe_state(game_engine)

    assert game_engine.ship.current_fuel == game_engine.ship.fuel_capacity
    assert game_engine.ship.current_hull == game_engine.ship.get_effective_stats().get_effective_hull_points()
    assert game_engine.ship.credits == 1000
    assert game_engine.ship.emergency_fuel_active == False
    assert game_engine.ship.afterburner_active == False
    assert game_engine.ship.afterburner_cooldown == 0.0
