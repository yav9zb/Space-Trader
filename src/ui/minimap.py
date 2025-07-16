import pygame
from pygame import Vector2

from src.entities.planet import Planet

class Minimap:
    def __init__(self, screen_width, screen_height, map_size=150):
        self.map_size = map_size
        self.padding = 10
        self.position = Vector2(screen_width - map_size - self.padding, 
                              self.padding)
        
        # Local view radius in world units
        self.view_radius = 2000
        
        # Scale factor for local view
        self.scale = map_size / (self.view_radius * 2)
        
        # Create surface for minimap
        self.surface = pygame.Surface((map_size, map_size))
        self.border_color = (100, 100, 100)
        self.background_color = (0, 0, 40)
        
        # Center point of the minimap
        self.center = Vector2(map_size // 2, map_size // 2)

    def world_to_local_map_coords(self, world_pos, ship_pos):
        """Convert world coordinates to local minimap coordinates"""
        # Calculate relative position from ship
        relative_pos = world_pos - ship_pos
        
        # Convert to minimap coordinates (centered on ship)
        map_x = self.center.x + (relative_pos.x * self.scale)
        map_y = self.center.y + (relative_pos.y * self.scale)
        
        return Vector2(map_x, map_y)

    def draw(self, screen, ship, stations, planets):
        # Fill background
        self.surface.fill(self.background_color)
        
        ship_pos = ship.position
        
        # Draw range circle to show view radius
        pygame.draw.circle(self.surface, (40, 40, 80), 
                         (int(self.center.x), int(self.center.y)), 
                         int(self.view_radius * self.scale), 1)
        
        # Draw planets within view radius
        for planet in planets:
            distance = (planet.position - ship_pos).length()
            if distance <= self.view_radius:
                map_pos = self.world_to_local_map_coords(planet.position, ship_pos)
                if self._is_in_minimap(map_pos):
                    # Size based on distance (closer = larger)
                    size = max(1, 4 - int(distance / (self.view_radius * 0.3)))
                    pygame.draw.circle(self.surface, (100, 100, 255),
                                    (int(map_pos.x), int(map_pos.y)), size)
        
        # Draw stations within view radius
        for station in stations:
            distance = (station.position - ship_pos).length()
            if distance <= self.view_radius:
                map_pos = self.world_to_local_map_coords(station.position, ship_pos)
                if self._is_in_minimap(map_pos):
                    # Size based on distance and station importance
                    base_size = 4
                    size = max(2, base_size - int(distance / (self.view_radius * 0.4)))
                    
                    # Color based on station type or distance
                    color = (150, 150, 150)
                    if distance < 200:  # Close station
                        color = (255, 255, 150)
                    
                    pygame.draw.circle(self.surface, color, 
                                     (int(map_pos.x), int(map_pos.y)), size)
                    
                    # Draw station name if close enough
                    if distance < 500 and hasattr(station, 'name'):
                        font = pygame.font.Font(None, 16)
                        name_text = font.render(station.name[:8], True, (200, 200, 200))
                        text_pos = (int(map_pos.x - name_text.get_width() // 2), 
                                  int(map_pos.y + size + 2))
                        self.surface.blit(name_text, text_pos)
        
        # Draw player ship at center
        ship_map_pos = self.center
        pygame.draw.circle(self.surface, (0, 255, 0),
                         (int(ship_map_pos.x), int(ship_map_pos.y)), 3)
        
        # Draw ship direction indicator
        ship_direction = Vector2(0, -12).rotate(ship.rotation)
        pygame.draw.line(self.surface, (0, 255, 0),
                        ship_map_pos,
                        ship_map_pos + ship_direction,
                        2)
        
        # Draw border
        pygame.draw.rect(self.surface, self.border_color,
                        (0, 0, self.map_size, self.map_size), 2)
        
        # Draw minimap title
        font = pygame.font.Font(None, 20)
        title_text = font.render("Local Map", True, (200, 200, 200))
        self.surface.blit(title_text, (5, 5))
        
        # Draw scale indicator
        scale_text = f"{self.view_radius}m radius"
        scale_surface = pygame.font.Font(None, 16).render(scale_text, True, (150, 150, 150))
        self.surface.blit(scale_surface, (5, self.map_size - 20))
        
        # Draw minimap on main screen
        screen.blit(self.surface, (self.position.x, self.position.y))

    def set_view_radius(self, radius):
        """Change the view radius of the minimap"""
        self.view_radius = max(500, min(5000, radius))  # Clamp between 500-5000
        self.scale = self.map_size / (self.view_radius * 2)
    
    def _is_in_minimap(self, pos):
        """Check if a position is within the minimap boundaries"""
        return (0 <= pos.x < self.map_size and 
                0 <= pos.y < self.map_size)