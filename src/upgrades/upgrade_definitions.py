from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class UpgradeCategory(Enum):
    """Categories of ship upgrades."""
    CARGO = "Cargo Hold"
    ENGINE = "Engine"
    HULL = "Hull"
    SCANNER = "Scanner"


@dataclass
class UpgradeDefinition:
    """Definition of a ship upgrade."""
    id: str
    name: str
    category: UpgradeCategory
    tier: int
    cost: int
    description: str
    requirements: List[str]  # Required previous upgrade IDs
    stats: Dict[str, float]  # Stat modifications
    
    def __post_init__(self):
        """Validate upgrade definition."""
        if self.cost < 0:
            raise ValueError("Upgrade cost must be non-negative")
        if self.tier < 0:
            raise ValueError("Upgrade tier must be non-negative")


class UpgradeRegistry:
    """Registry of all available ship upgrades."""
    
    def __init__(self):
        self._upgrades: Dict[str, UpgradeDefinition] = {}
        self._initialize_default_upgrades()
    
    def _initialize_default_upgrades(self):
        """Initialize the standard set of ship upgrades."""
        default_upgrades = [
            # Cargo Hold Upgrades
            UpgradeDefinition(
                id="cargo_expanded",
                name="Expanded Hold",
                category=UpgradeCategory.CARGO,
                tier=1,
                cost=2000,
                description="Additional cargo compartments increase capacity by 15 units",
                requirements=[],
                stats={"cargo_capacity": 15}
            ),
            UpgradeDefinition(
                id="cargo_large",
                name="Large Hold",
                category=UpgradeCategory.CARGO,
                tier=2,
                cost=5000,
                description="Redesigned cargo bay layout increases capacity by 30 units",
                requirements=["cargo_expanded"],
                stats={"cargo_capacity": 30}
            ),
            UpgradeDefinition(
                id="cargo_commercial",
                name="Commercial Hold",
                category=UpgradeCategory.CARGO,
                tier=3,
                cost=12000,
                description="Commercial-grade cargo system increases capacity by 55 units",
                requirements=["cargo_large"],
                stats={"cargo_capacity": 55}
            ),
            UpgradeDefinition(
                id="cargo_freighter",
                name="Freighter Hold",
                category=UpgradeCategory.CARGO,
                tier=4,
                cost=25000,
                description="Massive cargo bay conversion increases capacity by 80 units",
                requirements=["cargo_commercial"],
                stats={"cargo_capacity": 80}
            ),
            
            # Engine Upgrades
            UpgradeDefinition(
                id="engine_enhanced",
                name="Enhanced Engine",
                category=UpgradeCategory.ENGINE,
                tier=1,
                cost=3000,
                description="Improved fuel injection increases speed and thrust",
                requirements=[],
                stats={"max_speed_multiplier": 1.2, "thrust_multiplier": 1.15}
            ),
            UpgradeDefinition(
                id="engine_racing",
                name="Racing Engine",
                category=UpgradeCategory.ENGINE,
                tier=2,
                cost=8000,
                description="High-performance racing engine for superior speed",
                requirements=["engine_enhanced"],
                stats={"max_speed_multiplier": 1.4, "thrust_multiplier": 1.3}
            ),
            UpgradeDefinition(
                id="engine_military",
                name="Military Engine",
                category=UpgradeCategory.ENGINE,
                tier=3,
                cost=18000,
                description="Military-grade propulsion system for maximum performance",
                requirements=["engine_racing"],
                stats={"max_speed_multiplier": 1.6, "thrust_multiplier": 1.5}
            ),
            UpgradeDefinition(
                id="engine_prototype",
                name="Prototype Engine",
                category=UpgradeCategory.ENGINE,
                tier=4,
                cost=40000,
                description="Experimental fusion drive technology",
                requirements=["engine_military"],
                stats={"max_speed_multiplier": 2.0, "thrust_multiplier": 1.75}
            ),
            
            # Hull Upgrades
            UpgradeDefinition(
                id="hull_reinforced",
                name="Reinforced Hull",
                category=UpgradeCategory.HULL,
                tier=1,
                cost=2500,
                description="Reinforced plating increases hull strength",
                requirements=[],
                stats={"hull_points": 50, "collision_resistance": 0.8}
            ),
            UpgradeDefinition(
                id="hull_armored",
                name="Armored Hull",
                category=UpgradeCategory.HULL,
                tier=2,
                cost=6000,
                description="Military-grade armor plating for superior protection",
                requirements=["hull_reinforced"],
                stats={"hull_points": 100, "collision_resistance": 0.6}
            ),
            UpgradeDefinition(
                id="hull_advanced",
                name="Advanced Hull",
                category=UpgradeCategory.HULL,
                tier=3,
                cost=15000,
                description="Advanced composite materials for maximum durability",
                requirements=["hull_armored"],
                stats={"hull_points": 200, "collision_resistance": 0.4}
            ),
            UpgradeDefinition(
                id="hull_titan",
                name="Titan Hull",
                category=UpgradeCategory.HULL,
                tier=4,
                cost=35000,
                description="Experimental titanium-alloy hull plating",
                requirements=["hull_advanced"],
                stats={"hull_points": 400, "collision_resistance": 0.2}
            ),
            
            # Scanner Upgrades
            UpgradeDefinition(
                id="scanner_enhanced",
                name="Enhanced Scanner",
                category=UpgradeCategory.SCANNER,
                tier=1,
                cost=1500,
                description="Improved sensor resolution and range",
                requirements=[],
                stats={"scanner_range_multiplier": 1.5, "scanner_detail": 1}
            ),
            UpgradeDefinition(
                id="scanner_long_range",
                name="Long Range Scanner",
                category=UpgradeCategory.SCANNER,
                tier=2,
                cost=4000,
                description="Extended range sensors for deep space scanning",
                requirements=["scanner_enhanced"],
                stats={"scanner_range_multiplier": 2.0, "scanner_detail": 2}
            ),
            UpgradeDefinition(
                id="scanner_military",
                name="Military Scanner",
                category=UpgradeCategory.SCANNER,
                tier=3,
                cost=10000,
                description="Military-grade tactical sensors",
                requirements=["scanner_long_range"],
                stats={"scanner_range_multiplier": 2.5, "scanner_detail": 3}
            ),
            UpgradeDefinition(
                id="scanner_deep_space",
                name="Deep Space Scanner",
                category=UpgradeCategory.SCANNER,
                tier=4,
                cost=22000,
                description="Research-grade sensors for maximum detection range",
                requirements=["scanner_military"],
                stats={"scanner_range_multiplier": 4.0, "scanner_detail": 4}
            )
        ]
        
        for upgrade in default_upgrades:
            self.register_upgrade(upgrade)
    
    def register_upgrade(self, upgrade: UpgradeDefinition):
        """Register a new upgrade in the system."""
        if upgrade.id in self._upgrades:
            raise ValueError(f"Upgrade with id '{upgrade.id}' already exists")
        self._upgrades[upgrade.id] = upgrade
    
    def get_upgrade(self, upgrade_id: str) -> UpgradeDefinition:
        """Get an upgrade by ID."""
        if upgrade_id not in self._upgrades:
            raise KeyError(f"Unknown upgrade id: {upgrade_id}")
        return self._upgrades[upgrade_id]
    
    def get_all_upgrades(self) -> List[UpgradeDefinition]:
        """Get all registered upgrades."""
        return list(self._upgrades.values())
    
    def get_upgrades_by_category(self, category: UpgradeCategory) -> List[UpgradeDefinition]:
        """Get all upgrades in a specific category."""
        upgrades = [u for u in self._upgrades.values() if u.category == category]
        # Sort by tier
        upgrades.sort(key=lambda u: u.tier)
        return upgrades
    
    def get_upgrades_by_tier(self, tier: int) -> List[UpgradeDefinition]:
        """Get all upgrades of a specific tier."""
        return [u for u in self._upgrades.values() if u.tier == tier]
    
    def get_available_upgrades(self, current_upgrades: Dict[str, bool], 
                              credits: int) -> List[UpgradeDefinition]:
        """Get upgrades that are available for purchase."""
        available = []
        
        for upgrade in self._upgrades.values():
            # Check if already purchased
            if current_upgrades.get(upgrade.id, False):
                continue
                
            # Check if player has enough credits
            if credits < upgrade.cost:
                continue
                
            # Check if requirements are met
            requirements_met = all(
                current_upgrades.get(req_id, False) 
                for req_id in upgrade.requirements
            )
            
            if requirements_met:
                available.append(upgrade)
        
        # Sort by category and tier
        available.sort(key=lambda u: (u.category.value, u.tier))
        return available
    
    def get_next_tier_upgrade(self, category: UpgradeCategory, 
                             current_tier: int) -> Optional[UpgradeDefinition]:
        """Get the next tier upgrade in a category."""
        category_upgrades = self.get_upgrades_by_category(category)
        
        for upgrade in category_upgrades:
            if upgrade.tier == current_tier + 1:
                return upgrade
        
        return None
    
    def get_upgrade_chain(self, category: UpgradeCategory) -> List[UpgradeDefinition]:
        """Get the complete upgrade chain for a category."""
        return self.get_upgrades_by_category(category)


# Global upgrade registry instance
upgrade_registry = UpgradeRegistry()