#!/usr/bin/env python3
"""Test script to verify weapon damage system is working correctly."""

import pygame
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import required modules
from pygame import Vector2

def test_weapon_damage():
    """Test that weapons can damage targets."""
    pygame.init()
    
    # Import here to avoid module loading issues
    from entities.ship import Ship
    from entities.asteroid import Asteroid, AsteroidType
    from entities.bandit import BanditShip, BanditType
    from combat.weapons import create_weapon, WeaponSystem
    
    # Create a ship with weapons
    ship = Ship(100, 100)
    
    # Create test targets closer to the ship
    asteroid = Asteroid(Vector2(150, 100), 30, AsteroidType.NORMAL)
    bandit = BanditShip(Vector2(200, 100), BanditType.SCOUT)
    
    print(f"Initial asteroid health: {asteroid.current_health}")
    print(f"Initial bandit health: {bandit.current_hull}")
    
    # Fire weapons directly at targets
    current_time = pygame.time.get_ticks() / 1000.0
    
    # Fire towards asteroid
    direction_to_asteroid = (asteroid.position - ship.position).normalize()
    ship.weapon_system.fire_weapons(ship.position, direction_to_asteroid, ship, current_time)
    
    # Fire towards bandit
    direction_to_bandit = (bandit.position - ship.position).normalize() 
    ship.weapon_system.fire_weapons(ship.position, direction_to_bandit, ship, current_time + 0.5)
    
    print(f"Projectiles created: {len(ship.weapon_system.projectiles)}")
    
    # Update projectiles for several frames to let them travel
    for i in range(20):
        ship.weapon_system.update(0.1)
        
        # Check for hits
        bandit_hits = ship.weapon_system.check_hits([bandit])
        asteroid_hits = ship.weapon_system.check_hits([asteroid])
        
        # Apply damage
        for projectile, target in bandit_hits:
            print(f"Bandit hit! Damage: {projectile.damage}")
            target.take_damage(projectile.damage)
        
        for projectile, target in asteroid_hits:
            print(f"Asteroid hit! Damage: {projectile.damage}")
            target.take_damage(projectile.damage)
    
    print(f"Final asteroid health: {asteroid.current_health}")
    print(f"Final bandit health: {bandit.current_hull}")
    
    # Test weapon system directly
    print("\nTesting basic weapon functionality...")
    weapon_system = WeaponSystem()
    basic_laser = create_weapon("basic_laser")
    weapon_system.add_weapon(basic_laser)
    
    # Fire weapon
    weapon_system.fire_weapons(Vector2(0, 0), Vector2(1, 0), ship, current_time + 2.0)
    print(f"Weapon system projectiles after firing: {len(weapon_system.projectiles)}")
    
    # Update weapon system
    weapon_system.update(0.1)
    print(f"Weapon system projectiles after update: {len(weapon_system.projectiles)}")
    
    pygame.quit()

if __name__ == "__main__":
    test_weapon_damage()