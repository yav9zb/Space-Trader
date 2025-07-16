# Save/Load System Documentation

## Overview

The Space Trader game now includes a comprehensive save/load system that allows players to:

- Save their game progress at any time
- Load previous save games
- Manage multiple save slots
- Automatic saves every 5 minutes during gameplay

## Features Implemented

### Core Save System (`src/save_system.py`)

- **JSON-based saves**: Human-readable save files in `saves/` directory
- **Complete state preservation**: Ship, cargo, upgrades, universe, market states
- **Save metadata**: Tracks save date, play time, credits, location
- **Multiple save slots**: Unlimited named save files
- **Auto-save**: Periodic automatic saves during gameplay

### Menu Integration

- **Main Menu**: Added "Load Game" option
- **Pause Menu**: Added "Save Game" option accessible during gameplay
- **Save Interface**: Type custom save names or overwrite existing saves
- **Load Interface**: Browse saves with detailed information, delete unwanted saves

### Data Preserved

#### Player Data
- Ship position, velocity, and rotation
- Credits and cargo hold contents
- All installed ship upgrades
- Current hull damage state

#### Universe State  
- All station positions, types, and market states
- Generated universe chunks
- Market prices, stock, and demand levels

#### Game Progress
- Total play time
- Current game state
- Save metadata for organization

## Usage

### Saving Games

1. **Manual Save**: Press ESC during gameplay → Select "Save Game"
2. **Auto-Save**: Automatically saves every 5 minutes as "autosave"
3. **Custom Names**: Type any name for your save file
4. **Overwrite**: Select existing save to overwrite

### Loading Games

1. **From Main Menu**: Select "Load Game" 
2. **Browse Saves**: Use UP/DOWN to select, ENTER to load
3. **Save Details**: View credits, location, and save date
4. **Delete**: Press DELETE to remove unwanted saves

### File Structure

```
saves/
├── autosave.json           # Automatic save
├── my_game.json           # Custom save
└── trading_run.json       # Another custom save
```

### Save File Format

```json
{
  "version": "1.0",
  "metadata": {
    "save_name": "my_game",
    "save_date": "2024-01-01T12:00:00",
    "play_time": 1800.5,
    "credits": 15000,
    "ship_upgrades_value": 2500,
    "location": "Near Trading Station Alpha"
  },
  "player": {
    "ship": { ... },
    "cargo": { ... },
    "upgrades": { ... }
  },
  "universe": {
    "stations": [ ... ],
    "generated_chunks": [ ... ]
  },
  "game_state": { ... }
}
```

## Technical Implementation

### Auto-Save System
- Triggers every 300 seconds (5 minutes) of gameplay
- Only saves during active gameplay (PLAYING state)
- Logs success/failure for debugging
- Non-intrusive (no UI notification)

### Error Handling
- Graceful failure for corrupted save files
- Validation of save file structure
- Automatic backup of save metadata
- Logging of all save/load operations

### Performance
- Efficient JSON serialization
- Minimal impact on gameplay
- Fast save/load operations
- Optimized for large universe states

## Configuration

### Auto-Save Interval
Default: 300 seconds (5 minutes)
Located in: `GameEngine.__init__()` → `self.auto_save_interval`

### Save Directory
Default: `saves/` (relative to game root)
Located in: `SaveSystem.__init__()` → `save_directory` parameter

## Future Enhancements

Planned improvements for the save system:

1. **Save Compression**: Reduce file sizes for large universes
2. **Save Game Screenshots**: Visual previews in load menu
3. **Quick Save/Load**: F5/F9 hotkeys for instant save/load
4. **Cloud Saves**: Optional cloud storage integration
5. **Save Verification**: Checksum validation for save integrity
6. **Export/Import**: Share save files between installations

## Troubleshooting

### Common Issues

**Save files not appearing**: Check `saves/` directory exists and has write permissions
**Load failures**: Verify save file is valid JSON and contains required fields
**Auto-save disabled**: Ensure game is in PLAYING state and interval has elapsed
**Missing upgrades**: Check upgrade system integration and serialization methods

### Debug Information

All save/load operations are logged to `game.log` with timestamps and error details.

## Testing

Run the test suite with:
```bash
python3 test_save_system.py
```

The save system has been thoroughly tested for:
- Save file creation and deletion
- Metadata handling
- Serialization accuracy
- Error recovery
- Integration with game states