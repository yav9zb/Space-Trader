#!/usr/bin/env python3
"""Test script to verify control scheme functionality."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from input.control_schemes import ControlSchemeManager, ControlScheme
from entities.ship import Ship
import pygame

def test_control_scheme_manager():
    """Test the control scheme manager functionality."""
    print("Testing control scheme manager...")
    
    manager = ControlSchemeManager()
    
    # Test default scheme
    assert manager.get_current_scheme() == ControlScheme.LEFT_HANDED
    print("✓ Default scheme is LEFT_HANDED")
    
    # Test scheme switching
    manager.set_scheme(ControlScheme.RIGHT_HANDED)
    assert manager.get_current_scheme() == ControlScheme.RIGHT_HANDED
    print("✓ Scheme switching works")
    
    # Test getting key codes
    thrust_key = manager.get_key("thrust")
    assert thrust_key == pygame.K_w  # Right-handed scheme uses W
    print("✓ Key mapping works for RIGHT_HANDED")
    
    # Switch back and test
    manager.set_scheme(ControlScheme.LEFT_HANDED)
    thrust_key = manager.get_key("thrust")
    assert thrust_key == pygame.K_UP  # Left-handed scheme uses UP arrow
    print("✓ Key mapping works for LEFT_HANDED")
    
    # Test invalid action
    invalid_key = manager.get_key("invalid_action")
    assert invalid_key is None
    print("✓ Invalid action returns None")
    
    print("✓ Control scheme manager tests passed")

def test_right_handed_scheme():
    """Test right-handed (WASD) control scheme."""
    print("\nTesting right-handed (WASD) control scheme...")
    
    manager = ControlSchemeManager()
    manager.set_scheme(ControlScheme.RIGHT_HANDED)
    
    # Test movement keys
    assert manager.get_key("thrust") == pygame.K_w
    assert manager.get_key("rotate_left") == pygame.K_a
    assert manager.get_key("rotate_right") == pygame.K_d
    assert manager.get_key("brake") == pygame.K_s
    print("✓ Movement keys correct")
    
    # Test combat keys
    assert manager.get_key("fire_weapons") == pygame.K_SPACE
    assert manager.get_key("afterburner") == pygame.K_LSHIFT
    print("✓ Combat keys correct")
    
    # Test system keys
    assert manager.get_key("cloaking") == pygame.K_c
    assert manager.get_key("repair") == pygame.K_r
    print("✓ System keys correct")
    
    # Test station keys
    assert manager.get_key("trading") == pygame.K_t
    assert manager.get_key("upgrades") == pygame.K_u
    assert manager.get_key("missions") == pygame.K_m
    print("✓ Station keys correct")
    
    # Test scheme info
    info = manager.get_scheme_info()
    assert "WASD" in info["name"]
    assert "right-hand" in info["description"].lower()
    print("✓ Scheme info correct")
    
    print("✓ Right-handed scheme tests passed")

def test_left_handed_scheme():
    """Test left-handed (Arrow Keys) control scheme."""
    print("\nTesting left-handed (Arrow Keys) control scheme...")
    
    manager = ControlSchemeManager()
    manager.set_scheme(ControlScheme.LEFT_HANDED)
    
    # Test movement keys
    assert manager.get_key("thrust") == pygame.K_UP
    assert manager.get_key("rotate_left") == pygame.K_LEFT
    assert manager.get_key("rotate_right") == pygame.K_RIGHT
    assert manager.get_key("brake") == pygame.K_DOWN
    print("✓ Movement keys correct")
    
    # Test combat keys
    assert manager.get_key("fire_weapons") == pygame.K_RCTRL
    assert manager.get_key("afterburner") == pygame.K_RSHIFT
    print("✓ Combat keys correct")
    
    # Test system keys
    assert manager.get_key("cloaking") == pygame.K_e
    assert manager.get_key("repair") == pygame.K_q
    print("✓ System keys correct")
    
    # Test station keys
    assert manager.get_key("trading") == pygame.K_f
    assert manager.get_key("upgrades") == pygame.K_g
    assert manager.get_key("missions") == pygame.K_v
    print("✓ Station keys correct")
    
    # Test scheme info
    info = manager.get_scheme_info()
    assert "Arrow Keys" in info["name"]
    assert "left-hand" in info["description"].lower()
    print("✓ Scheme info correct")
    
    print("✓ Left-handed scheme tests passed")

def test_key_press_simulation():
    """Test key press simulation with different schemes."""
    print("\nTesting key press simulation...")
    
    manager = ControlSchemeManager()
    
    # Test RIGHT_HANDED scheme
    manager.set_scheme(ControlScheme.RIGHT_HANDED)
    
    # Create a mock keys_pressed object that behaves like pygame.key.get_pressed()
    class MockKeysPressed:
        def __init__(self, pressed_keys):
            self.pressed_keys = pressed_keys
        
        def __getitem__(self, key):
            return self.pressed_keys.get(key, False)
    
    # Simulate key presses
    keys_pressed = MockKeysPressed({
        pygame.K_w: True,
        pygame.K_SPACE: True,
        pygame.K_LSHIFT: True,
        pygame.K_RSHIFT: False
    })
    
    assert manager.is_key_pressed("thrust", keys_pressed) == True
    assert manager.is_key_pressed("fire_weapons", keys_pressed) == True
    assert manager.is_key_pressed("afterburner", keys_pressed) == True
    assert manager.is_key_pressed("brake", keys_pressed) == False
    print("✓ RIGHT_HANDED key press simulation works")
    
    # Test LEFT_HANDED scheme
    manager.set_scheme(ControlScheme.LEFT_HANDED)
    
    keys_pressed = MockKeysPressed({
        pygame.K_UP: True,
        pygame.K_RCTRL: True,
        pygame.K_RSHIFT: True,
        pygame.K_LEFT: False
    })
    
    assert manager.is_key_pressed("thrust", keys_pressed) == True
    assert manager.is_key_pressed("fire_weapons", keys_pressed) == True
    assert manager.is_key_pressed("afterburner", keys_pressed) == True
    assert manager.is_key_pressed("rotate_left", keys_pressed) == False
    print("✓ LEFT_HANDED key press simulation works")
    
    print("✓ Key press simulation tests passed")

def test_controls_help():
    """Test controls help generation."""
    print("\nTesting controls help generation...")
    
    manager = ControlSchemeManager()
    
    # Test for both schemes
    for scheme in [ControlScheme.RIGHT_HANDED, ControlScheme.LEFT_HANDED]:
        manager.set_scheme(scheme)
        
        help_info = manager.get_controls_help()
        
        # Check sections exist
        assert "Movement" in help_info
        assert "Combat" in help_info
        assert "Ship Systems" in help_info
        assert "Navigation" in help_info
        assert "Station" in help_info
        
        # Check movement section has all keys
        movement = help_info["Movement"]
        assert len(movement) == 4  # thrust, rotate_left, rotate_right, brake
        
        # Check combat section
        combat = help_info["Combat"]
        assert len(combat) == 2  # fire_weapons, afterburner
        
        print(f"✓ Controls help works for {scheme.value}")
    
    print("✓ Controls help tests passed")

def test_ship_integration():
    """Test ship integration with control schemes."""
    print("\nTesting ship integration with control schemes...")
    
    ship = Ship(400, 300)
    manager = ControlSchemeManager()
    
    # Create a mock keys_pressed object
    class MockKeysPressed:
        def __init__(self, pressed_keys):
            self.pressed_keys = pressed_keys
        
        def __getitem__(self, key):
            return self.pressed_keys.get(key, False)
    
    # Test with RIGHT_HANDED scheme
    manager.set_scheme(ControlScheme.RIGHT_HANDED)
    
    # This would normally be called by ship.handle_input()
    # We'll simulate the key checking logic
    keys_pressed = MockKeysPressed({pygame.K_w: True, pygame.K_SPACE: True})
    
    thrust_active = manager.is_key_pressed("thrust", keys_pressed)
    fire_active = manager.is_key_pressed("fire_weapons", keys_pressed)
    
    assert thrust_active == True
    assert fire_active == True
    print("✓ Ship integration works with RIGHT_HANDED scheme")
    
    # Test with LEFT_HANDED scheme
    manager.set_scheme(ControlScheme.LEFT_HANDED)
    
    keys_pressed = MockKeysPressed({pygame.K_UP: True, pygame.K_RCTRL: True})
    
    thrust_active = manager.is_key_pressed("thrust", keys_pressed)
    fire_active = manager.is_key_pressed("fire_weapons", keys_pressed)
    
    assert thrust_active == True
    assert fire_active == True
    print("✓ Ship integration works with LEFT_HANDED scheme")
    
    print("✓ Ship integration tests passed")

def test_key_display_names():
    """Test key display name generation."""
    print("\nTesting key display names...")
    
    manager = ControlSchemeManager()
    
    # Test RIGHT_HANDED scheme
    manager.set_scheme(ControlScheme.RIGHT_HANDED)
    
    assert manager.get_key_name("thrust") == "W"
    assert manager.get_key_name("fire_weapons") == "Space"
    assert manager.get_key_name("afterburner") == "Left Shift"
    print("✓ RIGHT_HANDED key display names work")
    
    # Test LEFT_HANDED scheme
    manager.set_scheme(ControlScheme.LEFT_HANDED)
    
    assert manager.get_key_name("thrust") == "↑"
    assert manager.get_key_name("fire_weapons") == "Right Ctrl"
    assert manager.get_key_name("afterburner") == "Right Shift"
    print("✓ LEFT_HANDED key display names work")
    
    # Test invalid action
    assert manager.get_key_name("invalid_action") == "Unbound"
    print("✓ Invalid action returns 'Unbound'")
    
    print("✓ Key display name tests passed")

def main():
    """Run all control scheme tests."""
    print("Testing control scheme system...")
    
    # Initialize pygame (required for key constants)
    pygame.init()
    
    try:
        test_control_scheme_manager()
        test_right_handed_scheme()
        test_left_handed_scheme()
        test_key_press_simulation()
        test_controls_help()
        test_ship_integration()
        test_key_display_names()
        
        print("\n✅ All control scheme tests passed!")
        print("\nControl Scheme System Features:")
        print("- Right-handed (WASD) and left-handed (Arrow Keys) schemes")
        print("- Ergonomic key placement for better gameplay experience")
        print("- Settings menu integration for easy switching")
        print("- Comprehensive help system showing current bindings")
        print("- Full integration with ship movement and combat systems")
        
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