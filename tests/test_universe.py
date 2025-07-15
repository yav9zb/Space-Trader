import pytest
from src.universe import Universe
from src.entities.station import Station
from src.entities.planet import Planet
from src.entities.debris import Debris
from pygame import Vector2

def test_universe_initialization():
    universe = Universe()
    assert universe.width == 10000
    assert universe.height == 10000
    assert universe.sector_size == 1000
    assert isinstance(universe.sectors, dict)
    assert isinstance(universe.generated_chunks, set)
    assert isinstance(universe.stations, list)
    assert isinstance(universe.planets, list)
    assert isinstance(universe.debris, list)

def test_universe_custom_size():
    universe = Universe(5000, 8000)
    assert universe.width == 5000
    assert universe.height == 8000

def test_chunk_generation():
    universe = Universe()
    position = Vector2(500, 500)
    
    # Generate chunk
    universe.generate_chunk_around_position(position)
    
    # Check that chunk was marked as generated
    chunk_key = (0, 0)  # 500//1000 = 0
    assert chunk_key in universe.generated_chunks
    
    # Check that objects were created
    assert len(universe.stations) > 0
    assert len(universe.debris) > 0
    # Planets are optional (0-1 per chunk)

def test_chunk_generation_idempotent():
    universe = Universe()
    position = Vector2(500, 500)
    
    # Generate chunk twice
    universe.generate_chunk_around_position(position)
    initial_station_count = len(universe.stations)
    
    universe.generate_chunk_around_position(position)
    
    # Should not generate more objects in same chunk
    assert len(universe.stations) == initial_station_count

def test_multiple_chunk_generation():
    universe = Universe()
    
    # Generate different chunks
    universe.generate_chunk_around_position(Vector2(500, 500))    # Chunk (0,0)
    universe.generate_chunk_around_position(Vector2(1500, 1500))  # Chunk (1,1)
    
    assert len(universe.generated_chunks) == 2
    assert (0, 0) in universe.generated_chunks
    assert (1, 1) in universe.generated_chunks

def test_ensure_chunks_around_position():
    universe = Universe()
    position = Vector2(1500, 1500)
    
    # This should generate chunks around position
    universe.ensure_chunks_around_position(position, radius=1000)
    
    # Should have generated multiple chunks
    assert len(universe.generated_chunks) > 1
    
    # Should include the center chunk
    assert (1, 1) in universe.generated_chunks

def test_universe_update():
    universe = Universe()
    universe.generate_chunk_around_position(Vector2(500, 500))
    
    # Update should not crash
    universe.update(0.016)  # 60 FPS delta time

def test_add_station():
    universe = Universe()
    initial_count = len(universe.stations)
    
    universe._add_station(100, 200)
    
    assert len(universe.stations) == initial_count + 1
    assert universe.stations[-1].position == Vector2(100, 200)

def test_add_planet():
    universe = Universe()
    initial_count = len(universe.planets)
    
    universe._add_planet(300, 400)
    
    assert len(universe.planets) == initial_count + 1
    assert universe.planets[-1].position == Vector2(300, 400)

def test_add_to_sector():
    universe = Universe()
    station = Station(1500, 2500)  # Should be in sector (1, 2)
    
    universe._add_to_sector(station)
    
    assert (1, 2) in universe.sectors
    assert station in universe.sectors[(1, 2)]

def test_get_nearby_entities():
    universe = Universe()
    
    # Add a station manually
    station = Station(100, 100)
    universe.stations.append(station)
    universe._add_to_sector(station)
    
    # Search nearby
    nearby = universe.get_nearby_entities(Vector2(100, 100), 50)
    assert station in nearby
    
    # Search far away
    nearby = universe.get_nearby_entities(Vector2(1000, 1000), 50)
    assert station not in nearby

def test_generate_universe_backward_compatibility():
    universe = Universe()
    
    # This should work without errors
    universe.generate_universe()
    
    # Should have generated some content
    assert len(universe.stations) > 0 or len(universe.planets) > 0 or len(universe.debris) > 0