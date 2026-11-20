import json
import os
import pygame
from enum import Enum
from pygame import Vector2

class CameraMode(Enum):
    CENTERED = "Centered"
    SMOOTH = "Smooth"
    DEADZONE = "Deadzone"


class DisplayMode(Enum):
    WINDOWED = "Windowed"
    FULLSCREEN = "Fullscreen"
    BORDERLESS = "Borderless Fullscreen"


def get_available_resolutions(current=None):
    """Window sizes for the settings menu, in points, that fit this screen."""
    from . import display
    return display.resolution_options(display.usable_area(display.desktop_size()), current)


def get_desktop_resolution():
    """The desktop size in points (what a window can occupy), never below the
    smallest playable size."""
    from . import display
    width, height = display.desktop_size()
    print(f"Detected desktop resolution: {width}x{height}")
    return (max(800, width), max(600, height))


class Settings:
    def __init__(self):
        # Camera settings
        self.camera_mode = CameraMode.CENTERED
        self.camera_smoothing = 0.1  # For smooth camera mode
        self.camera_deadzone_radius = 50  # For deadzone camera mode
        
        # Display settings
        from . import display
        self.window_width, self.window_height = display.default_window_size(
            display.usable_area(get_desktop_resolution()))
        self.display_mode = DisplayMode.WINDOWED
        self.vsync = True
        self.show_fps = False
        self.show_debug = False
        self.hud_scale = 1.0  # HUD scaling factor
        
        # Docking: dock automatically when close and slow enough, and how fast
        # the ship may still be going (careful, standard or relaxed)
        self.auto_dock = True
        self.docking_speed = "standard"

        # Dev View settings
        self.dev_view_enabled = False
        self.dev_show_fps = True
        self.dev_show_ship_pos = True
        self.dev_show_docking = True
        self.dev_show_stations = True
        self.dev_show_camera = True
        
        # Available resolutions for settings menu
        self.available_resolutions = get_available_resolutions()
        
        # Audio settings
        self.master_volume = 0.8
        self.sfx_volume = 0.8
        self.music_volume = 0.6
        
        # Control settings
        self.invert_y = False
        self.mouse_sensitivity = 1.0
        self.control_scheme = "left_handed"  # Default control scheme
        
        # Universe generation settings
        self.universe_type = "realistic"  # Default universe type

        # Difficulty settings
        self.difficulty = "normal"  # Default difficulty level

        # Onboarding hints already shown (so they only appear once ever)
        self.hints_seen = []

        # Load settings from file if it exists
        self.load()
    
    def save(self, filename=None):
        """Save settings to a JSON file"""
        if filename is None:
            from .paths import get_user_data_path
            filename = get_user_data_path("settings.json")
        settings_dict = {
            "camera_mode": self.camera_mode.name,
            "camera_smoothing": self.camera_smoothing,
            "camera_deadzone_radius": self.camera_deadzone_radius,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "display_mode": self.display_mode.name,
            "vsync": self.vsync,
            "show_fps": self.show_fps,
            "show_debug": self.show_debug,
            "hud_scale": self.hud_scale,
            "master_volume": self.master_volume,
            "sfx_volume": self.sfx_volume,
            "music_volume": self.music_volume,
            "invert_y": self.invert_y,
            "mouse_sensitivity": self.mouse_sensitivity,
            "control_scheme": self.control_scheme,
            "universe_type": self.universe_type,
            "difficulty": self.difficulty,
            "hints_seen": self.hints_seen,
            "auto_dock": self.auto_dock,
            "docking_speed": self.docking_speed,
            "dev_view_enabled": self.dev_view_enabled,
            "dev_show_fps": self.dev_show_fps,
            "dev_show_ship_pos": self.dev_show_ship_pos,
            "dev_show_docking": self.dev_show_docking,
            "dev_show_stations": self.dev_show_stations,
            "dev_show_camera": self.dev_show_camera
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(settings_dict, f, indent=4)
        except Exception as e:
            print(f"Failed to save settings: {e}")
    
    def load(self, filename=None):
        """Load settings from a JSON file"""
        if filename is None:
            from .paths import get_user_data_path
            filename = get_user_data_path("settings.json")

        if not os.path.exists(filename):
            return  # Use defaults if file doesn't exist
            
        try:
            with open(filename, 'r') as f:
                settings_dict = json.load(f)
            
            # Load camera settings
            if "camera_mode" in settings_dict:
                try:
                    self.camera_mode = CameraMode[settings_dict["camera_mode"]]
                except KeyError:
                    self.camera_mode = CameraMode.CENTERED
            
            self.camera_smoothing = settings_dict.get("camera_smoothing", 0.1)
            self.camera_deadzone_radius = settings_dict.get("camera_deadzone_radius", 50)
            
            # Load display settings
            # A size saved on a bigger monitor must not outgrow the screen we are on now
            from . import display
            usable = display.usable_area(get_desktop_resolution())
            saved = (settings_dict.get("window_width", self.window_width),
                     settings_dict.get("window_height", self.window_height))
            self.window_width, self.window_height = display.clamp_size(saved, usable)
            
            # Handle legacy fullscreen setting
            if "fullscreen" in settings_dict and settings_dict["fullscreen"]:
                self.display_mode = DisplayMode.FULLSCREEN
            else:
                display_mode_name = settings_dict.get("display_mode", "WINDOWED")
                try:
                    self.display_mode = DisplayMode[display_mode_name]
                except KeyError:
                    self.display_mode = DisplayMode.WINDOWED
            
            self.vsync = settings_dict.get("vsync", True)
            self.show_fps = settings_dict.get("show_fps", False)
            self.show_debug = settings_dict.get("show_debug", False)
            self.hud_scale = settings_dict.get("hud_scale", 1.0)
            
            # Load audio settings
            self.master_volume = settings_dict.get("master_volume", 0.8)
            self.sfx_volume = settings_dict.get("sfx_volume", 0.8)
            self.music_volume = settings_dict.get("music_volume", 0.6)
            
            # Load control settings
            self.invert_y = settings_dict.get("invert_y", False)
            self.mouse_sensitivity = settings_dict.get("mouse_sensitivity", 1.0)
            self.control_scheme = settings_dict.get("control_scheme", "left_handed")
            
            # Load universe settings
            self.universe_type = settings_dict.get("universe_type", "realistic")

            # Load difficulty settings
            self.difficulty = settings_dict.get("difficulty", "normal")

            # Load docking settings, ignoring values that are not valid
            auto_dock = settings_dict.get("auto_dock", True)
            self.auto_dock = auto_dock if isinstance(auto_dock, bool) else True
            speed = settings_dict.get("docking_speed", "standard")
            self.docking_speed = speed if speed in ("careful", "standard", "relaxed") else "standard"

            # Load onboarding hints already shown
            self.hints_seen = settings_dict.get("hints_seen", [])

            # Load dev view settings
            self.dev_view_enabled = settings_dict.get("dev_view_enabled", False)
            self.dev_show_fps = settings_dict.get("dev_show_fps", True)
            self.dev_show_ship_pos = settings_dict.get("dev_show_ship_pos", True)
            self.dev_show_docking = settings_dict.get("dev_show_docking", True)
            self.dev_show_stations = settings_dict.get("dev_show_stations", True)
            self.dev_show_camera = settings_dict.get("dev_show_camera", True)
            
        except Exception as e:
            print(f"Failed to load settings: {e}")
            # Keep defaults if loading fails
    
    def get_camera_description(self):
        """Get description of current camera mode"""
        descriptions = {
            CameraMode.CENTERED: "Camera follows ship exactly, keeping it centered",
            CameraMode.SMOOTH: "Camera smoothly follows ship movement",
            CameraMode.DEADZONE: "Camera only moves when ship leaves center area"
        }
        return descriptions.get(self.camera_mode, "Unknown camera mode")
    
    def get_display_mode_description(self):
        """Get description of current display mode"""
        descriptions = {
            DisplayMode.WINDOWED: "Run in a window",
            DisplayMode.FULLSCREEN: "Run in exclusive fullscreen mode",
            DisplayMode.BORDERLESS: "Run fullscreen without window borders"
        }
        return descriptions.get(self.display_mode, "Unknown display mode")
    
    def apply_display_settings(self, screen):
        """Create or resize the window for the current display settings and
        return its surface."""
        import os
        from . import display

        desktop = get_desktop_resolution()
        usable = display.usable_area(desktop)
        mac = display.is_macos()
        flags = pygame.RESIZABLE

        try:
            if self.display_mode == DisplayMode.WINDOWED:
                # Never larger than this screen, never smaller than the minimum
                self.window_width, self.window_height = display.clamp_size(
                    (self.window_width, self.window_height), usable)
                size = (self.window_width, self.window_height)
                if screen is None:
                    os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
            elif mac:
                # Real fullscreen on macOS can black out a laptop display, so
                # "fullscreen" fills the whole usable screen with a window. The
                # saved windowed size is left alone for when you switch back.
                size = display.clamp_size(usable, usable)
                os.environ['SDL_VIDEO_WINDOW_POS'] = '0,%d' % display.MENU_BAR
            elif self.display_mode == DisplayMode.FULLSCREEN:
                flags = pygame.FULLSCREEN
                size = desktop
            else:
                flags = pygame.NOFRAME
                size = desktop

            new_screen = self._create_display(size, flags, screen)
            return new_screen
        except pygame.error as e:
            print(f"Failed to set display mode: {e}")
            # Fall back to a plain window of a sensible size
            self.display_mode = DisplayMode.WINDOWED
            self.window_width, self.window_height = display.default_window_size(usable)
            return pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)

    def _create_display(self, size, flags, existing):
        """The window and the surface the game draws into: the high-density
        window on a Retina Mac (the surface is then point-sized and scaled up
        each frame), otherwise an ordinary pygame display."""
        from . import hidpi
        if flags & pygame.RESIZABLE and (hidpi.get_presenter() is not None or hidpi.wanted()):
            surface = hidpi.configure("Space Trading Simulator", size, resizable=True)
            if surface is not None:
                return surface
        return pygame.display.set_mode(size, flags)

    def next_resolution(self, direction: int):
        """The window size one step larger (direction > 0) or smaller (< 0) than
        the current one, from the sizes that fit the screen the window is on now.
        The window may have been dragged to a size that is not in the list, in
        which case this moves to the nearest listed size in that direction."""
        current = (self.window_width, self.window_height)
        options = get_available_resolutions()
        area = lambda size: size[0] * size[1]
        if direction > 0:
            larger = [o for o in options if area(o) > area(current)]
            return larger[0] if larger else options[0]                    # wrap to the smallest
        smaller = [o for o in options if area(o) < area(current)]
        return smaller[-1] if smaller else options[-1]                    # wrap to the largest

    def get_resolution_string(self):
        """Get current resolution as a string."""
        return f"{self.window_width}x{self.window_height}"
    
    def set_resolution(self, width, height):
        """Set window resolution."""
        self.window_width = width
        self.window_height = height
    
    def toggle_fullscreen(self):
        """Toggle between windowed and fullscreen."""
        if self.display_mode == DisplayMode.WINDOWED:
            # Always use fullscreen mode, but on macOS it will be converted to borderless automatically
            self.display_mode = DisplayMode.FULLSCREEN
        else:
            self.display_mode = DisplayMode.WINDOWED

# Global settings instance
game_settings = Settings()