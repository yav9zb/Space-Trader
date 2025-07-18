"""
Core base building entities and components.
"""

import pygame
from pygame import Vector2
import random
import time
from enum import Enum, auto
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


class ModuleType(Enum):
    """Types of base modules that can be constructed."""
    # Core Infrastructure
    COMMAND_CENTER = "command_center"
    POWER_GENERATOR = "power_generator"
    HABITAT = "habitat"
    STORAGE = "storage"
    
    # Production Facilities
    REFINERY = "refinery"
    FACTORY = "factory"
    MINING_FACILITY = "mining_facility"
    RESEARCH_LAB = "research_lab"
    
    # Defense Systems
    TURRET = "turret"
    SHIELD_GENERATOR = "shield_generator"
    SENSOR_ARRAY = "sensor_array"
    
    # Trading and Logistics
    TRADE_HUB = "trade_hub"
    DOCKING_BAY = "docking_bay"
    CARGO_DEPOT = "cargo_depot"


@dataclass
class ModuleStats:
    """Statistics and properties for a base module."""
    power_consumption: int = 0
    power_generation: int = 0
    storage_capacity: int = 0
    crew_capacity: int = 0
    production_rate: float = 0.0
    defense_rating: int = 0
    cost: Dict[str, int] = field(default_factory=dict)
    build_time: float = 0.0  # seconds
    size: int = 1  # grid size (1x1, 2x2, etc.)


class BaseModule:
    """Individual module within a player base."""
    
    # Module definitions with their stats
    MODULE_DEFINITIONS = {
        ModuleType.COMMAND_CENTER: ModuleStats(
            power_consumption=50,
            crew_capacity=10,
            cost={"Metal": 1000, "Electronics": 500, "Credits": 50000},
            build_time=300.0,
            size=2
        ),
        ModuleType.POWER_GENERATOR: ModuleStats(
            power_generation=100,
            cost={"Metal": 500, "Electronics": 200, "Fuel": 100, "Credits": 25000},
            build_time=180.0,
            size=1
        ),
        ModuleType.HABITAT: ModuleStats(
            power_consumption=20,
            crew_capacity=20,
            cost={"Metal": 300, "Textiles": 100, "Credits": 15000},
            build_time=120.0,
            size=1
        ),
        ModuleType.STORAGE: ModuleStats(
            power_consumption=5,
            storage_capacity=1000,
            cost={"Metal": 200, "Credits": 8000},
            build_time=60.0,
            size=1
        ),
        ModuleType.REFINERY: ModuleStats(
            power_consumption=80,
            production_rate=2.0,
            cost={"Metal": 800, "Electronics": 400, "Machinery": 300, "Credits": 40000},
            build_time=240.0,
            size=2
        ),
        ModuleType.FACTORY: ModuleStats(
            power_consumption=60,
            production_rate=1.5,
            cost={"Metal": 600, "Electronics": 300, "Machinery": 200, "Credits": 30000},
            build_time=200.0,
            size=2
        ),
        ModuleType.MINING_FACILITY: ModuleStats(
            power_consumption=100,
            production_rate=3.0,
            cost={"Metal": 1200, "Machinery": 500, "Electronics": 200, "Credits": 60000},
            build_time=360.0,
            size=3
        ),
        ModuleType.RESEARCH_LAB: ModuleStats(
            power_consumption=40,
            crew_capacity=5,
            cost={"Metal": 400, "Electronics": 600, "Luxury": 200, "Credits": 35000},
            build_time=300.0,
            size=1
        ),
        ModuleType.TURRET: ModuleStats(
            power_consumption=30,
            defense_rating=50,
            cost={"Metal": 400, "Electronics": 200, "Weapons": 300, "Credits": 20000},
            build_time=150.0,
            size=1
        ),
        ModuleType.SHIELD_GENERATOR: ModuleStats(
            power_consumption=120,
            defense_rating=100,
            cost={"Metal": 600, "Electronics": 800, "Credits": 50000},
            build_time=240.0,
            size=2
        ),
        ModuleType.SENSOR_ARRAY: ModuleStats(
            power_consumption=25,
            cost={"Metal": 300, "Electronics": 400, "Credits": 18000},
            build_time=120.0,
            size=1
        ),
        ModuleType.TRADE_HUB: ModuleStats(
            power_consumption=40,
            storage_capacity=2000,
            cost={"Metal": 500, "Electronics": 300, "Credits": 30000},
            build_time=180.0,
            size=2
        ),
        ModuleType.DOCKING_BAY: ModuleStats(
            power_consumption=20,
            cost={"Metal": 800, "Electronics": 100, "Credits": 25000},
            build_time=200.0,
            size=3
        ),
        ModuleType.CARGO_DEPOT: ModuleStats(
            power_consumption=10,
            storage_capacity=5000,
            cost={"Metal": 400, "Credits": 15000},
            build_time=100.0,
            size=2
        )
    }
    
    def __init__(self, module_type: ModuleType, grid_x: int, grid_y: int):
        self.module_type = module_type
        self.grid_position = Vector2(grid_x, grid_y)
        self.stats = self.MODULE_DEFINITIONS[module_type]
        
        # Construction state
        self.construction_started = time.time()
        self.construction_time_elapsed = 0.0  # Track simulated time
        self.is_constructed = False
        self.construction_progress = 0.0
        
        # Operational state
        self.is_powered = False
        self.is_operational = False
        self.efficiency = 1.0  # 0.0 to 1.0
        self.damage_level = 0.0  # 0.0 to 1.0
        
        # Module-specific data
        self.stored_resources = {}
        self.production_queue = []
        self.crew_assigned = 0
        
        # Visual properties
        self.rotation = 0
        self.visual_effects = []
    
    def update(self, delta_time: float) -> None:
        """Update module state."""
        # Update construction progress
        if not self.is_constructed:
            self.construction_time_elapsed += delta_time
            self.construction_progress = min(1.0, self.construction_time_elapsed / self.stats.build_time)
            
            if self.construction_progress >= 1.0:
                self.is_constructed = True
                self.is_operational = True
        
        # Update operational status
        if self.is_constructed:
            self.is_operational = self.is_powered and self.damage_level < 0.8
            
            # Update efficiency based on power and damage
            efficiency_factor = 1.0
            if not self.is_powered:
                efficiency_factor *= 0.1  # Minimal operation without power
            efficiency_factor *= (1.0 - self.damage_level * 0.5)  # Damage reduces efficiency
            
            self.efficiency = max(0.0, min(1.0, efficiency_factor))
        
        # Update visual effects
        self._update_visual_effects(delta_time)
    
    def _update_visual_effects(self, delta_time: float) -> None:
        """Update visual effects for the module."""
        # Update existing effects
        for effect in self.visual_effects[:]:
            effect['life'] -= delta_time
            if effect['life'] <= 0:
                self.visual_effects.remove(effect)
        
        # Add new effects based on module state
        if self.is_operational:
            if self.module_type == ModuleType.POWER_GENERATOR:
                # Add energy pulse effect
                if random.random() < 0.1:  # 10% chance per frame
                    self.visual_effects.append({
                        'type': 'energy_pulse',
                        'life': 2.0,
                        'intensity': 1.0
                    })
            
            elif self.module_type in [ModuleType.REFINERY, ModuleType.FACTORY]:
                # Add production smoke
                if random.random() < 0.05:  # 5% chance per frame
                    self.visual_effects.append({
                        'type': 'production_smoke',
                        'life': 3.0,
                        'intensity': self.efficiency
                    })
    
    def get_power_consumption(self) -> int:
        """Get current power consumption."""
        if not self.is_constructed:
            return 0
        return int(self.stats.power_consumption * self.efficiency)
    
    def get_power_generation(self) -> int:
        """Get current power generation."""
        if not self.is_constructed or not self.is_operational:
            return 0
        return int(self.stats.power_generation * self.efficiency)
    
    def get_production_rate(self) -> float:
        """Get current production rate."""
        if not self.is_operational:
            return 0.0
        return self.stats.production_rate * self.efficiency
    
    def can_store_resource(self, resource_type: str, amount: int) -> bool:
        """Check if module can store the specified resource amount."""
        current_storage = sum(self.stored_resources.values())
        return current_storage + amount <= self.stats.storage_capacity
    
    def store_resource(self, resource_type: str, amount: int) -> int:
        """Store resource in module. Returns amount actually stored."""
        if resource_type not in self.stored_resources:
            self.stored_resources[resource_type] = 0
        
        current_storage = sum(self.stored_resources.values())
        available_space = self.stats.storage_capacity - current_storage
        amount_to_store = min(amount, available_space)
        
        self.stored_resources[resource_type] += amount_to_store
        return amount_to_store
    
    def remove_resource(self, resource_type: str, amount: int) -> int:
        """Remove resource from module. Returns amount actually removed."""
        if resource_type not in self.stored_resources:
            return 0
        
        available_amount = self.stored_resources[resource_type]
        amount_to_remove = min(amount, available_amount)
        
        self.stored_resources[resource_type] -= amount_to_remove
        if self.stored_resources[resource_type] <= 0:
            del self.stored_resources[resource_type]
        
        return amount_to_remove
    
    def repair(self, repair_amount: float) -> None:
        """Repair module damage."""
        self.damage_level = max(0.0, self.damage_level - repair_amount)
    
    def take_damage(self, damage_amount: float) -> None:
        """Apply damage to module."""
        self.damage_level = min(1.0, self.damage_level + damage_amount)
        
        # Module destruction
        if self.damage_level >= 1.0:
            self.is_operational = False
    
    def get_world_position(self, base_position: Vector2, grid_size: float) -> Vector2:
        """Get world position of module based on base position and grid."""
        return base_position + Vector2(
            self.grid_position.x * grid_size,
            self.grid_position.y * grid_size
        )
    
    def draw(self, screen, world_position: Vector2, camera_offset: Vector2, grid_size: float) -> None:
        """Draw the module."""
        screen_pos = world_position - camera_offset
        
        # Don't draw if off-screen
        screen_rect = screen.get_rect()
        if (screen_pos.x < -grid_size or screen_pos.x > screen_rect.width + grid_size or
            screen_pos.y < -grid_size or screen_pos.y > screen_rect.height + grid_size):
            return
        
        # Determine module color based on type and state
        color = self._get_module_color()
        
        # Draw module base
        module_size = grid_size * self.stats.size
        rect = pygame.Rect(
            screen_pos.x - module_size // 2,
            screen_pos.y - module_size // 2,
            module_size,
            module_size
        )
        
        # Draw construction progress
        if not self.is_constructed:
            # Show construction progress
            progress_color = (100, 100, 100)
            pygame.draw.rect(screen, progress_color, rect)
            
            # Progress bar
            progress_width = int(module_size * self.construction_progress)
            progress_rect = pygame.Rect(rect.x, rect.y + module_size - 5, progress_width, 5)
            pygame.draw.rect(screen, (0, 255, 0), progress_rect)
        else:
            # Draw operational module
            pygame.draw.rect(screen, color, rect)
            
            # Power indicator
            if self.is_powered:
                pygame.draw.circle(screen, (0, 255, 0), (rect.x + 5, rect.y + 5), 3)
            else:
                pygame.draw.circle(screen, (255, 0, 0), (rect.x + 5, rect.y + 5), 3)
            
            # Damage indicator
            if self.damage_level > 0:
                damage_overlay = pygame.Surface((module_size, module_size))
                damage_overlay.set_alpha(int(255 * self.damage_level * 0.5))
                damage_overlay.fill((255, 0, 0))
                screen.blit(damage_overlay, (rect.x, rect.y))
        
        # Draw visual effects
        self._draw_visual_effects(screen, screen_pos)
    
    def _get_module_color(self) -> tuple:
        """Get color for module based on type and state."""
        base_colors = {
            ModuleType.COMMAND_CENTER: (100, 150, 255),
            ModuleType.POWER_GENERATOR: (255, 255, 100),
            ModuleType.HABITAT: (150, 255, 150),
            ModuleType.STORAGE: (200, 200, 200),
            ModuleType.REFINERY: (255, 150, 100),
            ModuleType.FACTORY: (150, 100, 255),
            ModuleType.MINING_FACILITY: (139, 69, 19),
            ModuleType.RESEARCH_LAB: (100, 255, 255),
            ModuleType.TURRET: (255, 100, 100),
            ModuleType.SHIELD_GENERATOR: (100, 200, 255),
            ModuleType.SENSOR_ARRAY: (255, 200, 100),
            ModuleType.TRADE_HUB: (255, 255, 200),
            ModuleType.DOCKING_BAY: (180, 180, 180),
            ModuleType.CARGO_DEPOT: (160, 160, 160)
        }
        
        base_color = base_colors.get(self.module_type, (128, 128, 128))
        
        # Modify color based on operational state
        if not self.is_operational:
            # Darken non-operational modules
            return tuple(int(c * 0.5) for c in base_color)
        
        return base_color
    
    def _draw_visual_effects(self, screen, center_pos: Vector2) -> None:
        """Draw visual effects for the module."""
        for effect in self.visual_effects:
            alpha = effect['life'] / 2.0  # Fade out over life
            
            if effect['type'] == 'energy_pulse':
                # Draw pulsing energy effect
                radius = int(20 * (1 - alpha))
                color = (255, 255, 100, int(255 * alpha))
                pygame.draw.circle(screen, color[:3], 
                                 (int(center_pos.x), int(center_pos.y)), radius, 2)
            
            elif effect['type'] == 'production_smoke':
                # Draw smoke particles
                for i in range(3):
                    offset_x = random.randint(-10, 10)
                    offset_y = random.randint(-15, -5)
                    smoke_pos = (int(center_pos.x + offset_x), int(center_pos.y + offset_y))
                    color = (150, 150, 150, int(100 * alpha))
                    pygame.draw.circle(screen, color[:3], smoke_pos, 2)


class PlayerBase:
    """A player-constructed base with multiple modules."""
    
    def __init__(self, x: float, y: float, name: str = "New Base"):
        self.position = Vector2(x, y)
        self.name = name
        self.created_time = time.time()
        
        # Grid system for module placement
        self.grid_size = 50  # pixels per grid cell
        self.max_grid_size = 20  # 20x20 grid
        self.modules: Dict[tuple, BaseModule] = {}  # (grid_x, grid_y) -> BaseModule
        
        # Base resources and state
        self.stored_resources = {}
        self.power_generation = 0
        self.power_consumption = 0
        self.crew_count = 0
        self.crew_capacity = 0
        self.defense_rating = 0
        
        # Base status
        self.is_active = True
        self.last_updated = time.time()
        
        # Visual properties
        self.base_size = 100  # Base visual size
        self.detection_range = 200
        
        # Start with a command center
        self.add_module(ModuleType.COMMAND_CENTER, 0, 0)
    
    def add_module(self, module_type: ModuleType, grid_x: int, grid_y: int) -> bool:
        """Add a module to the base. Returns True if successful."""
        # Check if position is valid
        if not self.is_valid_position(grid_x, grid_y, module_type):
            return False
        
        # Check if we have required resources
        if not self.can_afford_module(module_type):
            return False
        
        # Create and place module
        module = BaseModule(module_type, grid_x, grid_y)
        
        # Occupy grid spaces for multi-cell modules
        size = module.stats.size
        for x in range(grid_x, grid_x + size):
            for y in range(grid_y, grid_y + size):
                self.modules[(x, y)] = module
        
        # Deduct resources
        self.deduct_construction_costs(module_type)
        
        return True
    
    def remove_module(self, grid_x: int, grid_y: int) -> bool:
        """Remove a module from the base."""
        if (grid_x, grid_y) not in self.modules:
            return False
        
        module = self.modules[(grid_x, grid_y)]
        
        # Can't remove command center if it's the only one
        command_centers = [m for m in self.modules.values() 
                          if m.module_type == ModuleType.COMMAND_CENTER]
        if module.module_type == ModuleType.COMMAND_CENTER and len(command_centers) <= 1:
            return False
        
        # Remove from all grid positions
        size = module.stats.size
        for x in range(grid_x, grid_x + size):
            for y in range(grid_y, grid_y + size):
                if (x, y) in self.modules:
                    del self.modules[(x, y)]
        
        return True
    
    def is_valid_position(self, grid_x: int, grid_y: int, module_type: ModuleType) -> bool:
        """Check if a position is valid for placing a module."""
        module_stats = BaseModule.MODULE_DEFINITIONS[module_type]
        size = module_stats.size
        
        # Check grid boundaries
        if (grid_x < -self.max_grid_size // 2 or 
            grid_y < -self.max_grid_size // 2 or
            grid_x + size > self.max_grid_size // 2 or
            grid_y + size > self.max_grid_size // 2):
            return False
        
        # Check for overlapping modules
        for x in range(grid_x, grid_x + size):
            for y in range(grid_y, grid_y + size):
                if (x, y) in self.modules:
                    return False
        
        return True
    
    def can_afford_module(self, module_type: ModuleType) -> bool:
        """Check if base has resources to build module."""
        costs = BaseModule.MODULE_DEFINITIONS[module_type].cost
        
        for resource, amount in costs.items():
            if resource == "Credits":
                # TODO: Check player credits
                continue
            
            available = self.stored_resources.get(resource, 0)
            if available < amount:
                return False
        
        return True
    
    def deduct_construction_costs(self, module_type: ModuleType) -> None:
        """Deduct resources for module construction."""
        costs = BaseModule.MODULE_DEFINITIONS[module_type].cost
        
        for resource, amount in costs.items():
            if resource == "Credits":
                # TODO: Deduct player credits
                continue
            
            if resource in self.stored_resources:
                self.stored_resources[resource] -= amount
                if self.stored_resources[resource] <= 0:
                    del self.stored_resources[resource]
    
    def update(self, delta_time: float) -> None:
        """Update base and all its modules."""
        self.last_updated = time.time()
        
        # Update all modules
        unique_modules = set(self.modules.values())
        for module in unique_modules:
            module.update(delta_time)
        
        # Update base statistics
        self._update_base_stats()
        
        # Update power distribution
        self._update_power_system()
        
        # Update production
        self._update_production(delta_time)
    
    def _update_base_stats(self) -> None:
        """Update base-wide statistics."""
        unique_modules = set(self.modules.values())
        
        self.power_generation = sum(m.get_power_generation() for m in unique_modules)
        self.power_consumption = sum(m.get_power_consumption() for m in unique_modules)
        self.crew_capacity = sum(m.stats.crew_capacity for m in unique_modules if m.is_constructed)
        self.defense_rating = sum(m.stats.defense_rating for m in unique_modules if m.is_operational)
    
    def _update_power_system(self) -> None:
        """Update power distribution to modules."""
        # Simple power system: if generation >= consumption, all modules powered
        power_available = self.power_generation >= self.power_consumption
        
        unique_modules = set(self.modules.values())
        for module in unique_modules:
            module.is_powered = power_available and module.is_constructed
    
    def _update_production(self, delta_time: float) -> None:
        """Update resource production."""
        unique_modules = set(self.modules.values())
        
        for module in unique_modules:
            if not module.is_operational:
                continue
            
            production_rate = module.get_production_rate()
            if production_rate <= 0:
                continue
            
            # Simple production: generate basic resources
            if module.module_type == ModuleType.MINING_FACILITY:
                resource_type = "Metal"
                amount = int(production_rate * delta_time)
                self.add_resource(resource_type, amount)
            
            elif module.module_type == ModuleType.REFINERY:
                # Refine raw materials into processed goods
                if self.has_resource("Metal", 1):
                    self.remove_resource("Metal", 1)
                    self.add_resource("Electronics", 1)
    
    def add_resource(self, resource_type: str, amount: int) -> int:
        """Add resource to base storage. Returns amount actually stored."""
        # Find storage modules with capacity
        storage_modules = [m for m in set(self.modules.values()) 
                          if m.is_operational and m.stats.storage_capacity > 0]
        
        remaining_amount = amount
        for module in storage_modules:
            if remaining_amount <= 0:
                break
            
            stored = module.store_resource(resource_type, remaining_amount)
            remaining_amount -= stored
        
        # Also store in base-level storage
        if remaining_amount > 0:
            if resource_type not in self.stored_resources:
                self.stored_resources[resource_type] = 0
            self.stored_resources[resource_type] += remaining_amount
        
        return amount - remaining_amount
    
    def remove_resource(self, resource_type: str, amount: int) -> int:
        """Remove resource from base storage. Returns amount actually removed."""
        # Remove from base-level storage first
        base_amount = self.stored_resources.get(resource_type, 0)
        base_removed = min(amount, base_amount)
        
        if base_removed > 0:
            self.stored_resources[resource_type] -= base_removed
            if self.stored_resources[resource_type] <= 0:
                del self.stored_resources[resource_type]
        
        remaining_to_remove = amount - base_removed
        
        # Remove from module storage
        storage_modules = [m for m in set(self.modules.values()) 
                          if m.is_operational and resource_type in m.stored_resources]
        
        for module in storage_modules:
            if remaining_to_remove <= 0:
                break
            
            removed = module.remove_resource(resource_type, remaining_to_remove)
            remaining_to_remove -= removed
        
        return amount - remaining_to_remove
    
    def has_resource(self, resource_type: str, amount: int) -> bool:
        """Check if base has specified amount of resource."""
        total_amount = self.get_resource_amount(resource_type)
        return total_amount >= amount
    
    def get_resource_amount(self, resource_type: str) -> int:
        """Get total amount of resource in base."""
        # Base storage
        total = self.stored_resources.get(resource_type, 0)
        
        # Module storage
        unique_modules = set(self.modules.values())
        for module in unique_modules:
            total += module.stored_resources.get(resource_type, 0)
        
        return total
    
    def get_total_storage_capacity(self) -> int:
        """Get total storage capacity of base."""
        unique_modules = set(self.modules.values())
        return sum(m.stats.storage_capacity for m in unique_modules if m.is_operational)
    
    def draw(self, screen, camera_offset: Vector2) -> None:
        """Draw the base and all its modules."""
        screen_pos = self.position - camera_offset
        
        # Don't draw if too far off-screen
        screen_rect = screen.get_rect()
        max_base_size = self.max_grid_size * self.grid_size
        if (screen_pos.x < -max_base_size or screen_pos.x > screen_rect.width + max_base_size or
            screen_pos.y < -max_base_size or screen_pos.y > screen_rect.height + max_base_size):
            return
        
        # Draw base foundation/platform
        base_rect = pygame.Rect(
            screen_pos.x - self.base_size // 2,
            screen_pos.y - self.base_size // 2,
            self.base_size,
            self.base_size
        )
        pygame.draw.rect(screen, (60, 60, 80), base_rect)
        pygame.draw.rect(screen, (100, 100, 120), base_rect, 2)
        
        # Draw grid (for construction mode)
        # This would be shown only in construction interface
        
        # Draw all modules
        unique_modules = set(self.modules.values())
        for module in unique_modules:
            world_pos = module.get_world_position(self.position, self.grid_size)
            module.draw(screen, world_pos, camera_offset, self.grid_size)
        
        # Draw base name and status
        if pygame.font.get_init():
            font = pygame.font.Font(None, 24)
            name_text = font.render(self.name, True, (255, 255, 255))
            name_rect = name_text.get_rect(center=(screen_pos.x, screen_pos.y - self.base_size // 2 - 20))
            screen.blit(name_text, name_rect)
            
            # Power status
            power_color = (0, 255, 0) if self.power_generation >= self.power_consumption else (255, 255, 0)
            power_text = f"Power: {self.power_generation}/{self.power_consumption}"
            power_surface = font.render(power_text, True, power_color)
            power_rect = power_surface.get_rect(center=(screen_pos.x, screen_pos.y + self.base_size // 2 + 20))
            screen.blit(power_surface, power_rect)