"""
Base Construction State - Handles the base building interface.
"""

import pygame
from pygame import Vector2
from enum import Enum, auto
from typing import Optional, Dict, Any

try:
    from ..states.game_state import State, GameStates
    from ..base_building.base_manager import base_manager
    from ..base_building.construction_system import ConstructionSystem, ConstructionMode
    from ..base_building.resource_production import ProductionSystem
    from ..base_building.base_entity import ModuleType
    from ..input.control_schemes import control_scheme_manager
except ImportError:
    from states.game_state import State, GameStates
    from base_building.base_manager import base_manager
    from base_building.construction_system import ConstructionSystem, ConstructionMode
    from base_building.resource_production import ProductionSystem
    from base_building.base_entity import ModuleType
    from input.control_schemes import control_scheme_manager


class BaseConstructionState(State):
    """Game state for base construction and management."""
    
    def __init__(self, game, base_id: str = None, previous_state=None):
        super().__init__(game)
        self.base_id = base_id
        self.previous_state = previous_state or GameStates.PLAYING
        
        # Initialize construction system
        self.construction_system = ConstructionSystem(base_manager)
        self.production_system = ProductionSystem()
        
        # UI state
        self.show_base_info = True
        self.show_production_info = False
        self.show_help = False
        self.selected_tab = "construction"  # construction, production, management
        
        # Camera control for construction view
        self.camera_speed = 200
        self.zoom_level = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 2.0
        
        # Mouse state
        self.mouse_world_pos = Vector2(0, 0)
        self.is_dragging = False
        self.drag_start = Vector2(0, 0)
        
        # Activate construction for the specified base
        if self.base_id:
            self.construction_system.activate_construction(self.base_id)
    
    def update(self, delta_time):
        """Update construction state."""
        # Update base manager
        if hasattr(self.game, 'player') and hasattr(self.game.player, 'position'):
            player_pos = self.game.player.position
        else:
            player_pos = Vector2(0, 0)
        
        base_manager.update(delta_time, player_pos)
        
        # Update production system
        self.production_system.update_production(base_manager.bases, delta_time)
        
        # Update mouse world position
        self._update_mouse_world_position()
        
        # Update construction system
        if self.construction_system.is_construction_active:
            self.construction_system.update_mouse_position(self.mouse_world_pos)
            self.construction_system.process_build_queue()
    
    def _update_mouse_world_position(self):
        """Update mouse world position based on camera."""
        mouse_pos = pygame.mouse.get_pos()
        camera_offset = getattr(self.game, 'camera_offset', Vector2(0, 0))
        
        # Apply zoom
        screen_center = Vector2(self.game.screen.get_width() // 2, self.game.screen.get_height() // 2)
        mouse_relative = Vector2(mouse_pos) - screen_center
        mouse_relative /= self.zoom_level
        
        self.mouse_world_pos = camera_offset + screen_center + mouse_relative
    
    def render(self, screen):
        """Render construction interface."""
        # Clear screen
        screen.fill((20, 20, 40))
        
        # Get camera offset
        camera_offset = getattr(self.game, 'camera_offset', Vector2(0, 0))
        
        # Draw bases
        if hasattr(self.game, 'player'):
            player_pos = self.game.player.position
        else:
            player_pos = Vector2(0, 0)
        
        base_manager.draw(screen, camera_offset, player_pos)
        
        # Draw construction interface
        if self.construction_system.is_construction_active:
            self.construction_system.draw_construction_interface(screen, camera_offset)
        
        # Draw UI panels
        self._draw_ui_panels(screen)
        
        # Draw help overlay
        if self.show_help:
            self._draw_help_overlay(screen)
    
    def _draw_ui_panels(self, screen):
        """Draw UI panels for base management."""
        if not pygame.font.get_init():
            return
        
        screen_rect = screen.get_rect()
        
        # Main info panel (left side)
        if self.show_base_info:
            self._draw_base_info_panel(screen)
        
        # Tab system (top)
        self._draw_tab_bar(screen)
        
        # Content based on selected tab
        if self.selected_tab == "construction":
            # Construction interface is handled by construction_system
            pass
        elif self.selected_tab == "production":
            self._draw_production_panel(screen)
        elif self.selected_tab == "management":
            self._draw_management_panel(screen)
        
        # Status bar (bottom)
        self._draw_status_bar(screen)
    
    def _draw_base_info_panel(self, screen):
        """Draw base information panel."""
        if not self.base_id:
            return
        
        base = base_manager.get_base(self.base_id)
        if not base:
            return
        
        panel_width = 250
        panel_height = 300
        panel_x = 10
        panel_y = 60
        
        # Panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (40, 40, 60), panel_rect)
        pygame.draw.rect(screen, (100, 100, 120), panel_rect, 2)
        
        font = pygame.font.Font(None, 20)
        small_font = pygame.font.Font(None, 16)
        
        y_offset = panel_y + 10
        
        # Base name
        name_text = font.render(base.name, True, (255, 255, 255))
        screen.blit(name_text, (panel_x + 10, y_offset))
        y_offset += 25
        
        # Position
        pos_text = small_font.render(f"Position: ({base.position.x:.0f}, {base.position.y:.0f})", 
                                   True, (200, 200, 200))
        screen.blit(pos_text, (panel_x + 10, y_offset))
        y_offset += 20
        
        # Power status
        power_color = (0, 255, 0) if base.power_generation >= base.power_consumption else (255, 255, 0)
        power_text = small_font.render(f"Power: {base.power_generation}/{base.power_consumption}", 
                                     True, power_color)
        screen.blit(power_text, (panel_x + 10, y_offset))
        y_offset += 15
        
        # Power bar
        bar_width = panel_width - 20
        bar_height = 8
        bar_rect = pygame.Rect(panel_x + 10, y_offset, bar_width, bar_height)
        pygame.draw.rect(screen, (60, 60, 60), bar_rect)
        
        if base.power_consumption > 0:
            power_ratio = min(1.0, base.power_generation / base.power_consumption)
            fill_width = int(bar_width * power_ratio)
            fill_rect = pygame.Rect(panel_x + 10, y_offset, fill_width, bar_height)
            fill_color = (0, 255, 0) if power_ratio >= 1.0 else (255, 255, 0)
            pygame.draw.rect(screen, fill_color, fill_rect)
        
        y_offset += 20
        
        # Crew status
        crew_text = small_font.render(f"Crew: {base.crew_count}/{base.crew_capacity}", 
                                    True, (200, 200, 200))
        screen.blit(crew_text, (panel_x + 10, y_offset))
        y_offset += 20
        
        # Module count
        unique_modules = set(base.modules.values())
        module_text = small_font.render(f"Modules: {len(unique_modules)}", 
                                      True, (200, 200, 200))
        screen.blit(module_text, (panel_x + 10, y_offset))
        y_offset += 20
        
        # Defense rating
        defense_text = small_font.render(f"Defense: {base.defense_rating}", 
                                       True, (200, 200, 200))
        screen.blit(defense_text, (panel_x + 10, y_offset))
        y_offset += 20
        
        # Resources (top 5)
        y_offset += 10
        resources_title = small_font.render("Resources:", True, (255, 255, 255))
        screen.blit(resources_title, (panel_x + 10, y_offset))
        y_offset += 15
        
        sorted_resources = sorted(base.stored_resources.items(), 
                                key=lambda x: x[1], reverse=True)[:5]
        
        for resource, amount in sorted_resources:
            if y_offset < panel_y + panel_height - 20:
                res_text = small_font.render(f"  {resource}: {amount}", 
                                           True, (180, 180, 180))
                screen.blit(res_text, (panel_x + 15, y_offset))
                y_offset += 15
    
    def _draw_tab_bar(self, screen):
        """Draw tab bar for different interfaces."""
        tab_width = 120
        tab_height = 30
        tab_y = 10
        start_x = (screen.get_width() - 3 * tab_width) // 2
        
        tabs = [
            ("construction", "Construction"),
            ("production", "Production"),
            ("management", "Management")
        ]
        
        font = pygame.font.Font(None, 20)
        
        for i, (tab_id, tab_name) in enumerate(tabs):
            tab_x = start_x + i * tab_width
            tab_rect = pygame.Rect(tab_x, tab_y, tab_width, tab_height)
            
            # Tab background
            if self.selected_tab == tab_id:
                pygame.draw.rect(screen, (80, 80, 100), tab_rect)
                text_color = (255, 255, 255)
            else:
                pygame.draw.rect(screen, (60, 60, 80), tab_rect)
                text_color = (200, 200, 200)
            
            pygame.draw.rect(screen, (100, 100, 120), tab_rect, 1)
            
            # Tab text
            text = font.render(tab_name, True, text_color)
            text_rect = text.get_rect(center=tab_rect.center)
            screen.blit(text, text_rect)
    
    def _draw_production_panel(self, screen):
        """Draw production information panel."""
        if not self.base_id:
            return
        
        base = base_manager.get_base(self.base_id)
        if not base:
            return
        
        panel_width = 400
        panel_height = 350
        panel_x = screen.get_width() - panel_width - 10
        panel_y = 60
        
        # Panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (40, 40, 60), panel_rect)
        pygame.draw.rect(screen, (100, 100, 120), panel_rect, 2)
        
        font = pygame.font.Font(None, 18)
        
        y_offset = panel_y + 10
        
        # Title
        title_text = font.render("Production Status", True, (255, 255, 255))
        screen.blit(title_text, (panel_x + 10, y_offset))
        y_offset += 25
        
        # Get production status
        status = self.production_system.get_production_status(base)
        
        # Summary
        summary_text = font.render(f"Active: {status['active_productions']}  "
                                 f"Idle: {status['idle_modules']}", 
                                 True, (200, 200, 200))
        screen.blit(summary_text, (panel_x + 10, y_offset))
        y_offset += 20
        
        # Module details
        for module_id, module_status in status['module_status'].items():
            if y_offset >= panel_y + panel_height - 30:
                break
            
            if module_status['status'] == 'producing':
                progress = module_status['progress']
                progress_text = font.render(f"Producing... {progress:.1%}", 
                                          True, (0, 255, 0))
                screen.blit(progress_text, (panel_x + 10, y_offset))
                
                # Progress bar
                bar_width = panel_width - 20
                bar_height = 6
                bar_rect = pygame.Rect(panel_x + 10, y_offset + 15, bar_width, bar_height)
                pygame.draw.rect(screen, (60, 60, 60), bar_rect)
                
                fill_width = int(bar_width * progress)
                fill_rect = pygame.Rect(panel_x + 10, y_offset + 15, fill_width, bar_height)
                pygame.draw.rect(screen, (0, 255, 0), fill_rect)
                
                y_offset += 30
            else:
                idle_text = font.render("Idle", True, (255, 255, 0))
                screen.blit(idle_text, (panel_x + 10, y_offset))
                y_offset += 20
    
    def _draw_management_panel(self, screen):
        """Draw base management panel."""
        if not self.base_id:
            return
        
        base = base_manager.get_base(self.base_id)
        if not base:
            return
        
        panel_width = 350
        panel_height = 300
        panel_x = screen.get_width() - panel_width - 10
        panel_y = 60
        
        # Panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (40, 40, 60), panel_rect)
        pygame.draw.rect(screen, (100, 100, 120), panel_rect, 2)
        
        font = pygame.font.Font(None, 18)
        
        y_offset = panel_y + 10
        
        # Title
        title_text = font.render("Base Management", True, (255, 255, 255))
        screen.blit(title_text, (panel_x + 10, y_offset))
        y_offset += 25
        
        # Get optimization suggestions
        suggestions = self.production_system.optimize_production_chain(base)
        
        if suggestions:
            suggestions_title = font.render("Optimization Suggestions:", True, (255, 255, 200))
            screen.blit(suggestions_title, (panel_x + 10, y_offset))
            y_offset += 20
            
            for suggestion in suggestions[:8]:  # Show max 8 suggestions
                if y_offset >= panel_y + panel_height - 30:
                    break
                
                # Wrap long suggestions
                if len(suggestion) > 45:
                    suggestion = suggestion[:42] + "..."
                
                sugg_text = font.render(f"• {suggestion}", True, (200, 200, 200))
                screen.blit(sugg_text, (panel_x + 15, y_offset))
                y_offset += 15
        else:
            no_sugg_text = font.render("Base is operating efficiently!", 
                                     True, (0, 255, 0))
            screen.blit(no_sugg_text, (panel_x + 10, y_offset))
    
    def _draw_status_bar(self, screen):
        """Draw status bar at bottom of screen."""
        status_height = 30
        status_y = screen.get_height() - status_height
        status_rect = pygame.Rect(0, status_y, screen.get_width(), status_height)
        
        pygame.draw.rect(screen, (30, 30, 50), status_rect)
        pygame.draw.line(screen, (100, 100, 120), 
                        (0, status_y), (screen.get_width(), status_y), 1)
        
        font = pygame.font.Font(None, 18)
        
        # Construction mode info
        if self.construction_system.is_construction_active:
            mode_text = f"Mode: {self.construction_system.construction_mode.value.title()}"
            if self.construction_system.construction_mode == ConstructionMode.PLACE:
                module_name = self.construction_system.selected_module_type.value.replace('_', ' ').title()
                mode_text += f" - {module_name}"
            
            mode_surface = font.render(mode_text, True, (255, 255, 255))
            screen.blit(mode_surface, (10, status_y + 8))
        
        # Controls hint
        controls_text = "F1: Help  Tab: Toggle Grid  ESC: Exit  1-7: Module Types"
        controls_surface = font.render(controls_text, True, (150, 150, 150))
        controls_rect = controls_surface.get_rect()
        controls_rect.right = screen.get_width() - 10
        controls_rect.centery = status_y + status_height // 2
        screen.blit(controls_surface, controls_rect)
    
    def _draw_help_overlay(self, screen):
        """Draw help overlay."""
        overlay_width = 500
        overlay_height = 400
        overlay_x = (screen.get_width() - overlay_width) // 2
        overlay_y = (screen.get_height() - overlay_height) // 2
        
        overlay_rect = pygame.Rect(overlay_x, overlay_y, overlay_width, overlay_height)
        
        # Semi-transparent background
        overlay_surface = pygame.Surface((screen.get_width(), screen.get_height()))
        overlay_surface.set_alpha(128)
        overlay_surface.fill((0, 0, 0))
        screen.blit(overlay_surface, (0, 0))
        
        # Help panel
        pygame.draw.rect(screen, (40, 40, 60), overlay_rect)
        pygame.draw.rect(screen, (100, 100, 120), overlay_rect, 3)
        
        font = pygame.font.Font(None, 20)
        small_font = pygame.font.Font(None, 16)
        
        y_offset = overlay_y + 20
        
        # Title
        title_text = font.render("Base Construction Help", True, (255, 255, 255))
        title_rect = title_text.get_rect(centerx=overlay_rect.centerx)
        title_rect.y = y_offset
        screen.blit(title_text, title_rect)
        y_offset += 40
        
        # Help sections
        help_sections = [
            ("Construction Controls:", [
                "1-7: Select module type",
                "Left Click: Place/Remove module",
                "Right Click: Cancel construction",
                "P: Place mode",
                "R: Remove mode",
                "Tab: Toggle grid"
            ]),
            ("Module Types:", [
                "1: Habitat (crew quarters)",
                "2: Power Generator",
                "3: Storage (resource storage)",
                "4: Refinery (process materials)",
                "5: Factory (advanced production)",
                "6: Turret (defense)",
                "7: Trade Hub (trading)"
            ]),
            ("Tips:", [
                "Build power generators first",
                "Connect modules with power grid",
                "Monitor resource flows",
                "Plan production chains"
            ])
        ]
        
        for section_title, items in help_sections:
            if y_offset >= overlay_y + overlay_height - 40:
                break
            
            section_text = font.render(section_title, True, (255, 255, 200))
            screen.blit(section_text, (overlay_x + 20, y_offset))
            y_offset += 25
            
            for item in items:
                if y_offset >= overlay_y + overlay_height - 40:
                    break
                
                item_text = small_font.render(f"  • {item}", True, (200, 200, 200))
                screen.blit(item_text, (overlay_x + 30, y_offset))
                y_offset += 18
            
            y_offset += 10
        
        # Close instruction
        close_text = small_font.render("Press F1 again to close", True, (150, 150, 150))
        close_rect = close_text.get_rect(centerx=overlay_rect.centerx)
        close_rect.bottom = overlay_rect.bottom - 10
        screen.blit(close_text, close_rect)
    
    def handle_input(self, event):
        """Handle input events."""
        # Let construction system handle input first
        if self.construction_system.handle_input(event):
            return
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Return to previous state
                self.construction_system.deactivate_construction()
                self.game.change_state(self.previous_state)
            
            elif event.key == pygame.K_F1:
                self.show_help = not self.show_help
            
            elif event.key == pygame.K_F2:
                self.show_base_info = not self.show_base_info
            
            elif event.key == pygame.K_F3:
                self.show_production_info = not self.show_production_info
            
            # Tab switching
            elif event.key == pygame.K_q:
                self.selected_tab = "construction"
            elif event.key == pygame.K_w:
                self.selected_tab = "production"
            elif event.key == pygame.K_e:
                self.selected_tab = "management"
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check if clicking on tabs
                mouse_pos = pygame.mouse.get_pos()
                if self._handle_tab_click(mouse_pos):
                    return
        
        elif event.type == pygame.MOUSEWHEEL:
            # Zoom control
            zoom_factor = 1.1 if event.y > 0 else 1.0 / 1.1
            self.zoom_level = max(self.min_zoom, min(self.max_zoom, self.zoom_level * zoom_factor))
    
    def _handle_tab_click(self, mouse_pos):
        """Handle clicks on tab bar."""
        tab_width = 120
        tab_height = 30
        tab_y = 10
        start_x = (self.game.screen.get_width() - 3 * tab_width) // 2
        
        tabs = ["construction", "production", "management"]
        
        for i, tab_id in enumerate(tabs):
            tab_x = start_x + i * tab_width
            tab_rect = pygame.Rect(tab_x, tab_y, tab_width, tab_height)
            
            if tab_rect.collidepoint(mouse_pos):
                self.selected_tab = tab_id
                return True
        
        return False