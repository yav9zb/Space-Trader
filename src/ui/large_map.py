import pygame
from pygame import Vector2
import math

class LargeMap:
    """Full-screen map overlay showing the entire universe."""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False
        
        # Map area (leave margin for UI)
        self.margin = 50
        self.map_width = screen_width - (self.margin * 2)
        self.map_height = screen_height - (self.margin * 2)
        
        # Universe size (adjust based on your universe)
        self.universe_width = 10000
        self.universe_height = 10000
        
        # Calculate scale to fit universe in map area
        scale_x = self.map_width / self.universe_width
        scale_y = self.map_height / self.universe_height
        self.scale = min(scale_x, scale_y) * 0.9  # 90% to leave some padding
        
        # Map center
        self.map_center = Vector2(screen_width // 2, screen_height // 2)
        
        # Colors
        self.background_color = (10, 10, 30)
        self.grid_color = (30, 30, 60)
        self.border_color = (100, 100, 150)
        
        # Fonts
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        
        # Zoom and pan
        self.zoom_level = 1.0
        self.pan_offset = Vector2(0, 0)
        self.min_zoom = 0.5
        self.max_zoom = 3.0
        
        # Selection
        self.selected_object = None
        
        # Mouse interaction
        self._pan_start = None
        
    def toggle_visibility(self):
        """Toggle the large map display."""
        self.visible = not self.visible
    
    def world_to_map_coords(self, world_pos):
        """Convert world coordinates to map screen coordinates."""
        # Center the universe in the map
        map_x = self.map_center.x + (world_pos.x - self.universe_width / 2) * self.scale * self.zoom_level + self.pan_offset.x
        map_y = self.map_center.y + (world_pos.y - self.universe_height / 2) * self.scale * self.zoom_level + self.pan_offset.y
        return Vector2(map_x, map_y)
    
    def map_to_world_coords(self, map_pos):
        """Convert map screen coordinates to world coordinates."""
        world_x = ((map_pos.x - self.map_center.x - self.pan_offset.x) / (self.scale * self.zoom_level)) + self.universe_width / 2
        world_y = ((map_pos.y - self.map_center.y - self.pan_offset.y) / (self.scale * self.zoom_level)) + self.universe_height / 2
        return Vector2(world_x, world_y)
    
    def handle_input(self, event):
        """Handle input events for the large map."""
        if not self.visible:
            return False
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m or event.key == pygame.K_ESCAPE:
                self.toggle_visibility()
                return True
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                self.zoom_in()
                return True
            elif event.key == pygame.K_MINUS:
                self.zoom_out()
                return True
            elif event.key == pygame.K_HOME:
                self.reset_view()
                return True
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self._handle_click(Vector2(event.pos))
                return True
            elif event.button == 2:  # Middle click - center on clicked location
                self._center_on_location(Vector2(event.pos))
                return True
            elif event.button == 3:  # Right click - start pan
                self._pan_start = Vector2(event.pos)
                return True
            elif event.button == 4:  # Mouse wheel up
                self._zoom_at_mouse(Vector2(event.pos), 1.2)
                return True
            elif event.button == 5:  # Mouse wheel down
                self._zoom_at_mouse(Vector2(event.pos), 1.0/1.2)
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:  # Right click release
                self._pan_start = None
                return True
                
        elif event.type == pygame.MOUSEMOTION:
            if pygame.mouse.get_pressed()[2] and hasattr(self, '_pan_start') and self._pan_start:  # Right mouse drag
                current_pos = Vector2(event.pos)
                delta = current_pos - self._pan_start
                self.pan_offset.x += delta.x
                self.pan_offset.y += delta.y
                self._pan_start = current_pos
                return True
        
        return False
    
    def _handle_click(self, click_pos):
        """Handle mouse clicks on the map."""
        # Convert click to world coordinates
        world_pos = self.map_to_world_coords(click_pos)
        # Here you could select objects, set waypoints, etc.
        print(f"Clicked at world position: {world_pos}")
    
    def _center_on_location(self, click_pos):
        """Center the map on the clicked location."""
        # Convert click to world coordinates
        world_pos = self.map_to_world_coords(click_pos)
        # Calculate the current center in world coordinates
        center_world_pos = self.map_to_world_coords(self.map_center)
        # Calculate the difference and adjust pan offset
        diff = world_pos - center_world_pos
        self.pan_offset.x -= diff.x * self.scale * self.zoom_level
        self.pan_offset.y -= diff.y * self.scale * self.zoom_level
    
    def _zoom_at_mouse(self, mouse_pos, zoom_factor):
        """Zoom in/out centered on mouse position."""
        # Store world position at mouse before zoom
        world_pos_before = self.map_to_world_coords(mouse_pos)
        
        # Apply zoom
        old_zoom = self.zoom_level
        self.zoom_level = max(self.min_zoom, min(self.max_zoom, self.zoom_level * zoom_factor))
        
        # Calculate world position at mouse after zoom
        world_pos_after = self.map_to_world_coords(mouse_pos)
        
        # Adjust pan offset to keep the same world position under the mouse
        diff = world_pos_after - world_pos_before
        self.pan_offset.x -= diff.x * self.scale * self.zoom_level
        self.pan_offset.y -= diff.y * self.scale * self.zoom_level
    
    def zoom_in(self):
        """Zoom in on the map."""
        self.zoom_level = min(self.max_zoom, self.zoom_level * 1.2)
    
    def zoom_out(self):
        """Zoom out on the map."""
        self.zoom_level = max(self.min_zoom, self.zoom_level / 1.2)
    
    def reset_view(self):
        """Reset zoom and pan to default."""
        self.zoom_level = 1.0
        self.pan_offset = Vector2(0, 0)
    
    def center_on_ship(self, ship_pos):
        """Center the map view on the ship."""
        # Calculate the offset needed to center the ship at the map center
        ship_map_pos = self.world_to_map_coords(ship_pos)
        self.pan_offset.x = self.map_center.x - ship_map_pos.x
        self.pan_offset.y = self.map_center.y - ship_map_pos.y
    
    def draw(self, surface, ship, stations, planets):
        """Draw the large map overlay."""
        if not self.visible:
            return
        
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(220)
        overlay.fill(self.background_color)
        surface.blit(overlay, (0, 0))
        
        # Draw grid
        self._draw_grid(surface)
        
        # Draw map border
        map_rect = pygame.Rect(self.margin, self.margin, self.map_width, self.map_height)
        pygame.draw.rect(surface, self.border_color, map_rect, 3)
        
        # Draw universe objects
        self._draw_planets(surface, planets)
        self._draw_stations(surface, stations)
        self._draw_ship(surface, ship)
        
        # Draw UI elements
        self._draw_title(surface)
        self._draw_legend(surface)
        self._draw_coordinates(surface, ship)
        self._draw_zoom_info(surface)
        self._draw_instructions(surface)
    
    def _draw_grid(self, surface):
        """Draw a coordinate grid on the map."""
        # Grid spacing in world units
        grid_spacing = 1000
        
        # Calculate grid lines
        start_x = -(self.universe_width // 2) // grid_spacing * grid_spacing
        start_y = -(self.universe_height // 2) // grid_spacing * grid_spacing
        
        # Vertical lines
        for x in range(int(start_x), int(self.universe_width), grid_spacing):
            world_pos = Vector2(x, 0)
            map_pos = self.world_to_map_coords(world_pos)
            if self.margin <= map_pos.x <= self.screen_width - self.margin:
                pygame.draw.line(surface, self.grid_color,
                               (map_pos.x, self.margin),
                               (map_pos.x, self.screen_height - self.margin), 1)
        
        # Horizontal lines
        for y in range(int(start_y), int(self.universe_height), grid_spacing):
            world_pos = Vector2(0, y)
            map_pos = self.world_to_map_coords(world_pos)
            if self.margin <= map_pos.y <= self.screen_height - self.margin:
                pygame.draw.line(surface, self.grid_color,
                               (self.margin, map_pos.y),
                               (self.screen_width - self.margin, map_pos.y), 1)
    
    def _draw_planets(self, surface, planets):
        """Draw planets on the large map."""
        for planet in planets:
            map_pos = self.world_to_map_coords(planet.position)
            if self._is_visible(map_pos):
                size = max(2, int(3 * self.zoom_level))
                pygame.draw.circle(surface, (100, 100, 255), 
                                 (int(map_pos.x), int(map_pos.y)), size)
                
                # Draw planet name if zoomed in enough
                if self.zoom_level > 1.5 and hasattr(planet, 'name'):
                    name_surface = self.font_small.render(planet.name, True, (150, 150, 255))
                    text_pos = (int(map_pos.x - name_surface.get_width() // 2),
                              int(map_pos.y + size + 2))
                    surface.blit(name_surface, text_pos)
    
    def _draw_stations(self, surface, stations):
        """Draw stations on the large map."""
        for station in stations:
            map_pos = self.world_to_map_coords(station.position)
            if self._is_visible(map_pos):
                size = max(3, int(5 * self.zoom_level))
                pygame.draw.circle(surface, (200, 200, 200), 
                                 (int(map_pos.x), int(map_pos.y)), size)
                pygame.draw.circle(surface, (255, 255, 255), 
                                 (int(map_pos.x), int(map_pos.y)), size, 1)
                
                # Draw station name
                if hasattr(station, 'name'):
                    name_surface = self.font_small.render(station.name, True, (255, 255, 255))
                    text_pos = (int(map_pos.x - name_surface.get_width() // 2),
                              int(map_pos.y + size + 2))
                    surface.blit(name_surface, text_pos)
    
    def _draw_ship(self, surface, ship):
        """Draw the player ship on the large map."""
        map_pos = self.world_to_map_coords(ship.position)
        if self._is_visible(map_pos):
            size = max(4, int(6 * self.zoom_level))
            
            # Draw ship as a triangle pointing in the direction it's facing
            ship_direction = Vector2(0, -size).rotate(ship.rotation)
            triangle_points = [
                map_pos + ship_direction,
                map_pos + Vector2(-size//2, size//2),
                map_pos + Vector2(size//2, size//2)
            ]
            
            pygame.draw.polygon(surface, (0, 255, 0), triangle_points)
            pygame.draw.polygon(surface, (255, 255, 255), triangle_points, 1)
            
            # Draw ship label
            ship_text = self.font_small.render("YOU", True, (0, 255, 0))
            text_pos = (int(map_pos.x - ship_text.get_width() // 2),
                      int(map_pos.y + size + 2))
            surface.blit(ship_text, text_pos)
    
    def _is_visible(self, map_pos):
        """Check if a position is visible on the map."""
        return (self.margin <= map_pos.x <= self.screen_width - self.margin and
                self.margin <= map_pos.y <= self.screen_height - self.margin)
    
    def _draw_title(self, surface):
        """Draw the map title."""
        title = self.font_large.render("UNIVERSE MAP", True, (255, 255, 255))
        title_pos = (self.screen_width // 2 - title.get_width() // 2, 10)
        surface.blit(title, title_pos)
    
    def _draw_legend(self, surface):
        """Draw the map legend."""
        legend_x = 20
        legend_y = 80
        line_height = 25
        
        legend_items = [
            ("Ship:", (0, 255, 0)),
            ("Stations:", (200, 200, 200)),
            ("Planets:", (100, 100, 255))
        ]
        
        for i, (label, color) in enumerate(legend_items):
            y_pos = legend_y + i * line_height
            
            # Draw color indicator
            pygame.draw.circle(surface, color, (legend_x + 10, y_pos + 8), 6)
            
            # Draw label
            text = self.font_small.render(label, True, (255, 255, 255))
            surface.blit(text, (legend_x + 25, y_pos))
    
    def _draw_coordinates(self, surface, ship):
        """Draw current ship coordinates."""
        coord_text = f"Ship Position: ({ship.position.x:.0f}, {ship.position.y:.0f})"
        coord_surface = self.font_small.render(coord_text, True, (200, 200, 200))
        surface.blit(coord_surface, (20, self.screen_height - 60))
    
    def _draw_zoom_info(self, surface):
        """Draw zoom level information."""
        zoom_text = f"Zoom: {self.zoom_level:.1f}x"
        zoom_surface = self.font_small.render(zoom_text, True, (200, 200, 200))
        surface.blit(zoom_surface, (20, self.screen_height - 40))
    
    def _draw_instructions(self, surface):
        """Draw control instructions."""
        instructions = [
            "M/ESC: Close map",
            "Mouse wheel: Zoom in/out",
            "Right drag: Pan map",
            "Middle click: Center on location",
            "Left click: Select location",
            "HOME: Reset view"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font_small.render(instruction, True, (150, 150, 150))
            x_pos = self.screen_width - text.get_width() - 20
            y_pos = 80 + i * 20
            surface.blit(text, (x_pos, y_pos))