import math
import pygame
from pygame import Vector2
import random
from enum import Enum



class PlanetType(Enum):
    TERRESTRIAL = "Terrestrial"
    GAS_GIANT = "Gas Giant"
    ICE_WORLD = "Ice World"
    LAVA_WORLD = "Lava World"
    DESERT_WORLD = "Desert World"

class Planet:
    # Color schemes for different planet types
    PLANET_COLORS = {
        PlanetType.TERRESTRIAL: [(34, 139, 34), (0, 100, 0), (46, 139, 87)],  # Green/blue
        PlanetType.GAS_GIANT: [(255, 140, 0), (255, 165, 0), (255, 69, 0)],   # Orange/red
        PlanetType.ICE_WORLD: [(176, 224, 230), (173, 216, 230), (135, 206, 235)],  # Light blue
        PlanetType.LAVA_WORLD: [(139, 0, 0), (178, 34, 34), (205, 92, 92)],   # Red
        PlanetType.DESERT_WORLD: [(210, 180, 140), (188, 143, 143), (222, 184, 135)]  # Tan
    }

    def __init__(self, x, y):
        self.position = Vector2(x, y)
        self.planet_type = random.choice(list(PlanetType))
        self.size = self._get_size_for_type()
        self.color = random.choice(self.PLANET_COLORS[self.planet_type])  # Changed from base_color to color
        self.features = [] # List to store surface features
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-0.5, 0.5)
        self.name = self._generate_name()

        # Generate surface features
        self._generate_features()

    def _get_size_for_type(self):
        """Get appropriate size range based on planet type"""
        size_ranges = {
            PlanetType.TERRESTRIAL: (40, 60),
            PlanetType.GAS_GIANT: (80, 120),
            PlanetType.ICE_WORLD: (30, 50),
            PlanetType.LAVA_WORLD: (35, 55),
            PlanetType.DESERT_WORLD: (40, 65)
        }
        return random.randint(*size_ranges[self.planet_type])

    def _generate_name(self):
        """Generate a random name for the planet"""
        prefixes = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
        suffixes = ["Prime", "Major", "Minor", "IX", "V"]
        return f"{random.choice(prefixes)}-{random.randint(100, 999)}-{random.choice(suffixes)}"
        
    def _generate_features(self):
        """Generate surface features based on planet type"""
        if self.planet_type == PlanetType.TERRESTRIAL:
            # Add continents
            num_features = random.randint(3, 7)
            for _ in range(num_features):
                self.features.append({
                    'type': 'continent',
                    'color': (0, random.randint(100, 150), 0),
                    'pos': (random.uniform(-0.8, 0.8), random.uniform(-0.8, 0.8)),
                    'size': random.uniform(0.2, 0.4)
                })

        elif self.planet_type == PlanetType.GAS_GIANT:
            # Add bands
            num_bands = random.randint(3, 6)
            for i in range(num_bands):
                self.features.append({
                    'type': 'band',
                    'color': (random.randint(200, 255), random.randint(100, 200), 0),
                    'pos': -0.8 + (i * 1.6 / num_bands),
                    'width': random.uniform(0.1, 0.3)
                })
            # Signature storm, Great-Red-Spot style
            self.features.append({
                'type': 'storm',
                'pos': (random.uniform(-0.5, 0.1), random.uniform(0.1, 0.5)),
                'size': random.uniform(0.16, 0.24),
                'color': (
                    random.randint(180, 220),
                    random.randint(50, 90),
                    random.randint(30, 60),
                ),
            })
            # Some gas giants have a ring system (2D ellipse illusion)
            self.has_rings = random.random() < 0.5
            if self.has_rings:
                self.ring_rx = self.size * random.uniform(1.5, 1.9)
                self.ring_ry = self.ring_rx * random.uniform(0.22, 0.32)
                self.ring_thickness = max(2, int(self.size * 0.09))
                tint = random.uniform(0.85, 1.15)
                self.ring_color = tuple(min(255, int(c * tint)) for c in (200, 190, 170))

            # Bands/storm are precomputed and static, so build the composed,
            # circle-clipped overlay once here rather than every draw() call
            self._build_gas_giant_overlay()

        elif self.planet_type == PlanetType.ICE_WORLD:
            # Precompute crack lines once - these used to be regenerated with
            # fresh random values on every single draw() call, which made
            # them flicker/jitter every frame instead of looking like a
            # stable surface
            for _ in range(3):
                angle = random.uniform(0, 360)
                length = random.uniform(0.3, 0.7)
                self.features.append({
                    'type': 'crack',
                    'angle': angle,
                    'length': length
                })

        elif self.planet_type == PlanetType.LAVA_WORLD:
            # Precompute flows and pools once, same reasoning as ice cracks
            for _ in range(4):
                self.features.append({
                    'type': 'flow',
                    'start': (random.uniform(-0.7, 0.7), random.uniform(-0.7, 0.7)),
                    'length': random.uniform(0.2, 0.4),
                    'angle': random.uniform(0, 360)
                })
            for _ in range(5):
                self.features.append({
                    'type': 'pool',
                    'pos': (random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6)),
                    'size': random.uniform(0.1, 0.2)
                })

        elif self.planet_type == PlanetType.DESERT_WORLD:
            # Dune bands, similar treatment to gas giant cloud bands
            num_dunes = random.randint(4, 7)
            for i in range(num_dunes):
                self.features.append({
                    'type': 'dune',
                    'pos': (random.uniform(-0.7, 0.7), random.uniform(-0.7, 0.7)),
                    'size': random.uniform(0.15, 0.3)
                })

    def draw(self, screen, camera_offset):
        """Draw the planet with its features"""
        screen_pos = self.position - camera_offset

        # Gas giants with rings: draw the ring first so the far side appears
        # to pass behind the planet body
        if self.planet_type == PlanetType.GAS_GIANT and self.has_rings:
            self._draw_rings(screen, screen_pos)

        # Draw base planet
        pygame.draw.circle(screen, self.color,
                         (int(screen_pos.x), int(screen_pos.y)),
                         self.size)

        # Draw features based on planet type
        if self.planet_type == PlanetType.TERRESTRIAL:
            self._draw_terrestrial_features(screen, screen_pos)
        elif self.planet_type == PlanetType.GAS_GIANT:
            self._draw_gas_giant_features(screen, screen_pos)
        elif self.planet_type == PlanetType.ICE_WORLD:
            self._draw_ice_features(screen, screen_pos)
        elif self.planet_type == PlanetType.LAVA_WORLD:
            self._draw_lava_features(screen, screen_pos)
        elif self.planet_type == PlanetType.DESERT_WORLD:
            self._draw_desert_features(screen, screen_pos)

        # Draw the near side of the ring on top, so it appears in front of
        # the planet body instead of being hidden behind it
        if self.planet_type == PlanetType.GAS_GIANT and self.has_rings:
            self._draw_rings(screen, screen_pos, front_only=True)

        # Draw atmosphere effect
        self._draw_atmosphere(screen, screen_pos)

    def _draw_terrestrial_features(self, screen, pos):
        """Draw features for terrestrial planets"""
        for feature in self.features:
            if feature['type'] == 'continent':
                x = pos.x + (feature['pos'][0] * self.size)
                y = pos.y + (feature['pos'][1] * self.size)
                radius = int(self.size * feature['size'])
                pygame.draw.circle(screen, feature['color'], (int(x), int(y)), radius)

    def _build_gas_giant_overlay(self):
        """Precompute the bands + storm spot once, clipped to the planet's
        circular silhouette, instead of drawing full-width rectangles
        straight onto the screen every frame - those ignored the circle
        entirely and stuck out past its curved edge like flat bars."""
        d = self.size * 2
        content = pygame.Surface((d, d), pygame.SRCALPHA)

        for feature in self.features:
            if feature['type'] == 'band':
                y = self.size + (feature['pos'] * self.size)
                height = int(self.size * feature['width'])
                rect = pygame.Rect(0, y - height // 2, d, height)
                pygame.draw.rect(content, feature['color'], rect)
            elif feature['type'] == 'storm':
                cx = self.size + feature['pos'][0] * self.size
                cy = self.size + feature['pos'][1] * self.size
                sw = self.size * feature['size']
                sh = sw * 0.7
                pygame.draw.ellipse(content, feature['color'],
                                   pygame.Rect(cx - sw, cy - sh, sw * 2, sh * 2))

        # Clip to a circle: multiply alpha by a circular mask so anything
        # drawn outside the planet's radius is discarded
        mask = pygame.Surface((d, d), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (self.size, self.size), self.size)
        content.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        self.gas_giant_overlay = content

    def _draw_gas_giant_features(self, screen, pos):
        """Blit the precomputed, circle-clipped band/storm overlay."""
        screen.blit(self.gas_giant_overlay, (pos.x - self.size, pos.y - self.size))

    def _draw_rings(self, screen, pos, front_only=False):
        """Draw the gas giant's ring as a flattened ellipse. Called twice by
        draw(): once before the planet body (far side, appears behind it)
        and once after with front_only=True, clipped to just the bottom arc
        so the near side appears to pass in front of the planet."""
        rect = pygame.Rect(pos.x - self.ring_rx, pos.y - self.ring_ry,
                          self.ring_rx * 2, self.ring_ry * 2)
        if front_only:
            original_clip = screen.get_clip()
            bottom_clip = pygame.Rect(pos.x - self.ring_rx - 4, pos.y,
                                     self.ring_rx * 2 + 8, self.ring_ry + 4)
            screen.set_clip(bottom_clip)
            pygame.draw.ellipse(screen, self.ring_color, rect, self.ring_thickness)
            screen.set_clip(original_clip)
        else:
            pygame.draw.ellipse(screen, self.ring_color, rect, self.ring_thickness)

    def _draw_ice_features(self, screen, pos):
        """Draw features for ice worlds"""
        # Draw ice caps
        cap_size = self.size * 0.4
        pygame.draw.circle(screen, (220, 220, 255),
                          (int(pos.x), int(pos.y - self.size * 0.6)), int(cap_size))
        pygame.draw.circle(screen, (220, 220, 255),
                          (int(pos.x), int(pos.y + self.size * 0.6)), int(cap_size))

        # Draw cracks in the ice (precomputed in _generate_features, stable
        # across frames instead of re-randomized every draw call)
        for feature in self.features:
            if feature['type'] == 'crack':
                length = feature['length'] * self.size
                end_x = pos.x + length * math.cos(math.radians(feature['angle']))
                end_y = pos.y + length * math.sin(math.radians(feature['angle']))
                pygame.draw.line(screen, (200, 200, 255),
                                (int(pos.x), int(pos.y)),
                                (int(end_x), int(end_y)), 2)

    def _draw_lava_features(self, screen, pos):
        """Draw features for lava worlds"""
        # Draw lava flows and glowing pools (precomputed in _generate_features,
        # stable across frames instead of re-randomized every draw call)
        for feature in self.features:
            if feature['type'] == 'flow':
                start_x = pos.x + feature['start'][0] * self.size
                start_y = pos.y + feature['start'][1] * self.size
                length = feature['length'] * self.size
                end_x = start_x + length * math.cos(math.radians(feature['angle']))
                end_y = start_y + length * math.sin(math.radians(feature['angle']))
                pygame.draw.line(screen, (255, 165, 0),
                                (int(start_x), int(start_y)),
                                (int(end_x), int(end_y)), 3)
            elif feature['type'] == 'pool':
                x = pos.x + feature['pos'][0] * self.size
                y = pos.y + feature['pos'][1] * self.size
                radius = feature['size'] * self.size
                pygame.draw.circle(screen, (255, 200, 0), (int(x), int(y)), int(radius))

    def _draw_desert_features(self, screen, pos):
        """Draw dune features for desert worlds"""
        for feature in self.features:
            if feature['type'] == 'dune':
                x = pos.x + feature['pos'][0] * self.size
                y = pos.y + feature['pos'][1] * self.size
                radius = int(self.size * feature['size'])
                pygame.draw.circle(screen, (180, 140, 90), (int(x), int(y)), radius)

    def _draw_atmosphere(self, screen, pos):
        """Draw atmospheric glow effect"""
        # Create a slightly larger, semi-transparent circle for atmosphere
        atmosphere_surf = pygame.Surface((self.size * 2 + 10, self.size * 2 + 10), pygame.SRCALPHA)
        pygame.draw.circle(atmosphere_surf, (*self.color, 30),
                         (self.size + 5, self.size + 5), self.size + 5)
        screen.blit(atmosphere_surf,
                   (pos.x - self.size - 5, pos.y - self.size - 5))