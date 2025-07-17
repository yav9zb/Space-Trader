"""Ship destruction and respawn system."""

import pygame
import random
from pygame import Vector2
from typing import Optional


class RespawnSystem:
    """Handles ship destruction and respawn mechanics."""
    
    def __init__(self):
        self.respawn_in_progress = False
        self.respawn_timer = 0.0
        self.respawn_delay = 3.0  # 3 seconds before respawn
        self.destruction_time = 0.0
        
        # Death effects
        self.explosion_particles = []
        self.destruction_sound_played = False
    
    def handle_ship_destruction(self, game_engine):
        """Handle when ship hull reaches 0."""
        if self.respawn_in_progress:
            return
            
        print("Ship destroyed! Respawning...")
        self.respawn_in_progress = True
        self.respawn_timer = 0.0
        self.destruction_time = pygame.time.get_ticks() / 1000.0
        
        # Create explosion effect at ship position
        self._create_destruction_effects(game_engine.ship.position)
        
        # Reset ship to safe state immediately
        self._reset_ship_to_safe_state(game_engine)
    
    def update(self, delta_time: float, game_engine):
        """Update respawn system."""
        if not self.respawn_in_progress:
            return
            
        self.respawn_timer += delta_time
        
        # Update destruction effects
        self._update_destruction_effects(delta_time)
        
        # Check if respawn should complete
        if self.respawn_timer >= self.respawn_delay:
            self._complete_respawn(game_engine)
    
    def _reset_ship_to_safe_state(self, game_engine):
        """Reset ship stats and position to safe starting state."""
        ship = game_engine.ship
        
        # Reset position to first station or safe spawn point
        if game_engine.universe.stations:
            first_station = game_engine.universe.stations[0]
            ship.position = Vector2(first_station.position.x + 150, first_station.position.y)
        else:
            ship.position = Vector2(500, 500)  # Default spawn
        
        # Stop all movement
        ship.velocity = Vector2(0, 0)
        ship.acceleration = Vector2(0, 0)
        
        # Reset rotation
        ship.rotation = 0
        ship.heading = Vector2(0, -1)
        
        # Reset hull to full
        effective_stats = ship.get_effective_stats()
        ship.current_hull = effective_stats.get_effective_hull_points()
        
        # Reset credits to starting amount (harsh penalty)
        ship.credits = 1000
        
        # Clear cargo hold (lose all cargo)
        ship.cargo_hold.clear()
        
        # Reset upgrades to basic level
        ship.upgrades.reset_upgrades()
        ship._update_cargo_capacity()  # Update capacity after upgrade reset
        
        # Reset weapon system to basic
        ship.weapon_system = None
        try:
            from ..combat.weapons import WeaponSystem, create_weapon
        except ImportError:
            from combat.weapons import WeaponSystem, create_weapon
        ship.weapon_system = WeaponSystem()
        basic_laser = create_weapon("basic_laser")
        ship.weapon_system.add_weapon(basic_laser)
        
        # Reset fuel to full capacity
        ship.current_fuel = ship.fuel_capacity
        
        # Reset emergency fuel system
        ship.emergency_fuel_active = False
        
        # Reset afterburner system
        ship.afterburner_active = False
        ship.afterburner_cooldown = 0.0
        
        # Reset ammo to starting amounts
        ship.ammo_storage = {
            "laser_cells": 50,
            "plasma_cartridges": 25,
            "missiles": 10,
            "railgun_slugs": 30
        }
        
        # Reset missions
        try:
            from ..missions.mission_manager import mission_manager
        except ImportError:
            from missions.mission_manager import mission_manager
        mission_manager.available_missions.clear()
        mission_manager.active_missions.clear()
        mission_manager.completed_missions.clear()
        mission_manager.failed_missions.clear()
        mission_manager.last_generation_time = 0
        mission_manager.initialize_missions(game_engine)
    
    def _create_destruction_effects(self, position: Vector2):
        """Create visual effects for ship destruction."""
        # Create explosion particles
        for _ in range(20):
            particle = {
                "position": Vector2(position),
                "velocity": Vector2(
                    (random.random() - 0.5) * 400,
                    (random.random() - 0.5) * 400
                ),
                "life": random.uniform(1.0, 2.5),
                "max_life": random.uniform(1.0, 2.5),
                "size": random.randint(2, 6),
                "color": random.choice([(255, 100, 0), (255, 150, 0), (255, 200, 100)])
            }
            self.explosion_particles.append(particle)
    
    def _update_destruction_effects(self, delta_time: float):
        """Update destruction visual effects."""
        # Update particles
        for particle in self.explosion_particles[:]:
            particle["position"] += particle["velocity"] * delta_time
            particle["velocity"] *= 0.95  # Slow down over time
            particle["life"] -= delta_time
            
            if particle["life"] <= 0:
                self.explosion_particles.remove(particle)
    
    def _complete_respawn(self, game_engine):
        """Complete the respawn process."""
        self.respawn_in_progress = False
        self.respawn_timer = 0.0
        self.explosion_particles.clear()
        self.destruction_sound_played = False
        
        print("Ship respawned! All progress reset.")
    
    def draw_effects(self, screen: pygame.Surface, camera_offset: Vector2):
        """Draw destruction effects."""
        if not self.respawn_in_progress:
            return
            
        # Draw explosion particles
        for particle in self.explosion_particles:
            screen_pos = particle["position"] - camera_offset
            alpha_factor = particle["life"] / particle["max_life"]
            
            # Fade out particle
            color = particle["color"]
            faded_color = (
                max(0, min(255, int(color[0] * alpha_factor))),
                max(0, min(255, int(color[1] * alpha_factor))),
                max(0, min(255, int(color[2] * alpha_factor)))
            )
            
            pygame.draw.circle(screen, faded_color, 
                             (int(screen_pos.x), int(screen_pos.y)), 
                             int(particle["size"] * alpha_factor))
    
    def draw_respawn_ui(self, screen: pygame.Surface):
        """Draw respawn countdown UI."""
        if not self.respawn_in_progress:
            return
            
        # Screen dimensions
        width, height = screen.get_size()
        
        # Semi-transparent overlay
        overlay = pygame.Surface((width, height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Death message
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 36)
        
        # "SHIP DESTROYED" message
        destroyed_text = font_large.render("SHIP DESTROYED", True, (255, 100, 100))
        destroyed_rect = destroyed_text.get_rect(center=(width // 2, height // 3))
        screen.blit(destroyed_text, destroyed_rect)
        
        # Respawn countdown
        time_remaining = max(0, self.respawn_delay - self.respawn_timer)
        if time_remaining > 0:
            countdown_text = font_medium.render(f"Respawning in {time_remaining:.1f}s", True, (255, 255, 255))
            countdown_rect = countdown_text.get_rect(center=(width // 2, height // 2))
            screen.blit(countdown_text, countdown_rect)
        
        # Penalty message
        penalty_lines = [
            "All progress lost:",
            "• Credits reset to 1,000",
            "• All upgrades removed", 
            "• Cargo lost",
            "• Fuel and ammo restored",
            "• Missions reset"
        ]
        
        y_offset = height // 2 + 60
        for line in penalty_lines:
            penalty_text = font_small.render(line, True, (255, 200, 200))
            penalty_rect = penalty_text.get_rect(center=(width // 2, y_offset))
            screen.blit(penalty_text, penalty_rect)
            y_offset += 35
    
    def is_respawning(self) -> bool:
        """Check if currently in respawn process."""
        return self.respawn_in_progress


# Global respawn system instance
respawn_system = RespawnSystem()