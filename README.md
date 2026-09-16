# Space Trader

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
- **Cloaking System**: Stealth mechanics with effectiveness, duration, and cooldown
- **Repair System**: Station repairs, emergency kits, and auto-repair when docked
- **Enhanced HUD**: Comprehensive status display, navigation info, and system indicators

#### User Interface
- **Minimap**: Real-time minimap showing nearby objects and ship position
- **Large Map**: Detailed universe overview with station locations
- **Enhanced HUD**: Multi-panel interface with ship stats, navigation, and mission info
- **Multiple Screens**: Trading, upgrades, missions, settings, save/load interfaces

### Planned Features 📋

#### Near Future (Next Release)
- **Afterburners**: Boost system for enhanced speed and maneuverability
- **WASD Controls**: Alternative control scheme for improved accessibility
- **Difficulty Levels**: Configurable challenge affecting hazard frequency, damage, and enemy strength
- **Enhanced Debris Physics**: Debris affected by gravitational pull from planets and black holes

#### Future Development
- **Advanced AI**: Improved enemy tactics and faction-based behaviors
- **Base Building**: Construct and manage your own stations
- **Multiplayer**: Cooperative and competitive multiplayer modes
- **Faction System**: Reputation and relationships with different groups
- **Story Mode**: Narrative campaign with scripted events
- **Audio System**: Sound effects and ambient music
- **Visual Effects**: Enhanced explosions, particle systems, and environmental effects

## Controls

### Gameplay
- **Arrow Keys**: Ship movement (Left/Right to rotate, Up to thrust, Down to brake)
- **SPACE**: Fire weapons
- **D**: Manual docking when near a station
- **X**: Undock from current station
- **T**: Trading interface (when docked)
- **U**: Upgrades interface (when docked at compatible stations)
- **M**: Mission board (when docked)
- **C**: Toggle cloaking device (if installed)
- **R**: Repair ship (station repair when docked, emergency repair in space)
- **TAB**: Toggle large map
- **ESC**: Pause game
- **F3**: Toggle debug mode

### Menus
- **UP/DOWN**: Navigate options
- **LEFT/RIGHT**: Adjust values (in settings)
- **ENTER**: Select/confirm
- **ESC**: Go back
- **A**: Accept mission/purchase (context-dependent)

## Getting Started

### Prerequisites
- Python 3.8+
- Pygame 2.0+

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/space_trader.git
   cd space_trader
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

## Development

### Running Tests
```bash
source venv/bin/activate
python -m pytest tests/ -v
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
│   ├── camera.py        # Camera system
│   ├── settings.py      # Configuration management
│   └── universe.py      # Universe generation
├── saves/               # Save game files
├── tests/               # Unit tests
├── settings.json        # Game configuration
└── requirements.txt     # Dependencies
```

## Gameplay Guide

### Getting Started
1. Launch the game and create a new game or load an existing save
2. Use arrow keys to pilot your ship through space
3. Approach stations (blue circles) and dock with 'D' when close and moving slowly
4. Trade commodities for profit using the 'T' key when docked
5. Accept missions from the mission board ('M' key) for additional income
6. Upgrade your ship at shipyards and research stations ('U' key)

### Combat
- Enemy bandit ships will attack on sight
- Use SPACE to fire weapons
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

## License

All rights reserved. This is a commercial project in development; source code is not licensed for reuse or redistribution.

## Acknowledgments

- Built with [Pygame](https://www.pygame.org/)
- Inspired by classic space trading games like Elite and Escape Velocity
- Community feedback and contributions welcome!