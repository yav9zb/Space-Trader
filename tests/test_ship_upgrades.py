import sys
import os

# Add src to Python path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from upgrades.upgrade_definitions import UpgradeDefinition, UpgradeCategory, upgrade_registry
from upgrades.ship_upgrades import ShipUpgrades, ShipStats
from upgrades.upgrade_system import UpgradeSystem, upgrade_system


def test_upgrade_definitions():
    """Test that upgrade definitions are loaded correctly."""
    print("Testing upgrade definitions...")
    
    # Test that upgrades are loaded
    all_upgrades = upgrade_registry.get_all_upgrades()
    assert len(all_upgrades) >= 16, f"Expected at least 16 upgrades, got {len(all_upgrades)}"
    
    # Test cargo upgrades
    cargo_upgrades = upgrade_registry.get_upgrades_by_category(UpgradeCategory.CARGO)
    assert len(cargo_upgrades) == 4, f"Expected 4 cargo upgrades, got {len(cargo_upgrades)}"
    
    # Test that upgrades are sorted by tier
    for i in range(1, len(cargo_upgrades)):
        assert cargo_upgrades[i].tier >= cargo_upgrades[i-1].tier
    
    # Test specific upgrade
    expanded_hold = upgrade_registry.get_upgrade("cargo_expanded")
    assert expanded_hold.name == "Expanded Hold"
    assert expanded_hold.cost == 2000
    assert expanded_hold.stats["cargo_capacity"] == 15
    
    print("✓ Upgrade definitions test passed")


def test_ship_upgrades():
    """Test ship upgrade tracking system."""
    print("Testing ship upgrade tracking...")
    
    ship_upgrades = ShipUpgrades()
    base_stats = ShipStats()
    
    # Test initial state
    assert ship_upgrades.cargo_tier == 0
    assert ship_upgrades.get_total_upgrade_value() == 0
    
    # Test installing an upgrade
    success = ship_upgrades.install_upgrade("cargo_expanded")
    assert success, "Should be able to install cargo_expanded"
    assert ship_upgrades.cargo_tier == 1
    assert ship_upgrades.is_upgrade_installed("cargo_expanded")
    
    # Test requirements - should not be able to install tier 2 without tier 1
    ship_upgrades2 = ShipUpgrades()
    success = ship_upgrades2.install_upgrade("cargo_large")  # tier 2
    assert not success, "Should not be able to install tier 2 without tier 1"
    
    # Test effective stats
    effective_stats = ship_upgrades.get_effective_stats(base_stats)
    assert effective_stats.cargo_capacity == 35, f"Expected 35 cargo capacity, got {effective_stats.cargo_capacity}"
    
    print("✓ Ship upgrades test passed")


def test_upgrade_system():
    """Test upgrade purchase system."""
    print("Testing upgrade purchase system...")
    
    ship_upgrades = ShipUpgrades()
    credits = 5000
    
    # Test successful purchase
    result, remaining_credits = upgrade_system.purchase_upgrade(
        ship_upgrades, "cargo_expanded", credits
    )
    
    assert result.success, f"Purchase should succeed: {result.message}"
    assert remaining_credits == 3000, f"Expected 3000 credits remaining, got {remaining_credits}"
    assert ship_upgrades.is_upgrade_installed("cargo_expanded")
    
    # Test insufficient credits
    result, remaining_credits = upgrade_system.purchase_upgrade(
        ship_upgrades, "engine_prototype", remaining_credits  # costs 40000, only have 3000
    )
    
    assert not result.success, "Purchase should fail due to insufficient credits"
    assert remaining_credits == 3000, "Credits should remain unchanged after failed purchase"
    
    # Test requirements not met
    result, remaining_credits = upgrade_system.purchase_upgrade(
        ship_upgrades, "cargo_commercial", remaining_credits  # requires cargo_large
    )
    
    assert not result.success, "Purchase should fail due to missing requirements"
    
    print("✓ Upgrade system test passed")


def test_station_availability():
    """Test station-specific upgrade availability."""
    print("Testing station upgrade availability...")
    
    ship_upgrades = ShipUpgrades()
    credits = 50000  # Plenty of credits
    
    # Test shipyard (should have all tier 1 upgrades available initially)
    shipyard_upgrades = upgrade_system.get_available_upgrades_for_station(
        ship_upgrades, "Shipyard", credits
    )
    assert len(shipyard_upgrades) >= 4, f"Shipyard should have tier 1 upgrades available, got {len(shipyard_upgrades)}"
    
    # Test research station (should have scanner and engine only)
    research_upgrades = upgrade_system.get_available_upgrades_for_station(
        ship_upgrades, "Research Station", credits
    )
    
    for upgrade in research_upgrades:
        assert upgrade.category in [UpgradeCategory.SCANNER, UpgradeCategory.ENGINE], \
            f"Research station should only have scanner/engine upgrades, got {upgrade.category}"
    
    # Test trading post (should have no upgrades)
    trading_upgrades = upgrade_system.get_available_upgrades_for_station(
        ship_upgrades, "Trading Post", credits
    )
    assert len(trading_upgrades) == 0, "Trading post should have no upgrades"
    
    print("✓ Station availability test passed")


def test_discounts():
    """Test station discount system."""
    print("Testing station discounts...")
    
    # Test hull upgrade discount at military base
    hull_upgrade = upgrade_registry.get_upgrade("hull_reinforced")
    
    # Military base should give 20% discount on hull
    military_price = upgrade_system.get_discounted_price(hull_upgrade, "Military Base")
    expected_price = int(hull_upgrade.cost * 0.8)
    assert military_price == expected_price, f"Expected {expected_price}, got {military_price}"
    
    # Shipyard should give 10% discount on hull
    shipyard_price = upgrade_system.get_discounted_price(hull_upgrade, "Shipyard")
    expected_price = int(hull_upgrade.cost * 0.9)
    assert shipyard_price == expected_price, f"Expected {expected_price}, got {shipyard_price}"
    
    # Trading post should give no discount
    trading_price = upgrade_system.get_discounted_price(hull_upgrade, "Trading Post")
    assert trading_price == hull_upgrade.cost, "Trading post should give no discount"
    
    print("✓ Discount system test passed")


def test_integration():
    """Test full integration scenario."""
    print("Testing full integration scenario...")
    
    ship_upgrades = ShipUpgrades()
    base_stats = ShipStats(cargo_capacity=20, max_speed=400, thrust_force=300)
    credits = 20000
    
    # Buy cargo upgrade
    result, credits = upgrade_system.purchase_upgrade(ship_upgrades, "cargo_expanded", credits)
    assert result.success
    
    # Buy next cargo upgrade
    result, credits = upgrade_system.purchase_upgrade(ship_upgrades, "cargo_large", credits)
    assert result.success
    
    # Buy engine upgrade
    result, credits = upgrade_system.purchase_upgrade(ship_upgrades, "engine_enhanced", credits)
    assert result.success
    
    # Check effective stats
    effective_stats = ship_upgrades.get_effective_stats(base_stats)
    
    # Should have cargo from both upgrades (base 20 + 15 + 30 = 65)
    # In this system, upgrades stack additively
    assert effective_stats.cargo_capacity == 65, f"Expected 65 cargo, got {effective_stats.cargo_capacity}"
    
    # Should have engine boost (400 * 1.2 = 480)
    assert effective_stats.get_effective_max_speed() == 480, f"Expected 480 speed, got {effective_stats.get_effective_max_speed()}"
    
    # Check upgrade summary
    summary = ship_upgrades.get_upgrade_summary()
    assert "Tier 2" in summary["Cargo Hold"]
    assert "Tier 1" in summary["Engine"]
    
    print("✓ Integration test passed")


if __name__ == "__main__":
    print("Running ship upgrade system tests...\n")
    
    try:
        test_upgrade_definitions()
        test_ship_upgrades()
        test_upgrade_system()
        test_station_availability()
        test_discounts()
        test_integration()
        
        print("\n🎉 All tests passed! Upgrade system is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()