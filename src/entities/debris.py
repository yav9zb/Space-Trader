import pygame
from pygame import Vector2
import random
import math

class Debris:
    def __init__(self, x, y):
        self.position = Vector2(x, y)
        self.velocity = Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        self.size = random.randint(1, 3)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-2, 2)
        self.color = (100, 100, 100)

    def update(self, delta_time):
        self.position += self.velocity * delta_time
        self.rotation += self.rotation_speed * delta_time

    def draw(self, screen, camera_offset):
        screen_pos = self.position - camera_offset
        points = []
        for i in range(random.randint(3, 5)):
            angle = math.radians(self.rotation + (i * 360 / 3))
            point = Vector2(
                screen_pos.x + math.cos(angle) * self.size,
                screen_pos.y + math.sin(angle) * self.size
            )
            points.append(point)
        pygame.draw.polygon(screen, self.color, points)