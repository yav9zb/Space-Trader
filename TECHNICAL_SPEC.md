# Technical Specification: Next Release Features

This document provides detailed technical specifications for the features planned for the next release.

## Feature 1: Afterburners System

### Overview
The afterburner system provides temporary speed boosts at the cost of energy consumption, adding tactical depth to ship movement and combat.

### Core Components

#### 1. AfterburnerSystem Class
```python
# src/systems/afterburner_system.py
class AfterburnerSystem:
    def __init__(self):
        self.is_active = False
        self.current_energy = 100.0
        self.max_energy = 100.0
        self.energy_consumption_rate = 25.0  # per second
        self.energy_recovery_rate = 10.0     # per second when inactive
        self.speed_multiplier = 2.0
        self.overheat_threshold = 0.2        # 20% energy remaining
        self.cooldown_timer = 0.0
        self.cooldown_duration = 2.0
        self.overheated = False
        
    def can_activate(self) -> bool:
        """Check if afterburner can be activated."""
        return (not self.is_active and 
                not self.overheated and 
                self.current_energy > 10.0 and
                self.cooldown_timer <= 0)
    
    def activate(self, ship_stats):
        """Activate afterburner if possible."""
        if self.can_activate():
            self.is_active = True
            return True
        return False
    
    def deactivate(self):
        """Deactivate afterburner."""
        self.is_active = False
        self.cooldown_timer = self.cooldown_duration
    
    def update(self, delta_time, ship_stats):
        """Update afterburner state."""
        if self.is_active:
            # Consume energy
            energy_consumed = self.energy_consumption_rate * delta_time
            self.current_energy = max(0, self.current_energy - energy_consumed)
            
            # Check for energy depletion
            if self.current_energy <= 0:
                self.deactivate()
                self.overheated = True
        else:
            # Recover energy
            recovery = self.energy_recovery_rate * delta_time
            self.current_energy = min(self.max_energy, self.current_energy + recovery)
            
            # Update cooldown
            if self.cooldown_timer > 0:
                self.cooldown_timer -= delta_time
            
            # Check overheat recovery
            if self.overheated and self.current_energy >= self.overheat_threshold * self.max_energy:
                self.overheated = False
    
    def get_speed_multiplier(self) -> float:
        """Get current speed multiplier."""
        return self.speed_multiplier if self.is_active else 1.0
    
    def draw_effects(self, screen, ship_position, ship_heading, camera_offset):
        """Draw afterburner visual effects."""
        if not self.is_active:
            return
            
        screen_pos = ship_position - camera_offset
        
        # Enhanced thrust flame
        flame_length = 30 + random.randint(-5, 5)
        flame_width = 8
        
        # Multiple flame particles
        for i in range(5):
            offset = Vector2(
                random.randint(-flame_width, flame_width),
                random.randint(0, flame_length)
            )
            
            # Rotate offset based on ship heading
            rotated_offset = offset.rotate(math.degrees(math.atan2(ship_heading.y, ship_heading.x)) + 90)
            particle_pos = screen_pos - rotated_offset
            
            # Color based on intensity
            intensity = 1.0 - (i / 5.0)
            color = (
                255,
                int(165 * intensity),
                int(50 * intensity)
            )
            
            pygame.draw.circle(screen, color, (int(particle_pos.x), int(particle_pos.y)), 3)
```

#### 2. Ship Integration
```python
# Modifications to src/entities/ship.py
class Ship:
    def __init__(self, x, y):
        # ... existing code ...
        self.afterburner_system = AfterburnerSystem()
        
    def handle_input(self, delta_time):
        keys = pygame.key.get_pressed()
        
        # ... existing movement code ...
        
        # Afterburner control
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            self.afterburner_system.activate(self.get_effective_stats())
        else:
            if self.afterburner_system.is_active:
                self.afterburner_system.deactivate()
    
    def update(self, delta_time):
        # ... existing code ...
        
        # Update afterburner system
        self.afterburner_system.update(delta_time, self.get_effective_stats())
        
        # Apply speed multiplier
        speed_multiplier = self.afterburner_system.get_speed_multiplier()
        if speed_multiplier > 1.0:
            self.velocity *= speed_multiplier
    
    def draw(self, screen, camera_offset):
        # ... existing drawing code ...
        
        # Draw afterburner effects
        self.afterburner_system.draw_effects(screen, self.position, self.heading, camera_offset)
```

#### 3. Upgrade System Integration
```python
# Addition to src/upgrades/upgrade_definitions.py
afterburner_upgrades = [
    UpgradeDefinition(
        id="afterburner_basic",
        name="Basic Afterburner",
        category=UpgradeCategory.ENGINE,
        tier=1,
        cost=5000,
        description="Basic afterburner system - 2x speed boost for 10 seconds",
        requirements=[],
        stats={
            "afterburner_speed_multiplier": 2.0,
            "afterburner_max_energy": 100.0,
            "afterburner_consumption_rate": 25.0
        }
    ),
    # ... additional tiers ...
]
```

---

## Feature 2: WASD Control Scheme

### Overview
Alternative control scheme using WASD keys for ship movement, providing modern gaming conventions.

### Core Components

#### 1. InputManager Class
```python
# src/input/input_manager.py (new file)
from enum import Enum
import pygame

class ControlScheme(Enum):
    ARROW_KEYS = "arrow_keys"
    WASD = "wasd"

class InputManager:
    def __init__(self):
        self.control_scheme = ControlScheme.ARROW_KEYS
        self.key_mappings = {
            ControlScheme.ARROW_KEYS: {
                'thrust': pygame.K_UP,
                'brake': pygame.K_DOWN,
                'rotate_left': pygame.K_LEFT,
                'rotate_right': pygame.K_RIGHT,
                'fire': pygame.K_SPACE,
                'afterburner': pygame.K_LSHIFT
            },
            ControlScheme.WASD: {
                'thrust': pygame.K_w,
                'brake': pygame.K_s,
                'rotate_left': pygame.K_a,
                'rotate_right': pygame.K_d,
                'fire': pygame.K_SPACE,
                'afterburner': pygame.K_LSHIFT
            }
        }
    
    def set_control_scheme(self, scheme: ControlScheme):
        """Change the active control scheme."""
        self.control_scheme = scheme
    
    def get_current_mapping(self) -> dict:
        """Get current key mappings."""
        return self.key_mappings[self.control_scheme]
    
    def is_key_pressed(self, action: str) -> bool:
        """Check if action key is pressed."""
        keys = pygame.key.get_pressed()
        mapping = self.get_current_mapping()
        return keys[mapping[action]]
    
    def get_ship_input(self) -> dict:
        """Get current ship input state."""
        return {
            'thrust': self.is_key_pressed('thrust'),
            'brake': self.is_key_pressed('brake'),
            'rotate_left': self.is_key_pressed('rotate_left'),
            'rotate_right': self.is_key_pressed('rotate_right'),
            'fire': self.is_key_pressed('fire'),
            'afterburner': self.is_key_pressed('afterburner')
        }
```

#### 2. Ship Input Integration
```python
# Modifications to src/entities/ship.py
class Ship:
    def __init__(self, x, y):
        # ... existing code ...
        from ..input.input_manager import InputManager
        self.input_manager = InputManager()
    
    def handle_input(self, delta_time):
        input_state = self.input_manager.get_ship_input()
        
        # Rotation
        if input_state['rotate_left']:
            self.rotation -= self.ROTATION_SPEED * delta_time
        if input_state['rotate_right']:
            self.rotation += self.ROTATION_SPEED * delta_time
        
        # ... rest of input handling using input_state ...
```

#### 3. Settings Integration
```python
# Addition to src/settings.py
class Settings:
    def __init__(self):
        # ... existing settings ...
        self.control_scheme = "arrow_keys"
    
    def get_control_scheme(self):
        return ControlScheme(self.control_scheme)
    
    def set_control_scheme(self, scheme: ControlScheme):
        self.control_scheme = scheme.value
        self.save_settings()
```

---

## Feature 3: Difficulty Levels

### Overview
Configurable difficulty settings that affect hazard frequency, enemy behavior, and mission parameters.

### Core Components

#### 1. DifficultyManager Class
```python
# src/difficulty/difficulty_manager.py (new file)
from enum import Enum
from dataclasses import dataclass

class DifficultyLevel(Enum):
    PEACEFUL = "peaceful"
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXTREME = "extreme"

@dataclass
class DifficultySettings:
    hazard_frequency_multiplier: float = 1.0
    enemy_spawn_multiplier: float = 1.0
    damage_multiplier: float = 1.0
    mission_time_multiplier: float = 1.0
    mission_reward_multiplier: float = 1.0
    repair_cost_multiplier: float = 1.0
    upgrade_cost_multiplier: float = 1.0
    enemy_aggression_multiplier: float = 1.0
    
class DifficultyManager:
    def __init__(self):
        self.current_difficulty = DifficultyLevel.NORMAL
        self.difficulty_settings = {
            DifficultyLevel.PEACEFUL: DifficultySettings(
                hazard_frequency_multiplier=0.3,
                enemy_spawn_multiplier=0.0,
                damage_multiplier=0.5,
                mission_time_multiplier=1.5,
                mission_reward_multiplier=1.0,
                repair_cost_multiplier=0.8,
                upgrade_cost_multiplier=0.9
            ),
            DifficultyLevel.EASY: DifficultySettings(
                hazard_frequency_multiplier=0.7,
                enemy_spawn_multiplier=0.6,
                damage_multiplier=0.8,
                mission_time_multiplier=1.3,
                mission_reward_multiplier=1.1,
                repair_cost_multiplier=0.9,
                upgrade_cost_multiplier=0.95
            ),
            DifficultyLevel.NORMAL: DifficultySettings(),
            DifficultyLevel.HARD: DifficultySettings(
                hazard_frequency_multiplier=1.4,
                enemy_spawn_multiplier=1.5,
                damage_multiplier=1.3,
                mission_time_multiplier=0.8,
                mission_reward_multiplier=1.2,
                repair_cost_multiplier=1.2,
                upgrade_cost_multiplier=1.1,
                enemy_aggression_multiplier=1.3
            ),
            DifficultyLevel.EXTREME: DifficultySettings(
                hazard_frequency_multiplier=2.0,
                enemy_spawn_multiplier=2.0,
                damage_multiplier=1.8,
                mission_time_multiplier=0.6,
                mission_reward_multiplier=1.5,
                repair_cost_multiplier=1.5,
                upgrade_cost_multiplier=1.2,
                enemy_aggression_multiplier=1.8
            )
        }
    
    def set_difficulty(self, difficulty: DifficultyLevel):
        """Set the current difficulty level."""
        self.current_difficulty = difficulty
    
    def get_settings(self) -> DifficultySettings:
        """Get current difficulty settings."""
        return self.difficulty_settings[self.current_difficulty]
    
    def apply_damage_multiplier(self, base_damage: float) -> float:
        """Apply difficulty damage multiplier."""
        return base_damage * self.get_settings().damage_multiplier
    
    def apply_mission_reward_multiplier(self, base_reward: int) -> int:
        """Apply difficulty mission reward multiplier."""
        return int(base_reward * self.get_settings().mission_reward_multiplier)
```

#### 2. Integration Points
```python
# Integration with universe generation
# src/universe.py - modify hazard generation
def generate_hazards(self, chunk_x, chunk_y):
    difficulty = difficulty_manager.get_settings()
    hazard_count = int(base_hazard_count * difficulty.hazard_frequency_multiplier)
    # ... rest of hazard generation ...

# Integration with combat system
# src/combat/combat_manager.py - modify damage calculations
def apply_damage(self, base_damage):
    return difficulty_manager.apply_damage_multiplier(base_damage)
```

---

## Feature 4: Enhanced Debris Physics

### Overview
Make debris affected by gravitational forces from planets and black holes for more realistic space physics.

### Core Components

#### 1. Enhanced Debris Class
```python
# Modifications to src/entities/debris.py
class Debris:
    def __init__(self, position, velocity=None, size=None):
        self.position = Vector2(position)
        self.velocity = velocity or Vector2(
            random.uniform(-20, 20),
            random.uniform(-20, 20)
        )
        self.size = size or random.uniform(2, 8)
        self.mass = self.size * 0.5  # Mass proportional to size
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-30, 30)
        self.affected_by_gravity = True
        self.max_velocity = 100.0
        self.drag_coefficient = 0.99
        
    def update(self, delta_time, gravitational_bodies):
        """Update debris position and physics."""
        if self.affected_by_gravity:
            # Apply gravitational forces
            for body in gravitational_bodies:
                if hasattr(body, 'calculate_gravitational_force'):
                    force = body.calculate_gravitational_force(self)
                    acceleration = force / self.mass
                    self.velocity += acceleration * delta_time
        
        # Apply drag
        self.velocity *= self.drag_coefficient
        
        # Limit velocity
        if self.velocity.length() > self.max_velocity:
            self.velocity = self.velocity.normalize() * self.max_velocity
        
        # Update position
        self.position += self.velocity * delta_time
        
        # Update rotation
        self.rotation += self.rotation_speed * delta_time
    
    def draw(self, screen, camera_offset):
        """Draw debris with motion trails."""
        screen_pos = self.position - camera_offset
        
        # Draw motion trail if moving fast enough
        if self.velocity.length() > 30:
            trail_length = min(self.velocity.length() / 5, 20)
            trail_end = screen_pos - self.velocity.normalize() * trail_length
            
            # Fade trail color
            trail_color = (100, 100, 100, 128)
            pygame.draw.line(screen, trail_color[:3], screen_pos, trail_end, 1)
        
        # Draw debris
        # ... existing drawing code with rotation ...
```

#### 2. Gravitational Body Interface
```python
# src/physics/gravitational_body.py (new file)
from abc import ABC, abstractmethod
import pygame
from pygame import Vector2

class GravitationalBody(ABC):
    """Interface for objects that exert gravitational force."""
    
    @abstractmethod
    def calculate_gravitational_force(self, other_object) -> Vector2:
        """Calculate gravitational force on another object."""
        pass
    
    @abstractmethod
    def get_mass(self) -> float:
        """Get the mass of this gravitational body."""
        pass
    
    @abstractmethod
    def get_position(self) -> Vector2:
        """Get the position of this gravitational body."""
        pass

# Implement interface for planets and black holes
class Planet(GravitationalBody):
    def calculate_gravitational_force(self, other_object) -> Vector2:
        # ... gravitational force calculation ...
        
class BlackHole(GravitationalBody):
    def calculate_gravitational_force(self, other_object) -> Vector2:
        # ... gravitational force calculation ...
```

---

## Integration Timeline

### Phase 1: Core Implementation (Week 1-2)
1. Implement AfterburnerSystem class
2. Add basic WASD input support
3. Create DifficultyManager structure
4. Enhance Debris physics

### Phase 2: Integration (Week 3)
1. Integrate afterburners with ship systems
2. Add input manager to ship controls
3. Connect difficulty settings to game systems
4. Update universe generation for debris physics

### Phase 3: Polish & Testing (Week 4)
1. Visual effects for afterburners
2. UI updates for control scheme selection
3. Difficulty balancing and testing
4. Performance optimization for enhanced physics

### Phase 4: Documentation & Release (Week 5)
1. Update all documentation
2. Create feature tutorials
3. Comprehensive testing
4. Release preparation

---

## Testing Strategy

### Unit Tests
- Individual system functionality
- Edge case handling
- Performance benchmarks

### Integration Tests
- System interactions
- Save/load compatibility
- Settings persistence

### User Experience Tests
- Control responsiveness
- Difficulty progression
- Visual feedback clarity

### Performance Tests
- Frame rate impact
- Memory usage
- Physics calculation efficiency