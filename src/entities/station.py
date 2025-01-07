import pygame

class Station:
    def __init__(self, x, y):
        self.position = pygame.Vector2(x, y)
        self.size = 30 # slighly smaller collision radius
        self.color = (150, 150, 150)
        self.collision_radius = self.size  # Explicit collision radius

        
    def draw(self, screen, camera_offset):
        # Calculate screen position by subtracting camera offset
        screen_pos = self.position - camera_offset
        
        # Draw the station
        pygame.draw.circle(screen, self.color, 
                         (int(self.position.x), int(self.position.y)), 
                         self.size)
        
        # Draw docking zone (slightly larger than staton)
        pygame.draw.circle(screen, (100, 100, 100), 
                           (int(self.position.x), int(self.position.y)), 
                           self.size + 10,
                           1)
        
        # Draw collision boundary
        pygame.draw.circle(screen, (255, 0, 0), 
                     (int(self.position.x), int(self.position.y)), 
                     self.size, 
                     1)  # Draw collision radius