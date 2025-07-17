"""Bandit ships and AI for combat encounters."""

import pygame
import math
import random
from pygame import Vector2
from typing import Optional, List
from enum import Enum

try:
    from ..combat.weapons import WeaponSystem, create_weapon
except ImportError:
    from combat.weapons import WeaponSystem, create_weapon


class BanditState(Enum):
    PATROLLING = "patrolling"
    HUNTING = "hunting"
    ATTACKING = "attacking"
    FLEEING = "fleeing"
    DISABLED = "disabled"


class BanditType(Enum):
    SCOUT = "scout"
    FIGHTER = "fighter"
    HEAVY = "heavy"
    BOSS = "boss"


class BanditShip:
    """AI-controlled bandit ship with combat capabilities."""
    
    def __init__(self, position: Vector2, bandit_type: BanditType = BanditType.SCOUT):
        self.position = Vector2(position)
        self.velocity = Vector2(0, 0)
        self.heading = Vector2(0, -1)
        self.rotation = 0
        self.bandit_type = bandit_type
        
        # Initialize stats based on type
        self._init_stats()
        
        # AI state
        self.state = BanditState.PATROLLING
        self.target = None
        self.detection_range = 800.0
        self.attack_range = 600.0
        self.flee_threshold = 0.3  # Flee when hull < 30%
        self.max_pursuit_distance = self._get_pursuit_distance()  # Max distance to chase player
        
        # AI behavior timers
        self.state_timer = 0.0
        self.decision_interval = 2.0  # Make decisions every 2 seconds
        self.last_target_position = Vector2(0, 0)
        
        # Patrol behavior
        self.patrol_center = Vector2(position)
        self.patrol_radius = 500.0
        self.patrol_target = self._get_random_patrol_point()
        
        # Combat behavior
        self.preferred_distance = 400.0  # Preferred combat distance
        self.circling_direction = random.choice([-1, 1])  # Clockwise or counter-clockwise
        
        # Weapon system
        self.weapon_system = WeaponSystem()
        self._setup_weapons()
        
        # Visual properties
        self.color = self._get_color()
        self.size = self.base_size
        self.shape_points = self._generate_shape()
    
    def _get_pursuit_distance(self) -> float:
        """Get maximum pursuit distance based on bandit type."""
        pursuit_map = {
            BanditType.SCOUT: 1500.0,    # Scouts give up pursuit quickly
            BanditType.FIGHTER: 2500.0,  # Fighters are persistent
            BanditType.HEAVY: 2000.0,    # Heavy ships are moderately persistent
            BanditType.BOSS: 3500.0      # Bosses pursue relentlessly
        }
        return pursuit_map.get(self.bandit_type, 2000.0)
        
    def _init_stats(self):
        """Initialize stats based on bandit type."""
        stats_map = {
            BanditType.SCOUT: {
                "max_hull": 50,
                "max_speed": 500,
                "thrust_force": 400,
                "base_size": 12,
                "credits_reward": 150
            },
            BanditType.FIGHTER: {
                "max_hull": 100,
                "max_speed": 400,
                "thrust_force": 350,
                "base_size": 15,
                "credits_reward": 300
            },
            BanditType.HEAVY: {
                "max_hull": 200,
                "max_speed": 250,
                "thrust_force": 300,
                "base_size": 20,
                "credits_reward": 500
            },
            BanditType.BOSS: {
                "max_hull": 400,
                "max_speed": 300,
                "thrust_force": 400,
                "base_size": 25,
                "credits_reward": 1000
            }
        }
        
        stats = stats_map[self.bandit_type]
        self.max_hull = stats["max_hull"]
        self.current_hull = self.max_hull
        self.max_speed = stats["max_speed"]
        self.thrust_force = stats["thrust_force"]
        self.base_size = stats["base_size"]
        self.credits_reward = stats["credits_reward"]
        self.mass = 1.0  # Default mass for physics calculations
        
        # Physics constants
        self.drag_coefficient = 0.98
        self.rotation_speed = 150  # degrees per second
    
    def _get_color(self) -> tuple:
        """Get bandit ship color based on type."""
        color_map = {
            BanditType.SCOUT: (255, 150, 150),
            BanditType.FIGHTER: (255, 100, 100),
            BanditType.HEAVY: (200, 50, 50),
            BanditType.BOSS: (150, 0, 0)
        }
        return color_map.get(self.bandit_type, (255, 100, 100))
    
    def _generate_shape(self) -> List[Vector2]:
        """Generate bandit ship shape (more angular/aggressive than player ship)."""
        if self.bandit_type == BanditType.BOSS:
            # Larger, more complex shape for boss
            return [
                Vector2(0, -self.base_size),
                Vector2(-self.base_size * 0.8, -self.base_size * 0.3),
                Vector2(-self.base_size * 0.6, self.base_size * 0.8),
                Vector2(-self.base_size * 0.3, self.base_size * 0.6),
                Vector2(0, self.base_size * 0.4),
                Vector2(self.base_size * 0.3, self.base_size * 0.6),
                Vector2(self.base_size * 0.6, self.base_size * 0.8),
                Vector2(self.base_size * 0.8, -self.base_size * 0.3)
            ]
        else:
            # Standard aggressive triangular shape
            return [
                Vector2(0, -self.base_size),
                Vector2(-self.base_size * 0.7, self.base_size * 0.7),
                Vector2(0, self.base_size * 0.3),
                Vector2(self.base_size * 0.7, self.base_size * 0.7)
            ]
    
    def _setup_weapons(self):
        """Setup weapons based on bandit type."""
        weapon_configs = {
            BanditType.SCOUT: ["basic_laser"],
            BanditType.FIGHTER: ["basic_laser", "plasma_cannon"],
            BanditType.HEAVY: ["plasma_cannon", "missile_launcher"],
            BanditType.BOSS: ["basic_laser", "plasma_cannon", "missile_launcher"]
        }
        
        for weapon_config in weapon_configs[self.bandit_type]:
            weapon = create_weapon(weapon_config)
            self.weapon_system.add_weapon(weapon)
    
    def _get_random_patrol_point(self) -> Vector2:
        """Get a random point within patrol radius."""
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0, self.patrol_radius)
        return self.patrol_center + Vector2(
            distance * math.cos(angle),
            distance * math.sin(angle)
        )
    
    def update(self, delta_time: float, player_ship, game_engine):
        """Update bandit AI and behavior."""
        self.state_timer += delta_time
        
        # Update weapon system
        self.weapon_system.update(delta_time)
        
        # AI decision making
        if self.state_timer >= self.decision_interval:
            self._make_decision(player_ship)
            self.state_timer = 0.0
        
        # Execute current behavior
        self._execute_behavior(delta_time, player_ship)
        
        # Update physics
        self._update_physics(delta_time)
        
        # Check for state transitions
        self._check_state_transitions(player_ship)
    
    def _make_decision(self, player_ship):
        """Make AI decisions based on current situation."""
        distance_to_player = (player_ship.position - self.position).length()
        hull_percentage = self.current_hull / self.max_hull
        
        # Check if we should flee
        if hull_percentage <= self.flee_threshold and self.state != BanditState.FLEEING:
            self.state = BanditState.FLEEING
            return
        
        # Check distance from patrol center to prevent infinite pursuit
        distance_from_patrol = (self.position - self.patrol_center).length()
        
        # Check detection range
        if distance_to_player <= self.detection_range and distance_from_patrol <= self.max_pursuit_distance:
            if distance_to_player <= self.attack_range:
                self.state = BanditState.ATTACKING
                self.target = player_ship
            else:
                self.state = BanditState.HUNTING
                self.target = player_ship
        else:
            # Return to patrol if player is too far or we've pursued too far from home
            if self.state in [BanditState.HUNTING, BanditState.ATTACKING]:
                self.state = BanditState.PATROLLING
                self.target = None
    
    def _execute_behavior(self, delta_time: float, player_ship):
        """Execute behavior based on current state."""
        if self.state == BanditState.PATROLLING:
            self._patrol_behavior(delta_time)
        elif self.state == BanditState.HUNTING:
            self._hunt_behavior(delta_time, player_ship)
        elif self.state == BanditState.ATTACKING:
            self._attack_behavior(delta_time, player_ship)
        elif self.state == BanditState.FLEEING:
            self._flee_behavior(delta_time, player_ship)
    
    def _patrol_behavior(self, delta_time: float):
        """Patrol around assigned area."""
        distance_to_patrol_target = (self.patrol_target - self.position).length()
        
        if distance_to_patrol_target < 50:
            # Reached patrol point, get new one
            self.patrol_target = self._get_random_patrol_point()
        
        # Move toward patrol target
        self._move_toward_target(self.patrol_target, delta_time)
    
    def _hunt_behavior(self, delta_time: float, player_ship):
        """Hunt the player ship."""
        # Move toward player
        self._move_toward_target(player_ship.position, delta_time)
    
    def _attack_behavior(self, delta_time: float, player_ship):
        """Attack the player ship."""
        distance_to_player = (player_ship.position - self.position).length()
        
        # Maintain preferred combat distance
        if distance_to_player > self.preferred_distance + 50:
            # Too far, move closer
            self._move_toward_target(player_ship.position, delta_time)
        elif distance_to_player < self.preferred_distance - 50:
            # Too close, move away
            direction_away = (self.position - player_ship.position).normalize()
            target_position = self.position + direction_away * 100
            self._move_toward_target(target_position, delta_time)
        else:
            # Good distance, circle around player
            self._circle_target(player_ship.position, delta_time)
        
        # Fire weapons if facing player
        if self._is_facing_target(player_ship.position):
            current_time = pygame.time.get_ticks() / 1000.0
            self.weapon_system.fire_weapons(
                self.position, 
                self.heading, 
                self, 
                current_time
            )
    
    def _flee_behavior(self, delta_time: float, player_ship):
        """Flee from the player ship."""
        # Move away from player
        direction_away = (self.position - player_ship.position).normalize()
        target_position = self.position + direction_away * 1000
        self._move_toward_target(target_position, delta_time)
    
    def _move_toward_target(self, target_position: Vector2, delta_time: float):
        """Move toward a target position."""
        direction_to_target = (target_position - self.position).normalize()
        
        # Turn toward target
        self._turn_toward_direction(direction_to_target, delta_time)
        
        # Thrust if facing roughly the right direction
        if self._is_facing_direction(direction_to_target, tolerance=30):
            self.velocity += self.heading * self.thrust_force * delta_time
    
    def _circle_target(self, target_position: Vector2, delta_time: float):
        """Circle around a target position."""
        to_target = target_position - self.position
        perpendicular = Vector2(-to_target.y, to_target.x).normalize() * self.circling_direction
        
        # Move in a circular pattern
        circle_target = self.position + perpendicular * 50
        self._move_toward_target(circle_target, delta_time)
    
    def _turn_toward_direction(self, direction: Vector2, delta_time: float):
        """Turn toward a specific direction."""
        target_angle = math.degrees(math.atan2(direction.y, direction.x)) + 90
        angle_diff = target_angle - self.rotation
        
        # Normalize angle difference to [-180, 180]
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360
        
        # Turn toward target
        if abs(angle_diff) > 5:
            turn_direction = 1 if angle_diff > 0 else -1
            self.rotation += turn_direction * self.rotation_speed * delta_time
        
        # Update heading vector
        angle_rad = math.radians(self.rotation - 90)
        self.heading = Vector2(math.cos(angle_rad), math.sin(angle_rad))
    
    def _is_facing_target(self, target_position: Vector2, tolerance: float = 15) -> bool:
        """Check if bandit is facing the target."""
        direction_to_target = (target_position - self.position).normalize()
        return self._is_facing_direction(direction_to_target, tolerance)
    
    def _is_facing_direction(self, direction: Vector2, tolerance: float = 15) -> bool:
        """Check if bandit is facing a specific direction."""
        angle_to_direction = math.degrees(math.atan2(direction.y, direction.x)) + 90
        angle_diff = abs(angle_to_direction - self.rotation)
        
        # Normalize angle difference
        while angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        return angle_diff <= tolerance
    
    def _update_physics(self, delta_time: float):
        """Update bandit physics."""
        # Apply drag
        self.velocity *= self.drag_coefficient
        
        # Limit speed
        speed = self.velocity.length()
        if speed > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed
        
        # Update position
        self.position += self.velocity * delta_time
    
    def _check_state_transitions(self, player_ship):
        """Check for automatic state transitions."""
        # Transition from fleeing back to patrol if far enough away
        if self.state == BanditState.FLEEING:
            distance_to_player = (player_ship.position - self.position).length()
            if distance_to_player > self.detection_range * 2:
                self.state = BanditState.PATROLLING
    
    def take_damage(self, damage: float) -> bool:
        """Apply damage to bandit ship."""
        self.current_hull -= damage
        
        if self.current_hull <= 0:
            self.state = BanditState.DISABLED
            return True  # Bandit destroyed
        
        return False
    
    def draw(self, screen: pygame.Surface, camera_offset: Vector2):
        """Draw the bandit ship."""
        screen_pos = self.position - camera_offset
        
        # Transform shape points
        transformed_points = []
        for point in self.shape_points:
            rotated_point = point.rotate(self.rotation)
            screen_point = screen_pos + rotated_point
            transformed_points.append((screen_point.x, screen_point.y))
        
        # Draw ship based on state
        if self.state == BanditState.DISABLED:
            # Draw as wreckage
            color = (100, 50, 50)
        else:
            color = self.color
        
        pygame.draw.polygon(screen, color, transformed_points)
        pygame.draw.polygon(screen, (200, 200, 200), transformed_points, 2)
        
        # Draw hull bar above ship
        if self.current_hull < self.max_hull and self.state != BanditState.DISABLED:
            bar_width = 30
            bar_height = 4
            bar_x = screen_pos.x - bar_width // 2
            bar_y = screen_pos.y - self.base_size - 10
            
            # Background
            pygame.draw.rect(screen, (100, 100, 100), 
                           (bar_x, bar_y, bar_width, bar_height))
            
            # Health bar
            hull_percentage = self.current_hull / self.max_hull
            fill_width = int(bar_width * hull_percentage)
            health_color = (255, 0, 0) if hull_percentage < 0.3 else (255, 255, 0) if hull_percentage < 0.7 else (0, 255, 0)
            
            if fill_width > 0:
                pygame.draw.rect(screen, health_color,
                               (bar_x, bar_y, fill_width, bar_height))
        
        # Draw weapon projectiles
        self.weapon_system.draw(screen, camera_offset)
    
    def get_info(self) -> dict:
        """Get bandit information."""
        return {
            "type": self.bandit_type.value,
            "state": self.state.value,
            "hull": f"{self.current_hull:.0f}/{self.max_hull}",
            "position": (self.position.x, self.position.y),
            "credits_reward": self.credits_reward,
            "weapons": self.weapon_system.get_weapon_info()
        }


def create_bandit_encounter(center: Vector2, encounter_type: str = "random") -> List[BanditShip]:
    """Create a bandit encounter with multiple ships."""
    bandits = []
    
    if encounter_type == "scout_patrol":
        # 2-3 scout ships
        for i in range(random.randint(2, 3)):
            angle = (2 * math.pi * i) / 3
            offset = Vector2(100 * math.cos(angle), 100 * math.sin(angle))
            bandit = BanditShip(center + offset, BanditType.SCOUT)
            bandits.append(bandit)
    
    elif encounter_type == "fighter_squad":
        # 1-2 fighters with 1-2 scouts
        for i in range(random.randint(1, 2)):
            offset = Vector2(random.uniform(-150, 150), random.uniform(-150, 150))
            bandit = BanditShip(center + offset, BanditType.FIGHTER)
            bandits.append(bandit)
        
        for i in range(random.randint(1, 2)):
            offset = Vector2(random.uniform(-200, 200), random.uniform(-200, 200))
            bandit = BanditShip(center + offset, BanditType.SCOUT)
            bandits.append(bandit)
    
    elif encounter_type == "heavy_escort":
        # 1 heavy with escorts
        heavy = BanditShip(center, BanditType.HEAVY)
        bandits.append(heavy)
        
        for i in range(2):
            angle = math.pi * i
            offset = Vector2(150 * math.cos(angle), 150 * math.sin(angle))
            escort = BanditShip(center + offset, BanditType.FIGHTER)
            bandits.append(escort)
    
    elif encounter_type == "boss_fleet":
        # Boss with full escort
        boss = BanditShip(center, BanditType.BOSS)
        bandits.append(boss)
        
        # Heavy escorts
        for i in range(2):
            angle = (math.pi * 2 * i) / 2
            offset = Vector2(200 * math.cos(angle), 200 * math.sin(angle))
            heavy = BanditShip(center + offset, BanditType.HEAVY)
            bandits.append(heavy)
        
        # Fighter escorts
        for i in range(4):
            angle = (math.pi * 2 * i) / 4
            offset = Vector2(300 * math.cos(angle), 300 * math.sin(angle))
            fighter = BanditShip(center + offset, BanditType.FIGHTER)
            bandits.append(fighter)
    
    else:  # random encounter
        encounter_types = ["scout_patrol", "fighter_squad", "heavy_escort"]
        weights = [0.5, 0.3, 0.2]  # More common encounters are more likely
        chosen_type = random.choices(encounter_types, weights=weights)[0]
        return create_bandit_encounter(center, chosen_type)
    
    return bandits