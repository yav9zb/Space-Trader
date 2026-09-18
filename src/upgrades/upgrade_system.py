from typing import Optional, Tuple, List
from .upgrade_definitions import UpgradeDefinition, UpgradeCategory, upgrade_registry
from .ship_upgrades import ShipUpgrades, ShipStats
from ..difficulty.difficulty_manager import difficulty_manager


class UpgradeResult:
    """Result of an upgrade operation."""
    
    def __init__(self, success: bool, message: str, upgrade: Optional[UpgradeDefinition] = None):
        self.success = success
        self.message = message
        self.upgrade = upgrade


class UpgradeSystem:
    """System for managing ship upgrades."""
    
    def __init__(self):
        pass
    
    def purchase_upgrade(self, ship_upgrades: ShipUpgrades, upgrade_id: str,
                        current_credits: int, reputation: int = 0) -> Tuple[UpgradeResult, int]:
        """
        Attempt to purchase and install an upgrade.

        Returns:
            Tuple of (UpgradeResult, remaining_credits)
        """
        try:
            upgrade = upgrade_registry.get_upgrade(upgrade_id)
        except KeyError:
            return UpgradeResult(False, f"Unknown upgrade: {upgrade_id}"), current_credits

        # Top tier requires a minimum rank - belt-and-suspenders in case this
        # is ever reached outside the already-filtered available-upgrades list
        if upgrade.tier >= 4:
            from ..missions.rank_system import TIER_4_MIN_REPUTATION, get_rank_name
            if reputation < TIER_4_MIN_REPUTATION:
                from ..audio.sound_manager import sound_manager
                sound_manager.play("ui_error")
                required_rank = get_rank_name(TIER_4_MIN_REPUTATION)
                current_rank = get_rank_name(reputation)
                return UpgradeResult(
                    False,
                    f"Requires {required_rank} rank (currently {current_rank})"
                ), current_credits

        # Check if player has enough credits (cost scaled by current difficulty)
        effective_cost = difficulty_manager.apply_upgrade_cost_multiplier(upgrade.cost)
        if current_credits < effective_cost:
            from ..audio.sound_manager import sound_manager
            sound_manager.play("ui_error")
            return UpgradeResult(
                False,
                f"Insufficient credits. Need {effective_cost}, have {current_credits}"
            ), current_credits
        
        # Check if upgrade can be installed
        if not ship_upgrades.can_install_upgrade(upgrade_id):
            # Check specific reason
            if ship_upgrades.is_upgrade_installed(upgrade_id):
                return UpgradeResult(
                    False, 
                    f"{upgrade.name} is already installed"
                ), current_credits
            else:
                # Check requirements
                missing_requirements = []
                for req_id in upgrade.requirements:
                    if not ship_upgrades.is_upgrade_installed(req_id):
                        try:
                            req_upgrade = upgrade_registry.get_upgrade(req_id)
                            missing_requirements.append(req_upgrade.name)
                        except KeyError:
                            missing_requirements.append(req_id)
                
                if missing_requirements:
                    req_text = ", ".join(missing_requirements)
                    return UpgradeResult(
                        False,
                        f"Missing requirements: {req_text}"
                    ), current_credits
        
        # Install the upgrade
        if ship_upgrades.install_upgrade(upgrade_id):
            remaining_credits = current_credits - effective_cost
            return UpgradeResult(
                True,
                f"Successfully installed {upgrade.name}",
                upgrade
            ), remaining_credits
        else:
            return UpgradeResult(
                False,
                f"Failed to install {upgrade.name}"
            ), current_credits
    
    def get_upgrade_preview(self, ship_upgrades: ShipUpgrades, base_stats: ShipStats,
                           upgrade_id: str) -> Optional[Tuple[ShipStats, ShipStats]]:
        """
        Get before/after stats preview for an upgrade.
        
        Returns:
            Tuple of (current_stats, upgraded_stats) or None if invalid upgrade
        """
        try:
            upgrade = upgrade_registry.get_upgrade(upgrade_id)
        except KeyError:
            return None
        
        # Get current effective stats
        current_stats = ship_upgrades.get_effective_stats(base_stats)
        
        # Create temporary upgrade state
        temp_upgrades = ShipUpgrades(
            installed_upgrades=ship_upgrades.installed_upgrades.copy(),
            cargo_tier=ship_upgrades.cargo_tier,
            engine_tier=ship_upgrades.engine_tier,
            hull_tier=ship_upgrades.hull_tier,
            scanner_tier=ship_upgrades.scanner_tier
        )
        
        # Install the upgrade temporarily
        if temp_upgrades.install_upgrade(upgrade_id):
            upgraded_stats = temp_upgrades.get_effective_stats(base_stats)
            return current_stats, upgraded_stats
        
        return None
    
    def get_available_upgrades_for_station(self, ship_upgrades: ShipUpgrades,
                                          station_type: str,
                                          credits: int, reputation: int = 0) -> List[UpgradeDefinition]:
        """Get upgrades available at a specific station type."""
        all_available = upgrade_registry.get_available_upgrades(
            ship_upgrades.installed_upgrades,
            credits,
            reputation
        )
        
        # Filter by station type
        station_upgrades = []
        
        for upgrade in all_available:
            if self._is_upgrade_available_at_station(upgrade, station_type):
                station_upgrades.append(upgrade)
        
        return station_upgrades
    
    def _is_upgrade_available_at_station(self, upgrade: UpgradeDefinition, 
                                        station_type: str) -> bool:
        """Check if an upgrade is available at a station type."""
        station_lower = station_type.lower()
        
        # Shipyards have all upgrades
        if "shipyard" in station_lower:
            return True
        
        # Research labs have scanner and engine upgrades
        if "research" in station_lower:
            return upgrade.category in [UpgradeCategory.SCANNER, UpgradeCategory.ENGINE]
        
        # Military bases have hull and engine upgrades
        if "military" in station_lower:
            return upgrade.category in [UpgradeCategory.HULL, UpgradeCategory.ENGINE]
        
        # Other stations don't have upgrades
        return False
    
    def get_upgrade_discount(self, upgrade: UpgradeDefinition, station_type: str,
                            faction_standing: int = 0) -> float:
        """Get discount multiplier for an upgrade at a station (1.0 = no discount).
        Stacks the existing station-type discount with a faction-standing
        multiplier - allied factions discount further, hostile ones mark up."""
        station_lower = station_type.lower()
        station_multiplier = 1.0

        # Shipyard discounts
        if "shipyard" in station_lower:
            if upgrade.category == UpgradeCategory.HULL:
                station_multiplier = 0.9  # 10% discount on hull upgrades

        # Research lab discounts
        elif "research" in station_lower:
            if upgrade.category == UpgradeCategory.SCANNER:
                station_multiplier = 0.85  # 15% discount on scanner upgrades

        # Military base discounts
        elif "military" in station_lower:
            if upgrade.category == UpgradeCategory.HULL:
                station_multiplier = 0.8  # 20% discount on hull upgrades

        from ..factions import get_faction_price_multiplier
        return station_multiplier * get_faction_price_multiplier(faction_standing)

    def get_discounted_price(self, upgrade: UpgradeDefinition, station_type: str,
                            faction_standing: int = 0) -> int:
        """Get the discounted price for an upgrade at a station."""
        discount = self.get_upgrade_discount(upgrade, station_type, faction_standing)
        return int(upgrade.cost * discount)
    
    def get_upgrade_chain_progress(self, ship_upgrades: ShipUpgrades, 
                                  category: UpgradeCategory) -> Tuple[int, int]:
        """
        Get progress in an upgrade chain.
        
        Returns:
            Tuple of (current_tier, max_tier)
        """
        current_tier = ship_upgrades.get_current_tier(category)
        category_upgrades = upgrade_registry.get_upgrades_by_category(category)
        max_tier = max(upgrade.tier for upgrade in category_upgrades) if category_upgrades else 0
        
        return current_tier, max_tier
    
    def get_next_recommended_upgrade(self, ship_upgrades: ShipUpgrades, 
                                    credits: int) -> Optional[UpgradeDefinition]:
        """Get the next recommended upgrade based on current progress and credits."""
        available_upgrades = upgrade_registry.get_available_upgrades(
            ship_upgrades.installed_upgrades,
            credits
        )
        
        if not available_upgrades:
            return None
        
        # Prioritize lower tier upgrades first
        available_upgrades.sort(key=lambda u: (u.tier, u.cost))
        
        # Prefer cargo upgrades early game
        cargo_upgrades = [u for u in available_upgrades if u.category == UpgradeCategory.CARGO]
        if cargo_upgrades and ship_upgrades.cargo_tier < 2:
            return cargo_upgrades[0]
        
        # Then engine upgrades for efficiency
        engine_upgrades = [u for u in available_upgrades if u.category == UpgradeCategory.ENGINE]
        if engine_upgrades and ship_upgrades.engine_tier < 2:
            return engine_upgrades[0]
        
        # Return the cheapest available upgrade
        return available_upgrades[0]
    
    def calculate_upgrade_value(self, upgrade: UpgradeDefinition) -> float:
        """Calculate the relative value of an upgrade (higher is better)."""
        # Simple value calculation based on stats per credit
        total_stat_value = 0
        
        for stat_name, stat_value in upgrade.stats.items():
            if stat_name == "cargo_capacity":
                # Cargo is very valuable
                total_stat_value += stat_value * 100
            elif stat_name.endswith("_multiplier"):
                # Multipliers are valuable
                total_stat_value += (stat_value - 1.0) * 1000
            elif stat_name == "hull_points":
                # Hull points are moderately valuable
                total_stat_value += stat_value * 2
            else:
                # Other stats have base value
                total_stat_value += stat_value * 10
        
        return total_stat_value / max(upgrade.cost, 1)


# Global upgrade system instance
upgrade_system = UpgradeSystem()