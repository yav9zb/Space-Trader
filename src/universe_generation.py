"""Universe generation types and configurations."""

from enum import Enum
from typing import Dict, Any, Tuple
import math
import random
from pygame import Vector2


class UniverseType(Enum):
    """Different universe generation types."""
    DENSE = "dense"
    REALISTIC = "realistic"
    FRONTIER = "frontier"
    STAR_SYSTEMS = "star_systems"
    EMPTY = "empty"


class UniverseConfig:
    """Configuration for universe generation types."""
    
    @staticmethod
    def get_config(universe_type: UniverseType) -> Dict[str, Any]:
        """Get configuration for a specific universe type."""
        configs = {
            UniverseType.DENSE: {
                "name": "Dense Universe",
                "description": "Stations and planets everywhere - like the original game",
                "stations_per_chunk": (1, 2),
                "planets_per_chunk": (0, 1),
                "station_probability": 1.0,
                "planet_probability": 0.5,
                "civilized_space_radius": 0,  # No special areas
                "frontier_space_radius": 0,
                "wild_space_radius": 0,
                "debris_density": "normal",
                "bandit_encounters": "normal",
                "empty_chunk_probability": 0.0,
            },
            
            UniverseType.REALISTIC: {
                "name": "Realistic Universe",
                "description": "More realistic spacing - stations are rare and valuable",
                "stations_per_chunk": (0, 1),
                "planets_per_chunk": (0, 2),
                "station_probability": 0.15,  # 15% chance per chunk
                "planet_probability": 0.3,    # 30% chance per chunk
                "civilized_space_radius": 2000,  # Central civilized area
                "frontier_space_radius": 4000,  # Frontier area
                "wild_space_radius": 6000,     # Wild space beyond
                "debris_density": "normal",
                "bandit_encounters": "normal",
                "empty_chunk_probability": 0.4,  # 40% of chunks are empty
            },
            
            UniverseType.FRONTIER: {
                "name": "Frontier Universe",
                "description": "Sparse civilization, dangerous frontier exploration",
                "stations_per_chunk": (0, 1),
                "planets_per_chunk": (0, 1),
                "station_probability": 0.05,  # Very rare stations
                "planet_probability": 0.2,    # Some planets
                "civilized_space_radius": 1500,  # Small civilized core
                "frontier_space_radius": 3000,  # Large frontier
                "wild_space_radius": 8000,     # Vast wild space
                "debris_density": "high",
                "bandit_encounters": "high",
                "empty_chunk_probability": 0.6,  # 60% empty chunks
            },
            
            UniverseType.STAR_SYSTEMS: {
                "name": "Star Systems",
                "description": "Realistic star systems with multiple planets and stations",
                "stations_per_chunk": (0, 2),
                "planets_per_chunk": (0, 6),
                "station_probability": 0.1,   # Stations only in systems
                "planet_probability": 0.15,   # Systems are rare but rich
                "civilized_space_radius": 0,  # No special areas
                "frontier_space_radius": 0,
                "wild_space_radius": 0,
                "debris_density": "normal",
                "bandit_encounters": "normal",
                "empty_chunk_probability": 0.8,  # 80% empty space
                "star_system_mode": True,
                "system_probability": 0.1,    # 10% chance of star system per chunk
                "planets_per_system": (2, 6),
                "stations_per_system": (1, 3),
            },
            
            UniverseType.EMPTY: {
                "name": "Empty Universe",
                "description": "Vast empty space with minimal structures - for exploration",
                "stations_per_chunk": (0, 1),
                "planets_per_chunk": (0, 1),
                "station_probability": 0.02,  # Extremely rare
                "planet_probability": 0.05,   # Very rare
                "civilized_space_radius": 1000,  # Tiny civilized area
                "frontier_space_radius": 2000,
                "wild_space_radius": 10000,   # Entire universe is wild
                "debris_density": "low",
                "bandit_encounters": "low",
                "empty_chunk_probability": 0.9,  # 90% empty chunks
            }
        }
        
        return configs.get(universe_type, configs[UniverseType.REALISTIC])
    
    @staticmethod
    def get_all_types() -> Dict[UniverseType, Dict[str, str]]:
        """Get all universe types with their display information."""
        return {
            universe_type: {
                "name": UniverseConfig.get_config(universe_type)["name"],
                "description": UniverseConfig.get_config(universe_type)["description"]
            }
            for universe_type in UniverseType
        }


class UniverseGenerator:
    """Handles universe generation based on selected type."""
    
    def __init__(self, universe_type: UniverseType = UniverseType.REALISTIC):
        self.universe_type = universe_type
        self.config = UniverseConfig.get_config(universe_type)
    
    def set_universe_type(self, universe_type: UniverseType):
        """Change the universe generation type."""
        self.universe_type = universe_type
        self.config = UniverseConfig.get_config(universe_type)
    
    def should_generate_chunk(self, chunk_x: int, chunk_y: int, distance_from_origin: float) -> bool:
        """Determine if a chunk should have any content."""
        # Always generate the origin area, regardless of empty-chunk odds
        if distance_from_origin < 1000:
            return True

        # Otherwise roll against the universe type's empty chunk probability
        return random.random() >= self.config["empty_chunk_probability"]
    
    def get_station_generation_params(self, chunk_x: int, chunk_y: int, distance_from_origin: float) -> Tuple[int, int, float]:
        """Get station generation parameters for a chunk."""
        # Check if we're in a special area
        civilized_radius = self.config["civilized_space_radius"]
        frontier_radius = self.config["frontier_space_radius"]
        
        base_probability = self.config["station_probability"]
        station_range = self.config["stations_per_chunk"]
        
        # Modify based on distance from origin
        if civilized_radius > 0 and distance_from_origin <= civilized_radius:
            # Civilized space - higher station density
            probability = base_probability * 2.0
        elif frontier_radius > 0 and distance_from_origin <= frontier_radius:
            # Frontier space - normal density
            probability = base_probability
        else:
            # Wild space - lower density
            probability = base_probability * 0.3
        
        return station_range[0], station_range[1], probability
    
    def get_planet_generation_params(self, chunk_x: int, chunk_y: int, distance_from_origin: float) -> Tuple[int, int, float]:
        """Get planet generation parameters for a chunk."""
        base_probability = self.config["planet_probability"]
        planet_range = self.config["planets_per_chunk"]
        
        # Planets are less affected by civilization distance
        return planet_range[0], planet_range[1], base_probability
    
    def should_generate_star_system(self, chunk_x: int, chunk_y: int) -> bool:
        """Check if this chunk should contain a star system."""
        if not self.config.get("star_system_mode", False):
            return False
        
        return random.random() < self.config["system_probability"]
    
    def generate_star_system(self, chunk_start_x: int, chunk_start_y: int, chunk_size: int) -> Tuple[list, list]:
        """Generate a complete star system with planets and stations."""
        # Place star at center of chunk
        star_x = chunk_start_x + chunk_size // 2
        star_y = chunk_start_y + chunk_size // 2
        star_pos = Vector2(star_x, star_y)
        
        planets = []
        stations = []
        
        # Generate planets in orbits around the star
        planet_range = self.config["planets_per_system"]
        num_planets = random.randint(planet_range[0], planet_range[1])
        
        for i in range(num_planets):
            # Place planets in orbital rings
            orbit_radius = 100 + (i * 80)  # Increasing orbital distance
            orbit_angle = random.uniform(0, 360)
            
            planet_x = star_x + orbit_radius * math.cos(math.radians(orbit_angle))
            planet_y = star_y + orbit_radius * math.sin(math.radians(orbit_angle))
            
            # Keep planets within chunk bounds
            planet_x = max(chunk_start_x + 50, min(chunk_start_x + chunk_size - 50, planet_x))
            planet_y = max(chunk_start_y + 50, min(chunk_start_y + chunk_size - 50, planet_y))
            
            planets.append(Vector2(planet_x, planet_y))
        
        # Generate stations - some orbiting planets, some at system edge
        station_range = self.config["stations_per_system"]
        num_stations = random.randint(station_range[0], station_range[1])
        
        for i in range(num_stations):
            if len(planets) > 0 and random.random() < 0.6:
                # Station orbiting a planet
                planet_pos = random.choice(planets)
                station_orbit = 30 + random.uniform(-10, 10)
                station_angle = random.uniform(0, 360)
                
                station_x = planet_pos.x + station_orbit * math.cos(math.radians(station_angle))
                station_y = planet_pos.y + station_orbit * math.sin(math.radians(station_angle))
            else:
                # Station at system edge or asteroid belt
                belt_radius = 200 + random.uniform(-50, 100)
                belt_angle = random.uniform(0, 360)
                
                station_x = star_x + belt_radius * math.cos(math.radians(belt_angle))
                station_y = star_y + belt_radius * math.sin(math.radians(belt_angle))
            
            # Keep stations within chunk bounds
            station_x = max(chunk_start_x + 50, min(chunk_start_x + chunk_size - 50, station_x))
            station_y = max(chunk_start_y + 50, min(chunk_start_y + chunk_size - 50, station_y))
            
            stations.append(Vector2(station_x, station_y))
        
        return stations, planets
    
    def get_debris_density_modifier(self, distance_from_origin: float) -> float:
        """Get debris density modifier based on universe type and distance."""
        density_type = self.config["debris_density"]
        
        if density_type == "low":
            return 0.3
        elif density_type == "high":
            return 2.0
        else:  # normal
            return 1.0
    
    def get_bandit_encounter_modifier(self, distance_from_origin: float) -> float:
        """Get bandit encounter modifier based on universe type and distance."""
        encounter_type = self.config["bandit_encounters"]
        civilized_radius = self.config["civilized_space_radius"]
        
        base_modifier = 1.0
        if encounter_type == "low":
            base_modifier = 0.3
        elif encounter_type == "high":
            base_modifier = 2.0
        
        # Reduce bandits in civilized space
        if civilized_radius > 0 and distance_from_origin <= civilized_radius:
            base_modifier *= 0.2
        
        return base_modifier


# Global universe generator instance
universe_generator = UniverseGenerator()