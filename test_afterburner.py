#!/usr/bin/env python3
"""Simple test script to verify afterburner functionality."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from entities.ship import Ship
from pygame import Vector2
import pygame

def test_afterburner_initialization():
    """Test that afterburner system initializes correctly."""
    ship = Ship(400, 300)
    
    # Check afterburner attributes exist
    assert hasattr(ship, 'afterburner_active')
    assert hasattr(ship, 'afterburner_cooldown')
    assert hasattr(ship, 'afterburner_max_cooldown')
    assert hasattr(ship, 'afterburner_speed_multiplier')
    assert hasattr(ship, 'afterburner_fuel_multiplier')
    
    # Check initial values
    assert ship.afterburner_active == False
    assert ship.afterburner_cooldown == 0.0
    assert ship.afterburner_max_cooldown == 3.0
    assert ship.afterburner_speed_multiplier == 2.0
    assert ship.afterburner_fuel_multiplier == 5.0
    
    print("✓ Afterburner initialization test passed")

def test_afterburner_status():
    """Test afterburner status method."""
    ship = Ship(400, 300)
    
    status = ship.get_afterburner_status()
    
    # Check status dictionary structure
    assert 'active' in status
    assert 'cooldown' in status
    assert 'max_cooldown' in status
    assert 'ready' in status
    assert 'speed_multiplier' in status
    assert 'fuel_multiplier' in status
    
    # Check initial status
    assert status['active'] == False
    assert status['cooldown'] == 0.0
    assert status['ready'] == True
    
    print("✓ Afterburner status test passed")

def test_afterburner_cooldown():
    """Test afterburner cooldown system."""
    ship = Ship(400, 300)
    
    # Simulate afterburner activation and deactivation
    ship.afterburner_active = True
    ship.afterburner_active = False
    ship.afterburner_cooldown = ship.afterburner_max_cooldown
    
    # Update ship to process cooldown
    ship.update(1.0)  # 1 second
    
    # Check cooldown decreased
    assert ship.afterburner_cooldown == 2.0
    
    # Update more to clear cooldown
    ship.update(2.5)  # 2.5 more seconds
    
    # Check cooldown is cleared
    assert ship.afterburner_cooldown == 0.0
    
    print("✓ Afterburner cooldown test passed")

def test_afterburner_fuel_consumption():
    """Test afterburner fuel consumption."""
    ship = Ship(400, 300)
    
    # Set up initial fuel
    initial_fuel = ship.current_fuel
    ship.thrusting = True
    
    # Test normal fuel consumption
    ship.update(1.0)  # 1 second
    normal_consumption = initial_fuel - ship.current_fuel
    
    # Reset fuel
    ship.current_fuel = initial_fuel
    
    # Test afterburner fuel consumption
    ship.afterburner_active = True
    ship.thrusting = True
    ship.update(1.0)  # 1 second
    afterburner_consumption = initial_fuel - ship.current_fuel
    
    # Check that afterburner consumes more fuel
    assert afterburner_consumption > normal_consumption
    assert afterburner_consumption == normal_consumption * ship.afterburner_fuel_multiplier
    
    print("✓ Afterburner fuel consumption test passed")

def main():
    """Run all afterburner tests."""
    print("Testing afterburner system...")
    
    # Initialize pygame (required for Vector2)
    pygame.init()
    
    try:
        test_afterburner_initialization()
        test_afterburner_status()
        test_afterburner_cooldown()
        test_afterburner_fuel_consumption()
        
        print("\n✅ All afterburner tests passed!")
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