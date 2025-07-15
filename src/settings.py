import json
import os
from enum import Enum
from pygame import Vector2

class CameraMode(Enum):
    CENTERED = "Centered"
    SMOOTH = "Smooth"
    DEADZONE = "Deadzone"

class Settings:
    def __init__(self):
        # Camera settings
        self.camera_mode = CameraMode.CENTERED
        self.camera_smoothing = 0.1  # For smooth camera mode
        self.camera_deadzone_radius = 50  # For deadzone camera mode
        
        # Display settings
        self.window_width = 800
        self.window_height = 600
        self.fullscreen = False
        self.show_debug = False
        
        # Audio settings (for future use)
        self.master_volume = 0.8
        self.sfx_volume = 0.8
        self.music_volume = 0.6
        
        # Control settings (for future use)
        self.invert_y = False
        self.mouse_sensitivity = 1.0
        
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
            "fullscreen": self.fullscreen,
            "show_debug": self.show_debug,
            "master_volume": self.master_volume,
            "sfx_volume": self.sfx_volume,
            "music_volume": self.music_volume,
            "invert_y": self.invert_y,
            "mouse_sensitivity": self.mouse_sensitivity
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
            self.window_width = settings_dict.get("window_width", 800)
            self.window_height = settings_dict.get("window_height", 600)
            self.fullscreen = settings_dict.get("fullscreen", False)
            self.show_debug = settings_dict.get("show_debug", False)
            
            # Load audio settings
            self.master_volume = settings_dict.get("master_volume", 0.8)
            self.sfx_volume = settings_dict.get("sfx_volume", 0.8)
            self.music_volume = settings_dict.get("music_volume", 0.6)
            
            # Load control settings
            self.invert_y = settings_dict.get("invert_y", False)
            self.mouse_sensitivity = settings_dict.get("mouse_sensitivity", 1.0)
            
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

# Global settings instance
game_settings = Settings()