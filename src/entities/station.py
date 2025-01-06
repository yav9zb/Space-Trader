import pygame

class Station:
    def __init__(self, x, y):
        self.position = pygame.Vector2(x, y)
        self.size = 40
        self.color = (150, 150, 150)
        
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, 
                         (int(self.position.x), int(self.position.y)), 
                         self.size)