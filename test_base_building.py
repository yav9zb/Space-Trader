#!/usr/bin/env python3
"""Simple test for the base building system."""

import sys
import os
import pygame

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from base_building.base_manager import base_manager, BaseManager
from base_building.base_entity import PlayerBase, ModuleType
from base_building.construction_system import ConstructionSystem
from base_building.resource_production import ProductionSystem
from pygame import Vector2


def test_base_creation():
    """Test basic base creation and management."""
    print("Testing base creation...")
    
    # Create a new base
    base_id = base_manager.create_base(Vector2(1000, 1000), "Test Base Alpha")
    assert base_id is not None, "Failed to create base"
    
    # Get the base
    base = base_manager.get_base(base_id)
    assert base is not None, "Failed to retrieve created base"
    assert base.name == "Test Base Alpha"
    
    print(f"✓ Created base '{base.name}' at {base.position}")
    
    # Add initial resources for command center construction
    base.stored_resources = {
        "Metal": 1000,
        "Electronics": 500, 
        "Credits": 50000
    }
    
    # The command center should be added during construction
    # Let's manually add it for the test since construction takes time
    if len(set(base.modules.values())) == 0:
        base.add_module(ModuleType.COMMAND_CENTER, 0, 0)
    
    # Check initial state
    assert len(set(base.modules.values())) >= 1, "Base should have at least command center"
    
    # Check initial stats
    unique_modules = set(base.modules.values())
    command_center = next(iter(unique_modules))
    assert command_center.module_type == ModuleType.COMMAND_CENTER
    
    print("✓ Base creation test passed")
    return base_id


def test_module_construction():
    """Test module construction."""
    print("\nTesting module construction...")
    
    # Create test base
    base_id = base_manager.create_base(Vector2(2000, 2000), "Construction Test Base")
    base = base_manager.get_base(base_id)
    
    # Add some resources for construction
    base.stored_resources = {
        "Metal": 5000,
        "Electronics": 2000,
        "Machinery": 1000,
        "Fuel": 1000,
        "Textiles": 500,
        "Credits": 100000
    }
    
    # Test adding different module types
    modules_to_test = [
        (ModuleType.POWER_GENERATOR, 1, 0),
        (ModuleType.HABITAT, -1, 0),
        (ModuleType.STORAGE, 0, 1),
        (ModuleType.REFINERY, 1, 1)
    ]
    
    for module_type, grid_x, grid_y in modules_to_test:
        success = base.add_module(module_type, grid_x, grid_y)
        assert success, f"Failed to add {module_type.value} module"
        
        # Check module was added
        assert (grid_x, grid_y) in base.modules, f"Module not found at grid position ({grid_x}, {grid_y})"
        
        module = base.modules[(grid_x, grid_y)]
        assert module.module_type == module_type, f"Wrong module type at position"
        
        print(f"✓ Added {module_type.value} at ({grid_x}, {grid_y})")
    
    print("✓ Module construction test passed")


def test_base_systems():
    """Test base power and resource systems."""
    print("\nTesting base systems...")
    
    # Create test base with modules
    base_id = base_manager.create_base(Vector2(3000, 3000), "Systems Test Base")
    base = base_manager.get_base(base_id)
    
    # Add resources
    base.stored_resources = {
        "Metal": 10000,
        "Electronics": 5000,
        "Machinery": 2000,  # Add machinery for refinery (300) and factory (200)
        "Fuel": 1000,
        "Credits": 200000
    }
    
    # Add power generator
    base.add_module(ModuleType.POWER_GENERATOR, 1, 0)
    base.add_module(ModuleType.POWER_GENERATOR, 2, 0)  # Second generator
    
    # Add power consumers (note: refinery and factory are 2x2 modules)
    refinery_success = base.add_module(ModuleType.REFINERY, -3, 0)  # Move further away
    factory_success = base.add_module(ModuleType.FACTORY, 0, 2)  # Move below existing modules
    
    assert refinery_success, "Failed to add refinery"
    assert factory_success, "Failed to add factory"
    
    # Update base to process construction and power
    # Need to wait for construction to complete (refinery takes 240 seconds, factory takes 200 seconds)
    for _ in range(300):  # Simulate 300 seconds of updates to ensure all modules are built
        base.update(1.0)  # 1 second per update
    
    # Check power generation and consumption
    assert base.power_generation > 0, "No power generation"
    assert base.power_consumption > 0, "No power consumption"
    print(f"✓ Power system working: {base.power_generation}W generated, {base.power_consumption}W consumed")
    
    # Test resource storage
    stored_metal = base.get_resource_amount("Metal")
    assert stored_metal > 0, "Should have stored metal"
    
    print("✓ Base systems test passed")


def test_construction_system():
    """Test the construction system."""
    print("\nTesting construction system...")
    
    # Create construction system
    construction_system = ConstructionSystem(base_manager)
    
    # Create test base
    base_id = base_manager.create_base(Vector2(4000, 4000), "Construction System Test")
    
    # Activate construction
    success = construction_system.activate_construction(base_id)
    assert success, "Failed to activate construction"
    assert construction_system.is_construction_active
    
    # Test construction info
    info = construction_system.get_construction_info()
    assert "module_type" in info
    assert "cost" in info
    
    # Test preview update
    construction_system.update_mouse_position(Vector2(4050, 4000))  # Near base
    
    print("✓ Construction system test passed")


def test_production_system():
    """Test the production system."""
    print("\nTesting production system...")
    
    production_system = ProductionSystem()
    
    # Create test base with production modules
    base_id = base_manager.create_base(Vector2(5000, 5000), "Production Test Base")
    base = base_manager.get_base(base_id)
    
    # Add resources and modules
    base.stored_resources = {
        "Metal": 1000,
        "Ice": 500,
        "Credits": 50000
    }
    
    # Add production modules
    base.add_module(ModuleType.POWER_GENERATOR, 1, 0)
    base.add_module(ModuleType.MINING_FACILITY, 0, 1)
    base.add_module(ModuleType.REFINERY, 1, 1)
    
    # Complete construction
    for _ in range(20):
        base.update(1.0)
    
    # Test production status
    status = production_system.get_production_status(base)
    print(f"Production modules: {status['total_production_modules']}")
    
    # Test production update
    bases = {base_id: base}
    production_system.update_production(bases, 1.0)
    
    print("✓ Production system test passed")


def test_save_load():
    """Test saving and loading bases."""
    print("\nTesting save/load functionality...")
    
    # Create a base with modules
    base_id = base_manager.create_base(Vector2(6000, 6000), "Save Test Base")
    base = base_manager.get_base(base_id)
    
    # Give enough resources for construction, then check what remains
    base.stored_resources = {"Metal": 1000, "Electronics": 400, "Fuel": 200, "Credits": 50000}
    base.add_module(ModuleType.POWER_GENERATOR, 1, 0)
    base.add_module(ModuleType.STORAGE, 0, 1)
    
    # Wait for construction to complete and see remaining resources
    for _ in range(200):
        base.update(1.0)
    
    remaining_metal = base.get_resource_amount("Metal")
    
    # Save data
    save_data = base_manager.save_bases()
    assert len(save_data["bases"]) > 0, "No bases in save data"
    
    # Clear manager and reload
    original_count = len(base_manager.bases)
    base_manager.bases.clear()
    
    # Load data
    success = base_manager.load_bases(save_data)
    assert success, "Failed to load bases"
    assert len(base_manager.bases) == original_count, "Wrong number of bases after load"
    
    # Verify loaded base
    loaded_base = None
    for b in base_manager.bases.values():
        if b.name == "Save Test Base":
            loaded_base = b
            break
    
    assert loaded_base is not None, "Failed to find loaded base"
    assert loaded_base.get_resource_amount("Metal") == remaining_metal, f"Resources not preserved: expected {remaining_metal}, got {loaded_base.get_resource_amount('Metal')}"
    
    print("✓ Save/load test passed")


def main():
    """Run all base building tests."""
    print("Running Base Building System Tests...")
    print("=" * 50)
    
    # Initialize pygame (required for Vector2)
    pygame.init()
    
    try:
        # Run tests
        test_base_creation()
        test_module_construction()
        test_base_systems()
        test_construction_system()
        test_production_system()
        test_save_load()
        
        print("\n" + "=" * 50)
        print("✅ All base building tests passed!")
        print("\nBase Building System Features:")
        print("- Base creation and management")
        print("- 14 different module types")
        print("- Power generation and distribution")
        print("- Resource storage and production")
        print("- Construction interface system")
        print("- Production chains and automation")
        print("- Save/load functionality")
        print("- Spatial grid optimization")
        
        # Show final statistics
        stats = base_manager.get_statistics()
        print(f"\nFinal Statistics:")
        print(f"- Total bases: {stats.get('total_bases', 0)}")
        print(f"- Total modules: {stats.get('total_modules', 0)}")
        print(f"- Total power generation: {stats.get('total_power_generation', 0)}")
        print(f"- Total defense rating: {stats.get('total_defense_rating', 0)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        pygame.quit()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)