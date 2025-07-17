import pygame
from pygame import Vector2
import random
import math
from enum import Enum
from typing import List, Optional


class DebrisType(Enum):
    """Types of debris with different properties."""
    METAL = "metal"
    ICE = "ice"
    SHIP_PART = "ship_part"
    ASTEROID_CHUNK = "asteroid_chunk"


class DebrisPhysics:
    """Physics calculations for debris."""
    
    # Physical constants
    SPACE_FRICTION = 0.99  # Gradual momentum loss
    GRAVITATIONAL_CONSTANT = 100.0  # Simplified gravity
    MIN_INTERACTION_DISTANCE = 100.0  # Minimum distance for physics interactions
    MAX_INTERACTION_DISTANCE = 300.0  # Maximum distance for physics interactions
    
    @staticmethod
    def calculate_gravity(debris1, debris2) -> Vector2:
        """Calculate gravitational force between two debris pieces."""
        distance_vec = debris2.position - debris1.position
        distance = distance_vec.length()
        
        if distance < DebrisPhysics.MIN_INTERACTION_DISTANCE or distance > DebrisPhysics.MAX_INTERACTION_DISTANCE:
            return Vector2(0, 0)
        
        # Only larger debris exert meaningful gravity
        if debris2.mass < debris1.mass * 2:
            return Vector2(0, 0)
        
        # F = G * m1 * m2 / r^2
        force_magnitude = (DebrisPhysics.GRAVITATIONAL_CONSTANT * debris1.mass * debris2.mass) / (distance * distance)
        force_direction = distance_vec.normalize()
        
        return force_direction * force_magnitude
    
    @staticmethod
    def calculate_collision_response(debris1, debris2):
        """Calculate collision response between two debris pieces."""
        # Calculate collision normal
        collision_vec = debris2.position - debris1.position
        distance = collision_vec.length()
        
        if distance == 0:
            return  # Avoid division by zero
        
        collision_normal = collision_vec.normalize()
        
        # Calculate relative velocity
        relative_velocity = debris1.velocity - debris2.velocity
        
        # Calculate relative velocity in collision normal direction
        vel_along_normal = relative_velocity.dot(collision_normal)
        
        # Don't resolve if velocities are separating
        if vel_along_normal > 0:
            return
        
        # Calculate restitution (bounciness)
        restitution = (debris1.restitution + debris2.restitution) / 2
        
        # Calculate impulse scalar
        impulse_scalar = -(1 + restitution) * vel_along_normal
        impulse_scalar /= (1 / debris1.mass + 1 / debris2.mass)
        
        # Apply impulse
        impulse = collision_normal * impulse_scalar
        debris1.velocity += impulse / debris1.mass
        debris2.velocity -= impulse / debris2.mass
        
        # Separate overlapping debris
        overlap = (debris1.size + debris2.size) - distance
        if overlap > 0:
            separation = collision_normal * (overlap / 2)
            debris1.position -= separation
            debris2.position += separation


class Debris:
    """Enhanced debris with realistic physics."""
    
    def __init__(self, x, y, debris_type: DebrisType = None):
        self.position = Vector2(x, y)
        self.debris_type = debris_type or random.choice(list(DebrisType))
        
        # Initialize properties based on debris type
        self._init_type_properties()
        
        # Physics properties
        self.velocity = Vector2(random.uniform(-20, 20), random.uniform(-20, 20))
        self.acceleration = Vector2(0, 0)
        self.angular_velocity = random.uniform(-30, 30)  # degrees per second
        self.angular_acceleration = 0
        
        # Visual properties
        self.rotation = random.uniform(0, 360)
        self.shape_points = self._generate_shape()
        self.lifetime = random.uniform(300, 600)  # seconds
        self.age = 0
        
        # Particle effects
        self.particle_trail = []
        self.collision_sparks = []
        
    def _init_type_properties(self):
        """Initialize properties based on debris type."""
        if self.debris_type == DebrisType.METAL:
            self.size = random.uniform(8, 25)
            self.mass = self.size * 2.0  # Dense
            self.restitution = 0.6  # Somewhat bouncy
            self.color = (120, 120, 130)
            self.friction = 0.98
            self.magnetic = True
            
        elif self.debris_type == DebrisType.ICE:
            self.size = random.uniform(5, 15)
            self.mass = self.size * 0.5  # Light
            self.restitution = 0.3  # Less bouncy
            self.color = (180, 200, 255)
            self.friction = 0.95
            self.magnetic = False
            self.sublimation_rate = 0.1  # Gradually disappears
            
        elif self.debris_type == DebrisType.SHIP_PART:
            self.size = random.uniform(10, 30)
            self.mass = self.size * 1.5  # Medium density
            self.restitution = 0.4
            self.color = (100, 80, 60)
            self.friction = 0.97
            self.magnetic = True
            self.salvage_value = random.randint(10, 50)
            
        elif self.debris_type == DebrisType.ASTEROID_CHUNK:
            self.size = random.uniform(20, 50)
            self.mass = self.size * 3.0  # Very dense
            self.restitution = 0.2  # Not very bouncy
            self.color = (80, 70, 60)
            self.friction = 0.99
            self.magnetic = False
            
    def _generate_shape(self):
        """Generate random shape points for visual variety."""
        num_points = random.randint(4, 8)
        points = []
        
        for i in range(num_points):
            angle = (i / num_points) * 360
            # Add some randomness to the radius
            radius = self.size * random.uniform(0.6, 1.0)
            angle_rad = math.radians(angle)
            
            point = Vector2(
                math.cos(angle_rad) * radius,
                math.sin(angle_rad) * radius
            )
            points.append(point)
        
        return points
    
    def update(self, delta_time: float, nearby_debris: List['Debris'] = None):
        """Update debris physics and state."""
        self.age += delta_time
        
        # Reset acceleration for this frame
        self.acceleration = Vector2(0, 0)
        
        # Apply gravitational forces from nearby debris
        if nearby_debris:
            for other in nearby_debris:
                if other != self:
                    gravity_force = DebrisPhysics.calculate_gravity(self, other)
                    self.acceleration += gravity_force / self.mass
        
        # Apply space friction
        self.velocity *= self.friction
        
        # Update physics
        self.velocity += self.acceleration * delta_time
        self.position += self.velocity * delta_time
        
        # Update rotation
        self.angular_velocity *= 0.999  # Gradual slowdown
        self.rotation += self.angular_velocity * delta_time
        
        # Handle special type behaviors
        if self.debris_type == DebrisType.ICE:
            # Sublimation effect
            if hasattr(self, 'sublimation_rate'):
                self.size *= (1 - self.sublimation_rate * delta_time * 0.001)
                if self.size < 1:
                    self.lifetime = 0  # Mark for removal
        
        # Update particle trail
        self._update_particle_trail(delta_time)
        
        # Update collision sparks
        self._update_collision_sparks(delta_time)
    
    def _update_particle_trail(self, delta_time: float):
        """Update particle trail effect."""
        # Add new particle if moving fast enough
        velocity_length = self.velocity.length()
        if velocity_length > 10:
            self.particle_trail.append({
                'position': Vector2(self.position),
                'life': 1.0,
                'max_life': 1.0,
                'size': self.size * 0.1
            })
        
        # Update existing particles
        for particle in self.particle_trail[:]:
            particle['life'] -= delta_time
            if particle['life'] <= 0:
                self.particle_trail.remove(particle)
    
    def _update_collision_sparks(self, delta_time: float):
        """Update collision spark effects."""
        for spark in self.collision_sparks[:]:
            spark['life'] -= delta_time
            spark['position'] += spark['velocity'] * delta_time
            spark['velocity'] *= 0.95  # Friction
            
            if spark['life'] <= 0:
                self.collision_sparks.remove(spark)
    
    def collide_with(self, other: 'Debris'):
        """Handle collision with another debris piece."""
        # Check if collision is possible
        distance = (self.position - other.position).length()
        if distance > (self.size + other.size):
            return False
        
        # Calculate collision response
        DebrisPhysics.calculate_collision_response(self, other)
        
        # Create collision sparks
        self._create_collision_sparks(other)
        
        return True
    
    def _create_collision_sparks(self, other: 'Debris'):
        """Create spark effects at collision point."""
        collision_point = (self.position + other.position) / 2
        
        # Create several sparks
        for _ in range(random.randint(3, 8)):
            spark = {
                'position': Vector2(collision_point),
                'velocity': Vector2(
                    random.uniform(-50, 50),
                    random.uniform(-50, 50)
                ),
                'life': random.uniform(0.2, 0.5),
                'size': random.uniform(1, 3),
                'color': (255, 200, 100)
            }
            self.collision_sparks.append(spark)
    
    def draw(self, screen, camera_offset):
        """Draw debris with enhanced visuals."""
        screen_pos = self.position - camera_offset
        
        # Don't draw if off-screen (with buffer)
        screen_rect = screen.get_rect()
        buffer = self.size + 50
        if (screen_pos.x < -buffer or screen_pos.x > screen_rect.width + buffer or
            screen_pos.y < -buffer or screen_pos.y > screen_rect.height + buffer):
            return
        
        # Draw particle trail
        self._draw_particle_trail(screen, camera_offset)
        
        # Draw main debris
        self._draw_main_debris(screen, screen_pos)
        
        # Draw collision sparks
        self._draw_collision_sparks(screen, camera_offset)
    
    def _draw_particle_trail(self, screen, camera_offset):
        """Draw particle trail effect."""
        for particle in self.particle_trail:
            alpha = particle['life'] / particle['max_life']
            if alpha > 0:
                screen_pos = particle['position'] - camera_offset
                color = (int(self.color[0] * alpha), 
                        int(self.color[1] * alpha), 
                        int(self.color[2] * alpha))
                
                # Draw small circle for particle
                pygame.draw.circle(screen, color, 
                                 (int(screen_pos.x), int(screen_pos.y)), 
                                 max(1, int(particle['size'] * alpha)))
    
    def _draw_main_debris(self, screen, screen_pos):
        """Draw the main debris shape."""
        # Transform shape points
        transformed_points = []
        for point in self.shape_points:
            rotated_point = point.rotate(self.rotation)
            transformed_point = rotated_point + screen_pos
            transformed_points.append(transformed_point)
        
        # Draw main shape
        if len(transformed_points) >= 3:
            pygame.draw.polygon(screen, self.color, transformed_points)
            
            # Add outline for better visibility
            outline_color = (min(255, self.color[0] + 30), 
                           min(255, self.color[1] + 30), 
                           min(255, self.color[2] + 30))
            pygame.draw.polygon(screen, outline_color, transformed_points, 1)
    
    def _draw_collision_sparks(self, screen, camera_offset):
        """Draw collision spark effects."""
        for spark in self.collision_sparks:
            screen_pos = spark['position'] - camera_offset
            alpha = spark['life'] / 0.5  # Assuming max life is 0.5
            
            if alpha > 0:
                color = (int(spark['color'][0] * alpha),
                        int(spark['color'][1] * alpha),
                        int(spark['color'][2] * alpha))
                
                pygame.draw.circle(screen, color,
                                 (int(screen_pos.x), int(screen_pos.y)),
                                 max(1, int(spark['size'] * alpha)))
    
    def is_expired(self) -> bool:
        """Check if debris should be removed."""
        return self.age >= self.lifetime or self.size < 1
    
    def get_kinetic_energy(self) -> float:
        """Calculate kinetic energy for physics interactions."""
        return 0.5 * self.mass * (self.velocity.length() ** 2)
    
    def fragment(self, num_fragments: int = None) -> List['Debris']:
        """Break debris into smaller pieces."""
        if self.size < 10:  # Too small to fragment
            return []
        
        if num_fragments is None:
            num_fragments = random.randint(2, 4)
        
        fragments = []
        fragment_size = self.size / math.sqrt(num_fragments)
        
        for i in range(num_fragments):
            # Create fragment at slightly offset position
            offset = Vector2(
                random.uniform(-self.size/2, self.size/2),
                random.uniform(-self.size/2, self.size/2)
            )
            
            fragment = Debris(
                self.position.x + offset.x,
                self.position.y + offset.y,
                self.debris_type
            )
            
            # Smaller size and mass
            fragment.size = fragment_size * random.uniform(0.8, 1.2)
            fragment.mass = fragment.mass * (fragment.size / self.size)
            
            # Inherit some velocity plus random component
            fragment.velocity = self.velocity * 0.5 + Vector2(
                random.uniform(-30, 30),
                random.uniform(-30, 30)
            )
            
            fragments.append(fragment)
        
        return fragments