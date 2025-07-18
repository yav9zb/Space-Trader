"""Control scheme management system for different input layouts."""

import pygame
from enum import Enum
from typing import Dict, Any


class ControlScheme(Enum):
    """Available control schemes."""
    RIGHT_HANDED = "right_handed"  # WASD-based
    LEFT_HANDED = "left_handed"    # Arrow keys-based


class ControlSchemeManager:
    """Manages different control schemes for the game."""
    
    def __init__(self):
        self.current_scheme = ControlScheme.LEFT_HANDED  # Default to current system
        self.schemes = self._initialize_schemes()
        self.load_from_settings()
    
    def _initialize_schemes(self) -> Dict[ControlScheme, Dict[str, Any]]:
        """Initialize all available control schemes."""
        return {
            ControlScheme.RIGHT_HANDED: {
                # Ship movement
                "thrust": pygame.K_w,
                "rotate_left": pygame.K_a,
                "rotate_right": pygame.K_d,
                "brake": pygame.K_s,
                
                # Combat
                "fire_weapons": pygame.K_SPACE,
                "afterburner": pygame.K_LSHIFT,
                
                # Ship systems
                "cloaking": pygame.K_c,
                "repair": pygame.K_r,
                
                # Navigation
                "toggle_map": pygame.K_TAB,
                "dock": pygame.K_x,
                "undock": pygame.K_z,
                
                # Station interfaces
                "trading": pygame.K_t,
                "upgrades": pygame.K_u,
                "missions": pygame.K_m,
                "base_construction": pygame.K_b,
                
                # Menu navigation
                "pause": pygame.K_ESCAPE,
                
                # Map controls
                "zoom_in": pygame.K_EQUALS,
                "zoom_out": pygame.K_MINUS,
                "map_reset": pygame.K_HOME,
                
                # Display name
                "name": "Right-Handed (WASD)",
                "description": "WASD movement with right-hand secondary controls"
            },
            
            ControlScheme.LEFT_HANDED: {
                # Ship movement
                "thrust": pygame.K_UP,
                "rotate_left": pygame.K_LEFT,
                "rotate_right": pygame.K_RIGHT,
                "brake": pygame.K_DOWN,
                
                # Combat
                "fire_weapons": pygame.K_RCTRL,
                "afterburner": pygame.K_RSHIFT,
                
                # Ship systems
                "cloaking": pygame.K_e,
                "repair": pygame.K_q,
                
                # Navigation
                "toggle_map": pygame.K_TAB,
                "dock": pygame.K_f,
                "undock": pygame.K_g,
                
                # Station interfaces
                "trading": pygame.K_f,
                "upgrades": pygame.K_g,
                "missions": pygame.K_v,
                "base_construction": pygame.K_b,
                
                # Menu navigation
                "pause": pygame.K_ESCAPE,
                
                # Map controls
                "zoom_in": pygame.K_EQUALS,
                "zoom_out": pygame.K_MINUS,
                "map_reset": pygame.K_HOME,
                
                # Display name
                "name": "Left-Handed (Arrow Keys)",
                "description": "Arrow key movement with left-hand secondary controls"
            }
        }
    
    def set_scheme(self, scheme: ControlScheme):
        """Set the current control scheme."""
        if scheme in self.schemes:
            self.current_scheme = scheme
            print(f"Control scheme changed to: {self.schemes[scheme]['name']}")
            self.save_to_settings()
        else:
            print(f"Invalid control scheme: {scheme}")
    
    def get_current_scheme(self) -> ControlScheme:
        """Get the current control scheme."""
        return self.current_scheme
    
    def get_key(self, action: str) -> int:
        """Get the key code for a specific action in the current scheme."""
        scheme_config = self.schemes[self.current_scheme]
        return scheme_config.get(action, None)
    
    def get_scheme_info(self, scheme: ControlScheme = None) -> Dict[str, str]:
        """Get display information for a control scheme."""
        if scheme is None:
            scheme = self.current_scheme
        
        scheme_config = self.schemes[scheme]
        return {
            "name": scheme_config["name"],
            "description": scheme_config["description"]
        }
    
    def get_all_schemes(self) -> Dict[ControlScheme, Dict[str, str]]:
        """Get all available control schemes with their display info."""
        return {
            scheme: self.get_scheme_info(scheme)
            for scheme in self.schemes.keys()
        }
    
    def is_key_pressed(self, action: str, keys_pressed) -> bool:
        """Check if a key for a specific action is pressed."""
        key_code = self.get_key(action)
        if key_code is None:
            return False
        
        # Handle special cases for shift keys
        if action == "afterburner":
            if self.current_scheme == ControlScheme.RIGHT_HANDED:
                return keys_pressed[pygame.K_LSHIFT] or keys_pressed[pygame.K_RSHIFT]
            else:
                return keys_pressed[pygame.K_RSHIFT]
        
        return keys_pressed[key_code]
    
    def get_key_name(self, action: str) -> str:
        """Get the display name for a key in the current scheme."""
        key_code = self.get_key(action)
        if key_code is None:
            return "Unbound"
        
        # Custom key names for better display
        key_names = {
            pygame.K_w: "W",
            pygame.K_a: "A", 
            pygame.K_s: "S",
            pygame.K_d: "D",
            pygame.K_UP: "↑",
            pygame.K_DOWN: "↓",
            pygame.K_LEFT: "←",
            pygame.K_RIGHT: "→",
            pygame.K_SPACE: "Space",
            pygame.K_LSHIFT: "Left Shift",
            pygame.K_RSHIFT: "Right Shift",
            pygame.K_RCTRL: "Right Ctrl",
            pygame.K_TAB: "Tab",
            pygame.K_ESCAPE: "Esc",
            pygame.K_EQUALS: "=",
            pygame.K_MINUS: "-",
            pygame.K_HOME: "Home"
        }
        
        return key_names.get(key_code, pygame.key.name(key_code).upper())
    
    def get_controls_help(self) -> Dict[str, Dict[str, str]]:
        """Get help text for current control scheme."""
        help_sections = {
            "Movement": {
                "thrust": "Thrust Forward",
                "rotate_left": "Rotate Left",
                "rotate_right": "Rotate Right",
                "brake": "Brake/Reverse"
            },
            "Combat": {
                "fire_weapons": "Fire Weapons",
                "afterburner": "Afterburner"
            },
            "Ship Systems": {
                "cloaking": "Toggle Cloaking",
                "repair": "Repair Ship"
            },
            "Navigation": {
                "toggle_map": "Toggle Map",
                "dock": "Dock/Undock",
                "pause": "Pause Game"
            },
            "Station": {
                "trading": "Trading",
                "upgrades": "Ship Upgrades",
                "missions": "Mission Board"
            }
        }
        
        # Convert to display format with key names
        result = {}
        for section, actions in help_sections.items():
            result[section] = {}
            for action, description in actions.items():
                key_name = self.get_key_name(action)
                result[section][key_name] = description
        
        return result
    
    def load_from_settings(self):
        """Load control scheme from settings."""
        try:
            # Import here to avoid circular imports
            try:
                from ..settings import game_settings
            except ImportError:
                from settings import game_settings
            
            scheme_name = game_settings.control_scheme
            scheme = ControlScheme(scheme_name)
            if scheme in self.schemes:
                self.current_scheme = scheme
                print(f"Loaded control scheme: {self.schemes[scheme]['name']}")
        except (ImportError, ValueError, AttributeError) as e:
            print(f"Failed to load control scheme from settings: {e}")
            # Keep default scheme
    
    def save_to_settings(self):
        """Save current control scheme to settings."""
        try:
            # Import here to avoid circular imports
            try:
                from ..settings import game_settings
            except ImportError:
                from settings import game_settings
            
            game_settings.control_scheme = self.current_scheme.value
            game_settings.save()
            print(f"Saved control scheme: {self.schemes[self.current_scheme]['name']}")
        except ImportError as e:
            print(f"Failed to save control scheme to settings: {e}")


# Global control scheme manager instance
control_scheme_manager = ControlSchemeManager()