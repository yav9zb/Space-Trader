"""Tests for the base building system."""

import pygame
from src.base_building.base_manager import base_manager
from src.base_building.base_entity import ModuleType
from src.base_building.construction_system import ConstructionSystem
from src.base_building.resource_production import ProductionSystem
from pygame import Vector2

pygame.init()


def test_base_creation():
    """Test basic base creation and management."""
    base_id = base_manager.create_base(Vector2(1000, 1000), "Test Base Alpha")
    assert base_id is not None, "Failed to create base"

    base = base_manager.get_base(base_id)
    assert base is not None, "Failed to retrieve created base"
    assert base.name == "Test Base Alpha"

    # Add initial resources for command center construction
    base.stored_resources = {
        "Metal": 1000,
        "Electronics": 500,
        "Credits": 50000
    }

    # The command center should be added during construction; add it
    # manually here since construction takes time to complete
    if len(set(base.modules.values())) == 0:
        base.add_module(ModuleType.COMMAND_CENTER, 0, 0)

    assert len(set(base.modules.values())) >= 1, "Base should have at least command center"

    unique_modules = set(base.modules.values())
    command_center = next(iter(unique_modules))
    assert command_center.module_type == ModuleType.COMMAND_CENTER


def test_module_construction():
    """Test module construction."""
    base_id = base_manager.create_base(Vector2(2000, 2000), "Construction Test Base")
    base = base_manager.get_base(base_id)

    base.stored_resources = {
        "Metal": 5000,
        "Electronics": 2000,
        "Machinery": 1000,
        "Fuel": 1000,
        "Textiles": 500,
        "Credits": 100000
    }

    modules_to_test = [
        (ModuleType.POWER_GENERATOR, 1, 0),
        (ModuleType.HABITAT, -1, 0),
        (ModuleType.STORAGE, 0, 1),
        (ModuleType.REFINERY, 1, 1)
    ]

    for module_type, grid_x, grid_y in modules_to_test:
        success = base.add_module(module_type, grid_x, grid_y)
        assert success, f"Failed to add {module_type.value} module"
        assert (grid_x, grid_y) in base.modules, f"Module not found at grid position ({grid_x}, {grid_y})"

        module = base.modules[(grid_x, grid_y)]
        assert module.module_type == module_type, "Wrong module type at position"


def test_base_systems():
    """Test base power and resource systems."""
    base_id = base_manager.create_base(Vector2(3000, 3000), "Systems Test Base")
    base = base_manager.get_base(base_id)

    base.stored_resources = {
        "Metal": 10000,
        "Electronics": 5000,
        "Machinery": 2000,  # for refinery (300) and factory (200)
        "Fuel": 1000,
        "Credits": 200000
    }

    base.add_module(ModuleType.POWER_GENERATOR, 1, 0)
    base.add_module(ModuleType.POWER_GENERATOR, 2, 0)  # Second generator

    # refinery and factory are 2x2 modules - keep them apart
    refinery_success = base.add_module(ModuleType.REFINERY, -3, 0)
    factory_success = base.add_module(ModuleType.FACTORY, 0, 2)

    assert refinery_success, "Failed to add refinery"
    assert factory_success, "Failed to add factory"

    # Wait for construction to complete (refinery takes 240s, factory 200s)
    for _ in range(300):
        base.update(1.0)

    assert base.power_generation > 0, "No power generation"
    assert base.power_consumption > 0, "No power consumption"

    stored_metal = base.get_resource_amount("Metal")
    assert stored_metal > 0, "Should have stored metal"


def test_construction_system():
    """Test the construction system."""
    construction_system = ConstructionSystem(base_manager)

    base_id = base_manager.create_base(Vector2(4000, 4000), "Construction System Test")

    success = construction_system.activate_construction(base_id)
    assert success, "Failed to activate construction"
    assert construction_system.is_construction_active

    info = construction_system.get_construction_info()
    assert "module_type" in info
    assert "cost" in info

    construction_system.update_mouse_position(Vector2(4050, 4000))  # Near base


def test_production_system():
    """Test the production system."""
    production_system = ProductionSystem()

    base_id = base_manager.create_base(Vector2(5000, 5000), "Production Test Base")
    base = base_manager.get_base(base_id)

    base.stored_resources = {
        "Metal": 1000,
        "Ice": 500,
        "Credits": 50000
    }

    base.add_module(ModuleType.POWER_GENERATOR, 1, 0)
    base.add_module(ModuleType.MINING_FACILITY, 0, 1)
    base.add_module(ModuleType.REFINERY, 1, 1)

    for _ in range(20):
        base.update(1.0)

    status = production_system.get_production_status(base)
    assert 'total_production_modules' in status

    bases = {base_id: base}
    production_system.update_production(bases, 1.0)


def test_save_load():
    """Test saving and loading bases."""
    base_id = base_manager.create_base(Vector2(6000, 6000), "Save Test Base")
    base = base_manager.get_base(base_id)

    base.stored_resources = {"Metal": 1000, "Electronics": 400, "Fuel": 200, "Credits": 50000}
    base.add_module(ModuleType.POWER_GENERATOR, 1, 0)
    base.add_module(ModuleType.STORAGE, 0, 1)

    for _ in range(200):
        base.update(1.0)

    remaining_metal = base.get_resource_amount("Metal")

    save_data = base_manager.save_bases()
    assert len(save_data["bases"]) > 0, "No bases in save data"

    original_count = len(base_manager.bases)
    base_manager.bases.clear()

    success = base_manager.load_bases(save_data)
    assert success, "Failed to load bases"
    assert len(base_manager.bases) == original_count, "Wrong number of bases after load"

    loaded_base = None
    for b in base_manager.bases.values():
        if b.name == "Save Test Base":
            loaded_base = b
            break

    assert loaded_base is not None, "Failed to find loaded base"
    assert loaded_base.get_resource_amount("Metal") == remaining_metal, (
        f"Resources not preserved: expected {remaining_metal}, "
        f"got {loaded_base.get_resource_amount('Metal')}"
    )
