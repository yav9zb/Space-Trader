"""Combat manager to handle all combat-related interactions."""

import pygame
import random
from pygame import Vector2
from typing import List, Tuple, Optional

try:
    from ..entities.asteroid import Asteroid, AsteroidType
    from ..entities.bandit import BanditShip, BanditState
    from ..entities.black_hole import BlackHole
    from ..systems.respawn_system import respawn_system
    from .weapons import WeaponSystem
except ImportError:
    from entities.asteroid import Asteroid, AsteroidType
    from entities.bandit import BanditShip, BanditState
    from entities.black_hole import BlackHole
    from systems.respawn_system import respawn_system
    from weapons import WeaponSystem


class CombatManager:
    """Manages all combat interactions in the game."""
    
    def __init__(self):
        self.active_asteroids: List[Asteroid] = []
        self.active_bandits: List[BanditShip] = []
        self.active_black_holes: List[BlackHole] = []
        self.explosions: List[dict] = []
        
        # Combat statistics
        self.bandits_defeated = 0
        self.asteroids_destroyed = 0
        self.debris_destroyed = 0
        self.damage_dealt = 0.0
        self.damage_taken = 0.0
        
    def update(self, delta_time: float, game_engine):
        """Update all combat entities and check interactions."""
        ship = game_engine.ship
        
        # Update respawn system
        respawn_system.update(delta_time, game_engine)
        
        # Skip combat updates if respawning
        if respawn_system.is_respawning():
            return
        
        # Update asteroids
        for asteroid in self.active_asteroids[:]:
            asteroid.update(delta_time)
            self._check_asteroid_interactions(asteroid, ship, delta_time)
        
        # Update black holes
        for black_hole in self.active_black_holes[:]:
            black_hole.update(delta_time)
            self._check_black_hole_interactions(black_hole, ship, delta_time)
        
        # Update bandits
        for bandit in self.active_bandits[:]:
            if bandit.state != BanditState.DISABLED:
                bandit.update(delta_time, ship, game_engine)
                self._check_bandit_combat(bandit, ship, game_engine)
                # Check hazard damage for bandits
                self._check_bandit_hazard_damage(bandit, delta_time)
        
        # Update explosions
        self._update_explosions(delta_time)
        
        # Check player weapon hits
        if hasattr(ship, 'weapon_system'):
            self._check_player_weapon_hits(ship.weapon_system, game_engine)
        
        # Check if ship hull is depleted
        if ship.current_hull <= 0:
            respawn_system.handle_ship_destruction(game_engine)
    
    def _check_asteroid_interactions(self, asteroid: Asteroid, ship, delta_time: float):
        """Check asteroid interactions with the ship."""
        if asteroid.destroyed:
            # Remove destroyed asteroids
            if asteroid in self.active_asteroids:
                self.active_asteroids.remove(asteroid)
            return
            
        # Check collision damage
        collision_damage = asteroid.check_ship_collision(ship)
        if collision_damage > 0:
            ship.take_damage(collision_damage)
            self.damage_taken += collision_damage
            # Also damage the asteroid from collision
            asteroid.take_damage(collision_damage * 0.5)
            
        if asteroid.asteroid_type == AsteroidType.RADIOACTIVE:
            # Apply radiation damage
            radiation_damage = asteroid.check_radiation_damage(ship)
            if radiation_damage > 0:
                actual_damage = radiation_damage * delta_time
                ship.take_damage(actual_damage)
                self.damage_taken += actual_damage
                
        elif asteroid.asteroid_type == AsteroidType.EXPLOSIVE:
            # Check for explosion trigger
            if asteroid.check_explosion_trigger(ship):
                self._create_explosion(asteroid.position, asteroid.explosion_radius)
                explosion_damage = asteroid.get_explosion_damage(ship.position)
                if explosion_damage > 0:
                    ship.take_damage(explosion_damage)
                    self.damage_taken += explosion_damage
                
                # Remove exploded asteroid
                if asteroid in self.active_asteroids:
                    self.active_asteroids.remove(asteroid)
    
    def _check_black_hole_interactions(self, black_hole: BlackHole, ship, delta_time: float):
        """Check black hole interactions with the ship."""
        # Apply gravitational force
        gravity_force = black_hole.apply_gravity_to_ship(ship)
        ship.velocity += gravity_force * delta_time / ship.mass
    
    def _check_bandit_hazard_damage(self, bandit: BanditShip, delta_time: float):
        """Check if bandit takes damage from hazards."""
        # Check asteroid collisions and damage
        for asteroid in self.active_asteroids[:]:
            if asteroid.destroyed:
                continue
                
            # Check collision damage
            collision_damage = asteroid.check_ship_collision(bandit)
            if collision_damage > 0:
                bandit.take_damage(collision_damage)
                # Also damage the asteroid from collision
                asteroid.take_damage(collision_damage * 0.5)
                
            # Check radiation damage for radioactive asteroids
            if asteroid.asteroid_type == AsteroidType.RADIOACTIVE:
                radiation_damage = asteroid.check_radiation_damage(bandit)
                if radiation_damage > 0:
                    actual_damage = radiation_damage * delta_time
                    bandit.take_damage(actual_damage)
                    
            # Check explosion trigger for explosive asteroids
            elif asteroid.asteroid_type == AsteroidType.EXPLOSIVE:
                if asteroid.check_explosion_trigger(bandit):
                    self._create_explosion(asteroid.position, asteroid.explosion_radius)
                    explosion_damage = asteroid.get_explosion_damage(bandit.position)
                    if explosion_damage > 0:
                        bandit.take_damage(explosion_damage)
                    
                    # Remove exploded asteroid
                    if asteroid in self.active_asteroids:
                        self.active_asteroids.remove(asteroid)
        
        # Check black hole damage
        for black_hole in self.active_black_holes[:]:
            # Apply gravitational force to bandit
            gravity_force = black_hole.apply_gravity_to_bandit(bandit)
            bandit.velocity += gravity_force * delta_time / bandit.mass
            
            # Apply black hole damage
            black_hole_damage = black_hole.check_ship_damage(bandit)
            if black_hole_damage > 0:
                actual_damage = black_hole_damage * delta_time
                bandit.take_damage(actual_damage)
    
    def _check_bandit_combat(self, bandit: BanditShip, ship, game_engine):
        """Check bandit combat interactions."""
        # Check bandit weapon hits on player
        hits = bandit.weapon_system.check_hits([ship])
        for projectile, target in hits:
            damage = projectile.damage
            ship.take_damage(damage)
            self.damage_taken += damage
            
        # Check collisions between bandit and ship
        distance = (bandit.position - ship.position).length()
        collision_distance = bandit.size + ship.size + 10
        
        if distance <= collision_distance:
            # Apply collision damage to both
            collision_damage = 20.0
            ship.take_damage(collision_damage)
            bandit.take_damage(collision_damage)
            self.damage_taken += collision_damage
            
            # Separate ships
            separation_vec = (ship.position - bandit.position).normalize()
            ship.position += separation_vec * (collision_distance - distance) * 0.6
            bandit.position -= separation_vec * (collision_distance - distance) * 0.4
            
            # Apply velocity changes
            ship.velocity += separation_vec * 100
            bandit.velocity -= separation_vec * 50
    
    def _check_player_weapon_hits(self, weapon_system: WeaponSystem, game_engine):
        """Check player weapon hits on bandits and asteroids."""
        # Check hits on bandits
        hits = weapon_system.check_hits(self.active_bandits)
        for projectile, bandit in hits:
            damage = projectile.damage
            destroyed = bandit.take_damage(damage)
            self.damage_dealt += damage
            
            if destroyed:
                self._handle_bandit_destroyed(bandit, game_engine.ship)
        
        # Check hits on asteroids
        alive_asteroids = [a for a in self.active_asteroids if not a.destroyed]
        hits = weapon_system.check_hits(alive_asteroids)
        for projectile, asteroid in hits:
            damage = projectile.damage
            destroyed = asteroid.take_damage(damage)
            self.damage_dealt += damage
            
            if destroyed:
                self.asteroids_destroyed += 1
                # Create small explosion effect
                self._create_explosion(asteroid.position, asteroid.size)
                
                # Special handling for explosive asteroids
                if asteroid.asteroid_type == AsteroidType.EXPLOSIVE:
                    # Trigger larger explosion
                    self._apply_explosion_damage(asteroid.position, asteroid.explosion_radius, 
                                               asteroid.explosion_damage, game_engine)
        
        # Check hits on debris
        from ..systems.debris_field_manager import debris_field_manager
        nearby_debris = debris_field_manager.get_debris_at_position(
            game_engine.ship.position, 1000  # Check within 1000 units of ship
        )
        
        hits = weapon_system.check_hits(nearby_debris)
        for projectile, debris in hits:
            damage = projectile.damage
            destroyed = debris.take_damage(damage)
            self.damage_dealt += damage
            
            if destroyed:
                self.debris_destroyed += 1
                # Create small explosion effect
                self._create_explosion(debris.position, debris.size * 0.5)
                
                # Create fragments for larger debris
                if debris.size > 15:
                    fragments = debris.fragment(2)
                    for fragment in fragments:
                        debris_field_manager.add_debris(fragment)
                
                # Remove destroyed debris
                debris_field_manager.remove_debris(debris)
    
    def _handle_bandit_destroyed(self, bandit: BanditShip, player_ship):
        """Handle when a bandit is destroyed."""
        self.bandits_defeated += 1
        
        # Award credits to player
        player_ship.credits += bandit.credits_reward
        
        # Create explosion effect
        self._create_explosion(bandit.position, bandit.base_size * 2)
        
        # Chance to drop loot (could be implemented later)
        # self._create_loot_drop(bandit.position)
    
    def _create_explosion(self, position: Vector2, radius: float):
        """Create an explosion effect."""
        explosion = {
            "position": Vector2(position),
            "radius": radius,
            "max_radius": radius,
            "age": 0.0,
            "duration": 1.0,  # Explosion lasts 1 second
            "color": (255, 150, 0)
        }
        self.explosions.append(explosion)
    
    def _apply_explosion_damage(self, explosion_pos: Vector2, explosion_radius: float, 
                               base_damage: float, game_engine):
        """Apply explosion damage to all entities in range."""
        # Damage player ship
        ship = game_engine.ship
        distance_to_ship = (explosion_pos - ship.position).length()
        if distance_to_ship <= explosion_radius:
            damage_factor = 1.0 - (distance_to_ship / explosion_radius)
            damage = base_damage * damage_factor
            ship.take_damage(damage)
            self.damage_taken += damage
        
        # Damage bandits
        for bandit in self.active_bandits:
            if bandit.state == BanditState.DISABLED:
                continue
                
            distance_to_bandit = (explosion_pos - bandit.position).length()
            if distance_to_bandit <= explosion_radius:
                damage_factor = 1.0 - (distance_to_bandit / explosion_radius)
                damage = base_damage * damage_factor
                destroyed = bandit.take_damage(damage)
                
                if destroyed:
                    self._handle_bandit_destroyed(bandit, game_engine.ship)
    
    def _update_explosions(self, delta_time: float):
        """Update explosion animations."""
        for explosion in self.explosions[:]:
            explosion["age"] += delta_time
            
            # Expand explosion
            progress = explosion["age"] / explosion["duration"]
            if progress < 0.5:
                # Expanding phase
                explosion["radius"] = explosion["max_radius"] * (progress * 2)
            else:
                # Fading phase
                explosion["radius"] = explosion["max_radius"] * (2 - progress * 2)
            
            # Remove expired explosions
            if explosion["age"] >= explosion["duration"]:
                self.explosions.remove(explosion)
    
    def add_asteroid(self, asteroid: Asteroid):
        """Add an asteroid to combat tracking."""
        self.active_asteroids.append(asteroid)
    
    def add_bandit(self, bandit: BanditShip):
        """Add a bandit to combat tracking."""
        self.active_bandits.append(bandit)
    
    def add_black_hole(self, black_hole: BlackHole):
        """Add a black hole to combat tracking."""
        self.active_black_holes.append(black_hole)
    
    def remove_asteroid(self, asteroid: Asteroid):
        """Remove an asteroid from combat tracking."""
        if asteroid in self.active_asteroids:
            self.active_asteroids.remove(asteroid)
    
    def remove_bandit(self, bandit: BanditShip):
        """Remove a bandit from combat tracking."""
        if bandit in self.active_bandits:
            self.active_bandits.remove(bandit)
    
    def remove_black_hole(self, black_hole: BlackHole):
        """Remove a black hole from combat tracking."""
        if black_hole in self.active_black_holes:
            self.active_black_holes.remove(black_hole)
    
    def draw_combat_effects(self, screen: pygame.Surface, camera_offset: Vector2):
        """Draw combat effects like explosions."""
        # Draw explosions
        for explosion in self.explosions:
            screen_pos = explosion["position"] - camera_offset
            radius = int(explosion["radius"])
            
            if radius > 0:
                # Draw explosion with fading effect
                age_factor = explosion["age"] / explosion["duration"]
                alpha = int(255 * (1.0 - age_factor))
                
                # Create explosion surface with alpha
                explosion_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                color = (*explosion["color"], alpha)
                pygame.draw.circle(explosion_surface, color, (radius, radius), radius)
                
                # Blit to screen
                screen.blit(explosion_surface, 
                          (screen_pos.x - radius, screen_pos.y - radius))
        
        # Draw respawn effects
        respawn_system.draw_effects(screen, camera_offset)
    
    def draw_entities(self, screen: pygame.Surface, camera_offset: Vector2):
        """Draw all combat entities."""
        # Draw black holes first (background)
        for black_hole in self.active_black_holes:
            black_hole.draw(screen, camera_offset)
            
        # Draw asteroids
        for asteroid in self.active_asteroids:
            asteroid.draw(screen, camera_offset)
        
        # Draw bandits
        for bandit in self.active_bandits:
            bandit.draw(screen, camera_offset)
    
    def get_nearby_threats(self, position: Vector2, radius: float) -> dict:
        """Get information about nearby threats."""
        threats = {
            "asteroids": [],
            "bandits": [],
            "black_holes": [],
            "total_count": 0
        }
        
        # Check asteroids
        for asteroid in self.active_asteroids:
            distance = (asteroid.position - position).length()
            if distance <= radius:
                threats["asteroids"].append({
                    "type": asteroid.asteroid_type.value,
                    "distance": distance,
                    "position": asteroid.position
                })
        
        # Check bandits
        for bandit in self.active_bandits:
            if bandit.state == BanditState.DISABLED:
                continue
                
            distance = (bandit.position - position).length()
            if distance <= radius:
                threats["bandits"].append({
                    "type": bandit.bandit_type.value,
                    "state": bandit.state.value,
                    "distance": distance,
                    "position": bandit.position,
                    "hull_percentage": bandit.current_hull / bandit.max_hull
                })
        
        # Check black holes
        for black_hole in self.active_black_holes:
            distance = (black_hole.position - position).length()
            if distance <= radius:
                threats["black_holes"].append({
                    "threat_level": black_hole.get_threat_level(position),
                    "distance": distance,
                    "position": black_hole.position,
                    "size": black_hole.size
                })
        
        threats["total_count"] = (len(threats["asteroids"]) + 
                                len(threats["bandits"]) + 
                                len(threats["black_holes"]))
        return threats
    
    def get_combat_stats(self) -> dict:
        """Get combat statistics."""
        active_bandit_count = sum(1 for b in self.active_bandits if b.state != BanditState.DISABLED)
        active_asteroid_count = sum(1 for a in self.active_asteroids if not a.destroyed)
        
        return {
            "bandits_defeated": self.bandits_defeated,
            "asteroids_destroyed": self.asteroids_destroyed,
            "debris_destroyed": self.debris_destroyed,
            "active_bandits": active_bandit_count,
            "active_asteroids": active_asteroid_count,
            "active_black_holes": len(self.active_black_holes),
            "active_explosions": len(self.explosions),
            "damage_dealt": self.damage_dealt,
            "damage_taken": self.damage_taken
        }
    
    def clear_all(self):
        """Clear all combat entities (for game reset)."""
        self.active_asteroids.clear()
        self.active_bandits.clear()
        self.active_black_holes.clear()
        self.explosions.clear()
        
        # Reset stats
        self.bandits_defeated = 0
        self.asteroids_destroyed = 0
        self.debris_destroyed = 0
        self.damage_dealt = 0.0
        self.damage_taken = 0.0


# Global combat manager instance
combat_manager = CombatManager()