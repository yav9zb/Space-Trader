"""Tests for settings screen navigation (returning to the correct previous state)."""

import pygame
from src.states.game_state import SettingsState, GameStates

pygame.init()


class MockGame:
    """Mock game object for testing."""
    def __init__(self):
        self.current_state = GameStates.MAIN_MENU
        self.states = {}

    def change_state(self, new_state):
        self.current_state = new_state


def test_settings_from_main_menu():
    """Test settings navigation from main menu."""
    game = MockGame()
    game.current_state = GameStates.MAIN_MENU

    settings_state = SettingsState(game, GameStates.MAIN_MENU)

    assert settings_state.previous_state == GameStates.MAIN_MENU

    settings_state.game.change_state(settings_state.previous_state)
    assert game.current_state == GameStates.MAIN_MENU


def test_settings_from_pause_menu():
    """Test settings navigation from pause menu."""
    game = MockGame()
    game.current_state = GameStates.PAUSED

    settings_state = SettingsState(game, GameStates.PAUSED)

    assert settings_state.previous_state == GameStates.PAUSED

    settings_state.game.change_state(settings_state.previous_state)
    assert game.current_state == GameStates.PAUSED


def test_settings_default_behavior():
    """Test settings default behavior when no previous state provided."""
    game = MockGame()

    settings_state = SettingsState(game)

    assert settings_state.previous_state == GameStates.MAIN_MENU

    settings_state.game.change_state(settings_state.previous_state)
    assert game.current_state == GameStates.MAIN_MENU


def test_settings_back_selection():
    """Test settings back option selection."""
    game = MockGame()
    game.current_state = GameStates.PAUSED

    settings_state = SettingsState(game, GameStates.PAUSED)

    # Simulate selecting "Back" option (index 5)
    settings_state.selected_category = 5
    settings_state._select_main_option()

    assert game.current_state == GameStates.PAUSED
