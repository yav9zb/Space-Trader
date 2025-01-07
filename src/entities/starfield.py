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
        
        self.screen_width = screen_width
        self.screen_height = screen_height
    
    def draw(self, screen, camera_offset):
        """Draw stars with parallax scrolling effect"""
        for x, y, brightness in self.stars:
            # Create parallax effect by moving stars slowly relative to camera
            parallax_x = (x - camera_offset.x * 0.1) % self.screen_width
            parallax_y = (y - camera_offset.y * 0.1) % self.screen_height
            
            pygame.draw.circle(screen, 
                               (brightness, brightness, brightness), 
                               (int(parallax_x), int(parallax_y)), 
                               1)
