"""Weapon system for combat encounters."""

import pygame
import math
import random
from pygame import Vector2

try:
    from ..ui import gfx
except ImportError:     # run as a plain script
    from ui import gfx
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
    ammo_type: str = "laser_cells"  # Type of ammo consumed
    ammo_per_shot: int = 1  # Amount of ammo consumed per shot


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
    
    def _palette(self):
        """(outer, core) colours: who fired a shot should be readable at a glance.
        The player's are cool cyan, patrols' green, everyone else's hot red."""
        owner = self.owner
        if hasattr(owner, "cargo_hold"):
            return (60, 170, 255), (220, 245, 255)
        if hasattr(owner, "faction"):          # patrols (bandits have no faction)
            return (70, 220, 120), (225, 255, 235)
        return (230, 60, 40), (255, 215, 190)

    def draw(self, screen: pygame.Surface, camera_offset: Vector2):
        """Draw the projectile."""
        screen_pos = self.position - camera_offset
        heading = self.velocity.normalize() if self.velocity.length() > 0 else Vector2(0, -1)
        outer, core = self._palette()
        pos = (int(screen_pos.x), int(screen_pos.y))

        if self.weapon_type == WeaponType.LASER:
            # A bolt with a fading tail and a glow
            gfx.draw_glow(screen, screen_pos, 13, outer, 0.8)
            for width, back, color in ((5, 14, gfx.darken(outer, 0.45)), (3, 12, outer), (1, 9, core)):
                pygame.draw.line(screen, color, screen_pos - heading * back, screen_pos, width)
        elif self.weapon_type == WeaponType.PLASMA:
            # A pulsing energy orb dragging a short tail
            pulse = gfx.flicker(self.age * 3.0, speed=1.2, low=0.7)
            for k in (3, 2, 1):
                trail = screen_pos - heading * (k * 6)
                pygame.draw.circle(screen, gfx.darken((90, 240, 130), 0.2 + 0.2 * k),
                                   (int(trail.x), int(trail.y)), max(1, 5 - k))
            gfx.draw_glow(screen, screen_pos, int(18 * pulse), (60, 220, 110), 0.9)
            pygame.draw.circle(screen, (60, 180, 90), pos, 5)
            pygame.draw.circle(screen, (200, 255, 215), pos, 3)
        elif self.weapon_type == WeaponType.MISSILE:
            # A small body with a real exhaust flame
            gfx.draw_glow(screen, screen_pos, 12, (255, 150, 40), 0.55)
            nose = screen_pos + heading * 6
            tail = screen_pos - heading * 5
            side = Vector2(-heading.y, heading.x) * 2.5
            pygame.draw.polygon(screen, (235, 235, 215), [nose, tail + side, tail - side])
            pygame.draw.polygon(screen, (150, 150, 140), [tail + side, tail - side, tail - heading * 2])
            angle = math.degrees(math.atan2(heading.y, heading.x)) + 90
            gfx.draw_engine_flame(screen, tail, angle, 6, (255, 120, 20), (255, 235, 160), power=1.2,
                                  seed=self.age * 5, offset=0.1)
        elif self.weapon_type == WeaponType.RAILGUN:
            # A hypervelocity tracer: a long thin streak with a bright head
            gfx.draw_glow(screen, screen_pos, 14, (90, 150, 255), 0.7)
            for width, back, color in ((4, 26, (50, 90, 180)), (2, 22, (110, 170, 255)), (1, 18, (235, 245, 255))):
                pygame.draw.line(screen, color, screen_pos - heading * back, screen_pos, width)
            pygame.draw.circle(screen, (240, 248, 255), pos, 2)

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
        
    def can_fire(self, current_time: float, ship=None) -> bool:
        """Check if weapon can fire."""
        time_since_last_shot = current_time - self.last_fire_time
        fire_interval = 1.0 / self.stats.fire_rate
        
        # Check basic firing conditions
        if not (time_since_last_shot >= fire_interval and self.energy >= self.stats.energy_cost):
            return False
        
        # Check ammo availability if ship is provided
        if ship and hasattr(ship, 'has_ammo'):
            return ship.has_ammo(self.stats.ammo_type, self.stats.ammo_per_shot)
        
        return True
    
    def fire(self, position: Vector2, direction: Vector2, owner, current_time: float) -> Optional[Projectile]:
        """Fire the weapon and return a projectile."""
        if not self.can_fire(current_time, owner):
            return None
            
        # Consume ammo if ship has ammo system
        if hasattr(owner, 'consume_ammo'):
            if not owner.consume_ammo(self.stats.ammo_type, self.stats.ammo_per_shot):
                return None  # Not enough ammo
        
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

        from ..audio.sound_manager import sound_manager
        fire_sounds = {
            WeaponType.LASER: "laser_fire",
            WeaponType.PLASMA: "plasma_fire",
            WeaponType.MISSILE: "missile_launch",
            WeaponType.RAILGUN: "railgun_fire",
        }
        sound_manager.play(fire_sounds.get(self.weapon_type, "laser_fire"))

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
        spread=2.0,
        ammo_type="laser_cells",
        ammo_per_shot=1
    ),
    "plasma_cannon": WeaponStats(
        damage=25.0,
        range=600.0,
        fire_rate=1.5,
        energy_cost=20.0,
        projectile_speed=800.0,
        spread=5.0,
        ammo_type="plasma_cartridges",
        ammo_per_shot=1
    ),
    "missile_launcher": WeaponStats(
        damage=50.0,
        range=1200.0,
        fire_rate=0.5,
        energy_cost=40.0,
        projectile_speed=600.0,
        spread=1.0,
        ammo_type="missiles",
        ammo_per_shot=1
    ),
    "railgun": WeaponStats(
        damage=75.0,
        range=1500.0,
        fire_rate=0.3,
        energy_cost=60.0,
        projectile_speed=2000.0,
        spread=0.5,
        ammo_type="railgun_slugs",
        ammo_per_shot=1
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