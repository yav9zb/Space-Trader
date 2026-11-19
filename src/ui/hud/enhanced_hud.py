import logging
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


from .. import gfx
from . import panel_kit

logger = logging.getLogger(__name__)


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
        """Draw the status bar: a dark trough with a lit fill, turning from the
        bar's colour through amber to red as it empties, and pulsing when it
        is nearly empty."""
        if self.value < 0.3:
            color = (235, 70, 50)
            if self.value < 0.15:
                color = gfx.mix((120, 30, 25), color, gfx.flicker(0.0, speed=0.8, low=0.0))
        elif self.value < 0.6:
            color = (235, 190, 50)
        else:
            color = self.color
        gfx.draw_bar(surface, (x, y, self.width, self.height), self.value, color, background=self.bg_color)


class EnhancedHUD:
    """Enhanced HUD system with comprehensive information display."""
    
    def __init__(self, screen_width: int, screen_height: int, ratio: float = 1.0):
        """`ratio` is pixels per point: 1.0 normally, 2.0 when this HUD draws at
        full resolution on a Retina display (screen_width/height are then the
        pixel size, and sizes are chosen as for the point size, then doubled)."""
        self.ratio = ratio
        self.minimap = None          # the radar this HUD sits beside, if not the engine's
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.scale = game_settings.hud_scale
        
        # Initialize UI layout system
        self.ui_layout = UILayout(screen_width, screen_height, self.scale)
        self._apply_ratio()
        
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
    
    def _apply_ratio(self):
        """At a pixel ratio above 1, lay out as for the point size and then
        scale the lengths, so a Retina HUD is the same size on screen but
        drawn with twice the pixels."""
        if self.ratio == 1.0:
            return
        layout = self.ui_layout
        layout.resize(round(self.screen_width / self.ratio), round(self.screen_height / self.ratio))
        layout.margin_x = round(layout.margin_x * self.ratio)
        layout.margin_y = round(layout.margin_y * self.ratio)
        layout.padding = round(layout.padding * self.ratio)
        layout.screen_width, layout.screen_height = self.screen_width, self.screen_height

    def render_pointer(self, surface: pygame.Surface, game_engine):
        """Arrow toward the current mission objective. It lives in the world,
        so on a Retina display it is drawn with the world, not the sharp layer."""
        try:
            from .. import objective_pointer
            objective_pointer.draw(surface, game_engine, self.font_small)
        except Exception:
            logger.exception("Objective pointer failed")

    def render_panels(self, surface: pygame.Surface, game_engine):
        """The panels: ship status, navigation and the mission tracker."""
        self.ui_layout.clear_reserved_areas()
        if self.show_ship_status or self.show_navigation:
            self._render_left_column(surface, game_engine)
        if self.show_mission_tracker:
            self._render_mission_tracker(surface, game_engine)

    def render_overlays(self, surface: pygame.Surface, game_engine):
        """Everything else the HUD can show (market info, fps, dev view, alerts)."""
        if self.show_market_info:
            self._render_market_info(surface, game_engine)
        if game_settings.show_fps:
            self._render_fps(surface, game_engine)
        self.dev_view.render(surface, game_engine)
        self._render_alerts(surface)

    def render(self, surface: pygame.Surface, game_engine):
        """Render the complete HUD."""
        # The pointer is drawn first, so the panels sit on top of it rather
        # than being covered by its label
        self.render_pointer(surface, game_engine)
        self.render_panels(surface, game_engine)
        self.render_overlays(surface, game_engine)

    # ---- panels ------------------------------------------------------------------

    FACTION_COLORS = {"Trade Guild": (232, 190, 90), "Independent": (150, 180, 215),
                      "Pirate Territory": (238, 105, 88)}
    DOCKING_COLORS = {"free_flight": panel_kit.DIM, "approaching": panel_kit.BLUE, "docking": panel_kit.AMBER,
                      "docked": panel_kit.GREEN, "undocking": panel_kit.AMBER}

    def _metrics(self):
        """Pixel metrics for the current window size, rebuilt only when it changes."""
        key = (self.ui_layout.font_scale, self.ratio)
        if getattr(self, "_metrics_for", None) != key:
            self._metrics_cache = panel_kit.make_metrics(key[0], self.ratio)
            self._metrics_for = key
        return self._metrics_cache

    def _left_width(self, m) -> int:
        return max(190, min(int(235 * m.unit), int(self.screen_width * 0.34)))

    def build_ship_status(self, game_engine, compact: bool = False) -> panel_kit.Panel:
        """The ship status panel's content (separate from drawing, so layout is testable)."""
        from ...missions.rank_system import get_rank_name
        ship = game_engine.ship
        m = self._metrics()
        panel = panel_kit.Panel("SHIP STATUS", UIElementType.SHIP_STATUS, (150, 175, 255), m, self._left_width(m))

        credits = int(self.credits_display)
        panel.stat("Credits", f"{credits:,}", panel_kit.AMBER if credits > 10000 else panel_kit.TEXT,
                   icon="credits", icon_color=panel_kit.AMBER)
        if not compact:
            panel.divider()

        max_hull = ship.get_effective_stats().get_effective_hull_points()
        hull = self.hull_bar.value
        panel.bar("hull", "HULL", f"{ship.current_hull:.0f}/{max_hull}", hull, panel_kit.level_color(hull))

        cargo = self.cargo_bar.value
        panel.bar("cargo", "CARGO", f"{ship.cargo_hold.get_used_capacity()}/{ship.cargo_hold.capacity}",
                  cargo, panel_kit.AMBER if cargo >= 0.95 else panel_kit.BLUE)

        if ship.get_emergency_fuel_status()['active']:
            panel.chip("EMERGENCY MODE", panel_kit.RED, label="FUEL")
        else:
            fuel = self.fuel_bar.value
            panel.bar("fuel", "FUEL", f"{ship.current_fuel:.0f}/{ship.fuel_capacity:.0f}", fuel,
                      panel_kit.level_color(fuel, (90, 170, 250)))
        if not compact:
            panel.divider()

        cells = []
        for label, kind in (("LASER", "laser_cells"), ("PLASMA", "plasma_cartridges"),
                            ("MISSILE", "missiles"), ("RAIL", "railgun_slugs")):
            have, cap = ship.get_ammo_count(kind), max(1, ship.get_max_ammo_capacity(kind))
            cells.append((label, str(have), have / cap, panel_kit.level_color(have / cap, (120, 190, 255))))
        panel.grid(cells, columns=4 if compact else None)
        if not compact:
            panel.divider()

        stats = ship.get_effective_stats()
        panel.stat("Speed", f"{ship.velocity.length():.0f}/{stats.get_effective_max_speed():.0f}", icon="speed")

        afterburner, emergency = ship.get_afterburner_status(), ship.get_emergency_fuel_status()
        if emergency['active']:
            text, color = "DISABLED", panel_kit.DIM
        elif afterburner['active']:
            text, color = "ACTIVE", panel_kit.BLUE
        elif afterburner['cooldown'] > 0:
            text, color = f"{afterburner['cooldown']:.1f}s", panel_kit.AMBER
        else:
            text, color = "READY", panel_kit.GREEN
        panel.chip(text, color, label="BOOST")

        reputation = game_engine.mission_manager.reputation
        panel.stat("Rank", f"{get_rank_name(reputation)}  {reputation}", (170, 235, 180), icon="rank",
                   icon_color=(170, 235, 180))
        if not compact:
            summary = ship.upgrades.get_upgrade_summary()
            panel.stat("Upgrades", f"{sum(1 for v in summary.values() if v != 'None')}/4")
        return panel

    def build_navigation(self, game_engine, compact: bool = False) -> panel_kit.Panel:
        from ...factions import get_controlling_faction
        ship = game_engine.ship
        m = self._metrics()
        panel = panel_kit.Panel("NAVIGATION", UIElementType.NAVIGATION, (150, 225, 160), m, self._left_width(m))

        sector_x, sector_y = int(ship.position.x // 1000), int(-ship.position.y // 1000)
        panel.big("SECTOR", f"({sector_x}, {sector_y})", icon="sector")

        faction = get_controlling_faction(sector_x, -sector_y, game_engine.world_seed)
        standing = game_engine.mission_manager.get_faction_standing(faction)
        panel.chip(f"{faction} {standing:+d}", self.FACTION_COLORS.get(faction, panel_kit.DIM), label="SPACE")
        if not compact:
            panel.divider()

        if self.nearest_station:
            distance = (self.nearest_station.position - ship.position).length()
            if compact:
                panel.stat(self.nearest_station.name, f"{distance:,.0f}m", icon="station")
            else:
                panel.stat("Nearest", self.nearest_station.name, icon="station")
                panel.stat("Distance", f"{distance:,.0f}m")
        if hasattr(game_engine, 'docking_manager'):
            state = game_engine.docking_manager.docking_state.value
            panel.chip(state.replace("_", " ").title(), self.DOCKING_COLORS.get(state, panel_kit.DIM), label="STATUS")
        return panel

    def _left_column(self, game_engine):
        """(panel, name, rect) for the left-hand column, stacked with a constant
        gap. If the full panels would run off the bottom of the window, the
        compact versions (fewer, tighter rows) are used instead."""
        m = self._metrics()
        for compact in (False, True):
            panels = []
            if self.show_ship_status:
                panels.append((self.build_ship_status(game_engine, compact), "ship_status"))
            if self.show_navigation:
                panels.append((self.build_navigation(game_engine, compact), "navigation"))
            rects = panel_kit.stack([p for p, _ in panels], self.ui_layout.margin_x,
                                    self.ui_layout.margin_y, m.gap + 4)
            bottom = rects[-1].bottom if rects else 0
            if bottom <= self.screen_height - self.ui_layout.margin_y:
                break
        return [(p, name, r) for (p, name), r in zip(panels, rects)]

    def _render_left_column(self, surface: pygame.Surface, game_engine):
        for panel, name, rect in self._left_column(game_engine):
            panel.draw(surface, rect.x, rect.y)
            self.ui_layout.reserve_area(rect.x, rect.y, rect.width, rect.height, name)

    def _render_mission_tracker(self, surface: pygame.Surface, game_engine):
        """Active missions, below the minimap in the top-right corner."""
        active = mission_manager.active_missions
        if not active:
            return
        m = self._metrics()
        width = max(210, min(int(270 * m.unit), int(self.screen_width * 0.4)))
        panel = panel_kit.Panel("ACTIVE MISSIONS", UIElementType.MISSION_TRACKER, (255, 200, 110), m, width)
        for mission in active[:3]:
            destination = getattr(mission, 'destination_station_id', None)
            coords = ""
            if destination:
                coords = (mission_manager.get_station_coordinates(destination, game_engine.universe.stations) or "")
                coords = coords.replace("Sector ", "")
            time_left = mission.get_formatted_time_remaining()
            right = "" if time_left == "No time limit" else time_left
            panel.entry(mission.title, right, f"-> {destination}" if destination else "", coords,
                        mission.completion_percentage,
                        right_color=panel_kit.RED if "EXPIRED" in right else panel_kit.DIM)
        if len(active) > 3:
            panel.note(f"+{len(active) - 3} more in the Mission Board")

        minimap = self.minimap if self.minimap is not None else getattr(game_engine, 'minimap', None)
        top = (minimap.rect.bottom + m.gap) if minimap is not None else self.ui_layout.margin_y
        x = self.screen_width - width - self.ui_layout.margin_x
        rect = panel.draw(surface, x, top)
        self.ui_layout.reserve_area(rect.x, rect.y, rect.width, rect.height, "mission_tracker")

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
        self._apply_ratio()
        
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