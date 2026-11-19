"""Cloaking system for ship stealth mechanics."""

import pygame
import math
from pygame import Vector2


class CloakingSystem:
    """Manages ship cloaking mechanics."""
    
    def __init__(self):
        self.is_cloaked = False
        self.cloak_time_remaining = 0.0
        self.cloak_cooldown_remaining = 0.0
        self.cloak_activation_time = 0.0
        
        # Visual effects
        self.shimmer_timer = 0.0
        self.cloak_alpha = 255  # Ship opacity when cloaked
        
    def can_activate_cloak(self, ship_stats) -> bool:
        """Check if cloak can be activated."""
        return (not self.is_cloaked and 
                self.cloak_cooldown_remaining <= 0 and 
                ship_stats.cloak_effectiveness > 0)
    
    def activate_cloak(self, ship_stats):
        """Activate cloaking device."""
        if not self.can_activate_cloak(ship_stats):
            return False
            
        self.is_cloaked = True
        self.cloak_time_remaining = ship_stats.cloak_duration
        self.cloak_activation_time = pygame.time.get_ticks() / 1000.0
        self.shimmer_timer = 0.0

        from ..audio.sound_manager import sound_manager
        sound_manager.play("cloak")

        print(f"Cloaking activated! Duration: {ship_stats.cloak_duration:.1f}s")
        return True
    
    def deactivate_cloak(self, ship_stats):
        """Deactivate cloaking device."""
        if not self.is_cloaked:
            return
            
        self.is_cloaked = False
        self.cloak_time_remaining = 0.0
        self.cloak_cooldown_remaining = ship_stats.cloak_cooldown
        self.cloak_alpha = 255
        
        print(f"Cloaking deactivated! Cooldown: {ship_stats.cloak_cooldown:.1f}s")
    
    def update(self, delta_time: float, ship_stats):
        """Update cloaking system."""
        # Update cooldown
        if self.cloak_cooldown_remaining > 0:
            self.cloak_cooldown_remaining -= delta_time
            if self.cloak_cooldown_remaining <= 0:
                self.cloak_cooldown_remaining = 0.0
        
        # Update active cloak
        if self.is_cloaked:
            self.cloak_time_remaining -= delta_time
            self.shimmer_timer += delta_time
            
            # Update visual opacity based on effectiveness
            base_alpha = 255 * (1.0 - ship_stats.cloak_effectiveness)
            shimmer = math.sin(self.shimmer_timer * 8) * 20
            self.cloak_alpha = max(0, min(255, base_alpha + shimmer))
            
            # Check if cloak expires
            if self.cloak_time_remaining <= 0:
                self.deactivate_cloak(ship_stats)
    
    def handle_input(self, event, ship_stats):
        """Handle cloaking input."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
            if self.is_cloaked:
                self.deactivate_cloak(ship_stats)
            else:
                self.activate_cloak(ship_stats)
    
    def get_detection_multiplier(self, ship_stats) -> float:
        """Get how detectable the ship is (1.0 = fully visible, 0.0 = invisible)."""
        if not self.is_cloaked:
            return 1.0
        return 1.0 - ship_stats.cloak_effectiveness
    
    def should_draw_ship(self, ship_stats) -> bool:
        """Check if ship should be drawn (for player visibility)."""
        if not self.is_cloaked:
            return True
        # Always draw for player, but with reduced alpha
        return True
    
    def get_ship_alpha(self, ship_stats) -> int:
        """Get ship drawing alpha value."""
        if not self.is_cloaked:
            return 255
        return int(self.cloak_alpha)
    
    def is_detected_by_enemy(self, ship_stats, enemy_distance: float) -> bool:
        """Check if ship is detected by an enemy at given distance."""
        if not self.is_cloaked:
            return True
            
        detection_multiplier = self.get_detection_multiplier(ship_stats)
        
        # Closer enemies can detect cloaked ships more easily
        distance_factor = max(0.1, min(1.0, enemy_distance / 500.0))
        detection_chance = detection_multiplier * distance_factor
        
        # Add some randomness
        import random
        return random.random() < detection_chance
    
    def break_cloak_from_action(self, ship_stats, action_type: str):
        """Break cloak due to aggressive actions."""
        if not self.is_cloaked:
            return
            
        # Different actions have different chances to break cloak
        break_chances = {
            "firing": 0.8,  # 80% chance firing breaks cloak
            "collision": 1.0,  # 100% chance collision breaks cloak
            "taking_damage": 0.6  # 60% chance taking damage breaks cloak
        }
        
        break_chance = break_chances.get(action_type, 0.0)
        
        import random
        if random.random() < break_chance:
            self.deactivate_cloak(ship_stats)
            print(f"Cloak disrupted by {action_type}!")
    
    def get_status_info(self, ship_stats) -> dict:
        """Get cloaking system status information."""
        return {
            "is_cloaked": self.is_cloaked,
            "can_activate": self.can_activate_cloak(ship_stats),
            "time_remaining": self.cloak_time_remaining,
            "cooldown_remaining": self.cloak_cooldown_remaining,
            "effectiveness": ship_stats.cloak_effectiveness,
            "max_duration": ship_stats.cloak_duration,
            "max_cooldown": ship_stats.cloak_cooldown
        }
    
    def draw_cloak_effects(self, screen: pygame.Surface, ship_position: Vector2, camera_offset: Vector2):
        """Cloaking: expanding ripples, a pulsing glow and bent-light flecks
        around the (faint) ship."""
        if not self.is_cloaked:
            return
        from ..ui import gfx

        screen_pos = ship_position - camera_offset
        t = self.shimmer_timer

        # A cool pulsing glow where the ship is
        pulse = 0.5 + 0.5 * math.sin(t * 5)
        gfx.draw_glow(screen, screen_pos, 34, (70, 140, 255), 0.25 + 0.2 * pulse)

        # Two ripples spreading outward and fading, half a cycle apart
        for offset in (0.0, 0.5):
            phase = (t * 0.9 + offset) % 1.0
            gfx.draw_ring_glow(screen, screen_pos, 10 + 34 * phase, 3, (110, 180, 255), 0.8 * (1 - phase))

        # Flecks of bent light orbiting the hull
        for i in range(5):
            angle = math.radians((t * 70 + i * 72) % 360)
            radius = 20 + 5 * math.sin(t * 3 + i)
            at = (screen_pos.x + math.cos(angle) * radius, screen_pos.y + math.sin(angle) * radius)
            gfx.draw_glow(screen, at, 6, (170, 215, 255), 0.7)


# Global cloaking system instance
cloaking_system = CloakingSystem()