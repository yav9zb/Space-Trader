import random
from pygame import Vector2
from .entities.station import Station
from .entities.planet import Planet

class Universe:
    def __init__(self, width=10000, height=10000):
        self.width = width
        self.height = height
        self.sectors = {}  # Grid-based sector system
        self.sector_size = 1000  # Size of each sector
        
        # Initialize containers
        self.stations = []
        self.planets = []

        # Generate the universe immediately
        self.generate_universe()
        
    def generate_universe(self, num_stations=10, num_planets=5):
        """Generate the universe with stations and planets"""
        # Generate stations
        for _ in range(num_stations):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            station = Station(x, y)
            self.stations.append(station)
            
        # Generate planets
        for _ in range(num_planets):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            planet = Planet(x, y)
            self.planets.append(planet)
    
    def _add_station(self, x, y):
        """Add a station to the universe"""
        from .entities.station import Station
        station = Station(x, y)
        self.stations.append(station)
        self._add_to_sector(station)
    
    def _add_planet(self, x, y):
        """Add a planet to the universe"""
        from .entities.planet import Planet
        planet = Planet(x, y)
        self.planets.append(planet)
        self._add_to_sector(planet)
    
    def _add_to_sector(self, entity):
        """Add entity to appropriate sector for spatial partitioning"""
        sector_x = int(entity.position.x / self.sector_size)
        sector_y = int(entity.position.y / self.sector_size)
        sector_key = (sector_x, sector_y)
        
        if sector_key not in self.sectors:
            self.sectors[sector_key] = []
        self.sectors[sector_key].append(entity)
    
    def get_nearby_entities(self, position, radius):
        """Get all entities within a radius of a position"""
        nearby = []
        sector_x = int(position.x / self.sector_size)
        sector_y = int(position.y / self.sector_size)
        
        # Check surrounding sectors
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                sector_key = (sector_x + dx, sector_y + dy)
                if sector_key in self.sectors:
                    for entity in self.sectors[sector_key]:
                        dist = (entity.position - position).length()
                        if dist <= radius:
                            nearby.append(entity)
        
        return nearby