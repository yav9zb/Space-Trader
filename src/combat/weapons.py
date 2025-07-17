"""Weapon system for combat encounters."""

import pygame
import math
import random
from pygame import Vector2
from typing import List, Optional
from enum import Enum
from dataclasses import dataclass


class WeaponType(Enum):
    LASER = "laser"
    PLASMA = "plasma"
    MISSILE = "missile"
    RAILGUN = "railgun"


@dataclass
class WeaponStats:
    """Statistics for a weapon."""
    damage: float
    range: float
    fire_rate: float  # shots per second
    energy_cost: float
    projectile_speed: float
    spread: float = 0.0  # accuracy spread in degrees


class Projectile:
    """Base class for weapon projectiles."""
    
    def __init__(self, position: Vector2, velocity: Vector2, damage: float, owner, weapon_type: WeaponType):
        self.position = Vector2(position)
        self.velocity = Vector2(velocity)
        self.damage = damage
        self.owner = owner
        self.weapon_type = weapon_type
        self.alive = True
        self.age = 0.0
        self.max_age = 3.0  # Projectiles expire after 3 seconds
        
    def update(self, delta_time: float):
        """Update projectile position and lifetime."""
        self.position += self.velocity * delta_time
        self.age += delta_time
        
        if self.age >= self.max_age:
            self.alive = False
    
    def draw(self, screen: pygame.Surface, camera_offset: Vector2):
        """Draw the projectile."""
        screen_pos = self.position - camera_offset
        
        if self.weapon_type == WeaponType.LASER:
            # Draw laser beam
            pygame.draw.circle(screen, (255, 100, 100), (int(screen_pos.x), int(screen_pos.y)), 2)
        elif self.weapon_type == WeaponType.PLASMA:
            # Draw plasma bolt
            pygame.draw.circle(screen, (100, 255, 100), (int(screen_pos.x), int(screen_pos.y)), 3)
        elif self.weapon_type == WeaponType.MISSILE:
            # Draw missile with trail
            pygame.draw.circle(screen, (255, 255, 100), (int(screen_pos.x), int(screen_pos.y)), 4)
            # Draw exhaust trail
            trail_end = self.position - self.velocity.normalize() * 10 if self.velocity.length() > 0 else self.position
            trail_screen = trail_end - camera_offset
            pygame.draw.line(screen, (255, 150, 0), screen_pos, trail_screen, 2)
        elif self.weapon_type == WeaponType.RAILGUN:
            # Draw railgun slug
            pygame.draw.circle(screen, (150, 150, 255), (int(screen_pos.x), int(screen_pos.y)), 1)
    
    def check_collision(self, target) -> bool:
        """Check if projectile hits a target."""
        if not self.alive or target == self.owner:
            return False
            
        distance = (self.position - target.position).length()
        return distance <= target.size


class Weapon:
    """Base weapon class."""
    
    def __init__(self, weapon_type: WeaponType, stats: WeaponStats):
        self.weapon_type = weapon_type
        self.stats = stats
        self.last_fire_time = 0.0
        self.energy = 100.0  # Current energy
        self.max_energy = 100.0
        self.energy_regen_rate = 20.0  # energy per second
        
    def can_fire(self, current_time: float) -> bool:
        """Check if weapon can fire."""
        time_since_last_shot = current_time - self.last_fire_time
        fire_interval = 1.0 / self.stats.fire_rate
        
        return (time_since_last_shot >= fire_interval and 
                self.energy >= self.stats.energy_cost)
    
    def fire(self, position: Vector2, direction: Vector2, owner, current_time: float) -> Optional[Projectile]:
        """Fire the weapon and return a projectile."""
        if not self.can_fire(current_time):
            return None
            
        # Apply spread
        if self.stats.spread > 0:
            spread_angle = (random.random() - 0.5) * self.stats.spread
            direction = direction.rotate(spread_angle)
        
        # Create projectile
        velocity = direction.normalize() * self.stats.projectile_speed
        projectile = Projectile(position, velocity, self.stats.damage, owner, self.weapon_type)
        
        # Update weapon state
        self.last_fire_time = current_time
        self.energy -= self.stats.energy_cost
        
        return projectile
    
    def update(self, delta_time: float):
        """Update weapon energy regeneration."""
        self.energy = min(self.max_energy, self.energy + self.energy_regen_rate * delta_time)


class WeaponSystem:
    """Manages multiple weapons for a ship."""
    
    def __init__(self):
        self.weapons: List[Weapon] = []
        self.projectiles: List[Projectile] = []
        
    def add_weapon(self, weapon: Weapon):
        """Add a weapon to the system."""
        self.weapons.append(weapon)
    
    def fire_weapons(self, position: Vector2, direction: Vector2, owner, current_time: float):
        """Fire all available weapons."""
        for weapon in self.weapons:
            projectile = weapon.fire(position, direction, owner, current_time)
            if projectile:
                self.projectiles.append(projectile)
    
    def update(self, delta_time: float):
        """Update all weapons and projectiles."""
        # Update weapons
        for weapon in self.weapons:
            weapon.update(delta_time)
        
        # Update projectiles
        for projectile in self.projectiles[:]:
            projectile.update(delta_time)
            if not projectile.alive:
                self.projectiles.remove(projectile)
    
    def draw(self, screen: pygame.Surface, camera_offset: Vector2):
        """Draw all projectiles."""
        for projectile in self.projectiles:
            projectile.draw(screen, camera_offset)
    
    def check_hits(self, targets: List) -> List[tuple]:
        """Check for projectile hits against targets and return (projectile, target) pairs."""
        hits = []
        
        for projectile in self.projectiles[:]:
            for target in targets:
                if projectile.check_collision(target):
                    hits.append((projectile, target))
                    projectile.alive = False
                    break
        
        return hits
    
    def get_weapon_info(self) -> dict:
        """Get information about all weapons."""
        return {
            "weapon_count": len(self.weapons),
            "total_projectiles": len(self.projectiles),
            "weapon_details": [
                {
                    "type": weapon.weapon_type.value,
                    "energy": weapon.energy,
                    "max_energy": weapon.max_energy,
                    "damage": weapon.stats.damage,
                    "range": weapon.stats.range
                }
                for weapon in self.weapons
            ]
        }


# Predefined weapon configurations
WEAPON_CONFIGS = {
    "basic_laser": WeaponStats(
        damage=15.0,
        range=800.0,
        fire_rate=3.0,
        energy_cost=10.0,
        projectile_speed=1000.0,
        spread=2.0
    ),
    "plasma_cannon": WeaponStats(
        damage=25.0,
        range=600.0,
        fire_rate=1.5,
        energy_cost=20.0,
        projectile_speed=800.0,
        spread=5.0
    ),
    "missile_launcher": WeaponStats(
        damage=50.0,
        range=1200.0,
        fire_rate=0.5,
        energy_cost=40.0,
        projectile_speed=600.0,
        spread=1.0
    ),
    "railgun": WeaponStats(
        damage=75.0,
        range=1500.0,
        fire_rate=0.3,
        energy_cost=60.0,
        projectile_speed=2000.0,
        spread=0.5
    )
}


def create_weapon(weapon_config: str) -> Weapon:
    """Create a weapon from a configuration name."""
    if weapon_config not in WEAPON_CONFIGS:
        raise ValueError(f"Unknown weapon config: {weapon_config}")
    
    stats = WEAPON_CONFIGS[weapon_config]
    
    # Map config names to weapon types
    type_mapping = {
        "basic_laser": WeaponType.LASER,
        "plasma_cannon": WeaponType.PLASMA,
        "missile_launcher": WeaponType.MISSILE,
        "railgun": WeaponType.RAILGUN
    }
    
    weapon_type = type_mapping[weapon_config]
    return Weapon(weapon_type, stats)