import math

import pygame
from pygame import Vector2


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
        self.size = 15 # slighly smaller collision radius
        self.mass = 1.0 # kg
        self.points = [Vector2(0, -self.size), 
                      Vector2(-self.size/2, self.size/2),
                      Vector2(self.size/2, self.size/2)]

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
            self.acceleration = self.heading * self.THRUST_FORCE
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
        
        # Limit speed
        speed = self.velocity.length()
        if speed > self.MAX_SPEED:
            self.velocity = self.velocity.normalize() * self.MAX_SPEED
            
        # Update position
        self.position += self.velocity * delta_time

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
