"""Asteroid entities with various hazard types."""

import pygame
import math
import random
from pygame import Vector2
from typing import Optional, List
from enum import Enum

from ..ui import gfx


class AsteroidType(Enum):
    NORMAL = "normal"
    RADIOACTIVE = "radioactive"
    EXPLOSIVE = "explosive"


class Asteroid:
    """Base asteroid class with collision and physics."""
    
    def __init__(self, position: Vector2, size: float, asteroid_type: AsteroidType = AsteroidType.NORMAL):
        self.position = Vector2(position)
        self.size = size
        self.asteroid_type = asteroid_type
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-30, 30)  # degrees per second
        self.velocity = Vector2(0, 0)
        self.mass = size ** 2 * 0.1  # Mass scales with size squared
        
        # Health system based on size
        self.max_health = size * 2.0  # Larger asteroids are tougher
        self.current_health = self.max_health
        self.destroyed = False
        
        # Damage properties
        self.collision_damage = size * 0.5  # Damage to ship on collision
        
        # Visual properties
        self.color = self._get_color()
        self.shape_points = self._generate_shape()
        
        # Special properties based on type
        self._init_special_properties()
        
    def _get_color(self) -> tuple:
        """Get asteroid color based on type."""
        color_map = {
            AsteroidType.NORMAL: (120, 120, 120),
            AsteroidType.RADIOACTIVE: (120, 200, 80),
            AsteroidType.EXPLOSIVE: (200, 120, 80)
        }
        return color_map.get(self.asteroid_type, (120, 120, 120))
    
    def _generate_shape(self) -> List[Vector2]:
        """Generate irregular asteroid shape."""
        points = []
        num_points = random.randint(6, 12)
        
        for i in range(num_points):
            angle = (2 * math.pi * i) / num_points
            # Add randomness to radius for irregular shape
            radius_variation = random.uniform(0.7, 1.3)
            radius = self.size * radius_variation
            
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            points.append(Vector2(x, y))
        
        return points
    
    def _init_special_properties(self):
        """Initialize type-specific properties."""
        if self.asteroid_type == AsteroidType.RADIOACTIVE:
            self.radiation_range = self.size * 3.0
            self.radiation_damage = 5.0  # Damage per second
            
        elif self.asteroid_type == AsteroidType.EXPLOSIVE:
            self.explosion_radius = self.size * 4.0
            self.explosion_damage = 100.0
            self.explosion_triggered = False
    
    def update(self, delta_time: float):
        """Update asteroid physics and rotation."""
        if self.destroyed:
            return
            
        # Update rotation
        self.rotation += self.rotation_speed * delta_time
        
        # Update position if moving
        self.position += self.velocity * delta_time
    
    def take_damage(self, damage: float) -> bool:
        """Apply damage to asteroid. Returns True if destroyed."""
        if self.destroyed:
            return True
            
        self.current_health -= damage
        
        if self.current_health <= 0:
            self.destroyed = True
            return True
        
        return False
    
    def get_health_percentage(self) -> float:
        """Get health as percentage (0.0 to 1.0)."""
        if self.max_health <= 0:
            return 1.0
        return max(0.0, min(1.0, self.current_health / self.max_health))
    
    def check_ship_collision(self, ship) -> float:
        """Check collision with ship and return damage to apply."""
        if self.destroyed:
            return 0.0
            
        distance = (self.position - ship.position).length()
        collision_distance = self.size + ship.size + 10
        
        if distance <= collision_distance:
            return self.collision_damage
        
        return 0.0
    
    def draw(self, screen: pygame.Surface, camera_offset: Vector2):
        """Draw the asteroid with type-specific visuals."""
        if self.destroyed:
            return
            
        screen_pos = self.position - camera_offset
        
        # Transform shape points
        transformed_points = []
        for point in self.shape_points:
            rotated_point = point.rotate(self.rotation)
            screen_point = screen_pos + rotated_point
            transformed_points.append((screen_point.x, screen_point.y))
        
        # Draw based on type
        if self.asteroid_type == AsteroidType.RADIOACTIVE:
            self._draw_radioactive(screen, screen_pos, transformed_points)
        elif self.asteroid_type == AsteroidType.EXPLOSIVE:
            self._draw_explosive(screen, screen_pos, transformed_points)
        else:
            self._draw_normal(screen, screen_pos, transformed_points)
        
        # Draw health bar if damaged
        if self.current_health < self.max_health:
            self._draw_health_bar(screen, screen_pos)
    
    def _craters(self):
        """A few craters, fixed for the life of this asteroid: (x, y, radius)
        as fractions of its size."""
        if not hasattr(self, "_crater_list"):
            rng = random.Random(int(self.size * 977) ^ int(self.max_health * 31))
            self._crater_list = [
                (rng.uniform(-0.45, 0.45), rng.uniform(-0.45, 0.45), rng.uniform(0.10, 0.2))
                for _ in range(rng.randint(2, 4))
            ]
        return self._crater_list

    def _draw_rock(self, screen: pygame.Surface, screen_pos: Vector2, points: List[tuple], base, edge):
        """The rock itself: a lit facet toward the upper left, a darker rim,
        and craters, so it reads as a solid lump rather than a flat polygon."""
        center = Vector2(screen_pos)
        pygame.draw.polygon(screen, base, points)
        facet = [center + (Vector2(p) - center) * 0.78 + Vector2(-0.1, -0.12) * self.size for p in points]
        pygame.draw.polygon(screen, gfx.lighten(base, 0.16), facet)
        shade = [center + (Vector2(p) - center) * 0.55 + Vector2(0.18, 0.2) * self.size for p in points]
        pygame.draw.polygon(screen, gfx.darken(base, 0.25), shade)
        for cx, cy, cr in self._craters():
            at = center + Vector2(cx, cy).rotate(self.rotation) * self.size
            radius = max(2, int(cr * self.size))
            pygame.draw.circle(screen, gfx.darken(base, 0.42), (int(at.x), int(at.y)), radius)
            pygame.draw.circle(screen, gfx.lighten(base, 0.3), (int(at.x - 1), int(at.y - 1)), radius, 1)
        pygame.draw.polygon(screen, edge, points, 2)

    def _draw_normal(self, screen: pygame.Surface, screen_pos: Vector2, points: List[tuple]):
        """Draw normal asteroid."""
        self._draw_rock(screen, screen_pos, points, self.color, gfx.darken(self.color, 0.55))
    
    def _draw_health_bar(self, screen: pygame.Surface, screen_pos: Vector2):
        """Draw health bar above asteroid."""
        bar_width = 40
        bar_height = 5
        bar_x = screen_pos.x - bar_width // 2
        bar_y = screen_pos.y - self.size - 10
        health_percentage = self.get_health_percentage()
        health_color = (230, 60, 50) if health_percentage < 0.3 else (235, 200, 50) if health_percentage < 0.7 else (80, 210, 90)
        gfx.draw_bar(screen, (int(bar_x), int(bar_y), bar_width, bar_height), health_percentage, health_color)
    
    def _draw_radioactive(self, screen: pygame.Surface, screen_pos: Vector2, points: List[tuple]):
        """Draw radioactive asteroid with a pulsing radiation glow."""
        pulse = gfx.flicker(self.position.x * 0.01, speed=0.4, low=0.55)
        gfx.draw_glow(screen, screen_pos, self.radiation_range * 0.85, (60, 230, 90), 0.28 * pulse)
        gfx.draw_ring_glow(screen, screen_pos, self.radiation_range, 3, (60, 200, 90), 0.5 * pulse)

        self._draw_rock(screen, screen_pos, points, self.color, (100, 255, 100))

        # Radiation trefoil, glowing
        symbol_size = self.size * 0.3
        symbol_x, symbol_y = int(screen_pos.x), int(screen_pos.y)
        gfx.draw_glow(screen, screen_pos, self.size * 0.7, (200, 255, 80), 0.5 * pulse)
        for angle in [0, 120, 240]:
            end_x = symbol_x + symbol_size * math.cos(math.radians(angle))
            end_y = symbol_y + symbol_size * math.sin(math.radians(angle))
            pygame.draw.line(screen, (255, 255, 110), (symbol_x, symbol_y), (end_x, end_y), 2)
    
    def _draw_explosive(self, screen: pygame.Surface, screen_pos: Vector2, points: List[tuple]):
        """Draw explosive asteroid: a hot, flickering warning glow."""
        pulse = gfx.flicker(self.position.y * 0.01, speed=0.9, low=0.4)
        gfx.draw_glow(screen, screen_pos, self.size * 2.0, (255, 120, 30), 0.35 * pulse)
        pygame.draw.circle(screen, (110, 55, 50), (int(screen_pos.x), int(screen_pos.y)),
                           int(self.explosion_radius), 1)

        self._draw_rock(screen, screen_pos, points, self.color, (255, 150, 100))

        # Warning stripes
        stripe_color = (255, 200, 0)
        for i in range(3):
            start_angle = i * 60 + self.rotation
            end_angle = start_angle + 30
            start_pos = screen_pos + Vector2(self.size * 0.5, 0).rotate(start_angle)
            end_pos = screen_pos + Vector2(self.size * 0.8, 0).rotate(end_angle)
            pygame.draw.line(screen, stripe_color, start_pos, end_pos, 3)
        # A glowing fault line
        gfx.draw_glow(screen, screen_pos, self.size * 0.8, (255, 140, 40), 0.5 * pulse)
    
    
    def check_radiation_damage(self, ship) -> float:
        """Check if ship takes radiation damage (radioactive asteroids only)."""
        if self.asteroid_type != AsteroidType.RADIOACTIVE:
            return 0.0
        
        distance = (self.position - ship.position).length()
        if distance <= self.radiation_range:
            # Damage decreases with distance
            damage_factor = 1.0 - (distance / self.radiation_range)
            return self.radiation_damage * damage_factor
        
        return 0.0
    
    def check_explosion_trigger(self, ship) -> bool:
        """Check if ship triggers explosion (explosive asteroids only)."""
        if (self.asteroid_type != AsteroidType.EXPLOSIVE or 
            self.explosion_triggered):
            return False
        
        distance = (self.position - ship.position).length()
        collision_distance = self.size + ship.size + ship.COLLISION_BUFFER
        
        if distance <= collision_distance:
            self.explosion_triggered = True
            return True
        
        return False
    
    def get_explosion_damage(self, ship_position: Vector2) -> float:
        """Calculate explosion damage based on distance (explosive asteroids only)."""
        if self.asteroid_type != AsteroidType.EXPLOSIVE:
            return 0.0
        
        distance = (self.position - ship_position).length()
        if distance <= self.explosion_radius:
            # Damage decreases with distance from explosion center
            damage_factor = 1.0 - (distance / self.explosion_radius)
            return self.explosion_damage * damage_factor
        
        return 0.0
    
    def get_info(self) -> dict:
        """Get asteroid information for display."""
        return {
            "type": self.asteroid_type.value,
            "size": self.size,
            "position": (self.position.x, self.position.y),
            "mass": self.mass,
            "special_properties": self._get_special_info()
        }
    
    def _get_special_info(self) -> dict:
        """Get type-specific information."""
        if self.asteroid_type == AsteroidType.RADIOACTIVE:
            return {
                "radiation_range": self.radiation_range,
                "radiation_damage": self.radiation_damage
            }
        elif self.asteroid_type == AsteroidType.EXPLOSIVE:
            return {
                "explosion_radius": self.explosion_radius,
                "explosion_damage": self.explosion_damage,
                "triggered": self.explosion_triggered
            }
        return {}


def create_asteroid_field(center: Vector2, field_radius: float, 
                         asteroid_count: int, special_chance: float = 0.2) -> List[Asteroid]:
    """Create a field of asteroids with some special types."""
    asteroids = []
    
    for _ in range(asteroid_count):
        # Random position within field
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0, field_radius)
        position = center + Vector2(
            distance * math.cos(angle),
            distance * math.sin(angle)
        )
        
        # Random size
        size = random.uniform(20, 80)
        
        # Determine asteroid type
        if random.random() < special_chance:
            # Choose special type (no black holes in asteroids anymore)
            special_types = [AsteroidType.RADIOACTIVE, AsteroidType.EXPLOSIVE]
            asteroid_type = random.choice(special_types)
        else:
            asteroid_type = AsteroidType.NORMAL
        
        asteroid = Asteroid(position, size, asteroid_type)
        asteroids.append(asteroid)
    
    return asteroids