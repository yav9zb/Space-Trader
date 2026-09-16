# Space Trader

**🚧 Beta** - this is a pre-release build. Core gameplay is complete and stable (146 automated tests, full manual playthrough verification), but expect rough edges. See [Known Issues / Beta Notes](#known-issues--beta-notes) below, and please [open an issue](https://github.com/yav9zb/Space-Trader/issues) for anything you run into.

A 2D space trading simulation game built with Python and Pygame. Navigate through a procedurally generated universe, dock with stations, trade commodities, complete missions, and survive in a hostile galaxy filled with hazards and enemies.

## Features

### Currently Implemented ✅

#### Core Systems
- **Ship Movement**: Smooth physics-based ship control with thrust, rotation, and momentum
- **Camera System**: Multiple camera modes (Centered, Smooth, Deadzone) with configurable settings  
- **Procedural Universe**: Infinite chunk-based universe generation with stations, planets, and debris
- **Collision Detection**: Accurate collision system between ships and space objects
- **Save/Load System**: Persistent game state with autosave and multiple save slots
- **Settings System**: Comprehensive settings with JSON persistence and in-game configuration
- **Debug Mode**: Toggle-able debug overlay with performance metrics and object information

#### Universe & Environment
- **Station Types**: Multiple station types (Trading, Military, Mining, Research, Shipyard) with unique appearances
- **Planet Generation**: Varied planet types with procedural features and atmosphere effects
- **Hazard System**: Dangerous asteroids, black holes, and environmental hazards
- **Debris Field**: Space debris affected by gravitational forces

#### Docking & Trading
- **Docking System**: Complete station docking with approach detection, visual feedback, and state management
- **Trading Interface**: Buy/sell commodities with dynamic market pricing
- **Commodity System**: 15+ commodities across 5 categories (Food, Metals, Technology, Energy, Consumer)
- **Market Dynamics**: Station-specific pricing and supply/demand mechanics

#### Mission System
- **5 Mission Types**: Delivery, Trading Contracts, Supply Runs, Emergency Delivery, Exploration
- **Mission Generation**: Dynamic mission creation based on station types and universe state
- **Mission Tracking**: Progress tracking, time limits, and completion rewards
- **Mission Cargo**: Special tracking for mission-related commodities

#### Combat System
- **Enemy Ships**: 4 types of bandit ships (Scout, Fighter, Heavy, Boss) with unique AI behaviors
- **Combat Hazards**: Destructible asteroids, radioactive zones, explosive asteroids, black holes
- **Weapon System**: 4 weapon types (Laser, Plasma, Missile, Railgun) with different characteristics
- **Ship Destruction**: Respawn system with progress penalties
- **Enemy AI**: Distance-based pursuit, state machine behaviors, hazard avoidance

#### Ship Systems
- **Upgrade System**: 5 upgrade categories (Cargo, Engine, Hull, Scanner, Stealth) with 4 tiers each
- **Afterburner**: Temporary speed boost with fuel cost, cooldown, and an emergency-fuel fallback mode
- **Cloaking System**: Stealth mechanics with effectiveness, duration, and cooldown
- **Repair System**: Station repairs, emergency kits, and auto-repair when docked
- **Enhanced HUD**: Comprehensive status display, navigation info, and system indicators

#### Base Building
- **Player Bases**: Construct and manage stations with 14 module types
- **Power & Resources**: Power generation/consumption, resource storage, and production chains

#### Difficulty & Accessibility
- **5 Difficulty Levels**: Peaceful, Easy, Normal, Hard, and Extreme, scaling hazard frequency, enemy spawns, damage, mission time/rewards, and repair/upgrade costs
- **Permadeath Mode**: Extreme difficulty ends the run permanently on ship destruction instead of respawning
- **Two Control Schemes**: Right-handed (WASD) and left-handed (arrow keys), switchable anytime in Settings

#### Audio
- **Sound Effects**: Weapon fire per weapon type, explosions, docking/undocking, engine thrust and afterburner loops, cloak activation, low-hull alerts, and UI feedback
- **Music Stingers**: Mission-complete and game-over cues
- **Volume Controls**: Master/SFX/Music sliders in Settings

#### User Interface
- **Minimap**: Real-time minimap showing nearby objects and ship position
- **Large Map**: Detailed universe overview with station locations
- **Enhanced HUD**: Multi-panel interface with ship stats, navigation, and mission info
- **Multiple Screens**: Trading, upgrades, missions, base construction, settings, save/load interfaces

### Planned Features 📋

- **Advanced AI**: Improved enemy tactics and faction-based behaviors
- **Multiplayer**: Cooperative and competitive multiplayer modes
- **Faction System**: Reputation and relationships with different groups
- **Story Mode**: Narrative campaign with scripted events
- **Visual Effects**: Enhanced explosions, particle systems, and environmental effects

## Controls

Two control schemes are available (Settings > Controls) - the exact bindings for whichever scheme you're using are always visible there under "Show Controls". Defaults:

| Action | Right-Handed (WASD) | Left-Handed (Arrows) |
|---|---|---|
| Thrust / Rotate / Brake | W / A+D / S | Up / Left+Right / Down |
| Fire weapons | Space | Right Ctrl |
| Afterburner (hold) | Left Shift | Right Shift |
| Dock / Undock | X / Z | F / G |
| Trading / Upgrades / Missions (when docked) | T / U / M | F / G / V |
| Cloak / Repair | C / R | E / Q |
| Base construction | B | B |
| Toggle large map | Tab | Tab |
| Pause | Esc | Esc |

**F4** toggles the developer view overlay (FPS, ship position, docking/camera debug info) regardless of control scheme.

### Menus
- **UP/DOWN**: Navigate options
- **LEFT/RIGHT**: Adjust values (in settings)
- **ENTER**: Select/confirm
- **ESC**: Go back

## Getting Started

### Option A: Download a build (recommended for players)

Grab the latest packaged build for your OS from the [Releases page](https://github.com/yav9zb/Space-Trader/releases) - no Python installation required. Extract and run.

### Option B: Run from source

#### Prerequisites
- Python 3.13 (developed and tested against this version; earlier 3.x versions likely work but aren't verified)
- pip

#### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yav9zb/Space-Trader.git
   cd Space-Trader
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the game:
   ```bash
   python launcher.py
   ```

### Building a standalone executable

```bash
pip install -r requirements-build.txt
pyinstaller spacetrader.spec
```

Produces a standalone build in `dist/` (`Space Trader.app` on macOS, an exe + folder on Windows/Linux). See `spacetrader.spec` for details.

## Architecture

### Core Systems
- **Game Engine** (`src/engine/game_engine.py`): Main game loop and state management
- **State Management** (`src/states/game_state.py`): Menu, playing, paused, trading, upgrades, missions states
- **Universe** (`src/universe.py`): Procedural generation and spatial partitioning
- **Camera** (`src/camera.py`): Multiple camera modes with smooth following
- **Settings** (`src/settings.py`): Configuration management with persistence

### Entity System
- **Ship** (`src/entities/ship.py`): Player-controlled vessel with physics and upgrade system
- **Station** (`src/entities/station.py`): Trading posts and service stations
- **Planet** (`src/entities/planet.py`): Procedural planets with unique features
- **Debris** (`src/entities/debris.py`): Space debris and obstacles
- **Bandit** (`src/entities/bandit.py`): Enemy ships with AI behaviors
- **Asteroid** (`src/entities/asteroid.py`): Hazardous space rocks with special types
- **Black Hole** (`src/entities/black_hole.py`): Gravitational hazards with event horizons

### Combat System
- **Combat Manager** (`src/combat/combat_manager.py`): Handles all combat interactions
- **Weapon System** (`src/combat/weapons.py`): Projectile weapons and firing mechanics
- **Respawn System** (`src/systems/respawn_system.py`): Ship destruction and revival

### Trading & Economy
- **Commodity System** (`src/trading/commodity.py`): Tradeable goods and categories
- **Market System** (`src/trading/market.py`): Dynamic pricing and station inventories
- **Cargo Hold** (`src/trading/cargo.py`): Inventory management with mission tracking

### Mission System
- **Mission Manager** (`src/missions/mission_manager.py`): Mission generation and tracking
- **Mission Types** (`src/missions/mission_types.py`): Base mission classes and structures
- **Specific Missions** (`src/missions/specific_missions.py`): Implementation of mission types

### Ship Systems
- **Upgrade System** (`src/upgrades/`): Ship improvement and enhancement systems
- **Cloaking System** (`src/systems/cloaking_system.py`): Stealth mechanics
- **Repair System** (`src/systems/repair_system.py`): Ship maintenance and healing

### User Interface
- **Enhanced HUD** (`src/ui/hud/enhanced_hud.py`): Multi-panel status display
- **Large Map** (`src/ui/large_map.py`): Universe overview interface
- **Minimap** (`src/ui/minimap.py`): Real-time local area display
- **Menu Style** (`src/ui/menu_style.py`): Shared starfield-background/panel styling used across every menu screen (main menu, trading, missions, upgrades, save/load, settings)

### Audio & Difficulty
- **Sound Manager** (`src/audio/sound_manager.py`): Loads and plays sfx/music, applies volume settings
- **Difficulty Manager** (`src/difficulty/difficulty_manager.py`): The 5 difficulty levels and their gameplay multipliers

### Platform / Packaging
- **Paths** (`src/paths.py`): Resolves settings/saves/logs/assets correctly whether running from source or as a packaged build
- **Steam** (`src/steam/steam_manager.py`): Optional Steamworks scaffolding, safe no-op without the real SDK - see [STEAM_RELEASE_CHECKLIST.md](STEAM_RELEASE_CHECKLIST.md)

## Development

### Running Tests
```bash
source venv/bin/activate
pip install -r requirements-dev.txt  # pytest isn't in the base requirements.txt
python -m pytest -v
```

### Project Structure
```
space_trader/
├── src/
│   ├── engine/          # Core game engine
│   ├── entities/        # Game objects (ship, stations, planets, enemies)
│   ├── states/          # Game state management
│   ├── ui/              # User interface components
│   ├── trading/         # Economy and commodity systems
│   ├── missions/        # Mission system
│   ├── combat/          # Combat mechanics
│   ├── upgrades/        # Ship upgrade system
│   ├── systems/         # Ship systems (cloak, repair, etc.)
│   ├── docking/         # Docking mechanics
│   ├── audio/           # Sound effects and music
│   ├── difficulty/      # Difficulty levels
│   ├── steam/           # Optional Steamworks scaffolding
│   ├── camera.py        # Camera system
│   ├── settings.py      # Configuration management
│   ├── paths.py         # Settings/saves/logs/assets path resolution
│   └── universe.py      # Universe generation
├── assets/              # Audio, icons (bundled into packaged builds)
├── tests/               # Unit tests (pytest)
├── scripts/             # Dev tooling (e.g. icon generation)
├── spacetrader.spec     # PyInstaller build spec
├── requirements.txt        # Runtime dependencies
├── requirements-dev.txt    # + test dependencies
└── requirements-build.txt  # + packaging dependencies (PyInstaller)
```

`saves/` and `settings.json` are created at runtime (gitignored - they're
per-player state, not project source; see `src/paths.py` for where they
land in a packaged build).

## Gameplay Guide

### Getting Started
1. Launch the game and create a new game or load an existing save
2. Pilot your ship through space (see Controls above for your scheme's keys)
3. Each of the 5 station types has a distinct shape and color - approach one and dock when close and moving slowly
4. Trade commodities for profit at the market when docked
5. Accept missions from the mission board when docked for additional income
6. Upgrade your ship at shipyards, research stations, and military bases when docked

### Combat
- Enemy bandit ships (4 types: Scout, Fighter, Heavy, Boss) will attack on sight
- Fire weapons to fight back or clear hazardous asteroids
- Different weapon types have varying damage, range, and energy costs
- Avoid or destroy hazardous asteroids
- Stay away from black holes - they're extremely dangerous
- Purchase stealth systems to avoid detection
- Use repair systems to maintain your ship's hull

### Trading Strategy
- Buy low at production stations, sell high at consumption stations
- Mining stations often have cheap metals
- Research stations pay well for technology
- Monitor market prices and station inventories
- Mission commodities are tracked separately from regular cargo

### Ship Progression
- Earn credits through trading and missions
- Purchase upgrades in categories: Cargo, Engine, Hull, Scanner, Stealth
- Each category has 4 tiers of improvements
- Higher tier upgrades require previous tiers
- Specialized stations offer discounts on certain upgrade types

## Known Issues / Beta Notes

- **No dedicated save-system test coverage** yet - save/load is stable in manual testing but not covered by the automated suite. See [SAVE_SYSTEM.md](SAVE_SYSTEM.md).
- **Display settings aren't configurable in-game** - the "Display" category in Settings is a placeholder; changing resolution/fullscreen currently requires editing `settings.json` directly.
- **No auto-dock** - docking is fully manual (approach at a safe speed, press the dock key).
- **Steam integration is unverified scaffolding**, not a tested integration - irrelevant unless you're building toward the Steam release; see [STEAM_RELEASE_CHECKLIST.md](STEAM_RELEASE_CHECKLIST.md).
- **Windows/Linux builds haven't been produced yet** - only verified on macOS so far; the GitHub Actions workflow (`.github/workflows/build.yml`) should produce them on a tag push, but hasn't been validated against real CI yet.
- Found something else? [Open an issue](https://github.com/yav9zb/Space-Trader/issues) - beta feedback is genuinely useful right now.

## License

All rights reserved. This is a commercial project in development; source code is not licensed for reuse or redistribution. Bug reports and feedback during the beta are welcome via GitHub Issues - this isn't an open-source contribution model (no PRs), just a request for testing help.

## Acknowledgments

- Built with [Pygame](https://www.pygame.org/)
- Inspired by classic space trading games like Elite and Escape Velocity
- Sound effects and music: [Kenney.nl](https://kenney.nl/) (CC0 / public domain) - Sci-Fi Sounds, Interface Sounds, and Music Jingles packs