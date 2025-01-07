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
        
        # Screen wrapping
        screen_width, screen_height = 800, 600
        self.position.x = self.position.x % screen_width
        self.position.y = self.position.y % screen_height

    def draw(self, screen, camera_offset):
        # Transform points based on position and rotation
        transformed_points = []
        screen_pos = self.position - camera_offset
        
        for point in self.points:
            rotated_point = point.rotate(self.rotation)
            transformed_point = (rotated_point + self.position)
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
                transformed_point = (rotated_point + self.position)
                flame_transformed.append(transformed_point)
                
            pygame.draw.polygon(screen, (255, 165, 0), flame_transformed)

        # Draw direction indicator (debug)
        direction_end = self.position + self.heading * 30
        pygame.draw.line(screen, (0, 255, 0), 
                         self.position, 
                         direction_end, 
                         2)
        
        # Debug: Draw collision circle
        if hasattr(self, 'in_collision'):
            color = (255, 0, 0) if self.in_collision else (0, 255, 0)
            pygame.draw.circle(screen, color, 
                             (int(self.position.x), int(self.position.y)), 
                             int(self.size), 
                             1)  # Draw ship's collision radius

    def check_collision_detailed(self, other_object):
        """Enhanced collision detection with visual debugging"""
        # Calculate distance between objects
        distance_vec = other_object.position - self.position
        distance = distance_vec.length()

        # Define collision radius
        collision_radius = self.size + other_object.size
        
        # Check for collision
        if distance < collision_radius:
            # Calculate collision normal
            collision_normal = distance_vec.normalize()
        
            # Calculate relative velocity
            approach_speed = self.velocity.dot(collision_normal)
        
            # Bounce with energy loss
            self.velocity = self.velocity.reflect(collision_normal) * 0.5
        
            # Push ship out of collision
            overlap = collision_radius - distance
            self.position -= collision_normal * overlap
        
            # Add some logging to debug
            print(f"Collision detected! Distance: {distance}, Radius: {collision_radius}")
            print(f"Ship position: {self.position}, Station position: {other_object.position}")
            print(f"New velocity: {self.velocity}")
        
            return True
        return False