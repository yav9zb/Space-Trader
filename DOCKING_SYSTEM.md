# Docking System Technical Documentation

## Overview

The docking system provides seamless interaction between ships and stations in the Space Trader game. This document outlines the technical implementation, design decisions, and integration points for the docking system.

## Architecture

### Core Components

1. **Docking Manager** (`src/docking/docking_manager.py`)
   - Central coordinator for all docking operations
   - Manages docking state transitions
   - Handles docking validation and requirements

2. **Docking Interface** (`src/states/docking_state.py`)
   - Game state for docked interactions
   - Trading interface and station services
   - Undocking procedures

3. **Docking Visual System** (`src/ui/docking_ui.py`)
   - Visual feedback for docking approach
   - Range indicators and status displays
   - Animation system for docking sequences

### State Machine

The docking system uses a finite state machine with the following states:

```
FREE_FLIGHT → APPROACHING → DOCKING → DOCKED
     ↑                                   ↓
     ←――――――――――― UNDOCKING ←―――――――――――――
```

#### State Definitions

- **FREE_FLIGHT**: Normal ship movement, no docking interaction
- **APPROACHING**: Ship is within detection range of a station
- **DOCKING**: Active docking sequence in progress
- **DOCKED**: Ship successfully docked, interface available
- **UNDOCKING**: Ship departing from station

### Docking Requirements

#### Primary Requirements
- **Proximity**: Ship must be within `station.size + ship.size + 20` units
- **Velocity**: Ship velocity must be < 50 units/second
- **Angle**: Optional alignment requirement (configurable)

#### Validation Logic
```python
def can_dock(ship, station):
    distance = (ship.position - station.position).length()
    max_distance = station.size + ship.size + 20
    max_speed = 50
    
    return (distance <= max_distance and 
            ship.velocity.length() <= max_speed)
```

## Implementation Plan

### Phase 1: Core Docking Mechanics

#### File: `src/docking/docking_manager.py`
```python
class DockingManager:
    def __init__(self):
        self.docking_state = DockingState.FREE_FLIGHT
        self.target_station = None
        self.docking_timer = 0.0
        
    def update(self, ship, stations, delta_time):
        # State machine logic
        # Proximity detection
        # Validation checks
        
    def initiate_docking(self, ship, station):
        # Begin docking sequence
        
    def complete_docking(self, ship, station):
        # Finalize docking
```

#### File: `src/docking/docking_state.py`
```python
from enum import Enum

class DockingState(Enum):
    FREE_FLIGHT = "free_flight"
    APPROACHING = "approaching"
    DOCKING = "docking"
    DOCKED = "docked"
    UNDOCKING = "undocking"
```

### Phase 2: Visual Feedback System

#### Docking Zone Indicators
- Circular range indicator around stations when approaching
- Color-coded feedback (green = valid, red = invalid, yellow = approaching)
- Distance and velocity displays

#### Status Messages
- "Approaching [Station Name]"
- "Docking parameters met - Press D to dock"
- "Velocity too high for docking"
- "Successfully docked at [Station Name]"

#### Implementation in `src/ui/docking_ui.py`
```python
class DockingUI:
    def draw_docking_zone(self, screen, station, ship, camera_offset):
        # Draw docking range indicator
        
    def draw_approach_feedback(self, screen, ship, target_station):
        # Show speed, distance, and status
        
    def draw_status_message(self, screen, message):
        # Display docking status text
```

### Phase 3: Integration with Game States

#### Modified Files

**`src/states/game_state.py`** - PlayingState updates:
```python
def update(self, delta_time):
    # Existing ship and camera updates...
    
    # Update docking system
    self.game.docking_manager.update(
        self.game.ship, 
        self.game.universe.stations, 
        delta_time
    )
    
def handle_input(self, event):
    # Existing input handling...
    
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_d:  # Manual docking
            self.game.docking_manager.attempt_docking()
```

**`src/engine/game_engine.py`** - Add docking manager:
```python
def __init__(self):
    # Existing initialization...
    from src.docking.docking_manager import DockingManager
    self.docking_manager = DockingManager()
```

### Phase 4: Docked Interface

#### New Game State: `src/states/docked_state.py`
```python
class DockedState(State):
    def __init__(self, game, station):
        super().__init__(game)
        self.station = station
        self.selected_option = 0
        self.menu_options = ["Trade", "Services", "Information", "Undock"]
        
    def render(self, screen):
        # Station interface UI
        
    def handle_input(self, event):
        # Navigation and selection logic
```

## Visual Design

### Docking Zone Visualization
- **Outer Ring**: Detection range (light blue, dotted)
- **Inner Ring**: Docking range (green when valid, red when invalid)
- **Approach Vector**: Line showing ship trajectory relative to station
- **Speed Indicator**: Color-coded velocity indicator

### UI Elements
- **HUD Integration**: Docking status in main gameplay HUD
- **Progress Bar**: Docking sequence progress during animation
- **Station Info Panel**: Basic station information during approach

### Animation Sequence
1. **Approach**: Ship moves toward station dock point
2. **Alignment**: Ship rotates to match station orientation
3. **Final Approach**: Smooth movement to docking position
4. **Interface Transition**: Fade to docked interface

## Configuration Options

### Settings Integration
```json
{
    "docking": {
        "auto_dock": true,
        "docking_assist": true,
        "max_approach_speed": 50,
        "docking_range_multiplier": 1.0,
        "require_confirmation": false,
        "show_docking_zones": true
    }
}
```

### Difficulty Scaling
- **Easy**: Larger docking zones, higher speed tolerance
- **Normal**: Standard parameters
- **Hard**: Precise positioning required, lower speed tolerance

## Testing Strategy

### Unit Tests
- `test_docking_manager.py`: Core docking logic
- `test_docking_validation.py`: Requirement checking
- `test_docking_states.py`: State machine transitions

### Integration Tests
- Ship-station interaction scenarios
- Edge cases (multiple stations, rapid state changes)
- Performance testing with many stations

### Test Scenarios
1. **Normal Docking**: Approach and dock successfully
2. **Failed Docking**: Too fast, too far, interrupted
3. **Auto Docking**: Automatic docking when conditions met
4. **Manual Docking**: Player-initiated docking
5. **Undocking**: Leave station and return to free flight

## Performance Considerations

### Optimization Strategies
- **Distance Culling**: Only check docking for nearby stations
- **State Caching**: Cache docking validations between frames
- **Event-Driven Updates**: Update docking state only when necessary

### Memory Management
- Minimal allocation during docking sequences
- Reuse UI elements and graphics
- Efficient collision detection for docking zones

## Future Enhancements

### Advanced Features
- **Multi-Ship Docking**: Support for AI ships docking
- **Docking Queues**: Multiple ships waiting to dock
- **Docking Animations**: More sophisticated approach sequences
- **Station-Specific Docking**: Different docking procedures per station type

### Integration Points
- **Combat System**: Disable docking during combat
- **Mission System**: Docking requirements for mission completion
- **Multiplayer**: Synchronized docking states between clients

## Implementation Timeline

### Week 1: Core System
- [ ] Create docking manager and state machine
- [ ] Implement basic proximity detection
- [ ] Add docking validation logic

### Week 2: Visual Feedback
- [ ] Implement docking zone indicators
- [ ] Add approach guidance UI
- [ ] Create status message system

### Week 3: Game Integration
- [ ] Integrate with game states
- [ ] Add manual docking controls
- [ ] Implement state transitions

### Week 4: Docked Interface
- [ ] Create docked game state
- [ ] Build station interface UI
- [ ] Add undocking procedures

This technical documentation provides the roadmap for implementing a robust, user-friendly docking system that enhances the Space Trader gameplay experience while maintaining code quality and performance standards.