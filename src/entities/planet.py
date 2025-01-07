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
        self.base_color = random.choice(self.PLANET_COLORS[self.planet_type])
        self.features = [] # List to store surface features
        self.rotation = random.uniform(-0.5, 0.5)
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

    def draw(self, screen, camera_offset):
        """Draw the planet with its features"""
        screen_pos = self.position - camera_offset
        
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

    def _draw_gas_giant_features(self, screen, pos):
        """Draw features for gas giants"""
        for feature in self.features:
            if feature['type'] == 'band':
                y = pos.y + (feature['pos'] * self.size)
                height = int(self.size * feature['width'])
                rect = pygame.Rect(pos.x - self.size, y - height//2, self.size * 2, height)
                pygame.draw.rect(screen, feature['color'], rect)

    def _draw_atmosphere(self, screen, pos):
        """Draw atmospheric glow effect"""
        # Create a slightly larger, semi-transparent circle for atmosphere
        atmosphere_surf = pygame.Surface((self.size * 2 + 10, self.size * 2 + 10), pygame.SRCALPHA)
        pygame.draw.circle(atmosphere_surf, (*self.base_color, 30),
                         (self.size + 5, self.size + 5), self.size + 5)
        screen.blit(atmosphere_surf,
                   (pos.x - self.size - 5, pos.y - self.size - 5))