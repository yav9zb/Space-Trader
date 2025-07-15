# Space Trader

A 2D space trading simulation game built with Python and Pygame. Navigate through a procedurally generated universe, dock with stations, trade commodities, and build your trading empire.

## Features

### Currently Implemented ✅
- **Ship Movement**: Smooth physics-based ship control with thrust, rotation, and momentum
- **Camera System**: Multiple camera modes (Centered, Smooth, Deadzone) with configurable settings
- **Procedural Universe**: Infinite chunk-based universe generation with stations, planets, and debris
- **Collision Detection**: Accurate collision system between ships and space objects
- **Station Types**: Multiple station types (Trading, Military, Mining, Research, Shipyard) with unique appearances
- **Planet Generation**: Varied planet types with procedural features and atmosphere effects
- **Settings System**: Comprehensive settings with JSON persistence and in-game configuration
- **Debug Mode**: Toggle-able debug overlay with performance metrics and object information
- **Minimap**: Real-time minimap showing nearby objects and ship position
- **Docking System**: Complete station docking with approach detection, visual feedback, and state management

### In Development 🚧
- **Trading Interface**: Buy/sell commodities with dynamic market pricing
- **Resource Management**: Fuel system and cargo capacity management

### Planned Features 📋
- **Economy System**: Dynamic market prices based on supply/demand
- **Mission System**: Delivery missions and contracts between stations
- **Ship Upgrades**: Engine improvements, cargo expansions, and specialized equipment
- **Save/Load System**: Persistent game state and player progress
- **Audio System**: Sound effects and ambient music
- **Advanced UI**: Comprehensive HUD with status indicators and information panels

## Controls

### Gameplay
- **Arrow Keys**: Ship movement (Left/Right to rotate, Up to thrust, Down to brake)
- **D**: Manual docking when near a station
- **U**: Undock from current station
- **ESC**: Pause game
- **F3**: Toggle debug mode

### Menus
- **UP/DOWN**: Navigate options
- **LEFT/RIGHT**: Adjust values (in settings)
- **ENTER**: Select/confirm
- **ESC**: Go back

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
- **State Management** (`src/states/game_state.py`): Menu, playing, paused, and settings states
- **Universe** (`src/universe.py`): Procedural generation and spatial partitioning
- **Camera** (`src/camera.py`): Multiple camera modes with smooth following
- **Settings** (`src/settings.py`): Configuration management with persistence

### Entity System
- **Ship** (`src/entities/ship.py`): Player-controlled vessel with physics
- **Station** (`src/entities/station.py`): Trading posts and service stations
- **Planet** (`src/entities/planet.py`): Procedural planets with unique features
- **Debris** (`src/entities/debris.py`): Space debris and obstacles

### Upcoming: Docking System

The docking system will provide seamless interaction between ships and stations:

#### Docking Requirements
- **Approach Speed**: Ships must approach stations at low velocity (< 50 units/sec)
- **Proximity**: Must be within docking range (station radius + 20 units)
- **Alignment**: Optional alignment requirements for realistic docking

#### Docking Process
1. **Approach Phase**: Ship approaches station within docking parameters
2. **Docking Request**: Automatic docking initiation when requirements are met
3. **Docking Animation**: Smooth transition animation to station
4. **Interface Access**: Access to trading, services, and station information

#### Visual Feedback
- **Docking Zone Indicators**: Visual range indicators around stations
- **Approach Guidance**: Speed and distance feedback during approach
- **Status Messages**: Clear docking status and requirement notifications

#### Technical Implementation
- **State Machine**: Clean docking state transitions (Approaching → Docking → Docked)
- **Event System**: Docking events for UI triggers and game state changes
- **Collision Integration**: Enhanced collision system for docking detection

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
│   ├── entities/        # Game objects (ship, stations, planets)
│   ├── states/          # Game state management
│   ├── ui/              # User interface components
│   ├── camera.py        # Camera system
│   ├── settings.py      # Configuration management
│   └── universe.py      # Universe generation
├── tests/               # Unit tests
├── settings.json        # Game configuration
└── requirements.txt     # Dependencies
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Roadmap

### Phase 1: Core Trading (Current)
- [x] Basic ship movement and physics
- [x] Universe generation and camera system
- [x] Docking system implementation
- [ ] Basic trading interface
- [ ] Resource management (fuel/cargo)

### Phase 2: Economy & Progression
- [ ] Dynamic market system
- [ ] Mission and contract system
- [ ] Ship upgrades and customization
- [ ] Player progression and achievements

### Phase 3: Advanced Features
- [ ] Multiplayer support
- [ ] Advanced AI for NPCs
- [ ] Combat system
- [ ] Station construction and management

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Pygame](https://www.pygame.org/)
- Inspired by classic space trading games like Elite and Escape Velocity
- Community feedback and contributions welcome!