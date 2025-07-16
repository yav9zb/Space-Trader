import pygame
import math
from typing import Optional

try:
    from ...settings import game_settings
except ImportError:
    from settings import game_settings


class DevView:
    """Developer view overlay with toggleable debug information."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Fonts
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        
        # Panel settings
        self.panel_width = 300
        self.panel_height = 400
        self.panel_x = screen_width - self.panel_width - 10
        self.panel_y = screen_height - self.panel_height - 10
        
        # Colors
        self.bg_color = (0, 0, 0)
        self.border_color = (100, 100, 150)
        self.text_color = (255, 255, 255)
        self.header_color = (200, 200, 255)
        self.value_color = (150, 255, 150)
        
        # Data storage
        self.fps_history = []
        self.frame_time_history = []
    
    def update(self, delta_time: float, game_engine):
        """Update dev view data."""
        # Update FPS tracking
        current_fps = game_engine.clock.get_fps()
        self.fps_history.append(current_fps)
        if len(self.fps_history) > 60:  # Keep last 60 frames
            self.fps_history.pop(0)
        
        # Update frame time tracking
        frame_time = delta_time * 1000  # Convert to milliseconds
        self.frame_time_history.append(frame_time)
        if len(self.frame_time_history) > 60:
            self.frame_time_history.pop(0)
    
    def render(self, surface: pygame.Surface, game_engine):
        """Render the dev view overlay."""
        if not game_settings.dev_view_enabled:
            return
        
        # Create semi-transparent panel background
        panel_surface = pygame.Surface((self.panel_width, self.panel_height))
        panel_surface.set_alpha(200)
        panel_surface.fill(self.bg_color)
        surface.blit(panel_surface, (self.panel_x, self.panel_y))
        
        # Draw border
        pygame.draw.rect(surface, self.border_color, 
                        (self.panel_x, self.panel_y, self.panel_width, self.panel_height), 2)
        
        # Draw title
        title = self.font_medium.render("DEV VIEW", True, self.header_color)
        surface.blit(title, (self.panel_x + 10, self.panel_y + 10))
        
        y_offset = self.panel_y + 40
        
        # Render each section based on settings
        if game_settings.dev_show_fps:
            y_offset = self._render_fps_section(surface, game_engine, y_offset)
        
        if game_settings.dev_show_ship_pos:
            y_offset = self._render_ship_section(surface, game_engine, y_offset)
        
        if game_settings.dev_show_docking:
            y_offset = self._render_docking_section(surface, game_engine, y_offset)
        
        if game_settings.dev_show_camera:
            y_offset = self._render_camera_section(surface, game_engine, y_offset)
        
        if game_settings.dev_show_stations:
            y_offset = self._render_stations_section(surface, game_engine, y_offset)
    
    def _render_fps_section(self, surface: pygame.Surface, game_engine, y_offset: int) -> int:
        """Render FPS and performance information."""
        # Section header
        header = self.font_small.render("PERFORMANCE", True, self.header_color)
        surface.blit(header, (self.panel_x + 10, y_offset))
        y_offset += 20
        
        # Current FPS
        current_fps = game_engine.clock.get_fps()
        fps_color = (0, 255, 0) if current_fps >= 50 else (255, 255, 0) if current_fps >= 30 else (255, 0, 0)
        fps_text = self.font_small.render(f"FPS: {current_fps:.1f}", True, fps_color)
        surface.blit(fps_text, (self.panel_x + 15, y_offset))
        y_offset += 15
        
        # Average FPS
        if self.fps_history:
            avg_fps = sum(self.fps_history) / len(self.fps_history)
            avg_text = self.font_small.render(f"Avg FPS: {avg_fps:.1f}", True, self.value_color)
            surface.blit(avg_text, (self.panel_x + 15, y_offset))
            y_offset += 15
        
        # Frame time
        if self.frame_time_history:
            avg_frame_time = sum(self.frame_time_history) / len(self.frame_time_history)
            frame_color = (0, 255, 0) if avg_frame_time <= 16.7 else (255, 255, 0) if avg_frame_time <= 33.3 else (255, 0, 0)
            frame_text = self.font_small.render(f"Frame Time: {avg_frame_time:.1f}ms", True, frame_color)
            surface.blit(frame_text, (self.panel_x + 15, y_offset))
            y_offset += 15
        
        return y_offset + 10
    
    def _render_ship_section(self, surface: pygame.Surface, game_engine, y_offset: int) -> int:
        """Render ship position and movement information."""
        ship = game_engine.ship
        
        # Section header
        header = self.font_small.render("SHIP", True, self.header_color)
        surface.blit(header, (self.panel_x + 10, y_offset))
        y_offset += 20
        
        # Position
        pos_text = f"Pos: ({ship.position.x:.1f}, {ship.position.y:.1f})"
        pos_surface = self.font_small.render(pos_text, True, self.value_color)
        surface.blit(pos_surface, (self.panel_x + 15, y_offset))
        y_offset += 15
        
        # Velocity
        velocity = ship.velocity
        speed = velocity.length()
        vel_text = f"Velocity: ({velocity.x:.1f}, {velocity.y:.1f})"
        vel_surface = self.font_small.render(vel_text, True, self.value_color)
        surface.blit(vel_surface, (self.panel_x + 15, y_offset))
        y_offset += 15
        
        # Speed
        speed_text = f"Speed: {speed:.1f}"
        speed_surface = self.font_small.render(speed_text, True, self.value_color)
        surface.blit(speed_surface, (self.panel_x + 15, y_offset))
        y_offset += 15
        
        # Rotation
        rotation_text = f"Rotation: {ship.rotation:.1f}°"
        rotation_surface = self.font_small.render(rotation_text, True, self.value_color)
        surface.blit(rotation_surface, (self.panel_x + 15, y_offset))
        y_offset += 15
        
        return y_offset + 10
    
    def _render_docking_section(self, surface: pygame.Surface, game_engine, y_offset: int) -> int:
        """Render docking system information."""
        docking_manager = game_engine.docking_manager
        
        # Section header
        header = self.font_small.render("DOCKING", True, self.header_color)
        surface.blit(header, (self.panel_x + 10, y_offset))
        y_offset += 20
        
        # Docking state
        state = docking_manager.get_docking_state()
        state_color = (0, 255, 0) if "docked" in state.value.lower() else (255, 255, 0) if "docking" in state.value.lower() else self.value_color
        state_text = f"State: {state.value.title()}"
        state_surface = self.font_small.render(state_text, True, state_color)
        surface.blit(state_surface, (self.panel_x + 15, y_offset))
        y_offset += 15
        
        # Target station
        target_station = docking_manager.get_target_station()
        if target_station:
            target_text = f"Target: {target_station.name}"
            target_surface = self.font_small.render(target_text, True, self.value_color)
            surface.blit(target_surface, (self.panel_x + 15, y_offset))
            y_offset += 15
            
            # Distance to target
            distance = (target_station.position - game_engine.ship.position).length()
            distance_text = f"Distance: {distance:.1f}"
            distance_surface = self.font_small.render(distance_text, True, self.value_color)
            surface.blit(distance_surface, (self.panel_x + 15, y_offset))
            y_offset += 15
        else:
            no_target_text = "Target: None"
            no_target_surface = self.font_small.render(no_target_text, True, (150, 150, 150))
            surface.blit(no_target_surface, (self.panel_x + 15, y_offset))
            y_offset += 15
        
        return y_offset + 10
    
    def _render_camera_section(self, surface: pygame.Surface, game_engine, y_offset: int) -> int:
        """Render camera system information."""
        camera = game_engine.camera
        
        # Section header
        header = self.font_small.render("CAMERA", True, self.header_color)
        surface.blit(header, (self.panel_x + 10, y_offset))
        y_offset += 20
        
        # Camera offset
        camera_offset = camera.get_offset()
        offset_text = f"Offset: ({camera_offset.x:.1f}, {camera_offset.y:.1f})"
        offset_surface = self.font_small.render(offset_text, True, self.value_color)
        surface.blit(offset_surface, (self.panel_x + 15, y_offset))
        y_offset += 15
        
        # Camera mode
        mode_text = f"Mode: {game_settings.camera_mode.name.title()}"
        mode_surface = self.font_small.render(mode_text, True, self.value_color)
        surface.blit(mode_surface, (self.panel_x + 15, y_offset))
        y_offset += 15
        
        # Smoothing (if applicable)
        if hasattr(camera, 'smoothing'):
            smoothing_text = f"Smoothing: {camera.smoothing:.2f}"
            smoothing_surface = self.font_small.render(smoothing_text, True, self.value_color)
            surface.blit(smoothing_surface, (self.panel_x + 15, y_offset))
            y_offset += 15
        
        return y_offset + 10
    
    def _render_stations_section(self, surface: pygame.Surface, game_engine, y_offset: int) -> int:
        """Render station information."""
        # Section header
        header = self.font_small.render("STATIONS", True, self.header_color)
        surface.blit(header, (self.panel_x + 10, y_offset))
        y_offset += 20
        
        # Total stations
        total_stations = len(game_engine.universe.stations)
        total_text = f"Total: {total_stations}"
        total_surface = self.font_small.render(total_text, True, self.value_color)
        surface.blit(total_surface, (self.panel_x + 15, y_offset))
        y_offset += 15
        
        # Find nearest station
        ship_pos = game_engine.ship.position
        nearest_station = None
        nearest_distance = float('inf')
        
        for station in game_engine.universe.stations:
            distance = (station.position - ship_pos).length()
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_station = station
        
        if nearest_station:
            nearest_text = f"Nearest: {nearest_station.name}"
            nearest_surface = self.font_small.render(nearest_text, True, self.value_color)
            surface.blit(nearest_surface, (self.panel_x + 15, y_offset))
            y_offset += 15
            
            distance_text = f"Distance: {nearest_distance:.1f}"
            distance_surface = self.font_small.render(distance_text, True, self.value_color)
            surface.blit(distance_surface, (self.panel_x + 15, y_offset))
            y_offset += 15
        
        return y_offset + 10
    
    def resize(self, screen_width: int, screen_height: int):
        """Handle screen resize."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.panel_x = screen_width - self.panel_width - 10
        self.panel_y = screen_height - self.panel_height - 10