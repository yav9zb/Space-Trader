"""Ship repair system and mechanics."""

import pygame
from pygame import Vector2
from typing import Optional


class RepairSystem:
    """Manages ship repair mechanics."""
    
    def __init__(self):
        self.repair_in_progress = False
        self.repair_timer = 0.0
        self.repair_duration = 3.0  # 3 seconds to complete repair
        self.auto_repair_rate = 0.5  # Hull points per second when docked
        
        # Repair costs
        self.repair_cost_per_hull = 10  # Credits per hull point
        self.emergency_repair_multiplier = 3.0  # Emergency repairs cost 3x more
        
    def can_repair_at_station(self, ship, station) -> bool:
        """Check if ship can repair at this station."""
        # Check if ship needs repair
        if ship.current_hull >= ship.get_effective_stats().get_effective_hull_points():
            return False
            
        # Check if station offers repair services
        return self._station_has_repair_service(station)
    
    def _station_has_repair_service(self, station) -> bool:
        """Check if station has repair facilities."""
        # All stations have basic repair, but some have better services
        return True
    
    def get_repair_cost(self, ship, repair_type: str = "full") -> int:
        """Calculate repair cost."""
        effective_stats = ship.get_effective_stats()
        max_hull = effective_stats.get_effective_hull_points()
        damage = max_hull - ship.current_hull
        
        if damage <= 0:
            return 0
            
        base_cost = int(damage * self.repair_cost_per_hull)
        
        if repair_type == "emergency":
            return int(base_cost * self.emergency_repair_multiplier)
        else:
            return base_cost
    
    def can_afford_repair(self, ship, repair_type: str = "full") -> bool:
        """Check if player can afford repair."""
        cost = self.get_repair_cost(ship, repair_type)
        return ship.credits >= cost
    
    def start_repair(self, ship, repair_type: str = "full") -> bool:
        """Start ship repair process."""
        if self.repair_in_progress:
            return False
            
        cost = self.get_repair_cost(ship, repair_type)
        if not self.can_afford_repair(ship, repair_type):
            print(f"Cannot afford repair: {cost} credits required, {ship.credits} available")
            return False
        
        # Deduct credits
        ship.credits -= cost
        self.repair_in_progress = True
        self.repair_timer = 0.0
        
        if repair_type == "emergency":
            self.repair_duration = 1.0  # Emergency repairs are faster
        else:
            self.repair_duration = 3.0
        
        print(f"Repair started! Cost: {cost} credits")
        return True
    
    def instant_repair(self, ship, repair_type: str = "full") -> bool:
        """Instantly repair ship (for emergency or station services)."""
        cost = self.get_repair_cost(ship, repair_type)
        if not self.can_afford_repair(ship, repair_type):
            return False
        
        # Deduct credits and repair
        ship.credits -= cost
        effective_stats = ship.get_effective_stats()
        ship.current_hull = effective_stats.get_effective_hull_points()
        
        print(f"Ship fully repaired! Cost: {cost} credits")
        return True
    
    def update(self, delta_time: float, ship, is_docked: bool = False):
        """Update repair system."""
        # Handle active repair
        if self.repair_in_progress:
            self.repair_timer += delta_time
            
            if self.repair_timer >= self.repair_duration:
                self._complete_repair(ship)
        
        # Auto-repair when docked (slow but free)
        elif is_docked and ship.current_hull < ship.get_effective_stats().get_effective_hull_points():
            self._auto_repair(ship, delta_time)
    
    def _complete_repair(self, ship):
        """Complete the repair process."""
        effective_stats = ship.get_effective_stats()
        ship.current_hull = effective_stats.get_effective_hull_points()
        self.repair_in_progress = False
        self.repair_timer = 0.0
        
        print("Repair completed!")
    
    def _auto_repair(self, ship, delta_time: float):
        """Slowly repair ship when docked (free but slow)."""
        effective_stats = ship.get_effective_stats()
        max_hull = effective_stats.get_effective_hull_points()
        
        repair_amount = self.auto_repair_rate * delta_time
        ship.current_hull = min(max_hull, ship.current_hull + repair_amount)
    
    def emergency_repair_kit(self, ship) -> bool:
        """Use emergency repair kit (partial repair, expensive)."""
        effective_stats = ship.get_effective_stats()
        max_hull = effective_stats.get_effective_hull_points()
        
        # Repair 50% of missing hull
        damage = max_hull - ship.current_hull
        if damage <= 0:
            print("Ship doesn't need repair!")
            return False
        
        repair_amount = damage * 0.5
        cost = int(repair_amount * self.repair_cost_per_hull * self.emergency_repair_multiplier)
        
        if ship.credits < cost:
            print(f"Cannot afford emergency repair: {cost} credits required")
            return False
        
        ship.credits -= cost
        ship.current_hull = min(max_hull, ship.current_hull + repair_amount)
        
        print(f"Emergency repair completed! Restored {repair_amount:.1f} hull for {cost} credits")
        return True
    
    def get_repair_options(self, ship, station=None) -> list:
        """Get available repair options."""
        options = []
        
        effective_stats = ship.get_effective_stats()
        max_hull = effective_stats.get_effective_hull_points()
        damage = max_hull - ship.current_hull
        
        if damage <= 0:
            return options
        
        # Full repair option
        full_cost = self.get_repair_cost(ship, "full")
        options.append({
            "type": "full",
            "name": "Full Repair",
            "description": f"Restore all hull points ({damage:.0f} HP)",
            "cost": full_cost,
            "affordable": ship.credits >= full_cost,
            "duration": self.repair_duration
        })
        
        # Emergency repair option (if not at station)
        if not station:
            emergency_cost = self.get_repair_cost(ship, "emergency")
            options.append({
                "type": "emergency",
                "name": "Emergency Repair Kit",
                "description": f"Restore 50% hull ({damage * 0.5:.0f} HP)",
                "cost": emergency_cost,
                "affordable": ship.credits >= emergency_cost,
                "duration": 1.0
            })
        
        return options
    
    def get_status_info(self, ship) -> dict:
        """Get repair system status."""
        effective_stats = ship.get_effective_stats()
        max_hull = effective_stats.get_effective_hull_points()
        
        return {
            "repair_in_progress": self.repair_in_progress,
            "repair_progress": self.repair_timer / self.repair_duration if self.repair_in_progress else 0.0,
            "current_hull": ship.current_hull,
            "max_hull": max_hull,
            "hull_percentage": ship.get_hull_percentage(),
            "repair_cost": self.get_repair_cost(ship),
            "can_afford_repair": self.can_afford_repair(ship)
        }
    
    def draw_repair_ui(self, screen: pygame.Surface, ship, station=None):
        """Draw repair interface when docked."""
        if not station:
            return
            
        # Only show if ship needs repair
        if ship.current_hull >= ship.get_effective_stats().get_effective_hull_points():
            return
        
        # Get screen dimensions
        width, height = screen.get_size()
        
        # Draw repair panel
        panel_width = 300
        panel_height = 150
        panel_x = width - panel_width - 20
        panel_y = height - panel_height - 20
        
        # Panel background
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((0, 0, 0, 200))
        pygame.draw.rect(panel_surface, (100, 100, 100), 
                        (0, 0, panel_width, panel_height), 2)
        
        # Title
        font_medium = pygame.font.Font(None, 24)
        font_small = pygame.font.Font(None, 18)
        
        title = font_medium.render("REPAIR SERVICES", True, (255, 255, 255))
        panel_surface.blit(title, (10, 10))
        
        # Hull status
        effective_stats = ship.get_effective_stats()
        max_hull = effective_stats.get_effective_hull_points()
        hull_text = f"Hull: {ship.current_hull:.0f}/{max_hull} ({ship.get_hull_percentage()*100:.0f}%)"
        hull_surface = font_small.render(hull_text, True, (255, 255, 255))
        panel_surface.blit(hull_surface, (10, 35))
        
        # Repair cost
        repair_cost = self.get_repair_cost(ship)
        cost_text = f"Repair Cost: {repair_cost} credits"
        cost_color = (0, 255, 0) if ship.credits >= repair_cost else (255, 100, 100)
        cost_surface = font_small.render(cost_text, True, cost_color)
        panel_surface.blit(cost_surface, (10, 55))
        
        # Auto-repair status
        auto_text = "Auto-repair: Active (free but slow)"
        auto_surface = font_small.render(auto_text, True, (200, 200, 255))
        panel_surface.blit(auto_surface, (10, 75))
        
        # Instructions
        if ship.credits >= repair_cost:
            instr_text = "Press R for instant repair"
            instr_color = (255, 255, 0)
        else:
            instr_text = "Insufficient credits for instant repair"
            instr_color = (255, 100, 100)
        
        instr_surface = font_small.render(instr_text, True, instr_color)
        panel_surface.blit(instr_surface, (10, 110))
        
        # Progress bar if repair in progress
        if self.repair_in_progress:
            progress = self.repair_timer / self.repair_duration
            bar_width = panel_width - 20
            bar_height = 8
            bar_x = 10
            bar_y = 130
            
            # Background
            pygame.draw.rect(panel_surface, (50, 50, 50), 
                           (bar_x, bar_y, bar_width, bar_height))
            
            # Progress
            fill_width = int(bar_width * progress)
            pygame.draw.rect(panel_surface, (0, 255, 0), 
                           (bar_x, bar_y, fill_width, bar_height))
        
        screen.blit(panel_surface, (panel_x, panel_y))
    
    def handle_input(self, event, ship, station=None):
        """Handle repair input."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            if station and self.can_repair_at_station(ship, station):
                if not self.repair_in_progress:
                    self.instant_repair(ship)
            else:
                # Emergency repair kit
                self.emergency_repair_kit(ship)


# Global repair system instance
repair_system = RepairSystem()