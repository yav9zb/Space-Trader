import pygame
from pygame import Vector2

class Minimap:
    def __init__(self, screen_width, screen_height, map_size=150):
        self.map_size = map_size
        self.padding = 10
        self.position = Vector2(screen_width - map_size - self.padding, 
                              self.padding)
        
        # Scale factor between game world and minimap
        self.scale = map_size / max(screen_width, screen_height)
        
        # Create surface for minimap
        self.surface = pygame.Surface((map_size, map_size))
        self.border_color = (100, 100, 100)
        self.background_color = (0, 0, 40)

    def world_to_map_coords(self, world_pos):
        """Convert world coordinates to minimap coordinates"""
        return Vector2(
            world_pos.x * self.scale,
            world_pos.y * self.scale
        )

    def draw(self, screen, ship, stations):
        # Fill background
        self.surface.fill(self.background_color)
        
        # Draw stations
        for station in stations:
            map_pos = self.world_to_map_coords(station.position)
            pygame.draw.circle(self.surface, (150, 150, 150), 
                             (int(map_pos.x), int(map_pos.y)), 3)
        
        # Draw player ship
        map_pos = self.world_to_map_coords(ship.position)
        # Draw direction indicator
        ship_direction = Vector2(0, -8).rotate(ship.rotation)
        pygame.draw.line(self.surface, (0, 255, 0),
                        map_pos,
                        map_pos + ship_direction,
                        2)
        pygame.draw.circle(self.surface, (0, 255, 0), 
                         (int(map_pos.x), int(map_pos.y)), 2)
        
        # Draw border
        pygame.draw.rect(self.surface, self.border_color, 
                        (0, 0, self.map_size, self.map_size), 1)
        
        # Draw minimap on main screen
        screen.blit(self.surface, (self.position.x, self.position.y))