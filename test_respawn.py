#!/usr/bin/env python3
"""Test script to verify respawn fuel and ammo reset functionality."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from entities.ship import Ship
from systems.respawn_system import RespawnSystem
from pygame import Vector2
import pygame

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
    print("Testing fuel reset on respawn...")
    
    # Create mock game engine
    game_engine = MockGameEngine()
    respawn_system = RespawnSystem()
    
    # Drain fuel to simulate low fuel
    game_engine.ship.current_fuel = 10.0
    
    # Trigger respawn
    respawn_system._reset_ship_to_safe_state(game_engine)
    
    # Check fuel is reset to full
    assert game_engine.ship.current_fuel == game_engine.ship.fuel_capacity
    print("✓ Fuel reset test passed")

def test_respawn_ammo_reset():
    """Test that ammo is reset to starting amounts on respawn."""
    print("Testing ammo reset on respawn...")
    
    # Create mock game engine
    game_engine = MockGameEngine()
    respawn_system = RespawnSystem()
    
    # Drain ammo to simulate low ammo
    game_engine.ship.ammo_storage = {
        "laser_cells": 5,
        "plasma_cartridges": 2,
        "missiles": 1,
        "railgun_slugs": 3
    }
    
    # Trigger respawn
    respawn_system._reset_ship_to_safe_state(game_engine)
    
    # Check ammo is reset to starting amounts
    expected_ammo = {
        "laser_cells": 50,
        "plasma_cartridges": 25,
        "missiles": 10,
        "railgun_slugs": 30
    }
    
    assert game_engine.ship.ammo_storage == expected_ammo
    print("✓ Ammo reset test passed")

def test_respawn_emergency_fuel_reset():
    """Test that emergency fuel system is reset on respawn."""
    print("Testing emergency fuel system reset on respawn...")
    
    # Create mock game engine
    game_engine = MockGameEngine()
    respawn_system = RespawnSystem()
    
    # Activate emergency fuel
    game_engine.ship.emergency_fuel_active = True
    
    # Trigger respawn
    respawn_system._reset_ship_to_safe_state(game_engine)
    
    # Check emergency fuel is deactivated
    assert game_engine.ship.emergency_fuel_active == False
    print("✓ Emergency fuel reset test passed")

def test_respawn_afterburner_reset():
    """Test that afterburner system is reset on respawn."""
    print("Testing afterburner system reset on respawn...")
    
    # Create mock game engine
    game_engine = MockGameEngine()
    respawn_system = RespawnSystem()
    
    # Set afterburner state
    game_engine.ship.afterburner_active = True
    game_engine.ship.afterburner_cooldown = 2.0
    
    # Trigger respawn
    respawn_system._reset_ship_to_safe_state(game_engine)
    
    # Check afterburner is reset
    assert game_engine.ship.afterburner_active == False
    assert game_engine.ship.afterburner_cooldown == 0.0
    print("✓ Afterburner reset test passed")

def test_complete_respawn_reset():
    """Test that all systems are properly reset on respawn."""
    print("Testing complete respawn reset...")
    
    # Create mock game engine
    game_engine = MockGameEngine()
    respawn_system = RespawnSystem()
    
    # Set ship to damaged state
    game_engine.ship.current_fuel = 5.0
    game_engine.ship.current_hull = 25.0
    game_engine.ship.credits = 5000
    game_engine.ship.emergency_fuel_active = True
    game_engine.ship.afterburner_active = True
    game_engine.ship.afterburner_cooldown = 1.5
    
    # Trigger respawn
    respawn_system._reset_ship_to_safe_state(game_engine)
    
    # Check all systems are reset
    assert game_engine.ship.current_fuel == game_engine.ship.fuel_capacity
    assert game_engine.ship.current_hull == game_engine.ship.get_effective_stats().get_effective_hull_points()
    assert game_engine.ship.credits == 1000
    assert game_engine.ship.emergency_fuel_active == False
    assert game_engine.ship.afterburner_active == False
    assert game_engine.ship.afterburner_cooldown == 0.0
    
    print("✓ Complete respawn reset test passed")

def main():
    """Run all respawn tests."""
    print("Testing respawn fuel and ammo reset system...")
    
    # Initialize pygame (required for Vector2)
    pygame.init()
    
    try:
        test_respawn_fuel_reset()
        test_respawn_ammo_reset()
        test_respawn_emergency_fuel_reset()
        test_respawn_afterburner_reset()
        test_complete_respawn_reset()
        
        print("\n✅ All respawn tests passed!")
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