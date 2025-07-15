import random
from pygame import Vector2
from .entities.station import Station
from .entities.planet import Planet
from .entities.debris import Debris

class Universe:
    def __init__(self, width=10000, height=10000):
        self.width = width
        self.height = height
        self.sectors = {}  # Grid-based sector system
        self.sector_size = 1000  # Size of each sector
        self.generated_chunks = set()  # Track which chunks have been generated
        
        # Initialize containers
        self.stations = []
        self.planets = []
        self.debris = []
        
    def generate_universe(self, num_stations=10, num_planets=5, num_debris=100):
        """Generate initial universe content - kept for backward compatibility"""
        # Generate initial area around spawn point
        self.generate_chunk_around_position(Vector2(500, 500))
        
    def generate_chunk_around_position(self, position):
        """Generate content for the chunk containing the given position"""
        chunk_x = int(position.x // self.sector_size)
        chunk_y = int(position.y // self.sector_size)
        chunk_key = (chunk_x, chunk_y)
        
        if chunk_key in self.generated_chunks:
            return  # Already generated
            
        self.generated_chunks.add(chunk_key)
        
        # Generate content for this chunk
        chunk_start_x = chunk_x * self.sector_size
        chunk_start_y = chunk_y * self.sector_size
        
        # Use chunk coordinates as seed for consistent generation
        random.seed(hash(chunk_key))
        
        # Generate 1-2 stations per chunk
        num_stations = random.randint(1, 2)
        for _ in range(num_stations):
            x = random.randint(chunk_start_x, chunk_start_x + self.sector_size)
            y = random.randint(chunk_start_y, chunk_start_y + self.sector_size)
            station = Station(x, y)
            self.stations.append(station)
            
        # Generate 0-1 planets per chunk
        num_planets = random.randint(0, 1)
        for _ in range(num_planets):
            x = random.randint(chunk_start_x, chunk_start_x + self.sector_size)
            y = random.randint(chunk_start_y, chunk_start_y + self.sector_size)
            planet = Planet(x, y)
            self.planets.append(planet)

        # Generate debris
        num_debris = random.randint(10, 20)
        for _ in range(num_debris):
            x = random.randint(chunk_start_x, chunk_start_x + self.sector_size)
            y = random.randint(chunk_start_y, chunk_start_y + self.sector_size)
            self.debris.append(Debris(x, y))
        
        # Reset random seed
        random.seed()
        
    def ensure_chunks_around_position(self, position, radius=2000):
        """Ensure chunks are generated around the given position"""
        chunk_x = int(position.x // self.sector_size)
        chunk_y = int(position.y // self.sector_size)
        chunk_radius = int(radius // self.sector_size) + 1
        
        for dx in range(-chunk_radius, chunk_radius + 1):
            for dy in range(-chunk_radius, chunk_radius + 1):
                chunk_pos = Vector2((chunk_x + dx) * self.sector_size + self.sector_size // 2,
                                   (chunk_y + dy) * self.sector_size + self.sector_size // 2)
                self.generate_chunk_around_position(chunk_pos)

    
    def update(self, delta_time):
        """Update all dynamic objects in the universe"""
        for debris in self.debris:
            debris.update(delta_time)
    
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