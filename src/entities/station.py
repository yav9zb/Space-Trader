import math
import random
from enum import Enum

import pygame
from pygame import Vector2

# Import StationMarket - handle circular import
StationMarket = None


class StationType(Enum):
    TRADING = "Trading Post"
    MILITARY = "Military Base"
    MINING = "Mining Station"
    RESEARCH = "Research Station"
    SHIPYARD = "Shipyard"

class Station:
    # Color schemes for different station types
    STATION_COLORS = {
        StationType.TRADING: (150, 150, 150),    # Gray
        StationType.MILITARY: (150, 0, 0),       # Red
        StationType.MINING: (188, 143, 143),     # Brown
        StationType.RESEARCH: (0, 150, 150),     # Cyan
        StationType.SHIPYARD: (150, 150, 0)      # Yellow
    }

    def __init__(self, x, y):
        self.position = pygame.Vector2(x, y)
        self.station_type = random.choice(list(StationType))
        self.size = self._get_size_for_type()
        self.color = self.STATION_COLORS[self.station_type]
        self.name = self._generate_name()
        self.rotation = 0
        self.rotation_speed = random.uniform(-1, 1)
        self.collision_radius = self.size  # Explicit collision radius

        # Generate the station's shape points
        self.shape_points = self._generate_shape()
        
        # Trading system - import here to avoid circular dependency
        global StationMarket
        if StationMarket is None:
            try:
                from ..trading.market import StationMarket
                from ..trading.market import StationType as MarketStationType
            except ImportError:
                from trading.market import StationMarket
                from trading.market import StationType as MarketStationType
        else:
            # Import the market station type for mapping
            try:
                from ..trading.market import StationType as MarketStationType
            except ImportError:
                from trading.market import StationType as MarketStationType
        
        # Map station type to market type
        market_type_mapping = {
            StationType.TRADING: MarketStationType.TRADING,
            StationType.MILITARY: MarketStationType.MILITARY,
            StationType.MINING: MarketStationType.MINING,
            StationType.RESEARCH: MarketStationType.RESEARCH,
            StationType.SHIPYARD: MarketStationType.SHIPYARD
        }
        
        market_type = market_type_mapping.get(self.station_type, MarketStationType.TRADING)
        self.market = StationMarket(market_type, self.name)

    def _get_size_for_type(self):
        """Get appropriate size range based on station type"""
        size_ranges = {
            StationType.TRADING: (30, 40),
            StationType.MILITARY: (40, 50),
            StationType.MINING: (35, 45),
            StationType.RESEARCH: (25, 35),
            StationType.SHIPYARD: (45, 55)
        }
        return random.randint(*size_ranges[self.station_type])

    def _generate_name(self):
        """Generate a name for the station"""
        prefixes = {
            StationType.TRADING: ["Market", "Exchange", "Trade"],
            StationType.MILITARY: ["Fort", "Base", "Outpost"],
            StationType.MINING: ["Excavation", "Quarry", "Dig"],
            StationType.RESEARCH: ["Lab", "Institute", "Center"],
            StationType.SHIPYARD: ["Dock", "Yard", "Port"]
        }
        return f"{random.choice(prefixes[self.station_type])}-{random.randint(100, 999)}"

    def _generate_shape(self):
        """Generate shape points based on station type"""
        if self.station_type == StationType.TRADING:
            # Octagonal shape for trading stations
            points = []
            for i in range(8):
                angle = math.radians(i * (360 / 8))  # Convert to radians
                x = self.size * math.cos(angle)
                y = self.size * math.sin(angle)
                points.append(Vector2(x, y))
            return points
        elif self.station_type == StationType.MILITARY:
            # Triangle shape for military bases
            return [
                Vector2(0, -self.size),
                Vector2(-self.size, self.size),
                Vector2(self.size, self.size)
            ]
        else:
            # Default rectangle shape
            return [
                Vector2(-self.size, -self.size),
                Vector2(self.size, -self.size),
                Vector2(self.size, self.size),
                Vector2(-self.size, self.size)
            ]
        
    def draw(self, screen, camera_offset):
        # Calculate screen position by subtracting camera offset
        screen_pos = self.position - camera_offset

        # Rotate shape points
        self.rotation += self.rotation_speed
        rotated_points = []
        for point in self.shape_points:
            rotated = point.rotate(self.rotation)
            final_pos = rotated + screen_pos
            rotated_points.append(final_pos)

        # Draw main structure
        pygame.draw.polygon(screen, self.color, rotated_points)
        pygame.draw.polygon(screen, (255, 255, 255), rotated_points, 2)

        # Draw docking port indicator
        dock_pos = Vector2(0, -self.size - 10).rotate(self.rotation) + screen_pos
        pygame.draw.circle(screen, (0, 255, 0), (int(dock_pos.x), int(dock_pos.y)), 5)

        # Draw station type indicator
        if self.station_type == StationType.MILITARY:
            self._draw_military_features(screen, screen_pos)
        elif self.station_type == StationType.MINING:
            self._draw_mining_features(screen, screen_pos)
        # Add more specific features for other types...

        # Draw the station
        pygame.draw.circle(screen, self.color, 
                         (int(screen_pos.x), int(screen_pos.y)), 
                         self.size)
        
        # Draw docking zone (slightly larger than staton)
        pygame.draw.circle(screen, (100, 100, 100), 
                           (int(screen_pos.x), int(screen_pos.y)), 
                           self.size + 10,
                           1)
        
        # Draw collision boundary
        pygame.draw.circle(screen, (255, 0, 0), 
                     (int(screen_pos.x), int(screen_pos.y)), 
                     self.size, 
                     1)  # Draw collision radius
        
    def _draw_military_features(self, screen, pos):
        """Draw military-specific features"""
        # Draw "radar" rotating line
        radar_angle = (pygame.time.get_ticks() / 10) % 360
        radar_end = Vector2(0, self.size * 0.8).rotate(radar_angle) + pos
        pygame.draw.line(screen, (255, 0, 0), pos, radar_end, 2)

    def _draw_mining_features(self, screen, pos):
        """Draw mining-specific features"""
        # Draw extending/retracting mining beam
        beam_length = abs(math.sin(pygame.time.get_ticks() / 500)) * self.size

        beam_end = Vector2(0, beam_length).rotate(self.rotation) + pos
        pygame.draw.line(screen, (255, 255, 0), pos, beam_end, 3)