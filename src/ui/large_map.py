import pygame
from pygame import Vector2
import math
try:
    from .ui_theme import ui_theme, UIElementType, UIState
except ImportError:
    from ui_theme import ui_theme, UIElementType, UIState

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
        
        # View radius (similar to minimap but larger)
        self.view_radius = 5000  # Default view radius in world units
        
        # Calculate scale to fit view area in map
        self.scale = min(self.map_width, self.map_height) / (self.view_radius * 2) * 0.9
        
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
    
    def world_to_map_coords(self, world_pos, center_pos):
        """Convert world coordinates to map screen coordinates relative to center position."""
        # Calculate relative position from center
        relative_pos = world_pos - center_pos
        
        # Convert to map coordinates (centered on map center)
        map_x = self.map_center.x + relative_pos.x * self.scale * self.zoom_level + self.pan_offset.x
        map_y = self.map_center.y + relative_pos.y * self.scale * self.zoom_level + self.pan_offset.y
        return Vector2(map_x, map_y)
    
    def map_to_world_coords(self, map_pos, center_pos):
        """Convert map screen coordinates to world coordinates relative to center position."""
        # Calculate relative map position
        relative_x = (map_pos.x - self.map_center.x - self.pan_offset.x) / (self.scale * self.zoom_level)
        relative_y = (map_pos.y - self.map_center.y - self.pan_offset.y) / (self.scale * self.zoom_level)
        
        # Convert to world coordinates
        world_x = center_pos.x + relative_x
        world_y = center_pos.y + relative_y
        return Vector2(world_x, world_y)
    
    def handle_input(self, event, ship_pos=None):
        """Handle input events for the large map."""
        if not self.visible:
            return False
        
        # Use ship position as default center if provided
        center_pos = ship_pos if ship_pos else Vector2(0, 0)
            
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
                self._handle_click(Vector2(event.pos), center_pos)
                return True
            elif event.button == 2:  # Middle click - center on clicked location
                self._center_on_location(Vector2(event.pos), center_pos)
                return True
            elif event.button == 3:  # Right click - start pan
                self._pan_start = Vector2(event.pos)
                return True
            elif event.button == 4:  # Mouse wheel up
                self._zoom_at_mouse(Vector2(event.pos), 1.2, center_pos)
                return True
            elif event.button == 5:  # Mouse wheel down
                self._zoom_at_mouse(Vector2(event.pos), 1.0/1.2, center_pos)
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
    
    def _handle_click(self, click_pos, center_pos):
        """Handle mouse clicks on the map."""
        # Convert click to world coordinates
        world_pos = self.map_to_world_coords(click_pos, center_pos)
        # Here you could select objects, set waypoints, etc.
        print(f"Clicked at world position: {world_pos}")
    
    def _center_on_location(self, click_pos, center_pos):
        """Center the map on the clicked location."""
        # Convert click to world coordinates
        world_pos = self.map_to_world_coords(click_pos, center_pos)
        # Calculate the current center in world coordinates
        center_world_pos = self.map_to_world_coords(self.map_center, center_pos)
        # Calculate the difference and adjust pan offset
        diff = world_pos - center_world_pos
        self.pan_offset.x -= diff.x * self.scale * self.zoom_level
        self.pan_offset.y -= diff.y * self.scale * self.zoom_level
    
    def _zoom_at_mouse(self, mouse_pos, zoom_factor, center_pos):
        """Zoom in/out centered on mouse position."""
        # Store world position at mouse before zoom
        world_pos_before = self.map_to_world_coords(mouse_pos, center_pos)
        
        # Apply zoom
        old_zoom = self.zoom_level
        self.zoom_level = max(self.min_zoom, min(self.max_zoom, self.zoom_level * zoom_factor))
        
        # Calculate world position at mouse after zoom
        world_pos_after = self.map_to_world_coords(mouse_pos, center_pos)
        
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
        # Reset pan offset to center on ship (ship will be at map center)
        self.pan_offset = Vector2(0, 0)
    
    def draw(self, surface, ship, stations, planets):
        """Draw the large map overlay."""
        if not self.visible:
            return
        
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(220)
        overlay.fill(self.background_color)
        surface.blit(overlay, (0, 0))
        
        ship_pos = ship.position
        
        # Draw grid
        self._draw_grid(surface, ship_pos)
        
        # Draw map border using theme
        map_rect = pygame.Rect(self.margin, self.margin, self.map_width, self.map_height)
        ui_theme.draw_border(surface, map_rect, UIElementType.LARGE_MAP)
        
        # Draw universe objects
        self._draw_planets(surface, planets, ship_pos)
        self._draw_stations(surface, stations, ship_pos)
        self._draw_ship(surface, ship, ship_pos)
        
        # Draw UI elements
        self._draw_title(surface)
        self._draw_legend(surface)
        self._draw_coordinates(surface, ship)
        self._draw_zoom_info(surface)
        self._draw_instructions(surface)
    
    def _draw_grid(self, surface, center_pos):
        """Draw a coordinate grid on the map."""
        # Grid spacing in world units
        grid_spacing = 1000
        
        # Calculate grid range around current view
        view_range = self.view_radius * self.zoom_level
        start_x = int((center_pos.x - view_range) // grid_spacing) * grid_spacing
        end_x = int((center_pos.x + view_range) // grid_spacing + 1) * grid_spacing
        start_y = int((center_pos.y - view_range) // grid_spacing) * grid_spacing
        end_y = int((center_pos.y + view_range) // grid_spacing + 1) * grid_spacing
        
        # Vertical lines
        for x in range(start_x, end_x, grid_spacing):
            world_pos = Vector2(x, center_pos.y)
            map_pos = self.world_to_map_coords(world_pos, center_pos)
            if self.margin <= map_pos.x <= self.screen_width - self.margin:
                pygame.draw.line(surface, self.grid_color,
                               (map_pos.x, self.margin),
                               (map_pos.x, self.screen_height - self.margin), 1)
        
        # Horizontal lines
        for y in range(start_y, end_y, grid_spacing):
            world_pos = Vector2(center_pos.x, y)
            map_pos = self.world_to_map_coords(world_pos, center_pos)
            if self.margin <= map_pos.y <= self.screen_height - self.margin:
                pygame.draw.line(surface, self.grid_color,
                               (self.margin, map_pos.y),
                               (self.screen_width - self.margin, map_pos.y), 1)
    
    def _draw_planets(self, surface, planets, center_pos):
        """Draw planets on the large map."""
        for planet in planets:
            # Only draw planets within reasonable distance
            distance = (planet.position - center_pos).length()
            if distance <= self.view_radius * self.zoom_level * 2:  # Extend range for zoom
                map_pos = self.world_to_map_coords(planet.position, center_pos)
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
    
    def _draw_stations(self, surface, stations, center_pos):
        """Draw stations on the large map."""
        for station in stations:
            # Only draw stations within reasonable distance
            distance = (station.position - center_pos).length()
            if distance <= self.view_radius * self.zoom_level * 2:  # Extend range for zoom
                map_pos = self.world_to_map_coords(station.position, center_pos)
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
    
    def _draw_ship(self, surface, ship, center_pos):
        """Draw the player ship on the large map."""
        # Ship position relative to center (usually at map center when center_pos is ship.position)
        map_pos = self.world_to_map_coords(ship.position, center_pos)
        
        # Ship should always be visible on the map
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
        # Invert Y coordinate for display consistency with other HUD elements
        coord_text = f"Ship Position: ({ship.position.x:.0f}, {-ship.position.y:.0f})"
        coord_surface = self.font_small.render(coord_text, True, (200, 200, 200))
        surface.blit(coord_surface, (20, self.screen_height - 80))
    
    def _draw_zoom_info(self, surface):
        """Draw zoom level and view radius information."""
        zoom_text = f"Zoom: {self.zoom_level:.1f}x"
        zoom_surface = self.font_small.render(zoom_text, True, (200, 200, 200))
        surface.blit(zoom_surface, (20, self.screen_height - 60))
        
        # Draw view radius info (similar to minimap)
        radius_text = f"View Radius: {self.view_radius}m"
        radius_surface = self.font_small.render(radius_text, True, (200, 200, 200))
        surface.blit(radius_surface, (20, self.screen_height - 40))
    
    def _draw_instructions(self, surface):
        """Draw control instructions."""
        instructions = [
            "M/ESC: Close map",
            "Mouse wheel: Zoom in/out",
            "Right drag: Pan map",
            "Middle click: Center on location",
            "Left click: Select location",
            "HOME: Reset view",
            "Centered on player"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font_small.render(instruction, True, (150, 150, 150))
            x_pos = self.screen_width - text.get_width() - 20
            y_pos = 80 + i * 20
            surface.blit(text, (x_pos, y_pos))