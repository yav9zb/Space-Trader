import random
import pygame

class StarField:
    def __init__(self, num_stars, screen_width, screen_height):
        self.stars = []
        for _ in range(num_stars):
            x = random.randint(0, screen_width)
            y = random.randint(0, screen_height)
            brightness = random.randint(100, 255)
            self.stars.append([x, y, brightness])
    
    def draw(self, screen):
        for x, y, brightness in self.stars:
            pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), 1)
