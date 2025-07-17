from dataclasses import dataclass, field
from typing import Dict, List
from .upgrade_definitions import UpgradeCategory, upgrade_registry


@dataclass
class ShipStats:
    """Ship statistics that can be modified by upgrades."""
    # Base stats
    cargo_capacity: int = 20
    max_speed: float = 400.0
    thrust_force: float = 300.0
    hull_points: int = 100
    scanner_range: float = 150.0
    
    # Calculated stats (from upgrades)
    max_speed_multiplier: float = 1.0
    thrust_multiplier: float = 1.0
    collision_resistance: float = 1.0  # 1.0 = normal damage, 0.5 = half damage
    scanner_range_multiplier: float = 1.0
    scanner_detail: int = 0  # 0 = basic, higher = more detailed info
    
    # Cloaking stats
    cloak_effectiveness: float = 0.0  # 0.0 = no cloak, 1.0 = perfect invisibility
    cloak_duration: float = 0.0  # Maximum cloak duration in seconds
    cloak_cooldown: float = 0.0  # Cooldown between cloak uses in seconds
    
    def get_effective_cargo_capacity(self) -> int:
        """Get the effective cargo capacity including upgrades."""
        return self.cargo_capacity
    
    def get_effective_max_speed(self) -> float:
        """Get the effective maximum speed including upgrades."""
        return self.max_speed * self.max_speed_multiplier
    
    def get_effective_thrust_force(self) -> float:
        """Get the effective thrust force including upgrades."""
        return self.thrust_force * self.thrust_multiplier
    
    def get_effective_hull_points(self) -> int:
        """Get the effective hull points including upgrades."""
        return self.hull_points
    
    def get_effective_scanner_range(self) -> float:
        """Get the effective scanner range including upgrades."""
        return self.scanner_range * self.scanner_range_multiplier
    
    def get_collision_damage_multiplier(self) -> float:
        """Get the damage multiplier for collisions (lower is better)."""
        return self.collision_resistance


@dataclass
class ShipUpgrades:
    """Tracking of installed ship upgrades."""
    # Installed upgrades by ID
    installed_upgrades: Dict[str, bool] = field(default_factory=dict)
    
    # Current tier in each category (for quick lookup)
    cargo_tier: int = 0
    engine_tier: int = 0
    hull_tier: int = 0
    scanner_tier: int = 0
    stealth_tier: int = 0
    
    def install_upgrade(self, upgrade_id: str) -> bool:
        """Install an upgrade if requirements are met."""
        try:
            upgrade = upgrade_registry.get_upgrade(upgrade_id)
        except KeyError:
            return False
        
        # Check if already installed
        if self.is_upgrade_installed(upgrade_id):
            return False
        
        # Check requirements
        for req_id in upgrade.requirements:
            if not self.is_upgrade_installed(req_id):
                return False
        
        # Install the upgrade
        self.installed_upgrades[upgrade_id] = True
        
        # Update tier tracking
        if upgrade.category == UpgradeCategory.CARGO:
            self.cargo_tier = max(self.cargo_tier, upgrade.tier)
        elif upgrade.category == UpgradeCategory.ENGINE:
            self.engine_tier = max(self.engine_tier, upgrade.tier)
        elif upgrade.category == UpgradeCategory.HULL:
            self.hull_tier = max(self.hull_tier, upgrade.tier)
        elif upgrade.category == UpgradeCategory.SCANNER:
            self.scanner_tier = max(self.scanner_tier, upgrade.tier)
        elif upgrade.category == UpgradeCategory.STEALTH:
            self.stealth_tier = max(self.stealth_tier, upgrade.tier)
        
        return True
    
    def is_upgrade_installed(self, upgrade_id: str) -> bool:
        """Check if an upgrade is installed."""
        return self.installed_upgrades.get(upgrade_id, False)
    
    def get_installed_upgrades(self) -> Dict[str, bool]:
        """Get all installed upgrades."""
        return self.installed_upgrades.copy()
    
    def get_current_tier(self, category: UpgradeCategory) -> int:
        """Get the current tier for a category."""
        if category == UpgradeCategory.CARGO:
            return self.cargo_tier
        elif category == UpgradeCategory.ENGINE:
            return self.engine_tier
        elif category == UpgradeCategory.HULL:
            return self.hull_tier
        elif category == UpgradeCategory.SCANNER:
            return self.scanner_tier
        return 0
    
    def get_total_upgrade_value(self) -> int:
        """Calculate total credits invested in upgrades."""
        total_value = 0
        for upgrade_id, installed in self.installed_upgrades.items():
            if installed:
                try:
                    upgrade = upgrade_registry.get_upgrade(upgrade_id)
                    total_value += upgrade.cost
                except KeyError:
                    continue
        return total_value
    
    def get_effective_stats(self, base_stats: ShipStats) -> ShipStats:
        """Apply all upgrade modifiers to base stats."""
        # Start with a copy of base stats
        effective_stats = ShipStats(
            cargo_capacity=base_stats.cargo_capacity,
            max_speed=base_stats.max_speed,
            thrust_force=base_stats.thrust_force,
            hull_points=base_stats.hull_points,
            scanner_range=base_stats.scanner_range
        )
        
        # Apply upgrades
        for upgrade_id, installed in self.installed_upgrades.items():
            if not installed:
                continue
                
            try:
                upgrade = upgrade_registry.get_upgrade(upgrade_id)
                
                # Apply stat modifications
                for stat_name, stat_value in upgrade.stats.items():
                    if hasattr(effective_stats, stat_name):
                        current_value = getattr(effective_stats, stat_name)
                        
                        # Handle different stat types
                        if stat_name.endswith('_multiplier'):
                            # Multipliers are applied multiplicatively
                            setattr(effective_stats, stat_name, current_value * stat_value)
                        else:
                            # Other stats are applied additively
                            setattr(effective_stats, stat_name, current_value + stat_value)
                            
            except KeyError:
                continue
        
        return effective_stats
    
    def get_upgrade_summary(self) -> Dict[str, str]:
        """Get a summary of installed upgrades by category."""
        summary = {}
        
        for category in UpgradeCategory:
            tier = self.get_current_tier(category)
            if tier > 0:
                # Find the highest tier upgrade in this category
                category_upgrades = upgrade_registry.get_upgrades_by_category(category)
                highest_upgrade = None
                
                for upgrade in category_upgrades:
                    if upgrade.tier == tier and self.is_upgrade_installed(upgrade.id):
                        highest_upgrade = upgrade
                        break
                
                if highest_upgrade:
                    summary[category.value] = f"Tier {tier}: {highest_upgrade.name}"
                else:
                    summary[category.value] = f"Tier {tier}"
            else:
                summary[category.value] = "None"
        
        return summary
    
    def can_install_upgrade(self, upgrade_id: str) -> bool:
        """Check if an upgrade can be installed (requirements met)."""
        try:
            upgrade = upgrade_registry.get_upgrade(upgrade_id)
        except KeyError:
            return False
        
        # Check if already installed
        if self.is_upgrade_installed(upgrade_id):
            return False
        
        # Check requirements
        for req_id in upgrade.requirements:
            if not self.is_upgrade_installed(req_id):
                return False
        
        return True
    
    def get_available_upgrades(self, credits: int) -> List[str]:
        """Get list of upgrade IDs that can be purchased and installed."""
        available = upgrade_registry.get_available_upgrades(
            self.installed_upgrades, 
            credits
        )
        
        return [upgrade.id for upgrade in available]
    
    def reset_upgrades(self):
        """Remove all upgrades (for testing or ship reset)."""
        self.installed_upgrades.clear()
        self.cargo_tier = 0
        self.engine_tier = 0
        self.hull_tier = 0
        self.scanner_tier = 0
        self.stealth_tier = 0
    
    def to_dict(self) -> Dict[str, any]:
        """Serialize upgrades to dictionary for saving."""
        return {
            "installed_upgrades": self.installed_upgrades,
            "cargo_tier": self.cargo_tier,
            "engine_tier": self.engine_tier,
            "hull_tier": self.hull_tier,
            "scanner_tier": self.scanner_tier,
            "stealth_tier": self.stealth_tier
        }
    
    def from_dict(self, data: Dict[str, any]):
        """Load upgrades from dictionary."""
        self.installed_upgrades = data.get("installed_upgrades", {})
        self.cargo_tier = data.get("cargo_tier", 0)
        self.engine_tier = data.get("engine_tier", 0)
        self.hull_tier = data.get("hull_tier", 0)
        self.scanner_tier = data.get("scanner_tier", 0)
        self.stealth_tier = data.get("stealth_tier", 0)