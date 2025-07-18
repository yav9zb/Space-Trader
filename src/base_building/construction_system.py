"""
Construction System - Handles base building mechanics and validation.
"""

import pygame
from pygame import Vector2
import time
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from .base_entity import PlayerBase, BaseModule, ModuleType
from .base_manager import BaseManager


class ConstructionMode(Enum):
    """Different construction modes."""
    PLACE = "place"
    REMOVE = "remove"
    UPGRADE = "upgrade"
    REPAIR = "repair"


class ConstructionSystem:
    """Handles construction interface and building mechanics."""
    
    def __init__(self, base_manager: BaseManager):
        self.base_manager = base_manager
        
        # Construction state
        self.construction_mode = ConstructionMode.PLACE
        self.selected_module_type = ModuleType.HABITAT
        self.selected_base_id: Optional[str] = None
        self.is_construction_active = False
        
        # Mouse and input state
        self.mouse_grid_position = Vector2(0, 0)
        self.preview_valid = False
        self.show_grid = True
        self.snap_to_grid = True
        
        # Construction preview
        self.preview_module: Optional[BaseModule] = None
        self.preview_positions: List[Tuple[int, int]] = []
        
        # UI state
        self.show_construction_menu = False
        self.show_module_info = False
        self.construction_menu_scroll = 0
        
        # Build queue for automation
        self.build_queue: List[Dict[str, Any]] = []
        self.auto_build_enabled = False
        
        # Performance settings
        self.grid_render_distance = 10  # Only show grid within this distance
        
    def activate_construction(self, base_id: str) -> bool:
        """Activate construction mode for a specific base."""
        base = self.base_manager.get_base(base_id)
        if not base:
            return False
        
        self.selected_base_id = base_id
        self.is_construction_active = True
        self.show_construction_menu = True
        self._update_preview()
        
        return True
    
    def deactivate_construction(self) -> None:
        """Deactivate construction mode."""
        self.is_construction_active = False
        self.show_construction_menu = False
        self.selected_base_id = None
        self.preview_module = None
        self.preview_positions.clear()
    
    def set_construction_mode(self, mode: ConstructionMode) -> None:
        """Set the construction mode."""
        self.construction_mode = mode
        self._update_preview()
    
    def set_selected_module_type(self, module_type: ModuleType) -> None:
        """Set the type of module to place."""
        self.selected_module_type = module_type
        self._update_preview()
    
    def update_mouse_position(self, mouse_world_pos: Vector2) -> None:
        """Update mouse position for construction preview."""
        if not self.is_construction_active or not self.selected_base_id:
            return
        
        base = self.base_manager.get_base(self.selected_base_id)
        if not base:
            return
        
        # Convert world position to grid position
        relative_pos = mouse_world_pos - base.position
        
        if self.snap_to_grid:
            grid_x = round(relative_pos.x / base.grid_size)
            grid_y = round(relative_pos.y / base.grid_size)
        else:
            grid_x = relative_pos.x / base.grid_size
            grid_y = relative_pos.y / base.grid_size
        
        self.mouse_grid_position = Vector2(grid_x, grid_y)
        self._update_preview()
    
    def _update_preview(self) -> None:
        """Update construction preview based on current state."""
        if not self.is_construction_active or not self.selected_base_id:
            self.preview_module = None
            self.preview_positions.clear()
            self.preview_valid = False
            return
        
        base = self.base_manager.get_base(self.selected_base_id)
        if not base:
            return
        
        grid_x, grid_y = int(self.mouse_grid_position.x), int(self.mouse_grid_position.y)
        
        if self.construction_mode == ConstructionMode.PLACE:
            # Create preview module
            self.preview_module = BaseModule(self.selected_module_type, grid_x, grid_y)
            
            # Check if placement is valid
            self.preview_valid = (
                base.is_valid_position(grid_x, grid_y, self.selected_module_type) and
                base.can_afford_module(self.selected_module_type)
            )
            
            # Update preview positions
            size = self.preview_module.stats.size
            self.preview_positions = [
                (grid_x + x, grid_y + y) 
                for x in range(size) 
                for y in range(size)
            ]
        
        elif self.construction_mode == ConstructionMode.REMOVE:
            # Check if there's a module to remove
            self.preview_valid = (grid_x, grid_y) in base.modules
            self.preview_positions = [(grid_x, grid_y)] if self.preview_valid else []
            
        else:
            self.preview_valid = False
            self.preview_positions.clear()
    
    def try_construct(self) -> bool:
        """Attempt to construct/modify at current mouse position."""
        if not self.is_construction_active or not self.selected_base_id:
            return False
        
        base = self.base_manager.get_base(self.selected_base_id)
        if not base:
            return False
        
        grid_x, grid_y = int(self.mouse_grid_position.x), int(self.mouse_grid_position.y)
        
        if self.construction_mode == ConstructionMode.PLACE:
            if self.preview_valid:
                success = base.add_module(self.selected_module_type, grid_x, grid_y)
                if success:
                    self._update_preview()  # Refresh preview after construction
                return success
        
        elif self.construction_mode == ConstructionMode.REMOVE:
            if self.preview_valid:
                success = base.remove_module(grid_x, grid_y)
                if success:
                    self._update_preview()  # Refresh preview after removal
                return success
        
        return False
    
    def get_module_at_position(self, grid_x: int, grid_y: int) -> Optional[BaseModule]:
        """Get module at grid position."""
        if not self.selected_base_id:
            return None
        
        base = self.base_manager.get_base(self.selected_base_id)
        if not base:
            return None
        
        return base.modules.get((grid_x, grid_y))
    
    def get_construction_info(self) -> Dict[str, Any]:
        """Get information about current construction state."""
        if not self.selected_module_type:
            return {}
        
        module_stats = BaseModule.MODULE_DEFINITIONS[self.selected_module_type]
        
        info = {
            'module_type': self.selected_module_type.value,
            'cost': module_stats.cost,
            'build_time': module_stats.build_time,
            'power_consumption': module_stats.power_consumption,
            'power_generation': module_stats.power_generation,
            'storage_capacity': module_stats.storage_capacity,
            'crew_capacity': module_stats.crew_capacity,
            'production_rate': module_stats.production_rate,
            'defense_rating': module_stats.defense_rating,
            'size': module_stats.size,
            'can_afford': False,
            'can_place': self.preview_valid
        }
        
        # Check affordability
        if self.selected_base_id:
            base = self.base_manager.get_base(self.selected_base_id)
            if base:
                info['can_afford'] = base.can_afford_module(self.selected_module_type)
        
        return info
    
    def add_to_build_queue(self, module_type: ModuleType, grid_x: int, grid_y: int) -> bool:
        """Add construction to build queue."""
        if not self.selected_base_id:
            return False
        
        base = self.base_manager.get_base(self.selected_base_id)
        if not base or not base.is_valid_position(grid_x, grid_y, module_type):
            return False
        
        build_item = {
            'base_id': self.selected_base_id,
            'module_type': module_type,
            'grid_x': grid_x,
            'grid_y': grid_y,
            'queued_time': time.time()
        }
        
        self.build_queue.append(build_item)
        return True
    
    def process_build_queue(self) -> None:
        """Process automatic building from queue."""
        if not self.auto_build_enabled or not self.build_queue:
            return
        
        # Process one item per call to avoid lag
        if self.build_queue:
            build_item = self.build_queue[0]
            
            base = self.base_manager.get_base(build_item['base_id'])
            if base and base.can_afford_module(build_item['module_type']):
                if base.is_valid_position(build_item['grid_x'], build_item['grid_y'], 
                                        build_item['module_type']):
                    success = base.add_module(
                        build_item['module_type'], 
                        build_item['grid_x'], 
                        build_item['grid_y']
                    )
                    
                    if success:
                        self.build_queue.pop(0)
                    else:
                        # Remove invalid build item
                        self.build_queue.pop(0)
                else:
                    # Position no longer valid, remove from queue
                    self.build_queue.pop(0)
    
    def draw_construction_interface(self, screen, camera_offset: Vector2) -> None:
        """Draw construction interface elements."""
        if not self.is_construction_active or not self.selected_base_id:
            return
        
        base = self.base_manager.get_base(self.selected_base_id)
        if not base:
            return
        
        # Draw grid
        if self.show_grid:
            self._draw_construction_grid(screen, base, camera_offset)
        
        # Draw preview
        self._draw_construction_preview(screen, base, camera_offset)
        
        # Draw construction menu
        if self.show_construction_menu:
            self._draw_construction_menu(screen)
    
    def _draw_construction_grid(self, screen, base: PlayerBase, camera_offset: Vector2) -> None:
        """Draw construction grid."""
        base_screen_pos = base.position - camera_offset
        screen_rect = screen.get_rect()
        
        # Only draw grid if base is visible
        if (base_screen_pos.x < -200 or base_screen_pos.x > screen_rect.width + 200 or
            base_screen_pos.y < -200 or base_screen_pos.y > screen_rect.height + 200):
            return
        
        grid_color = (100, 100, 100, 128)
        grid_size = base.grid_size
        
        # Calculate grid bounds to draw
        half_grid = base.max_grid_size // 2
        
        # Draw vertical lines
        for x in range(-half_grid, half_grid + 1):
            world_x = base.position.x + x * grid_size
            screen_x = world_x - camera_offset.x
            
            if -50 <= screen_x <= screen_rect.width + 50:
                start_y = base.position.y - half_grid * grid_size - camera_offset.y
                end_y = base.position.y + half_grid * grid_size - camera_offset.y
                pygame.draw.line(screen, grid_color[:3], 
                               (screen_x, start_y), (screen_x, end_y), 1)
        
        # Draw horizontal lines
        for y in range(-half_grid, half_grid + 1):
            world_y = base.position.y + y * grid_size
            screen_y = world_y - camera_offset.y
            
            if -50 <= screen_y <= screen_rect.height + 50:
                start_x = base.position.x - half_grid * grid_size - camera_offset.x
                end_x = base.position.x + half_grid * grid_size - camera_offset.x
                pygame.draw.line(screen, grid_color[:3], 
                               (start_x, screen_y), (end_x, screen_y), 1)
    
    def _draw_construction_preview(self, screen, base: PlayerBase, camera_offset: Vector2) -> None:
        """Draw construction preview."""
        if not self.preview_positions:
            return
        
        grid_size = base.grid_size
        
        # Determine preview color
        if self.construction_mode == ConstructionMode.PLACE:
            color = (0, 255, 0, 128) if self.preview_valid else (255, 0, 0, 128)
        elif self.construction_mode == ConstructionMode.REMOVE:
            color = (255, 100, 0, 128)
        else:
            color = (255, 255, 0, 128)
        
        # Draw preview squares
        for grid_x, grid_y in self.preview_positions:
            world_pos = Vector2(
                base.position.x + grid_x * grid_size,
                base.position.y + grid_y * grid_size
            )
            screen_pos = world_pos - camera_offset
            
            preview_rect = pygame.Rect(
                screen_pos.x - grid_size // 2,
                screen_pos.y - grid_size // 2,
                grid_size,
                grid_size
            )
            
            # Create surface with alpha for transparency
            preview_surface = pygame.Surface((grid_size, grid_size))
            preview_surface.set_alpha(color[3])
            preview_surface.fill(color[:3])
            screen.blit(preview_surface, preview_rect)
            
            # Draw border
            pygame.draw.rect(screen, color[:3], preview_rect, 2)
    
    def _draw_construction_menu(self, screen) -> None:
        """Draw construction menu UI."""
        if not pygame.font.get_init():
            return
        
        screen_rect = screen.get_rect()
        menu_width = 300
        menu_height = 400
        menu_x = screen_rect.width - menu_width - 10
        menu_y = 10
        
        # Menu background
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        pygame.draw.rect(screen, (40, 40, 60), menu_rect)
        pygame.draw.rect(screen, (100, 100, 120), menu_rect, 2)
        
        font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 18)
        
        y_offset = menu_y + 10
        
        # Title
        title_text = font.render("Construction Menu", True, (255, 255, 255))
        screen.blit(title_text, (menu_x + 10, y_offset))
        y_offset += 30
        
        # Mode selection
        mode_text = small_font.render(f"Mode: {self.construction_mode.value.title()}", 
                                     True, (200, 200, 200))
        screen.blit(mode_text, (menu_x + 10, y_offset))
        y_offset += 20
        
        # Current module info
        if self.construction_mode == ConstructionMode.PLACE:
            info = self.get_construction_info()
            
            # Module name
            module_name = self.selected_module_type.value.replace('_', ' ').title()
            name_text = font.render(module_name, True, (255, 255, 255))
            screen.blit(name_text, (menu_x + 10, y_offset))
            y_offset += 25
            
            # Cost
            cost_text = small_font.render("Cost:", True, (200, 200, 200))
            screen.blit(cost_text, (menu_x + 10, y_offset))
            y_offset += 15
            
            for resource, amount in info['cost'].items():
                cost_color = (0, 255, 0) if info['can_afford'] else (255, 100, 100)
                cost_line = small_font.render(f"  {resource}: {amount}", True, cost_color)
                screen.blit(cost_line, (menu_x + 20, y_offset))
                y_offset += 15
            
            # Stats
            y_offset += 5
            stats_text = small_font.render("Stats:", True, (200, 200, 200))
            screen.blit(stats_text, (menu_x + 10, y_offset))
            y_offset += 15
            
            stats = [
                ("Power Gen", info['power_generation']),
                ("Power Use", info['power_consumption']),
                ("Storage", info['storage_capacity']),
                ("Crew", info['crew_capacity']),
                ("Defense", info['defense_rating'])
            ]
            
            for stat_name, stat_value in stats:
                if stat_value > 0:
                    stat_line = small_font.render(f"  {stat_name}: {stat_value}", 
                                                True, (180, 180, 180))
                    screen.blit(stat_line, (menu_x + 20, y_offset))
                    y_offset += 15
        
        # Instructions
        y_offset += 10
        instructions = [
            "Left Click: Construct/Remove",
            "Right Click: Cancel",
            "Tab: Toggle Grid",
            "1-9: Select Module Type"
        ]
        
        for instruction in instructions:
            if y_offset < menu_y + menu_height - 20:
                inst_text = small_font.render(instruction, True, (150, 150, 150))
                screen.blit(inst_text, (menu_x + 10, y_offset))
                y_offset += 15
    
    def handle_input(self, event) -> bool:
        """Handle construction-related input. Returns True if event was consumed."""
        if not self.is_construction_active:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.show_grid = not self.show_grid
                return True
            
            elif event.key == pygame.K_ESCAPE:
                self.deactivate_construction()
                return True
            
            elif event.key == pygame.K_1:
                self.set_selected_module_type(ModuleType.HABITAT)
                return True
            elif event.key == pygame.K_2:
                self.set_selected_module_type(ModuleType.POWER_GENERATOR)
                return True
            elif event.key == pygame.K_3:
                self.set_selected_module_type(ModuleType.STORAGE)
                return True
            elif event.key == pygame.K_4:
                self.set_selected_module_type(ModuleType.REFINERY)
                return True
            elif event.key == pygame.K_5:
                self.set_selected_module_type(ModuleType.FACTORY)
                return True
            elif event.key == pygame.K_6:
                self.set_selected_module_type(ModuleType.TURRET)
                return True
            elif event.key == pygame.K_7:
                self.set_selected_module_type(ModuleType.TRADE_HUB)
                return True
            
            elif event.key == pygame.K_p:
                self.set_construction_mode(ConstructionMode.PLACE)
                return True
            elif event.key == pygame.K_r:
                self.set_construction_mode(ConstructionMode.REMOVE)
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                return self.try_construct()
            elif event.button == 3:  # Right click
                self.deactivate_construction()
                return True
        
        return False