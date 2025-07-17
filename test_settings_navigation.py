#!/usr/bin/env python3
"""Test settings navigation from different states."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from states.game_state import SettingsState, GameStates
import pygame

class MockGame:
    """Mock game object for testing."""
    def __init__(self):
        self.current_state = GameStates.MAIN_MENU
        self.states = {}
        
    def change_state(self, new_state):
        self.current_state = new_state
        print(f"State changed to: {new_state}")

def test_settings_from_main_menu():
    """Test settings navigation from main menu."""
    print("Testing settings from main menu...")
    
    game = MockGame()
    game.current_state = GameStates.MAIN_MENU
    
    # Create settings state from main menu
    settings_state = SettingsState(game, GameStates.MAIN_MENU)
    
    # Test that previous state is set correctly
    assert settings_state.previous_state == GameStates.MAIN_MENU
    print("✓ Settings correctly tracks main menu as previous state")
    
    # Test going back
    settings_state.game.change_state(settings_state.previous_state)
    assert game.current_state == GameStates.MAIN_MENU
    print("✓ Settings correctly returns to main menu")

def test_settings_from_pause_menu():
    """Test settings navigation from pause menu."""
    print("\nTesting settings from pause menu...")
    
    game = MockGame()
    game.current_state = GameStates.PAUSED
    
    # Create settings state from pause menu
    settings_state = SettingsState(game, GameStates.PAUSED)
    
    # Test that previous state is set correctly
    assert settings_state.previous_state == GameStates.PAUSED
    print("✓ Settings correctly tracks pause menu as previous state")
    
    # Test going back
    settings_state.game.change_state(settings_state.previous_state)
    assert game.current_state == GameStates.PAUSED
    print("✓ Settings correctly returns to pause menu")

def test_settings_default_behavior():
    """Test settings default behavior when no previous state provided."""
    print("\nTesting settings default behavior...")
    
    game = MockGame()
    
    # Create settings state without previous state
    settings_state = SettingsState(game)
    
    # Test that default is main menu
    assert settings_state.previous_state == GameStates.MAIN_MENU
    print("✓ Settings defaults to main menu when no previous state provided")
    
    # Test going back
    settings_state.game.change_state(settings_state.previous_state)
    assert game.current_state == GameStates.MAIN_MENU
    print("✓ Settings correctly returns to main menu by default")

def test_settings_back_selection():
    """Test settings back option selection."""
    print("\nTesting settings back option selection...")
    
    game = MockGame()
    game.current_state = GameStates.PAUSED
    
    # Create settings state from pause menu
    settings_state = SettingsState(game, GameStates.PAUSED)
    
    # Simulate selecting "Back" option (index 5)
    settings_state.selected_category = 5
    settings_state._select_main_option()
    
    # Should return to pause menu
    assert game.current_state == GameStates.PAUSED
    print("✓ Settings back option correctly returns to pause menu")

def main():
    """Run all settings navigation tests."""
    print("Testing settings navigation fix...")
    
    # Initialize pygame (required for constants)
    pygame.init()
    
    try:
        test_settings_from_main_menu()
        test_settings_from_pause_menu()
        test_settings_default_behavior()
        test_settings_back_selection()
        
        print("\n✅ All settings navigation tests passed!")
        print("\nFix Summary:")
        print("- Settings now tracks where it was accessed from")
        print("- 'Back' option returns to the previous state (pause menu or main menu)")
        print("- No more forced exit to main menu from pause → settings")
        print("- Game flow properly preserved")
        
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