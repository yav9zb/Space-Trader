"""Advanced debris field management system with physics interactions."""

import random
from typing import List, Dict, Tuple, Optional
from pygame import Vector2
import math

try:
    from ..entities.debris import Debris, DebrisType, DebrisPhysics
except ImportError:
    from entities.debris import Debris, DebrisType, DebrisPhysics


class SpatialGrid:
    """Spatial partitioning for efficient collision detection."""
    
    def __init__(self, cell_size: float = 200.0):
        self.cell_size = cell_size
        self.grid: Dict[Tuple[int, int], List[Debris]] = {}
    
    def clear(self):
        """Clear the grid."""
        self.grid.clear()
    
    def _get_cell_key(self, position: Vector2) -> Tuple[int, int]:
        """Get grid cell key for a position."""
        return (int(position.x // self.cell_size), int(position.y // self.cell_size))
    
    def add_debris(self, debris: Debris):
        """Add debris to the spatial grid."""
        key = self._get_cell_key(debris.position)
        if key not in self.grid:
            self.grid[key] = []
        self.grid[key].append(debris)
    
    def get_nearby_debris(self, position: Vector2, radius: float = 300.0) -> List[Debris]:
        """Get all debris within radius of position."""
        nearby = []
        cell_radius = int(math.ceil(radius / self.cell_size))
        center_key = self._get_cell_key(position)
        
        # Check surrounding cells
        for x_offset in range(-cell_radius, cell_radius + 1):
            for y_offset in range(-cell_radius, cell_radius + 1):
                cell_key = (center_key[0] + x_offset, center_key[1] + y_offset)
                if cell_key in self.grid:
                    for debris in self.grid[cell_key]:
                        distance = (debris.position - position).length()
                        if distance <= radius:
                            nearby.append(debris)
        
        return nearby
    
    def get_potential_collisions(self, debris: Debris) -> List[Debris]:
        """Get debris that might collide with the given debris."""
        nearby = self.get_nearby_debris(debris.position, debris.size * 3)
        potential_collisions = []
        
        for other in nearby:
            if other != debris:
                distance = (debris.position - other.position).length()
                if distance <= (debris.size + other.size + 5):  # Small buffer
                    potential_collisions.append(other)
        
        return potential_collisions


class DebrisFieldManager:
    """Manages debris fields with advanced physics."""
    
    def __init__(self):
        self.debris_list: List[Debris] = []
        self.spatial_grid = SpatialGrid()
        self.max_debris_count = 500  # Performance limit
        self.collision_pairs_processed = set()  # Avoid duplicate collision processing
        
        # Physics settings
        self.enable_gravity = True
        self.enable_collisions = True
        self.enable_fragmentation = True
        self.cleanup_expired = True
        
        # Statistics
        self.stats = {
            'total_debris': 0,
            'collisions_this_frame': 0,
            'fragments_created': 0,
            'debris_removed': 0
        }
    
    def add_debris(self, debris: Debris):
        """Add debris to the field."""
        if len(self.debris_list) < self.max_debris_count:
            self.debris_list.append(debris)
            self.stats['total_debris'] += 1
    
    def create_debris_field(self, center: Vector2, radius: float, num_debris: int, 
                           debris_types: List[DebrisType] = None) -> List[Debris]:
        """Create a debris field around a center point."""
        if debris_types is None:
            debris_types = [DebrisType.METAL, DebrisType.ICE, DebrisType.SHIP_PART]
        
        created_debris = []
        
        for _ in range(num_debris):
            # Random position within radius
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, radius)
            
            pos = center + Vector2(
                math.cos(angle) * distance,
                math.sin(angle) * distance
            )
            
            # Random debris type
            debris_type = random.choice(debris_types)
            
            # Create debris
            debris = Debris(pos.x, pos.y, debris_type)
            
            # Give it some initial velocity (orbital or dispersal)
            if debris_type == DebrisType.ASTEROID_CHUNK:
                # Large chunks move slowly
                debris.velocity = Vector2(
                    random.uniform(-5, 5),
                    random.uniform(-5, 5)
                )
            else:
                # Smaller debris can move faster
                debris.velocity = Vector2(
                    random.uniform(-30, 30),
                    random.uniform(-30, 30)
                )
            
            self.add_debris(debris)
            created_debris.append(debris)
        
        return created_debris
    
    def create_explosion_debris(self, center: Vector2, force: float, num_debris: int) -> List[Debris]:
        """Create debris from an explosion."""
        created_debris = []
        
        for _ in range(num_debris):
            # Random position near explosion center
            offset = Vector2(
                random.uniform(-20, 20),
                random.uniform(-20, 20)
            )
            pos = center + offset
            
            # Create debris (mostly ship parts and metal)
            debris_type = random.choice([DebrisType.SHIP_PART, DebrisType.METAL])
            debris = Debris(pos.x, pos.y, debris_type)
            
            # Explosion force pushes debris outward
            direction = offset.normalize() if offset.length() > 0 else Vector2(1, 0)
            debris.velocity = direction * force * random.uniform(0.5, 1.5)
            
            # High angular velocity from explosion
            debris.angular_velocity = random.uniform(-90, 90)
            
            self.add_debris(debris)
            created_debris.append(debris)
        
        return created_debris
    
    def update(self, delta_time: float):
        """Update all debris with advanced physics."""
        # Reset frame statistics
        self.stats['collisions_this_frame'] = 0
        self.collision_pairs_processed.clear()
        
        # Rebuild spatial grid
        self.spatial_grid.clear()
        for debris in self.debris_list:
            self.spatial_grid.add_debris(debris)
        
        # Update each debris piece
        for debris in self.debris_list[:]:  # Use slice to avoid modification during iteration
            # Get nearby debris for physics interactions
            nearby_debris = self.spatial_grid.get_nearby_debris(
                debris.position, 
                DebrisPhysics.MAX_INTERACTION_DISTANCE
            ) if self.enable_gravity else None
            
            # Update debris physics
            debris.update(delta_time, nearby_debris)
            
            # Handle collisions
            if self.enable_collisions:
                self._handle_collisions(debris)
            
            # Remove expired debris
            if self.cleanup_expired and debris.is_expired():
                self.debris_list.remove(debris)
                self.stats['debris_removed'] += 1
                self.stats['total_debris'] -= 1
        
        # Limit debris count for performance
        if len(self.debris_list) > self.max_debris_count:
            # Remove oldest debris
            excess = len(self.debris_list) - self.max_debris_count
            for _ in range(excess):
                if self.debris_list:
                    removed = self.debris_list.pop(0)
                    self.stats['debris_removed'] += 1
                    self.stats['total_debris'] -= 1
    
    def _handle_collisions(self, debris: Debris):
        """Handle collisions for a single debris piece."""
        potential_collisions = self.spatial_grid.get_potential_collisions(debris)
        
        for other in potential_collisions:
            # Create unique pair identifier
            pair_id = (id(debris), id(other)) if id(debris) < id(other) else (id(other), id(debris))
            
            if pair_id not in self.collision_pairs_processed:
                self.collision_pairs_processed.add(pair_id)
                
                if debris.collide_with(other):
                    self.stats['collisions_this_frame'] += 1
                    
                    # Handle fragmentation for high-energy collisions
                    if self.enable_fragmentation:
                        self._handle_fragmentation(debris, other)
    
    def _handle_fragmentation(self, debris1: Debris, debris2: Debris):
        """Handle fragmentation from high-energy collisions."""
        # Calculate collision energy
        energy1 = debris1.get_kinetic_energy()
        energy2 = debris2.get_kinetic_energy()
        total_energy = energy1 + energy2
        
        # Fragmentation threshold based on size and energy
        fragmentation_threshold = max(debris1.size, debris2.size) * 1000
        
        if total_energy > fragmentation_threshold:
            # Determine which debris fragments
            if debris1.size > 15 and energy2 > energy1 and debris1 in self.debris_list:
                fragments = debris1.fragment()
                self.debris_list.remove(debris1)
                self.stats['total_debris'] -= 1
                
                for fragment in fragments:
                    self.add_debris(fragment)
                    self.stats['fragments_created'] += 1
            
            elif debris2.size > 15 and energy1 > energy2 and debris2 in self.debris_list:
                fragments = debris2.fragment()
                self.debris_list.remove(debris2)
                self.stats['total_debris'] -= 1
                
                for fragment in fragments:
                    self.add_debris(fragment)
                    self.stats['fragments_created'] += 1
    
    def get_debris_at_position(self, position: Vector2, radius: float = 50.0) -> List[Debris]:
        """Get debris within radius of a position."""
        return self.spatial_grid.get_nearby_debris(position, radius)
    
    def remove_debris_at_position(self, position: Vector2, radius: float = 50.0) -> int:
        """Remove debris within radius of a position. Returns count removed."""
        nearby = self.get_debris_at_position(position, radius)
        removed_count = 0
        
        for debris in nearby:
            if debris in self.debris_list:
                self.debris_list.remove(debris)
                removed_count += 1
                self.stats['debris_removed'] += 1
                self.stats['total_debris'] -= 1
        
        return removed_count
    
    def apply_force_at_position(self, position: Vector2, force: Vector2, radius: float = 100.0):
        """Apply force to debris within radius of a position."""
        nearby = self.get_debris_at_position(position, radius)
        
        for debris in nearby:
            distance = (debris.position - position).length()
            if distance > 0:
                # Force decreases with distance
                force_factor = max(0, 1 - (distance / radius))
                applied_force = force * force_factor
                
                # Apply force based on mass
                debris.acceleration += applied_force / debris.mass
    
    def create_orbital_debris(self, center: Vector2, orbit_radius: float, 
                            num_debris: int, orbital_velocity: float = 50.0) -> List[Debris]:
        """Create debris in orbital patterns around a center point."""
        created_debris = []
        
        for i in range(num_debris):
            # Evenly distribute around orbit
            angle = (i / num_debris) * 2 * math.pi
            
            # Position on orbit with some randomness
            actual_radius = orbit_radius * random.uniform(0.8, 1.2)
            pos = center + Vector2(
                math.cos(angle) * actual_radius,
                math.sin(angle) * actual_radius
            )
            
            # Create debris
            debris = Debris(pos.x, pos.y, DebrisType.METAL)
            
            # Orbital velocity perpendicular to radius
            orbital_dir = Vector2(-math.sin(angle), math.cos(angle))
            debris.velocity = orbital_dir * orbital_velocity * random.uniform(0.8, 1.2)
            
            self.add_debris(debris)
            created_debris.append(debris)
        
        return created_debris
    
    def draw(self, screen, camera_offset):
        """Draw all debris in the field."""
        for debris in self.debris_list:
            debris.draw(screen, camera_offset)
    
    def get_stats(self) -> Dict:
        """Get debris field statistics."""
        return {
            **self.stats,
            'active_debris': len(self.debris_list),
            'spatial_grid_cells': len(self.spatial_grid.grid)
        }
    
    def clear_all_debris(self):
        """Remove all debris from the field."""
        removed_count = len(self.debris_list)
        self.debris_list.clear()
        self.spatial_grid.clear()
        self.stats['debris_removed'] += removed_count
        self.stats['total_debris'] = 0
    
    def set_physics_settings(self, gravity: bool = True, collisions: bool = True, 
                           fragmentation: bool = True, cleanup: bool = True):
        """Configure physics settings."""
        self.enable_gravity = gravity
        self.enable_collisions = collisions
        self.enable_fragmentation = fragmentation
        self.cleanup_expired = cleanup


# Global debris field manager instance
debris_field_manager = DebrisFieldManager()