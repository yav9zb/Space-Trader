import math

import pygame
from pygame import Vector2

try:
    from ..trading.cargo import CargoHold
    from ..upgrades.ship_upgrades import ShipUpgrades, ShipStats
    from ..upgrades.upgrade_system import upgrade_system
except ImportError:
    from trading.cargo import CargoHold
    from upgrades.ship_upgrades import ShipUpgrades, ShipStats
    from upgrades.upgrade_system import upgrade_system


class Ship:
    def __init__(self, x, y):
        self.position = Vector2(x, y)
        self.velocity = Vector2(0, 0)
        self.acceleration = Vector2(0, 0)
        self.heading = Vector2(0, -1)  # Points upward initially

        # Physics constants
        self.THRUST_FORCE = 300
        self.DRAG_COEFFICIENT = 0.99
        self.MAX_SPEED = 400
        self.ROTATION_SPEED = 180 # degrees per second
        self.COLLISION_BUFFER = 5  # Additional buffer for collision detection

        self.rotation_speed = 0  # Current rotation speed
        self.rotation = 0 # in degrees
        self.thrusting = False
        
        # Ship characteristics
        # Create a simple triangle shape for the ship
        self.size = 15 # slightly smaller collision radius
        self.mass = 1.0 # kg
        self.points = [Vector2(0, -self.size), 
                      Vector2(-self.size/2, self.size/2),
                      Vector2(self.size/2, self.size/2)]
        
        # Trading system
        self.cargo_hold = CargoHold(capacity=20)  # Starting ship has 20 cargo units
        self.credits = 1000  # Starting credits
        
        # Upgrade system
        self.upgrades = ShipUpgrades()
        self.base_stats = ShipStats(
            cargo_capacity=20,
            max_speed=400.0,
            thrust_force=300.0,
            hull_points=100,
            scanner_range=150.0
        )
        self.current_hull = 100  # Current hull damage state

    def handle_input(self, delta_time):
        keys = pygame.key.get_pressed()
        
        # Rotation
        if keys[pygame.K_LEFT]:
            self.rotation -= self.ROTATION_SPEED * delta_time
        if keys[pygame.K_RIGHT]:
            self.rotation += self.ROTATION_SPEED * delta_time
        
        # Update heading vector after any rotation
        angle_rad = math.radians(self.rotation - 90)
        self.heading = Vector2(math.cos(angle_rad), math.sin(angle_rad))
            
        # Thrust in ship's heading direction
        self.thrusting = keys[pygame.K_UP]
        if self.thrusting:
            # Use upgraded thrust force
            effective_stats = self.get_effective_stats()
            self.acceleration = self.heading * effective_stats.get_effective_thrust_force()
        else:
            self.acceleration = Vector2(0, 0)

        # Brake/reverse thrusters
        if keys[pygame.K_DOWN]:
            self.velocity *= 0.95

    def update(self, delta_time):
        # Apply acceleration in ships heading direction
        self.velocity += self.acceleration * delta_time
        
        # Apply drag
        self.velocity *= self.DRAG_COEFFICIENT
        
        # Limit speed using upgraded max speed
        effective_stats = self.get_effective_stats()
        max_speed = effective_stats.get_effective_max_speed()
        speed = self.velocity.length()
        if speed > max_speed:
            self.velocity = self.velocity.normalize() * max_speed
            
        # Update position
        self.position += self.velocity * delta_time
        
        # Update cargo hold capacity based on upgrades
        self._update_cargo_capacity()

    def draw(self, screen, camera_offset):
        # Transform points based on position and rotation
        transformed_points = []
        screen_pos = self.position - camera_offset
        
        for point in self.points:
            rotated_point = point.rotate(self.rotation)
            transformed_point = (rotated_point + screen_pos)
            transformed_points.append(transformed_point)

        # Draw the ship
        pygame.draw.polygon(screen, (255, 255, 255), transformed_points)
        
        # Draw thrust flame when accelerating
        if self.thrusting:
            flame_points = [
                Vector2(0, self.size/2),
                Vector2(-self.size/3, self.size),
                Vector2(self.size/3, self.size)
            ]
            
            flame_transformed = []
            for point in flame_points:
                rotated_point = point.rotate(self.rotation)
                transformed_point = (rotated_point + screen_pos)
                flame_transformed.append(transformed_point)
                
            pygame.draw.polygon(screen, (255, 165, 0), flame_transformed)

        # Draw direction indicator (debug)
        direction_end = screen_pos + self.heading * 30
        pygame.draw.line(screen, (0, 255, 0), 
                         screen_pos, 
                         direction_end, 
                         2)
        
        # Debug: Draw collision circle
        if hasattr(self, 'in_collision'):
            color = (255, 0, 0) if self.in_collision else (0, 255, 0)
            pygame.draw.circle(screen, color, 
                             (int(screen_pos.x), int(screen_pos.y)), 
                             int(self.size), 
                             1)  # Draw ship's collision radius

    def check_collision_detailed(self, other_object):
        """Enhanced collision detection with visual debugging"""
        # Calculate distance between objects
        distance_vec = other_object.position - self.position
        distance = distance_vec.length()

        # Define collision radius
        collision_radius = self.size + other_object.size + self.COLLISION_BUFFER
        
        # Check for collision
        if distance < collision_radius:
            # Added minimum separation to prevent oscillation
            MIN_SEPARATION = 2.0

            if hasattr(self, 'last_collision_time'):
                if pygame.time.get_ticks() - self.last_collision_time < 100:  # 100ms cooldown
                    return False

            self.last_collision_time = pygame.time.get_ticks()

            # Calculate normalized collision normal
            if distance_vec.length() > 0:
                collision_normal = distance_vec.normalize()
            else:
                # Objects are at same position - use default separation direction
                collision_normal = Vector2(1, 0)

            # Calculate penetration depth
            penetration = collision_radius - distance
        

            # Move ship out of collision 
            self.position -= collision_normal * penetration

            # Push objects apart with minimum separation
            separation = (collision_radius - distance + MIN_SEPARATION) 
            self.position -= collision_normal * separation

            # Handle velocity reflection
            if self.velocity.length() > 0:
                # Calculate reflection but maintain some forward momentum
                reflection = self.velocity.reflect(collision_normal)
                self.velocity = reflection * 0.25  # Dampen the reflection
            else:
                # If velocity is zero, give ship a small bounce in collision normal direction
                self.velocity = collision_normal * 50
            
            # Stop rotation on collision
            self.rotation_speed = 0
        
            # Add some logging to debug
            print(f"Collision detected! Distance: {distance}, Radius: {collision_radius}")
            print(f"Ship position: {self.position}, Station position: {other_object.position}")
            print(f"New velocity: {self.velocity}")
        
            return True
        return False

    def check_docking(self, station):
        """Check if ship can dock with station, return tuple of (can_dock, distance)"""
        # Calculate distance to station
        distance = (station.position - self.position).length()
    
        # Check if in docking range and moving slowly enough
        can_dock = (distance < station.size + self.size + 20 and 
                    self.velocity.length() < 50)
    
        return can_dock, distance
    
    def get_effective_stats(self) -> ShipStats:
        """Get the effective stats with all upgrades applied."""
        return self.upgrades.get_effective_stats(self.base_stats)
    
    def _update_cargo_capacity(self):
        """Update cargo hold capacity based on upgrades."""
        effective_stats = self.get_effective_stats()
        new_capacity = effective_stats.get_effective_cargo_capacity()
        
        # Only update if capacity changed
        if self.cargo_hold.capacity != new_capacity:
            self.cargo_hold.capacity = new_capacity
    
    def install_upgrade(self, upgrade_id: str) -> bool:
        """Install an upgrade on this ship."""
        result, remaining_credits = upgrade_system.purchase_upgrade(
            self.upgrades, upgrade_id, self.credits
        )
        
        if result.success:
            self.credits = remaining_credits
            # Update cargo capacity immediately
            self._update_cargo_capacity()
            return True
        return False
    
    def get_upgrade_cost(self, upgrade_id: str, station_type: str = "shipyard") -> int:
        """Get the cost of an upgrade at a specific station type."""
        try:
            from ..upgrades.upgrade_definitions import upgrade_registry
        except ImportError:
            from upgrades.upgrade_definitions import upgrade_registry
            
        try:
            upgrade = upgrade_registry.get_upgrade(upgrade_id)
            return upgrade_system.get_discounted_price(upgrade, station_type)
        except KeyError:
            return 0
    
    def can_afford_upgrade(self, upgrade_id: str, station_type: str = "shipyard") -> bool:
        """Check if the ship can afford an upgrade."""
        cost = self.get_upgrade_cost(upgrade_id, station_type)
        return self.credits >= cost
    
    def get_ship_info(self) -> dict:
        """Get comprehensive ship information including upgrades."""
        effective_stats = self.get_effective_stats()
        
        return {
            "credits": self.credits,
            "cargo_used": self.cargo_hold.get_used_capacity(),
            "cargo_capacity": effective_stats.get_effective_cargo_capacity(),
            "max_speed": effective_stats.get_effective_max_speed(),
            "thrust_force": effective_stats.get_effective_thrust_force(),
            "hull_current": self.current_hull,
            "hull_max": effective_stats.get_effective_hull_points(),
            "scanner_range": effective_stats.get_effective_scanner_range(),
            "total_upgrade_value": self.upgrades.get_total_upgrade_value(),
            "upgrade_summary": self.upgrades.get_upgrade_summary()
        }
    
    def take_damage(self, damage: float):
        """Apply damage to the ship, considering hull upgrades."""
        effective_stats = self.get_effective_stats()
        damage_multiplier = effective_stats.get_collision_damage_multiplier()
        actual_damage = damage * damage_multiplier
        
        self.current_hull = max(0, self.current_hull - actual_damage)
        
        # Check if ship is destroyed
        if self.current_hull <= 0:
            return True  # Ship destroyed
        return False  # Ship survived
    
    def repair_ship(self, repair_amount: float = None):
        """Repair the ship to full hull points."""
        effective_stats = self.get_effective_stats()
        max_hull = effective_stats.get_effective_hull_points()
        
        if repair_amount is None:
            self.current_hull = max_hull
        else:
            self.current_hull = min(max_hull, self.current_hull + repair_amount)
    
    def get_hull_percentage(self) -> float:
        """Get hull integrity as a percentage (0.0 to 1.0)."""
        effective_stats = self.get_effective_stats()
        max_hull = effective_stats.get_effective_hull_points()
        
        if max_hull <= 0:
            return 1.0
        return max(0.0, min(1.0, self.current_hull / max_hull))
