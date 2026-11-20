"""Placing and removing modules: where the cursor lands on the grid, what the
preview says, and what building costs."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest
from pygame import Vector2

from src.base_building.base_entity import BUILDABLE, BaseModule, ModuleType, PlayerBase
from src.base_building.base_manager import BaseManager
from src.base_building.construction_system import ConstructionMode, ConstructionSystem


class Wallet:
    def __init__(self, credits):
        self.credits = credits


@pytest.fixture
def setup():
    manager = BaseManager()
    wallet = Wallet(10 ** 6)
    base_id = manager.found_base(Vector2(5000, 5000), [], wallet)
    base = manager.get_base(base_id)
    system = ConstructionSystem(manager, wallet=wallet)
    system.activate_construction(base_id)
    return manager, wallet, base, system


def cell_centre(base, gx, gy):
    return base.position + Vector2((gx + 0.5) * base.grid_size, (gy + 0.5) * base.grid_size)


def test_a_one_cell_module_lands_on_the_cell_under_the_cursor(setup):
    _, _, base, system = setup
    system.set_selected_module_type(ModuleType.POWER_GENERATOR)
    system.update_mouse_position(cell_centre(base, 3, -2) + Vector2(10, -10))
    assert (int(system.mouse_grid_position.x), int(system.mouse_grid_position.y)) == (3, -2)
    assert system.preview_positions == [(3, -2)]


def test_a_two_cell_module_is_centred_on_the_cursor(setup):
    _, _, base, system = setup
    system.set_selected_module_type(ModuleType.MINING_FACILITY)
    # The corner shared by four cells: the module covers all four
    corner = base.position + Vector2(4 * base.grid_size, 3 * base.grid_size)
    system.update_mouse_position(corner)
    assert sorted(system.preview_positions) == [(3, 2), (3, 3), (4, 2), (4, 3)]


def test_the_preview_is_valid_only_on_free_cells_and_when_affordable(setup):
    _, wallet, base, system = setup
    system.set_selected_module_type(ModuleType.POWER_GENERATOR)
    base.add_resource("fuel_cells", 4)
    system.update_mouse_position(cell_centre(base, 3, -2))
    assert system.preview_valid
    system.update_mouse_position(cell_centre(base, 0, 0))               # on the command center
    assert not system.preview_valid
    system.update_mouse_position(cell_centre(base, 40, 0))              # off the grid
    assert not system.preview_valid
    wallet.credits = 0
    system.update_mouse_position(cell_centre(base, 3, -2))
    assert not system.preview_valid


def test_building_takes_credits_and_goods_and_places_the_module(setup):
    _, wallet, base, system = setup
    base.stored_resources.clear()
    base.add_resource("fuel_cells", 4)
    start = wallet.credits
    system.set_selected_module_type(ModuleType.POWER_GENERATOR)
    system.update_mouse_position(cell_centre(base, 3, -2))
    assert system.try_construct()
    assert base.modules[(3, -2)].module_type == ModuleType.POWER_GENERATOR
    assert wallet.credits == start - BaseModule.MODULE_DEFINITIONS[ModuleType.POWER_GENERATOR].cost_credits
    assert base.get_resource_amount("fuel_cells") == 0
    assert not system.try_construct()                                  # the cell is taken now


def test_nothing_is_built_when_the_preview_is_invalid(setup):
    _, wallet, base, system = setup
    base.stored_resources.clear()                                      # no goods
    start = wallet.credits
    system.set_selected_module_type(ModuleType.POWER_GENERATOR)
    system.update_mouse_position(cell_centre(base, 3, -2))
    assert not system.try_construct()
    assert (3, -2) not in base.modules and wallet.credits == start


def test_remove_mode_targets_the_whole_module_and_never_the_command_center(setup):
    _, wallet, base, system = setup
    base.add_module(ModuleType.MINING_FACILITY, 3, 0, free=True)
    system.set_construction_mode(ConstructionMode.REMOVE)
    system.update_mouse_position(cell_centre(base, 4, 1))              # the far corner of the 2x2
    assert system.preview_valid and sorted(system.preview_positions) == [(3, 0), (3, 1), (4, 0), (4, 1)]
    assert system.try_construct()
    assert (3, 0) not in base.modules and (4, 1) not in base.modules
    system.update_mouse_position(cell_centre(base, 0, 0))
    assert not system.preview_valid and not system.try_construct()


def test_the_number_keys_choose_the_buildable_modules_and_nothing_else(setup):
    _, _, _, system = setup
    for index, module_type in enumerate(BUILDABLE):
        key = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6][index]
        assert system.handle_input(pygame.event.Event(pygame.KEYDOWN, key=key))
        assert system.selected_module_type == module_type
    assert not system.handle_input(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_9))
    system.set_selected_module_type(ModuleType.COMMAND_CENTER)         # not buildable: ignored
    assert system.selected_module_type == BUILDABLE[-1]


def test_modes_and_the_grid_toggle(setup):
    _, _, _, system = setup
    system.handle_input(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
    assert system.construction_mode == ConstructionMode.REMOVE
    system.handle_input(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=(0, 0)))
    assert system.construction_mode == ConstructionMode.PLACE
    shown = system.show_grid
    system.handle_input(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB))
    assert system.show_grid is not shown


def test_the_info_names_what_is_missing(setup):
    _, wallet, base, system = setup
    base.stored_resources.clear()
    wallet.credits = 100
    system.set_selected_module_type(ModuleType.REFINERY)
    info = system.get_construction_info()
    assert not info["can_afford"] and "credits" in info["missing"] and "metal_ore" in info["missing"]
    assert info["label"] == "Refinery" and info["cost_credits"] == 5000


def test_an_inactive_system_ignores_input_and_draws_nothing(setup):
    _, _, _, system = setup
    system.deactivate_construction()
    assert not system.handle_input(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1))
    surface = pygame.Surface((200, 200))
    system.draw_world(surface, Vector2(0, 0))
    assert surface.get_at((100, 100))[:3] == (0, 0, 0)
