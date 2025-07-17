import pygame
import math
import time
from typing import Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from ...settings import game_settings
    from ...missions.mission_manager import mission_manager
    from .dev_view import DevView
    from ..ui_layout import UILayout, Anchor
    from ..ui_theme import ui_theme, UIElementType, UIState
except ImportError:
    from settings import game_settings
    from missions.mission_manager import mission_manager
    from dev_view import DevView
    from ui_layout import UILayout, Anchor
    from ui_theme import ui_theme, UIElementType, UIState


class HUDPosition(Enum):
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"


@dataclass
class HUDElement:
    """Base class for HUD elements."""
    position: HUDPosition
    enabled: bool = True
    alpha: float = 1.0
    scale: float = 1.0


class StatusBar:
    """Animated status bar widget."""
    
    def __init__(self, width: int, height: int, color: tuple, bg_color: tuple = (40, 40, 40)):
        self.width = width
        self.height = height
        self.color = color
        self.bg_color = bg_color
        self.value = 1.0
        self.target_value = 1.0
        self.animation_speed = 2.0
    
    def set_value(self, value: float):
        """Set target value (0.0 to 1.0)."""
        self.target_value = max(0.0, min(1.0, value))
    
    def update(self, delta_time: float):
        """Update animation."""
        if abs(self.target_value - self.value) > 0.01:
            direction = 1 if self.target_value > self.value else -1
            self.value += direction * self.animation_speed * delta_time
            self.value = max(0.0, min(1.0, self.value))
    
    def draw(self, surface: pygame.Surface, x: int, y: int):
        """Draw the status bar."""
        # Background
        pygame.draw.rect(surface, self.bg_color, (x, y, self.width, self.height))
        
        # Border using theme
        bar_rect = pygame.Rect(x, y, self.width, self.height)
        ui_theme.draw_border(surface, bar_rect, UIElementType.STATUS_BAR)
        
        # Fill
        fill_width = int(self.width * self.value)
        if fill_width > 0:
            # Color interpolation based on value
            if self.value < 0.3:
                color = (255, int(255 * self.value / 0.3), 0)  # Red to yellow
            elif self.value < 0.7:
                color = (int(255 * (0.7 - self.value) / 0.4), 255, 0)  # Yellow to green
            else:
                color = self.color  # Use default color
            
            pygame.draw.rect(surface, color, (x + 1, y + 1, fill_width - 2, self.height - 2))


class EnhancedHUD:
    """Enhanced HUD system with comprehensive information display."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.scale = game_settings.hud_scale
        
        # Initialize UI layout system
        self.ui_layout = UILayout(screen_width, screen_height, self.scale)
        
        # Update theme scale
        ui_theme.update_scale(self.ui_layout.font_scale)
        
        # Fonts with responsive sizing
        self.font_large = pygame.font.Font(None, self.ui_layout.get_font_size(36))
        self.font_medium = pygame.font.Font(None, self.ui_layout.get_font_size(24))
        self.font_small = pygame.font.Font(None, self.ui_layout.get_font_size(18))
        
        # Status bars with responsive sizing
        bar_width = int(120 * self.ui_layout.font_scale)
        bar_height = int(12 * self.ui_layout.font_scale)
        self.hull_bar = StatusBar(bar_width, bar_height, (0, 255, 0))
        self.cargo_bar = StatusBar(bar_width, bar_height, (255, 255, 0))
        self.fuel_bar = StatusBar(bar_width, bar_height, (0, 150, 255))
        
        # HUD panels
        self.show_ship_status = True
        self.show_navigation = True
        self.show_mission_tracker = True
        self.show_market_info = False
        
        # Animation states
        self.credits_display = 0
        self.credits_target = 0
        self.blink_timer = 0.0
        
        # Market tracking
        self.market_prices = {}
        self.price_alerts = []
        
        # Navigation
        self.waypoint = None
        self.nearest_station = None
        
        # Performance tracking
        self.fps_history = []
        self.frame_time_history = []
        
        # Dev View
        self.dev_view = DevView(screen_width, screen_height)
    
    def update(self, delta_time: float, game_engine):
        """Update HUD elements."""
        ship = game_engine.ship
        
        # Update status bars
        hull_percentage = ship.get_hull_percentage()
        self.hull_bar.set_value(hull_percentage)
        self.hull_bar.update(delta_time)
        
        cargo_percentage = ship.cargo_hold.get_used_capacity() / ship.cargo_hold.capacity
        self.cargo_bar.set_value(cargo_percentage)
        self.cargo_bar.update(delta_time)
        
        # Update fuel bar
        fuel_percentage = ship.get_fuel_percentage()
        self.fuel_bar.set_value(fuel_percentage)
        self.fuel_bar.update(delta_time)
        
        # Update credits animation
        self.credits_target = ship.credits
        if abs(self.credits_target - self.credits_display) > 1:
            credit_diff = self.credits_target - self.credits_display
            self.credits_display += credit_diff * min(5.0 * delta_time, 1.0)
        else:
            self.credits_display = self.credits_target
        
        # Update blink timer for alerts
        self.blink_timer += delta_time
        
        # Update FPS tracking
        current_fps = game_engine.clock.get_fps()
        self.fps_history.append(current_fps)
        if len(self.fps_history) > 60:  # Keep last 60 frames
            self.fps_history.pop(0)
        
        # Update dev view
        self.dev_view.update(delta_time, game_engine)
        
        # Update nearest station
        self._update_nearest_station(game_engine)
    
    def _update_nearest_station(self, game_engine):
        """Find the nearest station for navigation."""
        ship_pos = game_engine.ship.position
        nearest_dist = float('inf')
        self.nearest_station = None
        
        for station in game_engine.universe.stations:
            dist = (station.position - ship_pos).length()
            if dist < nearest_dist:
                nearest_dist = dist
                self.nearest_station = station
    
    def render(self, surface: pygame.Surface, game_engine):
        """Render the complete HUD."""
        # Clear reserved areas at start of each frame
        self.ui_layout.clear_reserved_areas()
        
        if self.show_ship_status:
            self._render_ship_status(surface, game_engine)
        
        if self.show_navigation:
            self._render_navigation(surface, game_engine)
        
        if self.show_mission_tracker:
            self._render_mission_tracker(surface, game_engine)
        
        if self.show_market_info:
            self._render_market_info(surface, game_engine)
        
        # Always show FPS if enabled
        if game_settings.show_fps:
            self._render_fps(surface, game_engine)
        
        # Render dev view overlay
        self.dev_view.render(surface, game_engine)
        
        # Render alerts
        self._render_alerts(surface)
    
    def _render_ship_status(self, surface: pygame.Surface, game_engine):
        """Render ship status panel."""
        ship = game_engine.ship
        
        # Panel dimensions using responsive sizing - made taller for fuel/ammo
        panel_width, panel_height = self.ui_layout.get_panel_size(250, 280, 0.3, 0.6)
        panel_x, panel_y = self.ui_layout.get_position(Anchor.TOP_LEFT, panel_width, panel_height)
        
        # Panel background and border using theme
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        ui_theme.draw_panel_background(surface, panel_rect, 180)
        ui_theme.draw_border(surface, panel_rect, UIElementType.SHIP_STATUS)
        
        # Title with theme color
        title_color = ui_theme.get_text_color(UIElementType.SHIP_STATUS)
        title = self.font_medium.render("SHIP STATUS", True, title_color)
        surface.blit(title, (panel_x + self.ui_layout.padding, panel_y + self.ui_layout.padding))
        
        y_offset = panel_y + self.ui_layout.get_responsive_spacing(35)
        
        # Credits
        credits_text = f"Credits: {int(self.credits_display):,}"
        credits_color = (255, 255, 0) if ship.credits > 10000 else (255, 255, 255)
        credits_surface = self.font_small.render(credits_text, True, credits_color)
        surface.blit(credits_surface, (panel_x + self.ui_layout.padding, y_offset))
        y_offset += self.ui_layout.get_responsive_spacing(20)
        
        # Hull status
        hull_text = f"Hull: {ship.current_hull:.0f}/{ship.get_effective_stats().get_effective_hull_points()}"
        hull_surface = self.font_small.render(hull_text, True, (255, 255, 255))
        surface.blit(hull_surface, (panel_x + self.ui_layout.padding, y_offset))
        
        # Hull bar
        bar_x = panel_x + int(120 * self.ui_layout.font_scale)
        self.hull_bar.draw(surface, bar_x, y_offset + 2)
        y_offset += self.ui_layout.get_responsive_spacing(25)
        
        # Cargo status
        cargo_used = ship.cargo_hold.get_used_capacity()
        cargo_total = ship.cargo_hold.capacity
        cargo_text = f"Cargo: {cargo_used}/{cargo_total}"
        cargo_surface = self.font_small.render(cargo_text, True, (255, 255, 255))
        surface.blit(cargo_surface, (panel_x + self.ui_layout.padding, y_offset))
        
        # Cargo bar
        cargo_bar_x = panel_x + int(120 * self.ui_layout.font_scale)
        self.cargo_bar.draw(surface, cargo_bar_x, y_offset + 2)
        y_offset += self.ui_layout.get_responsive_spacing(25)
        
        # Fuel status
        fuel_text = f"Fuel: {ship.current_fuel:.0f}/{ship.fuel_capacity:.0f}"
        fuel_surface = self.font_small.render(fuel_text, True, (255, 255, 255))
        surface.blit(fuel_surface, (panel_x + self.ui_layout.padding, y_offset))
        
        # Fuel bar
        fuel_bar_x = panel_x + int(120 * self.ui_layout.font_scale)
        self.fuel_bar.draw(surface, fuel_bar_x, y_offset + 2)
        y_offset += self.ui_layout.get_responsive_spacing(25)
        
        # Ammo status - show counts for each type
        ammo_text = "Ammo:"
        ammo_surface = self.font_small.render(ammo_text, True, (255, 255, 255))
        surface.blit(ammo_surface, (panel_x + self.ui_layout.padding, y_offset))
        y_offset += self.ui_layout.get_responsive_spacing(15)
        
        # Display ammo counts in compact format
        ammo_info = [
            f"Laser: {ship.get_ammo_count('laser_cells')}/{ship.get_max_ammo_capacity('laser_cells')}",
            f"Plasma: {ship.get_ammo_count('plasma_cartridges')}/{ship.get_max_ammo_capacity('plasma_cartridges')}",
            f"Missiles: {ship.get_ammo_count('missiles')}/{ship.get_max_ammo_capacity('missiles')}",
            f"Railgun: {ship.get_ammo_count('railgun_slugs')}/{ship.get_max_ammo_capacity('railgun_slugs')}"
        ]
        
        for i, ammo_line in enumerate(ammo_info):
            ammo_line_surface = self.font_small.render(ammo_line, True, (200, 200, 200))
            surface.blit(ammo_line_surface, (panel_x + self.ui_layout.padding + 10, y_offset))
            y_offset += self.ui_layout.get_responsive_spacing(12)
        
        y_offset += self.ui_layout.get_responsive_spacing(10)
        
        # Speed
        speed = ship.velocity.length()
        max_speed = ship.get_effective_stats().get_effective_max_speed()
        speed_text = f"Speed: {speed:.0f}/{max_speed:.0f}"
        speed_surface = self.font_small.render(speed_text, True, (255, 255, 255))
        surface.blit(speed_surface, (panel_x + self.ui_layout.padding, y_offset))
        y_offset += self.ui_layout.get_responsive_spacing(20)
        
        # Upgrades summary
        upgrade_summary = ship.upgrades.get_upgrade_summary()
        upgrade_text = f"Upgrades: {sum(1 for v in upgrade_summary.values() if v != 'None')}/4"
        upgrade_surface = self.font_small.render(upgrade_text, True, (200, 200, 255))
        surface.blit(upgrade_surface, (panel_x + self.ui_layout.padding, y_offset))
        
        # Reserve this area to prevent overlap
        self.ui_layout.reserve_area(panel_x, panel_y, panel_width, panel_height, "ship_status")
    
    def _render_navigation(self, surface: pygame.Surface, game_engine):
        """Render navigation panel."""
        ship = game_engine.ship
        
        # Panel dimensions using responsive sizing
        panel_width, panel_height = self.ui_layout.get_panel_size(250, 120, 0.3, 0.3)
        # Position below ship status panel with spacing - updated height
        ship_status_height = self.ui_layout.get_panel_size(250, 280, 0.3, 0.6)[1]
        offset_y = ship_status_height + self.ui_layout.get_responsive_spacing(20)
        panel_x, panel_y = self.ui_layout.get_position(Anchor.TOP_LEFT, panel_width, panel_height, 0, offset_y)
        
        # Panel background and border using theme
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        ui_theme.draw_panel_background(surface, panel_rect, 180)
        ui_theme.draw_border(surface, panel_rect, UIElementType.NAVIGATION)
        
        # Title with theme color
        title_color = ui_theme.get_text_color(UIElementType.NAVIGATION)
        title = self.font_medium.render("NAVIGATION", True, title_color)
        surface.blit(title, (panel_x + self.ui_layout.padding, panel_y + self.ui_layout.padding))
        
        y_offset = panel_y + self.ui_layout.get_responsive_spacing(35)
        
        # Current position (invert Y for display)
        sector_x = int(ship.position.x // 1000)
        sector_y = int(-ship.position.y // 1000)
        pos_text = f"Sector: ({sector_x}, {sector_y})"
        pos_surface = self.font_small.render(pos_text, True, (255, 255, 255))
        surface.blit(pos_surface, (panel_x + self.ui_layout.padding, y_offset))
        y_offset += self.ui_layout.get_responsive_spacing(20)
        
        # Nearest station
        if self.nearest_station:
            distance = (self.nearest_station.position - ship.position).length()
            station_text = f"Nearest: {self.nearest_station.name}"
            distance_text = f"Distance: {distance:.0f}m"
            
            station_surface = self.font_small.render(station_text, True, (255, 255, 255))
            distance_surface = self.font_small.render(distance_text, True, (200, 200, 200))
            
            surface.blit(station_surface, (panel_x + self.ui_layout.padding, y_offset))
            surface.blit(distance_surface, (panel_x + self.ui_layout.padding, y_offset + 15))
            y_offset += self.ui_layout.get_responsive_spacing(35)
        
        # Docking status
        if hasattr(game_engine, 'docking_manager'):
            docking_state = game_engine.docking_manager.docking_state.value
            state_color = (0, 255, 0) if "docked" in docking_state.lower() else (255, 255, 255)
            state_text = f"Status: {docking_state.title()}"
            state_surface = self.font_small.render(state_text, True, state_color)
            surface.blit(state_surface, (panel_x + self.ui_layout.padding, y_offset))
            
        # Reserve this area to prevent overlap
        self.ui_layout.reserve_area(panel_x, panel_y, panel_width, panel_height, "navigation")
    
    def _render_mission_tracker(self, surface: pygame.Surface, game_engine):
        """Render active missions tracker."""
        active_missions = mission_manager.active_missions
        if not active_missions:
            return
        
        # Calculate dynamic panel height based on missions
        mission_height = self.ui_layout.get_responsive_spacing(45)
        extra_height = sum(15 for mission in active_missions[:3] if hasattr(mission, 'destination_station_id') and mission.destination_station_id)
        base_height = len(active_missions[:3]) * mission_height + extra_height + 40
        
        # Panel dimensions using responsive sizing
        panel_width, panel_height = self.ui_layout.get_panel_size(280, base_height, 0.35, 0.6)
        panel_x, panel_y = self.ui_layout.get_position(Anchor.TOP_RIGHT, panel_width, panel_height)
        
        # Panel background and border using theme
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        ui_theme.draw_panel_background(surface, panel_rect, 180)
        ui_theme.draw_border(surface, panel_rect, UIElementType.MISSION_TRACKER)
        
        # Title with theme color
        title_color = ui_theme.get_text_color(UIElementType.MISSION_TRACKER)
        title = self.font_medium.render("ACTIVE MISSIONS", True, title_color)
        surface.blit(title, (panel_x + self.ui_layout.padding, panel_y + self.ui_layout.padding))
        
        y_offset = panel_y + self.ui_layout.get_responsive_spacing(35)
        
        for i, mission in enumerate(active_missions[:3]):  # Show up to 3 missions
            # Mission title with responsive text truncation
            max_chars = max(20, int(30 * self.ui_layout.font_scale))
            title_text = mission.title[:max_chars] + ("..." if len(mission.title) > max_chars else "")
            title_surface = self.font_small.render(title_text, True, (255, 255, 255))
            surface.blit(title_surface, (panel_x + self.ui_layout.padding, y_offset))
            
            # Destination info if available
            if hasattr(mission, 'destination_station_id') and mission.destination_station_id:
                dest_text = f"→ {mission.destination_station_id}"
                dest_surface = self.font_small.render(dest_text, True, (150, 200, 255))
                surface.blit(dest_surface, (panel_x + self.ui_layout.padding, y_offset + 15))
                progress_y_offset = self.ui_layout.get_responsive_spacing(30)
            else:
                progress_y_offset = self.ui_layout.get_responsive_spacing(15)
            
            # Progress bar with responsive sizing
            progress_width = int(200 * self.ui_layout.font_scale)
            progress_height = int(8 * self.ui_layout.font_scale)
            progress_x = panel_x + self.ui_layout.padding
            progress_y = y_offset + progress_y_offset
            
            pygame.draw.rect(surface, (40, 40, 40), (progress_x, progress_y, progress_width, progress_height))
            
            fill_width = int(progress_width * mission.completion_percentage)
            if fill_width > 0:
                pygame.draw.rect(surface, (100, 200, 255), (progress_x, progress_y, fill_width, progress_height))
            
            pygame.draw.rect(surface, (100, 100, 100), (progress_x, progress_y, progress_width, progress_height), 1)
            
            # Time remaining
            time_remaining = mission.get_formatted_time_remaining()
            if time_remaining != "No time limit":
                time_color = (255, 100, 100) if "EXPIRED" in time_remaining else (200, 200, 200)
                time_surface = self.font_small.render(time_remaining, True, time_color)
                time_x = panel_x + panel_width - time_surface.get_width() - self.ui_layout.padding
                surface.blit(time_surface, (time_x, y_offset))
            
            y_offset += mission_height + (15 if hasattr(mission, 'destination_station_id') and mission.destination_station_id else 0)
        
        # Reserve this area to prevent overlap
        self.ui_layout.reserve_area(panel_x, panel_y, panel_width, panel_height, "mission_tracker")
    
    def _render_market_info(self, surface: pygame.Surface, game_engine):
        """Render market information panel."""
        # This would show price trends, alerts, etc.
        # Implementation depends on market tracking system
        pass
    
    def _render_fps(self, surface: pygame.Surface, game_engine):
        """Render FPS counter."""
        if not self.fps_history:
            return
        
        avg_fps = sum(self.fps_history) / len(self.fps_history)
        
        fps_text = f"FPS: {avg_fps:.1f}"
        fps_color = (0, 255, 0) if avg_fps >= 50 else (255, 255, 0) if avg_fps >= 30 else (255, 0, 0)
        fps_surface = self.font_small.render(fps_text, True, fps_color)
        
        # Position using responsive layout
        fps_width, fps_height = fps_surface.get_size()
        fps_x, fps_y = self.ui_layout.find_non_overlapping_position(fps_width, fps_height, Anchor.TOP_RIGHT)
        
        surface.blit(fps_surface, (fps_x, fps_y))
    
    def _render_alerts(self, surface: pygame.Surface):
        """Render alert messages."""
        # Blinking alerts for critical situations
        if self.blink_timer % 1.0 < 0.5:  # Blink every 0.5 seconds
            # Example: Low hull warning
            # This would be expanded with proper alert system
            pass
    
    def set_waypoint(self, position: tuple):
        """Set navigation waypoint."""
        self.waypoint = position
    
    def clear_waypoint(self):
        """Clear navigation waypoint."""
        self.waypoint = None
    
    def add_price_alert(self, commodity: str, station: str, price: int):
        """Add a market price alert."""
        alert = {
            "commodity": commodity,
            "station": station,
            "price": price,
            "timestamp": time.time()
        }
        self.price_alerts.append(alert)
        
        # Keep only recent alerts
        current_time = time.time()
        self.price_alerts = [a for a in self.price_alerts if current_time - a["timestamp"] < 300]  # 5 minutes
    
    def resize(self, screen_width: int, screen_height: int):
        """Handle screen resize."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.scale = game_settings.hud_scale
        
        # Update UI layout system
        self.ui_layout.resize(screen_width, screen_height)
        
        # Update theme scale
        ui_theme.update_scale(self.ui_layout.font_scale)
        
        # Recreate fonts with responsive sizing
        self.font_large = pygame.font.Font(None, self.ui_layout.get_font_size(36))
        self.font_medium = pygame.font.Font(None, self.ui_layout.get_font_size(24))
        self.font_small = pygame.font.Font(None, self.ui_layout.get_font_size(18))
        
        # Recreate status bars with responsive sizing
        bar_width = int(120 * self.ui_layout.font_scale)
        bar_height = int(12 * self.ui_layout.font_scale)
        self.hull_bar = StatusBar(bar_width, bar_height, (0, 255, 0))
        self.cargo_bar = StatusBar(bar_width, bar_height, (255, 255, 0))
        self.fuel_bar = StatusBar(bar_width, bar_height, (0, 150, 255))
        
        # Resize dev view
        self.dev_view.resize(screen_width, screen_height)