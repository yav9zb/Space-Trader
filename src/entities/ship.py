import pygame
from pygame import Vector2
import math

class Ship:
    def __init__(self, x, y):
        self.position = Vector2(x, y)
        self.velocity = Vector2(0, 0)

        # Physics constants
        self.THRUST_FORCE = 200
        self.DRAG_COEFFICIENT = 0.98
        self.MAX_SPEED = 400
        self.ROTATION_SPEED = 180 # degrees per second

        self.rotation = 0 # in degrees
        self.thrusting = False
        
        # Ship characteristics
        # Create a simple triangle shape for the ship
        self.size = 20
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
            
        # Thrust
        self.thrusting = keys[pygame.K_UP]
        if self.thrusting:
            # Convert rotation to radians for calculation
            angle_rad = math.radians(self.rotation)
            thrust_vector = Vector2(-math.sin(angle_rad), -math.cos(angle_rad))
            self.acceleration = thrust_vector * self.THRUST_FORCE
        else:
            self.acceleration = Vector2(0, 0)

        # Brake/reverse thrusters
        if keys[pygame.K_DOWN]:
            self.velocity *= 0.98

    def update(self, delta_time):
        # Apply acceleration
        self.velocity += self.acceleration * delta_time
        
        # Apply drag
        self.velocity *= self.DRAG_COEFFICIENT
        
        # Limit speed
        if self.velocity.length() > self.MAX_SPEED:
            self.velocity.scale_to_length(self.MAX_SPEED)
            
        # Update position
        self.position += self.velocity * delta_time
        
        # Screen wrapping
        screen_width, screen_height = 800, 600
        self.position.x = self.position.x % screen_width
        self.position.y = self.position.y % screen_height

    def draw(self, screen):
        # Transform points based on position and rotation
        transformed_points = []
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

    def check_collision(self, other_object):
        # Check for collision with another object
        distance = (self.position - other_object.position).length()
        return distance < (self.size + other_object.size)