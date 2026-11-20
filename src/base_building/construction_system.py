"""
Construction System - placing and removing modules on a base's grid.

A cell (gx, gy) of a base spans [gx * grid_size, (gx + 1) * grid_size) from the
base's position, so the grid is centred on the base. A module's grid position
is its top-left cell.
"""

import math
import pygame
from pygame import Vector2
from typing import Any, Dict, List, Tuple
from enum import Enum

from .base_entity import PlayerBase, BaseModule, ModuleType, BUILDABLE
from .base_manager import BaseManager


class ConstructionMode(Enum):
    PLACE = "place"
    REMOVE = "remove"


class ConstructionSystem:
    """Handles construction mechanics and validation for one base at a time."""

    def __init__(self, base_manager: BaseManager, wallet=None):
        self.base_manager = base_manager
        self.wallet = wallet                       # anything with .credits: the ship
        self.construction_mode = ConstructionMode.PLACE
        self.selected_module_type = BUILDABLE[0]
        self.selected_base_id = None
        self.is_construction_active = False

        self.mouse_grid_position = Vector2(0, 0)   # the top-left cell under the cursor
        self.preview_valid = False
        self.show_grid = True
        self.preview_positions: List[Tuple[int, int]] = []

    # Activation ------------------------------------------------------------------------------------

    def activate_construction(self, base_id: str) -> bool:
        if not self.base_manager.get_base(base_id):
            return False
        self.selected_base_id = base_id
        self.is_construction_active = True
        self._update_preview()
        return True

    def deactivate_construction(self) -> None:
        self.is_construction_active = False
        self.selected_base_id = None
        self.preview_positions = []
        self.preview_valid = False

    def _base(self):
        return self.base_manager.get_base(self.selected_base_id) if self.selected_base_id else None

    def _credits(self) -> int:
        return int(getattr(self.wallet, "credits", 0))

    # Choosing ----------------------------------------------------------------------------------------

    def set_construction_mode(self, mode: ConstructionMode) -> None:
        self.construction_mode = mode
        self._update_preview()

    def set_selected_module_type(self, module_type: ModuleType) -> None:
        if module_type in BUILDABLE:
            self.selected_module_type = module_type
            self.construction_mode = ConstructionMode.PLACE
            self._update_preview()

    # The cursor --------------------------------------------------------------------------------------

    def update_mouse_position(self, mouse_world_pos: Vector2) -> None:
        """Follow the cursor: the module being placed is centred on it."""
        base = self._base()
        if base is None:
            return
        relative = (Vector2(mouse_world_pos) - base.position) / base.grid_size
        if self.construction_mode == ConstructionMode.PLACE:
            size = BaseModule.MODULE_DEFINITIONS[self.selected_module_type].size
            self.mouse_grid_position = Vector2(round(relative.x - size / 2), round(relative.y - size / 2))
        else:
            self.mouse_grid_position = Vector2(math.floor(relative.x), math.floor(relative.y))
        self._update_preview()

    def _update_preview(self) -> None:
        base = self._base()
        if base is None:
            self.preview_positions = []
            self.preview_valid = False
            return
        gx, gy = int(self.mouse_grid_position.x), int(self.mouse_grid_position.y)
        if self.construction_mode == ConstructionMode.PLACE:
            size = BaseModule.MODULE_DEFINITIONS[self.selected_module_type].size
            self.preview_positions = [(gx + x, gy + y) for x in range(size) for y in range(size)]
            self.preview_valid = (base.is_valid_position(gx, gy, self.selected_module_type)
                                  and base.can_afford_module(self.selected_module_type, self._credits()))
        else:
            module = base.modules.get((gx, gy))
            if module is not None:
                size = module.stats.size
                mx, my = int(module.grid_position.x), int(module.grid_position.y)
                self.preview_positions = [(mx + x, my + y) for x in range(size) for y in range(size)]
            else:
                self.preview_positions = [(gx, gy)]
            self.preview_valid = module is not None and module.module_type != ModuleType.COMMAND_CENTER

    # Acting ---------------------------------------------------------------------------------------------

    def try_construct(self) -> bool:
        """Place or remove at the cursor."""
        base = self._base()
        if base is None or not self.preview_valid:
            return False
        gx, gy = int(self.mouse_grid_position.x), int(self.mouse_grid_position.y)
        if self.construction_mode == ConstructionMode.PLACE:
            done = base.add_module(self.selected_module_type, gx, gy, wallet=self.wallet)
        else:
            done = base.remove_module(gx, gy, wallet=self.wallet)
        self._update_preview()
        return done

    def get_construction_info(self) -> Dict[str, Any]:
        """The module being placed: what it is, costs, and what is missing."""
        stats = BaseModule.MODULE_DEFINITIONS[self.selected_module_type]
        base = self._base()
        missing = base.shortfall(self.selected_module_type, self._credits()) if base else {}
        return {
            "module_type": self.selected_module_type.value,
            "label": stats.label,
            "blurb": stats.blurb,
            "cost_credits": stats.cost_credits,
            "cost_goods": dict(stats.cost_goods),
            "build_time": stats.build_time,
            "power_consumption": stats.power_consumption,
            "power_generation": stats.power_generation,
            "storage_capacity": stats.storage_capacity,
            "size": stats.size,
            "missing": missing,
            "can_afford": base is not None and not missing,
            "can_place": self.preview_valid,
        }

    # Drawing -----------------------------------------------------------------------------------------------

    def draw_world(self, screen, camera_offset: Vector2) -> None:
        """The grid and the placement preview, the parts that sit in the world."""
        base = self._base()
        if not self.is_construction_active or base is None:
            return
        grid = base.grid_size
        half = base.max_grid_size // 2
        if self.show_grid:
            for i in range(-half, half + 1):
                x = base.position.x + i * grid - camera_offset.x
                y = base.position.y + i * grid - camera_offset.y
                top = base.position.y - half * grid - camera_offset.y
                bottom = base.position.y + half * grid - camera_offset.y
                left = base.position.x - half * grid - camera_offset.x
                right = base.position.x + half * grid - camera_offset.x
                color = (70, 78, 104) if i % 5 == 0 else (42, 48, 70)
                pygame.draw.line(screen, color, (x, top), (x, bottom), 1)
                pygame.draw.line(screen, color, (left, y), (right, y), 1)

        if self.preview_positions:
            if self.construction_mode == ConstructionMode.REMOVE:
                color = (255, 140, 60) if self.preview_valid else (140, 90, 60)
            else:
                color = (80, 235, 130) if self.preview_valid else (240, 90, 90)
            for gx, gy in self.preview_positions:
                rect = pygame.Rect(base.position.x + gx * grid - camera_offset.x,
                                   base.position.y + gy * grid - camera_offset.y, grid, grid)
                overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
                overlay.fill((*color, 70))
                screen.blit(overlay, rect)
                pygame.draw.rect(screen, color, rect, 2)

    # Input ----------------------------------------------------------------------------------------------------

    def handle_input(self, event) -> bool:
        """Keys and clicks that build. Returns True if the event was used."""
        if not self.is_construction_active:
            return False
        if event.type == pygame.KEYDOWN:
            digits = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]
            if event.key in digits[:len(BUILDABLE)]:
                self.set_selected_module_type(BUILDABLE[digits.index(event.key)])
                return True
            if event.key == pygame.K_TAB:
                self.show_grid = not self.show_grid
                return True
            if event.key == pygame.K_p:
                self.set_construction_mode(ConstructionMode.PLACE)
                return True
            if event.key == pygame.K_r:
                self.set_construction_mode(ConstructionMode.REMOVE)
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                return self.try_construct()
            if event.button == 3:
                self.set_construction_mode(ConstructionMode.PLACE)
                return True
        return False
