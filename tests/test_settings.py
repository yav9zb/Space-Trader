import pytest
import os
import tempfile
from src.settings import Settings, CameraMode, game_settings

def test_settings_initialization():
    settings = Settings()
    # Don't assert specific camera mode since it might be loaded from file
    assert isinstance(settings.camera_mode, CameraMode)
    assert 0.01 <= settings.camera_smoothing <= 1.0
    assert 10 <= settings.camera_deadzone_radius <= 200
    assert settings.window_width > 0
    assert settings.window_height > 0
    assert isinstance(settings.fullscreen, bool)

def test_camera_mode_enum():
    assert CameraMode.CENTERED.value == "Centered"
    assert CameraMode.SMOOTH.value == "Smooth"
    assert CameraMode.DEADZONE.value == "Deadzone"

def test_camera_descriptions():
    settings = Settings()
    
    settings.camera_mode = CameraMode.CENTERED
    desc = settings.get_camera_description()
    assert "centered" in desc.lower()
    
    settings.camera_mode = CameraMode.SMOOTH
    desc = settings.get_camera_description()
    assert "smooth" in desc.lower()
    
    settings.camera_mode = CameraMode.DEADZONE
    desc = settings.get_camera_description()
    assert "deadzone" in desc.lower() or "center area" in desc.lower()

def test_settings_save_load():
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_filename = f.name
    
    try:
        # Create settings and modify them
        settings = Settings()
        settings.camera_mode = CameraMode.SMOOTH
        settings.camera_smoothing = 0.25
        settings.camera_deadzone_radius = 75
        settings.window_width = 1024
        settings.window_height = 768
        
        # Save to temporary file
        settings.save(temp_filename)
        
        # Create new settings instance and load
        new_settings = Settings()
        new_settings.load(temp_filename)
        
        # Verify values were loaded correctly
        assert new_settings.camera_mode == CameraMode.SMOOTH
        assert new_settings.camera_smoothing == 0.25
        assert new_settings.camera_deadzone_radius == 75
        assert new_settings.window_width == 1024
        assert new_settings.window_height == 768
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)

def test_global_settings_instance():
    # Test that the global settings instance exists and works
    assert game_settings is not None
    assert isinstance(game_settings.camera_mode, CameraMode)
    assert game_settings.window_width > 0
    assert game_settings.window_height > 0

def test_settings_load_nonexistent_file():
    # Test loading from a file that doesn't exist (should use defaults)
    settings = Settings()
    # Set known defaults before trying to load nonexistent file
    settings.camera_mode = CameraMode.CENTERED
    settings.window_width = 800
    settings.window_height = 600
    
    settings.load("nonexistent_file.json")
    
    # Should still have the values we set (since file doesn't exist)
    assert settings.camera_mode == CameraMode.CENTERED
    assert settings.window_width == 800
    assert settings.window_height == 600