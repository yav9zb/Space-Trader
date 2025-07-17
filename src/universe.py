import random
from pygame import Vector2
from .entities.station import Station
from .entities.planet import Planet
from .entities.debris import Debris

class Universe:
    def __init__(self, width=10000, height=10000, seed=None):
        self.width = width
        self.height = height
        self.sectors = {}  # Grid-based sector system
        self.sector_size = 1000  # Size of each sector
        self.generated_chunks = set()  # Track which chunks have been generated
        
        # World seed for deterministic generation
        if seed is None:
            seed = random.randint(0, 2**31 - 1)
        self.world_seed = seed
        
        # Initialize containers
        self.stations = []
        self.planets = []
        self.debris = []
        
    def generate_universe(self):
        """Generate initial universe content - kept for backward compatibility"""
        # Generate initial area around spawn point
        self.generate_chunk_around_position(Vector2(500, 500))
        
    def _get_chunk_seed(self, chunk_x, chunk_y, layer=0):
        """Generate a deterministic seed for a specific chunk and generation layer"""
        # Combine world seed with chunk coordinates and layer for unique seeds
        seed_string = f"{self.world_seed}_{chunk_x}_{chunk_y}_{layer}"
        return hash(seed_string) & 0x7FFFFFFF  # Keep positive 32-bit integer
    
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
        
        # Keep track of placed objects to avoid overlapping
        placed_objects = []
        
        # Generate stations using layer 0 seed
        station_seed = self._get_chunk_seed(chunk_x, chunk_y, 0)
        random.seed(station_seed)
        num_stations = random.randint(1, 2)
        for _ in range(num_stations):
            pos = self._find_safe_position(chunk_start_x, chunk_start_y, self.sector_size, placed_objects, min_distance=100)
            if pos:
                station = Station(pos.x, pos.y)
                self.stations.append(station)
                placed_objects.append((pos, station.size))
            
        # Generate planets using layer 1 seed
        planet_seed = self._get_chunk_seed(chunk_x, chunk_y, 1)
        random.seed(planet_seed)
        num_planets = random.randint(0, 1)
        for _ in range(num_planets):
            pos = self._find_safe_position(chunk_start_x, chunk_start_y, self.sector_size, placed_objects, min_distance=150)
            if pos:
                planet = Planet(pos.x, pos.y)
                self.planets.append(planet)
                placed_objects.append((pos, planet.size))

        # Generate debris using layer 2 seed
        debris_seed = self._get_chunk_seed(chunk_x, chunk_y, 2)
        random.seed(debris_seed)
        num_debris = random.randint(10, 20)
        for _ in range(num_debris):
            pos = self._find_safe_position(chunk_start_x, chunk_start_y, self.sector_size, placed_objects, min_distance=20)
            if pos:
                debris = Debris(pos.x, pos.y)
                self.debris.append(debris)
                placed_objects.append((pos, debris.size))
        
    def _find_safe_position(self, chunk_start_x, chunk_start_y, chunk_size, placed_objects, min_distance=50, max_attempts=100):
        """Find a position that doesn't overlap with existing objects"""
        for _ in range(max_attempts):
            # Generate random position within chunk bounds with some padding
            padding = 50  # Keep objects away from chunk edges
            x = random.randint(chunk_start_x + padding, chunk_start_x + chunk_size - padding)
            y = random.randint(chunk_start_y + padding, chunk_start_y + chunk_size - padding)
            candidate_pos = Vector2(x, y)
            
            # Check if position is safe (doesn't overlap with existing objects)
            safe = True
            for existing_pos, existing_size in placed_objects:
                distance = (candidate_pos - existing_pos).length()
                required_distance = min_distance + existing_size
                
                if distance < required_distance:
                    safe = False
                    break
            
            if safe:
                return candidate_pos
        
        # If we couldn't find a safe position after max_attempts, return None
        return None
        
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