import math
import random
from enum import Enum

import pygame
from pygame import Vector2

from ..ui import gfx

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

    def __init__(self, x, y, station_type=None):
        self.position = pygame.Vector2(x, y)
        # An explicit type (used for story stations) skips the random pick
        self.station_type = station_type or random.choice(list(StationType))
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
        self.market.station = self

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
        elif self.station_type == StationType.MINING:
            # Hexagon - industrial/drilling silhouette
            points = []
            for i in range(6):
                angle = math.radians(i * (360 / 6))
                points.append(Vector2(self.size * math.cos(angle), self.size * math.sin(angle)))
            return points
        elif self.station_type == StationType.RESEARCH:
            # Four-armed cross - sensor/instrument array
            arm = self.size * 0.4
            return [
                Vector2(-arm, -self.size), Vector2(arm, -self.size),
                Vector2(arm, -arm), Vector2(self.size, -arm),
                Vector2(self.size, arm), Vector2(arm, arm),
                Vector2(arm, self.size), Vector2(-arm, self.size),
                Vector2(-arm, arm), Vector2(-self.size, arm),
                Vector2(-self.size, -arm), Vector2(-arm, -arm),
            ]
        elif self.station_type == StationType.SHIPYARD:
            # Elongated hangar shape with angled ends
            return [
                Vector2(-self.size * 1.3, -self.size * 0.5),
                Vector2(-self.size * 0.8, -self.size),
                Vector2(self.size * 0.8, -self.size),
                Vector2(self.size * 1.3, -self.size * 0.5),
                Vector2(self.size * 1.3, self.size * 0.5),
                Vector2(self.size * 0.8, self.size),
                Vector2(-self.size * 0.8, self.size),
                Vector2(-self.size * 1.3, self.size * 0.5),
            ]
        else:
            # Default rectangle shape (fallback)
            return [
                Vector2(-self.size, -self.size),
                Vector2(self.size, -self.size),
                Vector2(self.size, self.size),
                Vector2(-self.size, self.size)
            ]
        
    def draw(self, screen, camera_offset):
        screen_pos = self.position - camera_offset
        self.rotation += self.rotation_speed

        # Soft halo in the station's own colour, then the type's own structure
        gfx.draw_glow(screen, screen_pos, self.size * 2.1, self.color, 0.30)
        art = {
            StationType.TRADING: self._art_trading,
            StationType.MILITARY: self._art_military,
            StationType.MINING: self._art_mining,
            StationType.RESEARCH: self._art_research,
            StationType.SHIPYARD: self._art_shipyard,
        }.get(self.station_type, self._art_trading)
        art(screen, screen_pos)

        # Docking port indicator
        dock_pos = Vector2(0, -self.size - 10).rotate(self.rotation) + screen_pos
        pygame.draw.circle(screen, (0, 255, 0), (int(dock_pos.x), int(dock_pos.y)), 5)
        gfx.draw_glow(screen, dock_pos, 12, (0, 200, 0), 0.6)

        # Docking zone (slightly larger than the station)
        pygame.draw.circle(screen, (100, 100, 100),
                           (int(screen_pos.x), int(screen_pos.y)),
                           self.size + 10,
                           1)

    # Station art ---------------------------------------------------------------
    # Each type is built from a few shapes in unit coordinates (1.0 = the
    # station's size), rotated with the station.

    def _p(self, pos, x, y):
        return Vector2(x * self.size, y * self.size).rotate(self.rotation) + pos

    def _poly(self, screen, pos, points, fill, outline=None, width=2):
        pts = [self._p(pos, x, y) for x, y in points]
        pygame.draw.polygon(screen, fill, pts)
        if outline:
            pygame.draw.polygon(screen, outline, pts, width)

    def _circle(self, screen, pos, x, y, radius, fill, outline=None, width=1):
        c = self._p(pos, x, y)
        r = max(1, int(radius * self.size))
        pygame.draw.circle(screen, fill, (int(c.x), int(c.y)), r)
        if outline:
            pygame.draw.circle(screen, outline, (int(c.x), int(c.y)), r, width)

    def _line(self, screen, pos, a, b, color, width=2):
        pygame.draw.line(screen, color, self._p(pos, *a), self._p(pos, *b), width)

    def _blink(self, screen, pos, x, y, color, seed=0.0, size=0.07):
        """A small warning light that pulses."""
        c = self._p(pos, x, y)
        level = gfx.flicker(seed + self.position.x * 0.01, speed=0.18, low=0.15)
        lit = tuple(int(v * level) for v in color)
        pygame.draw.circle(screen, lit, (int(c.x), int(c.y)), max(2, int(size * self.size)))
        gfx.draw_glow(screen, c, max(6, int(size * self.size * 3.2)), color, 0.6 * level)

    def _art_trading(self, screen, pos):
        """A hub ringed by a wheel of cargo pods."""
        base = self.color
        edge = gfx.lighten(base, 0.45)
        ring_r = 0.82
        pygame.draw.circle(screen, gfx.darken(base, 0.35), (int(pos.x), int(pos.y)),
                           int(ring_r * self.size), max(3, int(0.12 * self.size)))
        pygame.draw.circle(screen, edge, (int(pos.x), int(pos.y)), int(ring_r * self.size), 1)
        for k in range(4):
            a = math.radians(90 * k)
            outer = (math.cos(a) * ring_r, math.sin(a) * ring_r)
            self._line(screen, pos, (math.cos(a) * 0.3, math.sin(a) * 0.3), outer,
                       gfx.darken(base, 0.2), max(2, int(0.08 * self.size)))
            self._circle(screen, pos, outer[0], outer[1], 0.17, gfx.lighten(base, 0.12), edge)
        octagon = [(math.cos(math.radians(45 * i + 22.5)) * 0.42,
                    math.sin(math.radians(45 * i + 22.5)) * 0.42) for i in range(8)]
        self._poly(screen, pos, octagon, base, edge)
        self._circle(screen, pos, 0, 0, 0.12, gfx.lighten(base, 0.6))
        for k in range(4):
            a = math.radians(90 * k + 45)
            self._blink(screen, pos, math.cos(a) * 0.62, math.sin(a) * 0.62, (120, 220, 255), seed=k)

    def _art_military(self, screen, pos):
        """An armoured, angular fortress with gun turrets."""
        base = self.color
        edge = gfx.lighten(base, 0.5)
        spikes = [(0, -1.0), (0.28, -0.5), (0.5, -0.28), (1.0, 0), (0.5, 0.28), (0.28, 0.5),
                  (0, 1.0), (-0.28, 0.5), (-0.5, 0.28), (-1.0, 0), (-0.5, -0.28), (-0.28, -0.5)]
        self._poly(screen, pos, spikes, gfx.darken(base, 0.3), edge)
        self._poly(screen, pos, [(0, -0.55), (0.55, 0), (0, 0.55), (-0.55, 0)], base, edge)
        self._poly(screen, pos, [(0, -0.28), (0.28, 0), (0, 0.28), (-0.28, 0)], gfx.darken(base, 0.55),
                   gfx.lighten(base, 0.2))
        for x, y in ((0.72, 0), (-0.72, 0), (0, 0.72), (0, -0.72)):
            self._circle(screen, pos, x, y, 0.09, gfx.darken(base, 0.7), edge)
            self._line(screen, pos, (x, y), (x * 1.22, y * 1.22), edge, 2)
        self._blink(screen, pos, 0, 0, (255, 70, 60), size=0.1)

    def _art_mining(self, screen, pos):
        """A rugged core with two drill arms and ore pods."""
        base = self.color
        edge = gfx.lighten(base, 0.4)
        for side in (-1, 1):
            self._poly(screen, pos, [(side * 0.45, -0.14), (side * 0.92, -0.14), (side * 0.92, 0.14),
                                     (side * 0.45, 0.14)], gfx.darken(base, 0.3), edge)
            self._poly(screen, pos, [(side * 0.92, -0.2), (side * 1.2, 0), (side * 0.92, 0.2)],
                       (200, 170, 70), (255, 230, 130))
        hexagon = [(math.cos(math.radians(60 * i)) * 0.55, math.sin(math.radians(60 * i)) * 0.55)
                   for i in range(6)]
        self._poly(screen, pos, hexagon, base, edge)
        for x, y in ((0, -0.8), (0, 0.8), (0.3, -0.72), (-0.3, 0.72)):
            self._circle(screen, pos, x, y, 0.13, gfx.darken(base, 0.45), edge)
        self._circle(screen, pos, 0, 0, 0.16, gfx.lighten(base, 0.55))
        self._blink(screen, pos, 0.62, 0.34, (255, 190, 60), seed=1)
        self._blink(screen, pos, -0.62, -0.34, (255, 190, 60), seed=2)

    def _art_research(self, screen, pos):
        """A bright sphere inside a tilted ring, with a dish and antenna."""
        base = self.color
        edge = gfx.lighten(base, 0.5)
        ring = [(math.cos(math.radians(a)) * 1.0, math.sin(math.radians(a)) * 0.36) for a in range(0, 360, 20)]
        pts = [self._p(pos, x, y) for x, y in ring]
        pygame.draw.polygon(screen, gfx.darken(base, 0.4), pts, max(3, int(0.1 * self.size)))
        pygame.draw.polygon(screen, edge, pts, 1)
        self._circle(screen, pos, 0, 0, 0.52, base, edge, 2)
        self._circle(screen, pos, -0.14, -0.14, 0.18, gfx.lighten(base, 0.7))
        self._line(screen, pos, (0, -0.5), (0, -1.0), edge, 2)
        self._line(screen, pos, (-0.22, -0.82), (0.22, -0.82), edge, 2)
        self._line(screen, pos, (0, 0.5), (0, 0.9), gfx.darken(base, 0.1), 2)
        self._blink(screen, pos, 0, -1.0, (150, 255, 255), size=0.08)
        self._blink(screen, pos, 1.0, 0, (255, 255, 255), seed=3, size=0.06)

    def _art_shipyard(self, screen, pos):
        """A long gantry with docking arms and lit bays."""
        base = self.color
        edge = gfx.lighten(base, 0.45)
        self._poly(screen, pos, [(-1.0, -0.17), (1.0, -0.17), (1.0, 0.17), (-1.0, 0.17)],
                   gfx.darken(base, 0.3), edge)
        self._poly(screen, pos, [(-0.3, -0.75), (0.3, -0.75), (0.3, 0.75), (-0.3, 0.75)], base, edge)
        for k in range(-3, 4):
            self._line(screen, pos, (-0.3, k * 0.2), (0.3, k * 0.2), gfx.darken(base, 0.35), 1)
        for x in (-0.85, 0.85):
            self._poly(screen, pos, [(x - 0.1, -0.3), (x + 0.1, -0.3), (x + 0.1, 0.3), (x - 0.1, 0.3)],
                       gfx.darken(base, 0.45), edge)
        for x, y in ((-0.85, -0.25), (-0.85, 0.25), (0.85, -0.25), (0.85, 0.25)):
            self._blink(screen, pos, x, y, (255, 240, 150), seed=x + y, size=0.06)
        self._circle(screen, pos, 0, 0, 0.14, gfx.lighten(base, 0.55))

    def _draw_military_features(self, screen, pos):
        """Draw military-specific features"""
        # Radar visualization removed for cleaner visuals
        # TODO: Implement military visual features
        pass

    def _draw_mining_features(self, screen, pos):
        """Draw mining-specific features"""
        # Draw extending/retracting mining beam
        beam_length = abs(math.sin(pygame.time.get_ticks() / 500)) * self.size

        beam_end = Vector2(0, beam_length).rotate(self.rotation) + pos
        pygame.draw.line(screen, (255, 255, 0), pos, beam_end, 3)