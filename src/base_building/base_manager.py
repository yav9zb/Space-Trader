"""
Base Management System - Handles all player bases and their operations.
"""

import pygame
from pygame import Vector2
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from .base_entity import PlayerBase, BaseModule, ModuleType


class BaseManager:
    """Manages all player bases and base-related operations."""
    
    def __init__(self):
        self.bases: Dict[str, PlayerBase] = {}  # base_id -> PlayerBase
        self.active_base_id: Optional[str] = None
        self.next_base_id = 1
        
        # Construction settings
        self.max_bases_per_player = 10
        self.min_base_distance = 500  # Minimum distance between bases
        
        # Performance settings
        self.update_radius = 2000  # Only update bases within this range of player
        self.last_update_time = time.time()
        
        # Statistics
        self.stats = {
            'total_bases': 0,
            'total_modules': 0,
            'total_power_generation': 0,
            'total_power_consumption': 0,
            'total_defense_rating': 0
        }
    
    def create_base(self, position: Vector2, name: str = None) -> Optional[str]:
        """Create a new base at the specified position."""
        # Check base limit
        if len(self.bases) >= self.max_bases_per_player:
            return None
        
        # Check minimum distance from other bases
        for base in self.bases.values():
            distance = (position - base.position).length()
            if distance < self.min_base_distance:
                return None
        
        # Generate unique base ID
        base_id = f"base_{self.next_base_id}"
        self.next_base_id += 1
        
        # Create base
        if name is None:
            name = f"Base {len(self.bases) + 1}"
        
        base = PlayerBase(position.x, position.y, name)
        self.bases[base_id] = base
        
        # Set as active if it's the first base
        if self.active_base_id is None:
            self.active_base_id = base_id
        
        self.stats['total_bases'] += 1
        return base_id
    
    def remove_base(self, base_id: str) -> bool:
        """Remove a base."""
        if base_id not in self.bases:
            return False
        
        del self.bases[base_id]
        
        # Update active base if necessary
        if self.active_base_id == base_id:
            self.active_base_id = next(iter(self.bases.keys())) if self.bases else None
        
        self.stats['total_bases'] -= 1
        return True
    
    def get_base(self, base_id: str) -> Optional[PlayerBase]:
        """Get a base by ID."""
        return self.bases.get(base_id)
    
    def get_active_base(self) -> Optional[PlayerBase]:
        """Get the currently active base."""
        if self.active_base_id:
            return self.bases.get(self.active_base_id)
        return None
    
    def set_active_base(self, base_id: str) -> bool:
        """Set the active base."""
        if base_id in self.bases:
            self.active_base_id = base_id
            return True
        return False
    
    def get_nearest_base(self, position: Vector2) -> Optional[Tuple[str, PlayerBase, float]]:
        """Get the nearest base to a position. Returns (base_id, base, distance)."""
        nearest_base = None
        nearest_distance = float('inf')
        nearest_id = None
        
        for base_id, base in self.bases.items():
            distance = (position - base.position).length()
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_base = base
                nearest_id = base_id
        
        if nearest_base:
            return (nearest_id, nearest_base, nearest_distance)
        return None
    
    def get_bases_in_range(self, position: Vector2, radius: float) -> List[Tuple[str, PlayerBase, float]]:
        """Get all bases within range of a position."""
        bases_in_range = []
        
        for base_id, base in self.bases.items():
            distance = (position - base.position).length()
            if distance <= radius:
                bases_in_range.append((base_id, base, distance))
        
        # Sort by distance
        bases_in_range.sort(key=lambda x: x[2])
        return bases_in_range
    
    def can_place_base(self, position: Vector2) -> bool:
        """Check if a base can be placed at the specified position."""
        # Check base limit
        if len(self.bases) >= self.max_bases_per_player:
            return False
        
        # Check minimum distance from other bases
        for base in self.bases.values():
            distance = (position - base.position).length()
            if distance < self.min_base_distance:
                return False
        
        return True
    
    def update(self, delta_time: float, player_position: Vector2) -> None:
        """Update all bases within range of player."""
        current_time = time.time()
        
        # Update bases within range
        for base_id, base in self.bases.items():
            distance = (player_position - base.position).length()
            
            if distance <= self.update_radius:
                # Full update for nearby bases
                base.update(delta_time)
            else:
                # Simplified update for distant bases
                # Only update essential systems like production
                elapsed_since_last = current_time - base.last_updated
                if elapsed_since_last > 60.0:  # Update every minute when far away
                    base._update_production(elapsed_since_last)
                    base.last_updated = current_time
        
        # Update statistics
        self._update_statistics()
        
        self.last_update_time = current_time
    
    def _update_statistics(self) -> None:
        """Update manager-wide statistics."""
        self.stats['total_bases'] = len(self.bases)
        self.stats['total_modules'] = 0
        self.stats['total_power_generation'] = 0
        self.stats['total_power_consumption'] = 0
        self.stats['total_defense_rating'] = 0
        
        for base in self.bases.values():
            unique_modules = set(base.modules.values())
            self.stats['total_modules'] += len(unique_modules)
            self.stats['total_power_generation'] += base.power_generation
            self.stats['total_power_consumption'] += base.power_consumption
            self.stats['total_defense_rating'] += base.defense_rating
    
    def draw(self, screen, camera_offset: Vector2, player_position: Vector2) -> None:
        """Draw all bases within view distance."""
        screen_rect = screen.get_rect()
        view_distance = max(screen_rect.width, screen_rect.height) + 200
        
        for base in self.bases.values():
            # Only draw bases near the player or in view
            distance_to_player = (player_position - base.position).length()
            distance_to_camera = (base.position - (player_position - camera_offset)).length()
            
            if distance_to_player <= view_distance or distance_to_camera <= view_distance:
                base.draw(screen, camera_offset)
    
    def add_module_to_base(self, base_id: str, module_type: ModuleType, 
                          grid_x: int, grid_y: int) -> bool:
        """Add a module to a specific base."""
        base = self.get_base(base_id)
        if not base:
            return False
        
        return base.add_module(module_type, grid_x, grid_y)
    
    def remove_module_from_base(self, base_id: str, grid_x: int, grid_y: int) -> bool:
        """Remove a module from a specific base."""
        base = self.get_base(base_id)
        if not base:
            return False
        
        return base.remove_module(grid_x, grid_y)
    
    def get_base_info(self, base_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a base."""
        base = self.get_base(base_id)
        if not base:
            return None
        
        unique_modules = set(base.modules.values())
        module_counts = {}
        for module in unique_modules:
            module_type = module.module_type.value
            module_counts[module_type] = module_counts.get(module_type, 0) + 1
        
        return {
            'name': base.name,
            'position': (base.position.x, base.position.y),
            'created_time': base.created_time,
            'module_count': len(unique_modules),
            'module_types': module_counts,
            'power_generation': base.power_generation,
            'power_consumption': base.power_consumption,
            'power_efficiency': (base.power_generation / max(1, base.power_consumption)) * 100,
            'crew_count': base.crew_count,
            'crew_capacity': base.crew_capacity,
            'defense_rating': base.defense_rating,
            'storage_capacity': base.get_total_storage_capacity(),
            'stored_resources': dict(base.stored_resources),
            'is_active': base.is_active
        }
    
    def get_all_bases_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all bases."""
        return {base_id: self.get_base_info(base_id) for base_id in self.bases}
    
    def transfer_resources_between_bases(self, from_base_id: str, to_base_id: str,
                                       resource_type: str, amount: int) -> bool:
        """Transfer resources between two bases."""
        from_base = self.get_base(from_base_id)
        to_base = self.get_base(to_base_id)
        
        if not from_base or not to_base:
            return False
        
        # Check if source base has enough resources
        if not from_base.has_resource(resource_type, amount):
            return False
        
        # Remove from source
        removed = from_base.remove_resource(resource_type, amount)
        
        # Add to destination
        stored = to_base.add_resource(resource_type, removed)
        
        # Return any excess to source
        if stored < removed:
            excess = removed - stored
            from_base.add_resource(resource_type, excess)
        
        return stored > 0
    
    def get_base_construction_options(self, base_id: str) -> Dict[str, Any]:
        """Get available construction options for a base."""
        base = self.get_base(base_id)
        if not base:
            return {}
        
        options = {}
        
        for module_type in ModuleType:
            module_stats = BaseModule.MODULE_DEFINITIONS[module_type]
            
            # Check if base can afford the module
            can_afford = base.can_afford_module(module_type)
            
            # Find available positions
            available_positions = []
            for x in range(-base.max_grid_size // 2, base.max_grid_size // 2):
                for y in range(-base.max_grid_size // 2, base.max_grid_size // 2):
                    if base.is_valid_position(x, y, module_type):
                        available_positions.append((x, y))
            
            options[module_type.value] = {
                'can_afford': can_afford,
                'cost': module_stats.cost,
                'build_time': module_stats.build_time,
                'power_consumption': module_stats.power_consumption,
                'power_generation': module_stats.power_generation,
                'size': module_stats.size,
                'available_positions': available_positions[:20]  # Limit to first 20 positions
            }
        
        return options
    
    def save_bases(self) -> Dict[str, Any]:
        """Save all bases to a dictionary for persistence."""
        save_data = {
            'bases': {},
            'active_base_id': self.active_base_id,
            'next_base_id': self.next_base_id,
            'stats': dict(self.stats)
        }
        
        for base_id, base in self.bases.items():
            # Save base data
            modules_data = {}
            unique_modules = set(base.modules.values())
            for module in unique_modules:
                module_key = f"{int(module.grid_position.x)},{int(module.grid_position.y)}"
                modules_data[module_key] = {
                    'module_type': module.module_type.value,
                    'construction_started': module.construction_started,
                    'construction_time_elapsed': module.construction_time_elapsed,
                    'is_constructed': module.is_constructed,
                    'construction_progress': module.construction_progress,
                    'damage_level': module.damage_level,
                    'stored_resources': dict(module.stored_resources),
                    'crew_assigned': module.crew_assigned
                }
            
            save_data['bases'][base_id] = {
                'name': base.name,
                'position': [base.position.x, base.position.y],
                'created_time': base.created_time,
                'stored_resources': dict(base.stored_resources),
                'crew_count': base.crew_count,
                'is_active': base.is_active,
                'modules': modules_data
            }
        
        return save_data
    
    def load_bases(self, save_data: Dict[str, Any]) -> bool:
        """Load bases from saved data."""
        try:
            self.bases.clear()
            
            self.active_base_id = save_data.get('active_base_id')
            self.next_base_id = save_data.get('next_base_id', 1)
            self.stats = save_data.get('stats', {})
            
            for base_id, base_data in save_data.get('bases', {}).items():
                # Create base
                pos_data = base_data['position']
                base = PlayerBase(pos_data[0], pos_data[1], base_data['name'])
                
                # Restore base properties
                base.created_time = base_data.get('created_time', time.time())
                base.stored_resources = base_data.get('stored_resources', {})
                base.crew_count = base_data.get('crew_count', 0)
                base.is_active = base_data.get('is_active', True)
                
                # Clear default command center
                base.modules.clear()
                
                # Restore modules
                for module_key, module_data in base_data.get('modules', {}).items():
                    grid_x, grid_y = map(int, module_key.split(','))
                    module_type = ModuleType(module_data['module_type'])
                    
                    # Create module
                    module = BaseModule(module_type, grid_x, grid_y)
                    module.construction_started = module_data.get('construction_started', time.time())
                    module.construction_time_elapsed = module_data.get('construction_time_elapsed', 0.0)
                    module.is_constructed = module_data.get('is_constructed', False)
                    module.construction_progress = module_data.get('construction_progress', 0.0)
                    module.damage_level = module_data.get('damage_level', 0.0)
                    module.stored_resources = module_data.get('stored_resources', {})
                    module.crew_assigned = module_data.get('crew_assigned', 0)
                    
                    # Place module in grid
                    size = module.stats.size
                    for x in range(grid_x, grid_x + size):
                        for y in range(grid_y, grid_y + size):
                            base.modules[(x, y)] = module
                
                self.bases[base_id] = base
            
            return True
            
        except Exception as e:
            print(f"Error loading bases: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about all bases."""
        return dict(self.stats)


# Global base manager instance
base_manager = BaseManager()