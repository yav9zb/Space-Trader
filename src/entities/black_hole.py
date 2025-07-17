"""Black hole hazards separate from asteroids."""

import pygame
import math
import random
from pygame import Vector2
from typing import Optional


class BlackHole:
    """Gravitational hazard that pulls ships in and deals damage."""
    
    def __init__(self, position: Vector2, size: float = 60.0):
        self.position = Vector2(position)
        self.size = size
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(10, 30)  # Slow, ominous rotation
        
        # Gravitational properties
        self.gravity_strength = size * 75000  # Stronger than asteroid black holes
        self.event_horizon = size * 0.6  # Instant death zone
        self.accretion_disk_radius = size * 2.5
        self.damage_zone = size * 1.2  # Area that deals damage
        
        # Damage properties
        self.damage_per_second = 25.0
        self.contact_damage = 100.0  # Instant damage on event horizon contact
        
        # Visual effects
        self.pulse_timer = 0.0
        self.distortion_intensity = 0.0
        
    def update(self, delta_time: float):
        """Update black hole effects and rotation."""
        # Update rotation with chaotic variations
        variation = math.sin(self.pulse_timer * 2) * 5
        self.rotation += (self.rotation_speed + variation) * delta_time
        
        # Update pulse timer for visual effects
        self.pulse_timer += delta_time
        
        # Update distortion intensity (pulsing effect)
        self.distortion_intensity = 0.5 + 0.3 * math.sin(self.pulse_timer * 3)
    
    def apply_gravity_to_ship(self, ship) -> Vector2:
        """Apply gravitational force to a ship."""
        distance_vec = self.position - ship.position
        distance = distance_vec.length()
        
        if distance < self.event_horizon:
            # Inside event horizon - apply massive damage and pull
            ship.take_damage(self.contact_damage)
            force_magnitude = self.gravity_strength * 3.0
        elif distance < self.damage_zone:
            # In damage zone - apply damage over time
            damage = self.damage_per_second * (1.0 - (distance - self.event_horizon) / (self.damage_zone - self.event_horizon))
            ship.take_damage(damage * 0.016)  # Approximate delta_time of 1/60
            force_magnitude = self.gravity_strength / (distance ** 1.2)
        elif distance < self.accretion_disk_radius:
            # In accretion disk - strong pull but no damage
            force_magnitude = self.gravity_strength / (distance ** 1.5)
        else:
            # Outside disk - weaker gravitational influence
            force_magnitude = self.gravity_strength / (distance ** 2.2)
        
        # Cap the force to prevent extreme acceleration
        force_magnitude = min(force_magnitude, 8000.0)
        
        if distance > 0:
            force_direction = distance_vec.normalize()
            return force_direction * force_magnitude
        
        return Vector2(0, 0)
    
    def apply_gravity_to_bandit(self, bandit) -> Vector2:
        """Apply gravitational force to a bandit ship."""
        # Use the same logic as apply_gravity_to_ship
        return self.apply_gravity_to_ship(bandit)
    
    def check_ship_damage(self, ship) -> float:
        """Check if ship takes damage from black hole proximity."""
        distance = (self.position - ship.position).length()
        
        if distance <= self.event_horizon:
            # Inside event horizon - massive damage
            return self.contact_damage
        elif distance <= self.damage_zone:
            # In damage zone - proximity damage
            damage_factor = 1.0 - (distance - self.event_horizon) / (self.damage_zone - self.event_horizon)
            return self.damage_per_second * damage_factor
        
        return 0.0
    
    def draw(self, screen: pygame.Surface, camera_offset: Vector2):
        """Draw the black hole with gravitational effects."""
        screen_pos = self.position - camera_offset
        
        # Draw accretion disk (outermost layer)
        disk_color = (80 + int(20 * self.distortion_intensity), 
                     40 + int(30 * self.distortion_intensity), 
                     120 + int(20 * self.distortion_intensity))
        pygame.draw.circle(screen, disk_color, 
                         (int(screen_pos.x), int(screen_pos.y)), 
                         int(self.accretion_disk_radius), 3)
        
        # Draw gravitational distortion rings
        for i in range(3):
            ring_radius = self.size * (1.8 - i * 0.3)
            ring_alpha = int(100 * self.distortion_intensity * (1 - i * 0.3))
            ring_color = (60 + ring_alpha, 30 + ring_alpha//2, 100 + ring_alpha)
            pygame.draw.circle(screen, ring_color,
                             (int(screen_pos.x), int(screen_pos.y)),
                             int(ring_radius), 2)
        
        # Draw damage zone warning
        if self.damage_zone > self.event_horizon:
            warning_color = (200, 100, 100, int(50 * (1 + math.sin(self.pulse_timer * 4))))
            pygame.draw.circle(screen, (200, 100, 100),
                             (int(screen_pos.x), int(screen_pos.y)),
                             int(self.damage_zone), 1)
        
        # Draw event horizon (point of no return)
        horizon_color = (20, 10, 20)
        pygame.draw.circle(screen, horizon_color,
                         (int(screen_pos.x), int(screen_pos.y)),
                         int(self.event_horizon))
        
        # Draw the black hole core (absolute black)
        core_radius = self.size * 0.4
        pygame.draw.circle(screen, (0, 0, 0),
                         (int(screen_pos.x), int(screen_pos.y)),
                         int(core_radius))
        
        # Add pulsing energy effects around the core
        pulse_radius = core_radius + 5 * math.sin(self.pulse_timer * 5)
        if pulse_radius > core_radius:
            pulse_color = (100, 50, 150, int(100 * math.sin(self.pulse_timer * 5)))
            pygame.draw.circle(screen, (100, 50, 150),
                             (int(screen_pos.x), int(screen_pos.y)),
                             int(pulse_radius), 1)
        
        # Draw directional gravitational field lines (rotating)
        for angle_offset in range(0, 360, 45):
            angle = math.radians(self.rotation + angle_offset)
            start_radius = self.accretion_disk_radius * 0.8
            end_radius = self.size * 1.1
            
            start_x = screen_pos.x + start_radius * math.cos(angle)
            start_y = screen_pos.y + start_radius * math.sin(angle)
            end_x = screen_pos.x + end_radius * math.cos(angle)
            end_y = screen_pos.y + end_radius * math.sin(angle)
            
            line_color = (60, 30, 100)
            pygame.draw.line(screen, line_color, (start_x, start_y), (end_x, end_y), 1)
    
    def get_threat_level(self, ship_position: Vector2) -> str:
        """Get threat level description based on ship distance."""
        distance = (self.position - ship_position).length()
        
        if distance <= self.event_horizon:
            return "CRITICAL - Event Horizon"
        elif distance <= self.damage_zone:
            return "DANGER - Damage Zone"
        elif distance <= self.accretion_disk_radius:
            return "WARNING - Gravitational Field"
        elif distance <= self.accretion_disk_radius * 1.5:
            return "CAUTION - Gravity Detected"
        else:
            return "SAFE"
    
    def get_info(self) -> dict:
        """Get black hole information for display."""
        return {
            "type": "black_hole",
            "size": self.size,
            "position": (self.position.x, self.position.y),
            "gravity_strength": self.gravity_strength,
            "event_horizon": self.event_horizon,
            "damage_zone": self.damage_zone,
            "accretion_disk_radius": self.accretion_disk_radius,
            "damage_per_second": self.damage_per_second
        }


def create_black_hole_field(center: Vector2, field_radius: float, hole_count: int = 1) -> list:
    """Create a field of black holes."""
    black_holes = []
    
    for _ in range(hole_count):
        # Position within field
        if hole_count == 1:
            position = center
        else:
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, field_radius)
            position = center + Vector2(
                distance * math.cos(angle),
                distance * math.sin(angle)
            )
        
        # Random size (larger holes are rarer)
        size_roll = random.random()
        if size_roll < 0.7:
            size = random.uniform(40, 70)  # Small holes
        elif size_roll < 0.9:
            size = random.uniform(70, 100)  # Medium holes
        else:
            size = random.uniform(100, 150)  # Large holes (rare)
        
        black_hole = BlackHole(position, size)
        black_holes.append(black_hole)
    
    return black_holes