# Settings System

## Overview

The Space Trader game now includes a comprehensive settings system that allows players to customize their gameplay experience. Settings are automatically saved to a JSON file and persisted between game sessions.

## Camera Settings

### Camera Modes

1. **Centered** (Default)
   - Camera follows the ship exactly, keeping it perfectly centered on screen
   - Provides immediate, responsive camera movement
   - Best for precise navigation and combat

2. **Smooth**
   - Camera smoothly follows ship movement with interpolation
   - Reduces jarring camera movements
   - Configurable smoothing factor (0.01 - 1.0)
   - Best for cinematic feel and reduced motion sickness

3. **Deadzone**
   - Camera only moves when ship leaves a defined center area
   - Allows ship to move freely within the deadzone
   - Configurable deadzone radius (10 - 200 pixels)
   - Best for exploration while maintaining camera stability

### Camera Configuration

- **Smoothing**: Controls how quickly the smooth camera follows the ship (0.01 = very slow, 1.0 = instant)
- **Deadzone Radius**: Size of the center area where the ship can move without triggering camera movement

## Controls

### Main Menu
- **UP/DOWN**: Navigate menu options
- **ENTER**: Select option
- **ESC**: Go back

### Settings Menu
- **UP/DOWN**: Navigate categories
- **ENTER**: Enter category or confirm selection
- **ESC**: Go back to previous menu

### Camera Settings
- **UP/DOWN**: Navigate camera options
- **LEFT/RIGHT**: Adjust values
- **ENTER**: Select option
- **ESC**: Return to main settings

## File Structure

Settings are stored in `settings.json` in the game directory with the following structure:

```json
{
    "camera_mode": "CENTERED",
    "camera_smoothing": 0.1,
    "camera_deadzone_radius": 50,
    "window_width": 800,
    "window_height": 600,
    "fullscreen": false,
    "show_debug": false,
    "master_volume": 0.8,
    "sfx_volume": 0.8,
    "music_volume": 0.6,
    "invert_y": false,
    "mouse_sensitivity": 1.0
}
```

## Future Features

The settings system is designed to be extensible. Planned additions include:

- **Display Settings**: Resolution, fullscreen mode, graphics quality
- **Audio Settings**: Volume controls, sound effects toggle
- **Control Settings**: Key bindings, mouse sensitivity, controller support
- **Gameplay Settings**: Difficulty, tutorial mode, auto-save options

## Implementation Details

### Key Files
- `src/settings.py`: Core settings management and persistence
- `src/camera.py`: Camera implementation with multiple modes
- `src/states/game_state.py`: Settings UI and menu state
- `tests/test_settings.py`: Settings system tests

### Architecture
- **Singleton Pattern**: Global `game_settings` instance accessible throughout the game
- **JSON Persistence**: Settings automatically saved when changed
- **Type Safety**: Enum-based camera modes with validation
- **Graceful Defaults**: Falls back to defaults if settings file is missing or corrupted

The settings system integrates seamlessly with the existing game state management and provides a foundation for future customization options.