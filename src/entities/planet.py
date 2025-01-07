import pygame
from pygame import Vector2
import random
from enum import Enum


class Planet:
    def __init__(self, x, y):
        self.position = Vector2(x, y)
        self.size = random.randint(50, 100)
        self.color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )
        self.name = f"Planet-{random.randint(1000, 9999)}"
        
    def draw(self, screen, camera_offset):
        screen_pos = self.position - camera_offset
        pygame.draw.circle(screen, self.color,
                         (int(screen_pos.x), int(screen_pos.y)),
                         self.size)