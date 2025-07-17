# Features Roadmap

This document outlines the planned features for Space Trader, their implementation approach, and priority levels.

## Near Future Features (Next Release)

### 1. Afterburners System 🚀
**Priority:** High  
**Status:** Planned  

#### Description
A boost system that provides temporary speed enhancement at the cost of energy or fuel consumption.

#### Implementation Plan
- **Location:** `src/systems/afterburner_system.py`
- **Integration:** Add to ship systems alongside cloaking and repair
- **Upgrade Path:** 4 tiers of afterburner upgrades
- **Energy System:** Consume ship energy or introduce fuel system
- **Visual Effects:** Particle trails and enhanced thrust flames

#### Technical Details
```python
class AfterburnerSystem:
    def __init__(self):
        self.is_active = False
        self.energy_consumption_rate = 20.0  # per second
        self.speed_multiplier = 2.0
        self.max_duration = 10.0  # seconds
        self.cooldown_duration = 5.0  # seconds
        self.overheat_threshold = 0.8
```

#### Upgrades
- **Tier 1:** Basic Afterburner (2x speed, 5s duration)
- **Tier 2:** Enhanced Afterburner (2.2x speed, 7s duration)
- **Tier 3:** Military Afterburner (2.5x speed, 10s duration)
- **Tier 4:** Prototype Afterburner (3x speed, 15s duration, reduced energy cost)

#### Controls
- **Key:** `SHIFT` - Hold to activate afterburner
- **UI:** Energy/fuel meter with overheating indicator

---

### 2. WASD Control Scheme 🎮
**Priority:** Medium  
**Status:** Planned  

#### Description
Alternative control scheme using WASD keys for improved accessibility and modern gaming conventions.

#### Implementation Plan
- **Location:** `src/input/input_manager.py` (new)
- **Configuration:** Add to settings system
- **Dual Support:** Maintain arrow key support alongside WASD

#### Control Mapping
```
WASD Scheme:
- W: Thrust forward
- A: Rotate left  
- S: Brake/reverse thrust
- D: Rotate right
- SPACE: Fire weapons
- SHIFT: Afterburner
- Additional keys remain the same
```

#### Technical Details
- Create input abstraction layer
- Allow runtime switching between control schemes
- Save preference in settings
- Update UI to show current control scheme

---

### 3. Difficulty Levels ⚙️
**Priority:** High  
**Status:** Planned  

#### Description
Configurable difficulty settings that affect various game aspects for different player skill levels.

#### Implementation Plan
- **Location:** `src/difficulty/difficulty_manager.py` (new)
- **Integration:** Affect hazard generation, enemy AI, mission rewards
- **Persistence:** Save with game state

#### Difficulty Levels
```python
class DifficultyLevel(Enum):
    PEACEFUL = "peaceful"      # No enemies, reduced hazards
    EASY = "easy"             # Fewer enemies, more forgiving
    NORMAL = "normal"         # Balanced gameplay
    HARD = "hard"             # More enemies, higher damage
    EXTREME = "extreme"       # Maximum challenge
```

#### Affected Systems
- **Hazard Frequency:** Asteroid density, black hole count
- **Enemy Spawning:** Bandit ship frequency and aggression
- **Damage Scaling:** Collision and weapon damage multipliers
- **Mission Rewards:** Credit payouts and time limits
- **Resource Costs:** Repair costs and upgrade prices

#### Settings Integration
- Add difficulty selection to new game creation
- Allow difficulty changes with warnings about progress impact
- Display current difficulty in HUD

---

### 4. Enhanced Debris Physics 🌌
**Priority:** Medium  
**Status:** Planned  

#### Description
Make debris fields more dynamic by having them affected by gravitational forces from planets and black holes.

#### Implementation Plan
- **Location:** Enhance `src/entities/debris.py`
- **Physics:** Add gravitational force calculations
- **Visual:** Debris trails and movement indicators

#### Technical Details
```python
class Debris:
    def __init__(self, position, velocity):
        self.position = position
        self.velocity = velocity
        self.mass = random.uniform(0.1, 2.0)
        self.affected_by_gravity = True
        self.drift_speed = random.uniform(10, 50)
    
    def update(self, delta_time, gravitational_bodies):
        if self.affected_by_gravity:
            for body in gravitational_bodies:
                force = body.calculate_gravitational_force(self)
                self.velocity += force * delta_time / self.mass
```

#### Gravitational Effects
- **Black Holes:** Strong attraction, debris spiral inward
- **Planets:** Weak attraction, debris orbits at distance
- **Debris Clouds:** Form around gravitational bodies
- **Collision Chains:** Debris can collide and affect each other

#### Visual Enhancements
- Debris trails showing movement direction
- Dust clouds around gravitational bodies
- Particle effects for debris interactions

---

## Future Development Features

### 5. Advanced AI System 🤖
**Priority:** Medium  
**Status:** Concept  

#### Description
Enhanced enemy AI with tactical behaviors, formations, and adaptive strategies.

#### Planned Features
- **Formation Flying:** Coordinated group attacks
- **Tactical Retreat:** Strategic withdrawal and regrouping
- **Adaptive Behavior:** AI learns from player actions
- **Communication:** Enemies call for reinforcements
- **Patrol Patterns:** More realistic security behaviors

---

### 6. Base Building System 🏗️
**Priority:** Low  
**Status:** Concept  

#### Description
Allow players to construct and manage their own stations.

#### Planned Features
- **Station Construction:** Build custom stations with modules
- **Resource Management:** Manage station resources and production
- **Defense Systems:** Install weapons and shields
- **Trade Networks:** Establish trade routes between stations
- **Crew Management:** Hire and manage station personnel

---

### 7. Faction System 🏛️
**Priority:** Medium  
**Status:** Concept  

#### Description
Implement reputation and relationship mechanics with different factions.

#### Planned Features
- **Multiple Factions:** Trading guilds, military, pirates, corporations
- **Reputation System:** Actions affect standing with factions
- **Faction Missions:** Exclusive missions for allied factions
- **Territory Control:** Factions control different regions
- **Diplomatic Options:** Negotiate treaties and trade agreements

---

### 8. Multiplayer Support 🌐
**Priority:** Low  
**Status:** Concept  

#### Description
Add cooperative and competitive multiplayer modes.

#### Planned Features
- **Cooperative Mode:** Team up for trading and missions
- **Competitive Mode:** Player vs player combat and trading
- **Shared Universe:** Persistent multiplayer universe
- **Chat System:** In-game communication
- **Guilds:** Player organizations and alliances

---

## Implementation Priority

### Phase 1: Core Enhancements (v0.3.0)
1. **Afterburners System** - Adds excitement to ship movement
2. **Difficulty Levels** - Improves accessibility and replayability
3. **WASD Controls** - Modern control scheme option
4. **Enhanced Debris Physics** - Visual and gameplay improvements

### Phase 2: Advanced Features (v0.4.0)
1. **Advanced AI System** - More challenging and realistic enemies
2. **Faction System** - Adds depth to universe and missions
3. **Audio System** - Sound effects and music
4. **Visual Effects** - Enhanced graphics and particle systems

### Phase 3: Expansion Features (v0.5.0+)
1. **Base Building** - Major gameplay expansion
2. **Multiplayer Support** - Community features
3. **Story Mode** - Narrative campaign
4. **Advanced Economics** - Complex market simulation

---

## Technical Considerations

### Performance
- Ensure new systems don't impact frame rate
- Optimize physics calculations for debris and gravitational effects
- Implement efficient AI systems that scale with difficulty

### Compatibility
- Maintain backward compatibility with existing save files
- Ensure new features work with current control schemes
- Test on various hardware configurations

### User Experience
- Intuitive controls and interfaces
- Clear feedback for all new systems
- Comprehensive tutorials and documentation
- Accessibility options for different player needs

### Architecture
- Modular design for easy feature addition/removal
- Clean separation of concerns
- Comprehensive testing for all new features
- Consistent coding standards and documentation

---

## Feedback and Iteration

### Community Input
- Gather player feedback on proposed features
- Conduct playtesting sessions for new mechanics
- Iterate on designs based on user experience

### Development Process
- Implement features incrementally
- Maintain stable main branch
- Use feature branches for development
- Regular code reviews and testing

### Documentation
- Update all documentation with new features
- Create video tutorials for complex systems
- Maintain comprehensive API documentation
- Regular updates to roadmap based on progress