import pytest
from src.entities.station import Station, StationType
from pygame import Vector2
import random

def test_station_initialization():
    station = Station(100, 200)
    assert station.position == Vector2(100, 200)
    assert station.station_type in StationType
    assert station.size > 0
    assert station.name is not None
    assert station.collision_radius == station.size

def test_station_type_colors():
    station = Station(0, 0)
    assert station.color == Station.STATION_COLORS[station.station_type]

def test_station_size_ranges():
    # Test multiple stations to ensure sizes are within expected ranges
    for _ in range(10):
        station = Station(0, 0)
        if station.station_type == StationType.TRADING:
            assert 30 <= station.size <= 40
        elif station.station_type == StationType.MILITARY:
            assert 40 <= station.size <= 50
        elif station.station_type == StationType.MINING:
            assert 35 <= station.size <= 45
        elif station.station_type == StationType.RESEARCH:
            assert 25 <= station.size <= 35
        elif station.station_type == StationType.SHIPYARD:
            assert 45 <= station.size <= 55

def test_station_name_generation():
    station = Station(0, 0)
    assert "-" in station.name
    assert any(char.isdigit() for char in station.name)

def test_station_shape_generation():
    station = Station(0, 0)
    assert len(station.shape_points) > 0
    
    # Test specific shapes for different types
    if station.station_type == StationType.TRADING:
        assert len(station.shape_points) == 8  # Octagon
    elif station.station_type == StationType.MILITARY:
        assert len(station.shape_points) == 3  # Triangle
    else:
        assert len(station.shape_points) == 4  # Rectangle

def test_station_rotation():
    station = Station(0, 0)
    initial_rotation = station.rotation
    # Rotation speed should be within expected range
    assert -1 <= station.rotation_speed <= 1