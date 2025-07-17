import math

import pygame
from pygame import Vector2

try:
    from ..trading.cargo import CargoHold
    from ..upgrades.ship_upgrades import ShipUpgrades, ShipStats
    from ..upgrades.upgrade_system import upgrade_system
    from ..combat.weapons import WeaponSystem, create_weapon
    from ..systems.cloaking_system import cloaking_system
except ImportError:
    from trading.cargo import CargoHold
    from upgrades.ship_upgrades import ShipUpgrades, ShipStats
    from upgrades.upgrade_system import upgrade_system
    from combat.weapons import WeaponSystem, create_weapon
    from systems.cloaking_system import cloaking_system


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
        
        # Afterburner system
        self.afterburner_active = False
        self.afterburner_cooldown = 0.0
        self.afterburner_max_cooldown = 3.0  # 3 seconds
        self.afterburner_speed_multiplier = 2.0
        self.afterburner_fuel_multiplier = 5.0
        
        # Emergency fuel system
        self.emergency_fuel_active = False
        self.emergency_fuel_speed_multiplier = 0.25  # 25% speed
        
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
        
        # Combat system
        self.weapon_system = WeaponSystem()
        # Start with basic laser
        basic_laser = create_weapon("basic_laser")
        self.weapon_system.add_weapon(basic_laser)
        
        # Fuel and ammo systems
        self.fuel_capacity = 100.0  # Maximum fuel capacity
        self.current_fuel = 100.0   # Current fuel level
        self.fuel_consumption_rate = 2.0  # Fuel per second when thrusting
        self.idle_fuel_consumption = 0.1  # Fuel per second when idle
        
        # Ammo storage for different weapon types
        self.ammo_storage = {
            "laser_cells": 50,        # Starting ammo for laser weapons
            "plasma_cartridges": 25,  # Starting ammo for plasma weapons
            "missiles": 10,           # Starting ammo for missiles
            "railgun_slugs": 30       # Starting ammo for railgun
        }
        
        # Maximum ammo capacity
        self.max_ammo_capacity = {
            "laser_cells": 200,
            "plasma_cartridges": 100,
            "missiles": 50,
            "railgun_slugs": 150
        }

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
        
        # Afterburner input handling
        afterburner_input = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        if afterburner_input and self.afterburner_cooldown <= 0 and self.current_fuel > 0:
            self.afterburner_active = True
        else:
            if self.afterburner_active:
                # Start cooldown when afterburner is deactivated
                self.afterburner_cooldown = self.afterburner_max_cooldown
            self.afterburner_active = False
        
        if self.thrusting and self.current_fuel > 0:
            # Use upgraded thrust force
            effective_stats = self.get_effective_stats()
            thrust_force = effective_stats.get_effective_thrust_force()
            
            # Apply afterburner boost to thrust if active
            if self.afterburner_active:
                thrust_force *= self.afterburner_speed_multiplier
            
            self.acceleration = self.heading * thrust_force
        else:
            self.acceleration = Vector2(0, 0)

        # Brake/reverse thrusters
        if keys[pygame.K_DOWN]:
            self.velocity *= 0.95
        
        # Weapon firing
        if keys[pygame.K_SPACE]:
            current_time = pygame.time.get_ticks() / 1000.0
            self.weapon_system.fire_weapons(self.position, self.heading, self, current_time)
            # Firing can break cloak
            cloaking_system.break_cloak_from_action(self.get_effective_stats(), "firing")

    def update(self, delta_time):
        # Apply acceleration in ships heading direction
        self.velocity += self.acceleration * delta_time
        
        # Apply drag
        self.velocity *= self.DRAG_COEFFICIENT
        
        # Limit speed using upgraded max speed
        effective_stats = self.get_effective_stats()
        max_speed = effective_stats.get_effective_max_speed()
        
        # Apply afterburner speed boost if active
        if self.afterburner_active:
            max_speed *= self.afterburner_speed_multiplier
        
        speed = self.velocity.length()
        if speed > max_speed:
            self.velocity = self.velocity.normalize() * max_speed
            
        # Update position
        self.position += self.velocity * delta_time
        
        # Update cargo hold capacity based on upgrades
        self._update_cargo_capacity()
        
        # Update weapon system
        self.weapon_system.update(delta_time)
        
        # Update cloaking system
        cloaking_system.update(delta_time, self.get_effective_stats())
        
        # Update afterburner cooldown
        if self.afterburner_cooldown > 0:
            self.afterburner_cooldown -= delta_time
            if self.afterburner_cooldown < 0:
                self.afterburner_cooldown = 0
        
        # Update fuel consumption
        self._update_fuel_consumption(delta_time)

    def draw(self, screen, camera_offset):
        # Check if ship should be drawn (cloaking)
        effective_stats = self.get_effective_stats()
        if not cloaking_system.should_draw_ship(effective_stats):
            return
            
        # Transform points based on position and rotation
        transformed_points = []
        screen_pos = self.position - camera_offset
        
        for point in self.points:
            rotated_point = point.rotate(self.rotation)
            transformed_point = (rotated_point + screen_pos)
            transformed_points.append(transformed_point)

        # Get cloaking alpha
        ship_alpha = cloaking_system.get_ship_alpha(effective_stats)
        
        # Draw the ship with appropriate alpha
        if ship_alpha < 255:
            # Create surface with alpha for cloaked ship
            ship_surface = pygame.Surface((self.size * 4, self.size * 4), pygame.SRCALPHA)
            ship_surface.set_alpha(ship_alpha)
            
            # Adjust points for surface coordinates
            surface_center = Vector2(self.size * 2, self.size * 2)
            surface_points = []
            for point in self.points:
                rotated_point = point.rotate(self.rotation)
                surface_point = (rotated_point + surface_center)
                surface_points.append(surface_point)
            
            pygame.draw.polygon(ship_surface, (255, 255, 255), surface_points)
            screen.blit(ship_surface, (screen_pos.x - self.size * 2, screen_pos.y - self.size * 2))
        else:
            # Normal drawing
            pygame.draw.polygon(screen, (255, 255, 255), transformed_points)
        
        # Draw thrust flame when accelerating
        if self.thrusting:
            # Enhanced flame for afterburner
            if self.afterburner_active:
                flame_points = [
                    Vector2(0, self.size/2),
                    Vector2(-self.size/2, self.size * 1.5),
                    Vector2(self.size/2, self.size * 1.5)
                ]
                flame_color = (0, 150, 255)  # Blue flame for afterburner
            else:
                flame_points = [
                    Vector2(0, self.size/2),
                    Vector2(-self.size/3, self.size),
                    Vector2(self.size/3, self.size)
                ]
                flame_color = (255, 165, 0)  # Normal orange flame
            
            flame_transformed = []
            for point in flame_points:
                rotated_point = point.rotate(self.rotation)
                transformed_point = (rotated_point + screen_pos)
                flame_transformed.append(transformed_point)
                
            pygame.draw.polygon(screen, flame_color, flame_transformed)

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
        
        # Draw weapon projectiles
        self.weapon_system.draw(screen, camera_offset)
        
        # Draw cloaking effects
        cloaking_system.draw_cloak_effects(screen, self.position, camera_offset)

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
        
        # Taking damage can break cloak
        cloaking_system.break_cloak_from_action(effective_stats, "taking_damage")
        
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
    
    def _update_fuel_consumption(self, delta_time: float):
        """Update fuel consumption based on ship activity."""
        if self.thrusting:
            # Base fuel consumption when thrusting
            fuel_consumed = self.fuel_consumption_rate * delta_time
            
            # Apply afterburner fuel multiplier if active
            if self.afterburner_active:
                fuel_consumed *= self.afterburner_fuel_multiplier
            
            self.current_fuel = max(0, self.current_fuel - fuel_consumed)
        else:
            # Consume idle fuel for life support and basic systems
            idle_consumed = self.idle_fuel_consumption * delta_time
            self.current_fuel = max(0, self.current_fuel - idle_consumed)
    
    def get_fuel_percentage(self) -> float:
        """Get fuel level as a percentage (0.0 to 1.0)."""
        if self.fuel_capacity <= 0:
            return 1.0
        return max(0.0, min(1.0, self.current_fuel / self.fuel_capacity))
    
    def refuel(self, amount: float) -> float:
        """Add fuel to the ship. Returns actual amount added."""
        max_add = self.fuel_capacity - self.current_fuel
        actual_add = min(amount, max_add)
        self.current_fuel += actual_add
        return actual_add
    
    def can_add_fuel(self, amount: float) -> bool:
        """Check if fuel can be added to the ship."""
        return self.current_fuel + amount <= self.fuel_capacity
    
    def get_ammo_count(self, ammo_type: str) -> int:
        """Get current ammo count for a specific type."""
        return self.ammo_storage.get(ammo_type, 0)
    
    def get_max_ammo_capacity(self, ammo_type: str) -> int:
        """Get maximum ammo capacity for a specific type."""
        return self.max_ammo_capacity.get(ammo_type, 0)
    
    def add_ammo(self, ammo_type: str, amount: int) -> int:
        """Add ammo to the ship. Returns actual amount added."""
        if ammo_type not in self.ammo_storage:
            return 0
        
        current = self.ammo_storage[ammo_type]
        max_capacity = self.max_ammo_capacity[ammo_type]
        max_add = max_capacity - current
        actual_add = min(amount, max_add)
        
        self.ammo_storage[ammo_type] += actual_add
        return actual_add
    
    def can_add_ammo(self, ammo_type: str, amount: int) -> bool:
        """Check if ammo can be added to the ship."""
        if ammo_type not in self.ammo_storage:
            return False
        
        current = self.ammo_storage[ammo_type]
        max_capacity = self.max_ammo_capacity[ammo_type]
        return current + amount <= max_capacity
    
    def consume_ammo(self, ammo_type: str, amount: int) -> bool:
        """Consume ammo if available. Returns True if successful."""
        if ammo_type not in self.ammo_storage:
            return False
        
        current = self.ammo_storage[ammo_type]
        if current >= amount:
            self.ammo_storage[ammo_type] -= amount
            return True
        return False
    
    def has_ammo(self, ammo_type: str, amount: int = 1) -> bool:
        """Check if ship has enough ammo of a specific type."""
        return self.ammo_storage.get(ammo_type, 0) >= amount
    
    def get_afterburner_status(self) -> dict:
        """Get afterburner system status."""
        return {
            "active": self.afterburner_active,
            "cooldown": self.afterburner_cooldown,
            "max_cooldown": self.afterburner_max_cooldown,
            "ready": self.afterburner_cooldown <= 0,
            "speed_multiplier": self.afterburner_speed_multiplier,
            "fuel_multiplier": self.afterburner_fuel_multiplier
        }
