import pytest
from src.entities.planet import Planet, PlanetType
from pygame import Vector2
import random

def test_planet_initialization():
    planet = Planet(150, 250)
    assert planet.position == Vector2(150, 250)
    assert planet.planet_type in PlanetType
    assert planet.size > 0
    assert planet.name is not None
    assert planet.color is not None
    assert isinstance(planet.features, list)

def test_planet_type_colors():
    planet = Planet(0, 0)
    assert planet.color in Planet.PLANET_COLORS[planet.planet_type]

def test_planet_size_ranges():
    # Test multiple planets to ensure sizes are within expected ranges
    for _ in range(10):
        planet = Planet(0, 0)
        if planet.planet_type == PlanetType.TERRESTRIAL:
            assert 40 <= planet.size <= 60
        elif planet.planet_type == PlanetType.GAS_GIANT:
            assert 80 <= planet.size <= 120
        elif planet.planet_type == PlanetType.ICE_WORLD:
            assert 30 <= planet.size <= 50
        elif planet.planet_type == PlanetType.LAVA_WORLD:
            assert 35 <= planet.size <= 55
        elif planet.planet_type == PlanetType.DESERT_WORLD:
            assert 40 <= planet.size <= 65

def test_planet_name_generation():
    planet = Planet(0, 0)
    assert "-" in planet.name
    assert any(char.isdigit() for char in planet.name)

def test_planet_rotation():
    planet = Planet(0, 0)
    assert -0.5 <= planet.rotation_speed <= 0.5
    assert 0 <= planet.rotation <= 360

def test_terrestrial_planet_features():
    # Force a terrestrial planet by setting the type
    planet = Planet(0, 0)
    planet.planet_type = PlanetType.TERRESTRIAL
    planet._generate_features()
    
    # Check if continents were generated
    continent_features = [f for f in planet.features if f['type'] == 'continent']
    assert len(continent_features) >= 3
    assert len(continent_features) <= 7
    
    for feature in continent_features:
        assert 'color' in feature
        assert 'pos' in feature
        assert 'size' in feature
        assert 0.2 <= feature['size'] <= 0.4

def test_gas_giant_features():
    # Force a gas giant
    planet = Planet(0, 0)
    planet.planet_type = PlanetType.GAS_GIANT
    planet._generate_features()
    
    # Check if bands were generated
    band_features = [f for f in planet.features if f['type'] == 'band']
    assert len(band_features) >= 3
    assert len(band_features) <= 6
    
    for feature in band_features:
        assert 'color' in feature
        assert 'pos' in feature
        assert 'width' in feature
        assert 0.1 <= feature['width'] <= 0.3

def test_planet_feature_generation():
    planet = Planet(0, 0)
    if planet.planet_type in [PlanetType.TERRESTRIAL, PlanetType.GAS_GIANT]:
        assert len(planet.features) > 0
    # Ice and lava worlds don't have features in _generate_features method