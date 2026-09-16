"""Tests for the control scheme (input mapping) system."""

import pygame
from src.input.control_schemes import ControlSchemeManager, ControlScheme
from src.entities.ship import Ship

pygame.init()


class MockKeysPressed:
    """Mock for pygame.key.get_pressed()'s return value."""
    def __init__(self, pressed_keys):
        self.pressed_keys = pressed_keys

    def __getitem__(self, key):
        return self.pressed_keys.get(key, False)


def test_control_scheme_manager():
    """Test the control scheme manager functionality."""
    manager = ControlSchemeManager()

    # Default scheme comes from persisted settings, just check it's a valid scheme
    assert manager.get_current_scheme() in (ControlScheme.LEFT_HANDED, ControlScheme.RIGHT_HANDED)

    manager.set_scheme(ControlScheme.RIGHT_HANDED)
    assert manager.get_current_scheme() == ControlScheme.RIGHT_HANDED

    thrust_key = manager.get_key("thrust")
    assert thrust_key == pygame.K_w  # Right-handed scheme uses W

    manager.set_scheme(ControlScheme.LEFT_HANDED)
    thrust_key = manager.get_key("thrust")
    assert thrust_key == pygame.K_UP  # Left-handed scheme uses UP arrow

    invalid_key = manager.get_key("invalid_action")
    assert invalid_key is None


def test_right_handed_scheme():
    """Test right-handed (WASD) control scheme."""
    manager = ControlSchemeManager()
    manager.set_scheme(ControlScheme.RIGHT_HANDED)

    assert manager.get_key("thrust") == pygame.K_w
    assert manager.get_key("rotate_left") == pygame.K_a
    assert manager.get_key("rotate_right") == pygame.K_d
    assert manager.get_key("brake") == pygame.K_s

    assert manager.get_key("fire_weapons") == pygame.K_SPACE
    assert manager.get_key("afterburner") == pygame.K_LSHIFT

    assert manager.get_key("cloaking") == pygame.K_c
    assert manager.get_key("repair") == pygame.K_r

    assert manager.get_key("trading") == pygame.K_t
    assert manager.get_key("upgrades") == pygame.K_u
    assert manager.get_key("missions") == pygame.K_m

    info = manager.get_scheme_info()
    assert "WASD" in info["name"]
    assert "right-hand" in info["description"].lower()


def test_left_handed_scheme():
    """Test left-handed (Arrow Keys) control scheme."""
    manager = ControlSchemeManager()
    manager.set_scheme(ControlScheme.LEFT_HANDED)

    assert manager.get_key("thrust") == pygame.K_UP
    assert manager.get_key("rotate_left") == pygame.K_LEFT
    assert manager.get_key("rotate_right") == pygame.K_RIGHT
    assert manager.get_key("brake") == pygame.K_DOWN

    assert manager.get_key("fire_weapons") == pygame.K_RCTRL
    assert manager.get_key("afterburner") == pygame.K_RSHIFT

    assert manager.get_key("cloaking") == pygame.K_e
    assert manager.get_key("repair") == pygame.K_q

    assert manager.get_key("trading") == pygame.K_f
    assert manager.get_key("upgrades") == pygame.K_g
    assert manager.get_key("missions") == pygame.K_v

    info = manager.get_scheme_info()
    assert "Arrow Keys" in info["name"]
    assert "left-hand" in info["description"].lower()


def test_key_press_simulation():
    """Test key press simulation with different schemes."""
    manager = ControlSchemeManager()

    manager.set_scheme(ControlScheme.RIGHT_HANDED)
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


def test_controls_help():
    """Test controls help generation."""
    manager = ControlSchemeManager()

    for scheme in [ControlScheme.RIGHT_HANDED, ControlScheme.LEFT_HANDED]:
        manager.set_scheme(scheme)
        help_info = manager.get_controls_help()

        assert "Movement" in help_info
        assert "Combat" in help_info
        assert "Ship Systems" in help_info
        assert "Navigation" in help_info
        assert "Station" in help_info

        movement = help_info["Movement"]
        assert len(movement) == 4  # thrust, rotate_left, rotate_right, brake

        combat = help_info["Combat"]
        assert len(combat) == 2  # fire_weapons, afterburner


def test_ship_integration():
    """Test ship integration with control schemes."""
    ship = Ship(400, 300)
    manager = ControlSchemeManager()

    manager.set_scheme(ControlScheme.RIGHT_HANDED)
    keys_pressed = MockKeysPressed({pygame.K_w: True, pygame.K_SPACE: True})

    thrust_active = manager.is_key_pressed("thrust", keys_pressed)
    fire_active = manager.is_key_pressed("fire_weapons", keys_pressed)

    assert thrust_active == True
    assert fire_active == True

    manager.set_scheme(ControlScheme.LEFT_HANDED)
    keys_pressed = MockKeysPressed({pygame.K_UP: True, pygame.K_RCTRL: True})

    thrust_active = manager.is_key_pressed("thrust", keys_pressed)
    fire_active = manager.is_key_pressed("fire_weapons", keys_pressed)

    assert thrust_active == True
    assert fire_active == True


def test_key_display_names():
    """Test key display name generation."""
    manager = ControlSchemeManager()

    manager.set_scheme(ControlScheme.RIGHT_HANDED)
    assert manager.get_key_name("thrust") == "W"
    assert manager.get_key_name("fire_weapons") == "Space"
    assert manager.get_key_name("afterburner") == "Left Shift"

    manager.set_scheme(ControlScheme.LEFT_HANDED)
    assert manager.get_key_name("thrust") == "Up"
    assert manager.get_key_name("fire_weapons") == "Right Ctrl"
    assert manager.get_key_name("afterburner") == "Right Shift"

    assert manager.get_key_name("invalid_action") == "Unbound"
