import pygame
from pygame import Vector2

class Ship:
    def __init__(self, x, y):
        self.position = Vector2(x, y)
        self.velocity = Vector2(0, 0)
        self.acceleration = 0.5
        self.max_speed = 5
        self.rotation = 0
        
        # Create a simple triangle shape for the ship
        self.size = 20
        self.points = [Vector2(0, -self.size), 
                      Vector2(-self.size/2, self.size/2),
                      Vector2(self.size/2, self.size/2)]

    def update(self):
        # Update position based on velocity
        self.position += self.velocity

        # Screen wrapping
        screen_width, screen_height = 800, 600
        self.position.x = self.position.x % screen_width
        self.position.y = self.position.y % screen_height

    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        # Rotation
        if keys[pygame.K_LEFT]:
            self.rotation -= 5
        if keys[pygame.K_RIGHT]:
            self.rotation += 5

        # Thrust
        if keys[pygame.K_UP]:
            # Convert rotation to radians and calculate thrust vector
            thrust = Vector2(0, -self.acceleration).rotate(-self.rotation)
            self.velocity += thrust

        # Limit speed
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)

    def draw(self, screen):
        # Transform points based on position and rotation
        transformed_points = []
        for point in self.points:
            rotated_point = point.rotate(self.rotation)
            transformed_point = (rotated_point + self.position)
            transformed_points.append(transformed_point)

        # Draw the ship
        pygame.draw.polygon(screen, (255, 255, 255), transformed_points)

    def check_collision(self, other_object):
        # Check for collision with another object
        distance = (self.position - other_object.position).length()
        return distance < (self.size + other_object.size)