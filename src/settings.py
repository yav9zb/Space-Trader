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


def get_available_resolutions():
    """Get list of available screen resolutions."""
    try:
        pygame.display.init()
        modes = pygame.display.list_modes()
        if modes == -1:  # All modes supported
            # Return common resolutions
            return [(1920, 1080), (1680, 1050), (1600, 900), (1440, 900), 
                   (1366, 768), (1280, 720), (1024, 768), (800, 600)]
        else:
            # Filter for reasonable resolutions (minimum 800x600)
            return [mode for mode in modes if mode[0] >= 800 and mode[1] >= 600]
    except:
        # Fallback resolutions
        return [(1920, 1080), (1680, 1050), (1600, 900), (1440, 900), 
               (1366, 768), (1280, 720), (1024, 768), (800, 600)]


def get_desktop_resolution():
    """Get the desktop resolution."""
    try:
        pygame.display.init()
        info = pygame.display.Info()
        width, height = info.current_w, info.current_h
        
        # Ensure minimum resolution for playability
        width = max(800, width)
        height = max(600, height)
        
        print(f"Detected desktop resolution: {width}x{height}")
        return (width, height)
    except Exception as e:
        print(f"Failed to detect desktop resolution: {e}")
        return (1920, 1080)  # Fallback

class Settings:
    def __init__(self):
        # Camera settings
        self.camera_mode = CameraMode.CENTERED
        self.camera_smoothing = 0.1  # For smooth camera mode
        self.camera_deadzone_radius = 50  # For deadzone camera mode
        
        # Display settings
        desktop_res = get_desktop_resolution()
        self.window_width = min(1280, desktop_res[0])  # Default to 1280 or desktop width
        self.window_height = min(720, desktop_res[1])   # Default to 720 or desktop height
        self.display_mode = DisplayMode.WINDOWED
        self.vsync = True
        self.show_fps = False
        self.show_debug = False
        self.hud_scale = 1.0  # HUD scaling factor
        
        # Dev View settings
        self.dev_view_enabled = False
        self.dev_show_fps = True
        self.dev_show_ship_pos = True
        self.dev_show_docking = True
        self.dev_show_stations = True
        self.dev_show_camera = True
        
        # Available resolutions for settings menu
        self.available_resolutions = get_available_resolutions()
        
        # Audio settings (for future use)
        self.master_volume = 0.8
        self.sfx_volume = 0.8
        self.music_volume = 0.6
        
        # Control settings
        self.invert_y = False
        self.mouse_sensitivity = 1.0
        self.control_scheme = "left_handed"  # Default control scheme
        
        # Load settings from file if it exists
        self.load()
    
    def save(self, filename="settings.json"):
        """Save settings to a JSON file"""
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
    
    def load(self, filename="settings.json"):
        """Load settings from a JSON file"""
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
            desktop_res = get_desktop_resolution()
            self.window_width = settings_dict.get("window_width", min(1280, desktop_res[0]))
            self.window_height = settings_dict.get("window_height", min(720, desktop_res[1]))
            
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
        """Apply current display settings to the screen."""
        flags = 0
        
        if self.display_mode == DisplayMode.FULLSCREEN:
            flags |= pygame.FULLSCREEN
        elif self.display_mode == DisplayMode.BORDERLESS:
            flags |= pygame.NOFRAME
        
        if self.vsync:
            flags |= pygame.DOUBLEBUF
        
        try:
            # Check if we're on macOS to avoid multi-monitor issues
            import platform
            is_macos = platform.system() == "Darwin"
            
            if self.display_mode == DisplayMode.FULLSCREEN:
                if is_macos:
                    # On macOS, avoid fullscreen entirely and force windowed mode to prevent multi-monitor issues
                    print("macOS detected: Forcing windowed mode to prevent laptop screen blackout")
                    desktop_res = get_desktop_resolution()
                    
                    # Create a large windowed mode that covers most of the screen
                    windowed_width = desktop_res[0] - 50
                    windowed_height = desktop_res[1] - 100  # Leave room for dock/menu bar
                    
                    flags = pygame.RESIZABLE | (pygame.DOUBLEBUF if self.vsync else 0)
                    new_screen = pygame.display.set_mode((windowed_width, windowed_height), flags)
                    self.window_width, self.window_height = windowed_width, windowed_height
                    
                    # Set window position to center it on the current display
                    import os
                    os.environ['SDL_VIDEO_WINDOW_POS'] = '25,50'
                else:
                    # On other platforms, use traditional fullscreen
                    desktop_res = get_desktop_resolution()
                    if (800 <= self.window_width <= desktop_res[0] and 
                        600 <= self.window_height <= desktop_res[1]):
                        new_screen = pygame.display.set_mode((self.window_width, self.window_height), flags)
                    else:
                        new_screen = pygame.display.set_mode(desktop_res, flags)
                        self.window_width, self.window_height = desktop_res
            elif self.display_mode == DisplayMode.BORDERLESS:
                if is_macos:
                    # On macOS, even borderless can cause issues, so use large windowed mode
                    print("macOS detected: Using large windowed mode instead of borderless")
                    desktop_res = get_desktop_resolution()
                    windowed_width = desktop_res[0] - 50
                    windowed_height = desktop_res[1] - 100
                    flags = pygame.RESIZABLE | (pygame.DOUBLEBUF if self.vsync else 0)
                    new_screen = pygame.display.set_mode((windowed_width, windowed_height), flags)
                    self.window_width, self.window_height = windowed_width, windowed_height
                    import os
                    os.environ['SDL_VIDEO_WINDOW_POS'] = '25,50'
                else:
                    # For borderless on other platforms
                    desktop_res = get_desktop_resolution()
                    borderless_flags = pygame.NOFRAME | (pygame.DOUBLEBUF if self.vsync else 0)
                    new_screen = pygame.display.set_mode(desktop_res, borderless_flags)
                    self.window_width, self.window_height = desktop_res
            else:
                # For windowed mode, ensure size doesn't exceed desktop and make it resizable
                desktop_res = get_desktop_resolution()
                max_width = min(self.window_width, desktop_res[0] - 100)  # Leave some margin
                max_height = min(self.window_height, desktop_res[1] - 100)
                flags = pygame.RESIZABLE | (pygame.DOUBLEBUF if self.vsync else 0)
                new_screen = pygame.display.set_mode((max_width, max_height), flags)
                self.window_width, self.window_height = max_width, max_height
            
            return new_screen
        except pygame.error as e:
            print(f"Failed to set display mode: {e}")
            # Fallback to smaller windowed mode
            self.display_mode = DisplayMode.WINDOWED
            fallback_width = min(1280, get_desktop_resolution()[0] - 100)
            fallback_height = min(720, get_desktop_resolution()[1] - 100)
            self.window_width, self.window_height = fallback_width, fallback_height
            return pygame.display.set_mode((fallback_width, fallback_height))
    
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