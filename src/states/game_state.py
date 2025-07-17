import logging
from enum import Enum, auto

import pygame
from src.docking.docking_state import DockingResult
try:
    from ..trading.commodity import commodity_registry
    from ..systems.cloaking_system import cloaking_system
    from ..systems.repair_system import repair_system
except ImportError:
    from trading.commodity import commodity_registry
    from systems.cloaking_system import cloaking_system
    from systems.repair_system import repair_system

logger = logging.getLogger(__name__)


class GameStates(Enum):
    MAIN_MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    TRADING = auto()  # Added for market interface
    UPGRADES = auto()  # Added for ship upgrade interface
    MISSIONS = auto()  # Added for mission board
    SETTINGS = auto()  # Added for settings menu
    SAVE_GAME = auto()  # Added for save menu
    LOAD_GAME = auto()  # Added for load menu
    GAME_OVER = auto()

class State:
    def __init__(self, game):
        self.game = game

    def update(self, delta_time):
        pass

    def render(self, screen):
        pass

    def handle_input(self, event):
        pass

class MenuState(State):
    def __init__(self, game):
        super().__init__(game)
        self.title = "Space Trading Simulator"
        self.menu_options = ["New Game", "Load Game", "Settings", "Exit"]
        self.selected_option = 0
        self.option_rects = []  # Store rectangles for mouse interaction

    def render(self, screen):
        # Clear screan first
        screen.fill((0, 0, 20)) # Dark blue background

        # Draw title
        title_font = pygame.font.Font(None, 74)
        title = title_font.render(self.title, True, (255, 255, 255))
        title_rect = title.get_rect(center=(screen.get_width() // 2, 100))
        screen.blit(title, title_rect)

        # Draw menu options and store their rectangles
        option_font = pygame.font.Font(None, 48)  # Slightly larger font for options
        self.option_rects = []  # Reset rectangles
        for i, option in enumerate(self.menu_options):
            color = (255, 255, 0) if i == self.selected_option else (255, 255, 255)
            text = option_font.render(option, True, color)
            # Position each option, centered horizontally and spaced vertically
            text_rect = text.get_rect(center=(screen.get_width() // 2, 300 + i * 60))
            screen.blit(text, text_rect)
            
            # Store expanded rectangle for mouse interaction
            expanded_rect = text_rect.inflate(40, 20)
            self.option_rects.append(expanded_rect)

        # Draw current world seed in bottom right
        if hasattr(self.game, 'world_seed') and self.game.world_seed is not None:
            seed_font = pygame.font.Font(None, 24)
            seed_text = f"World Seed: {self.game.world_seed}"
            seed_surface = seed_font.render(seed_text, True, (150, 150, 150))
            seed_rect = seed_surface.get_rect(bottomright=(screen.get_width() - 10, screen.get_height() - 10))
            screen.blit(seed_surface, seed_rect)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.menu_options)
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.menu_options)
            elif event.key == pygame.K_RETURN:
                self._select_option()
        elif event.type == pygame.MOUSEMOTION:
            # Check if mouse is over any option
            mouse_pos = pygame.mouse.get_pos()
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected_option = i
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = pygame.mouse.get_pos()
                for i, rect in enumerate(self.option_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected_option = i
                        self._select_option()
                        break
    
    def _select_option(self):
        """Handle option selection"""
        if self.selected_option == 0:  # New Game
            self.game.create_new_universe()  # Create a new universe with random seed
            self.game.change_state(GameStates.PLAYING)
        elif self.selected_option == 1:  # Load Game
            self.game.change_state(GameStates.LOAD_GAME)
        elif self.selected_option == 2:  # Settings
            self.game.change_state(GameStates.SETTINGS)
        elif self.selected_option == 3:  # Exit
            self.game.running = False

class SettingsState(State):
    def __init__(self, game):
        super().__init__(game)
        from ..settings import game_settings, CameraMode
        self.settings = game_settings
        self.title = "Settings"
        self.categories = ["Camera", "Display", "Dev View", "Help", "Back"]
        self.selected_category = 0
        
        # Camera settings options
        self.camera_options = ["Camera Mode", "Smoothing", "Deadzone", "Back"]
        self.selected_camera_option = 0
        self.viewing_camera = False
        
        # Dev view settings options
        self.dev_options = ["Enable Dev View", "Show FPS", "Show Ship Pos", "Show Docking", "Show Stations", "Show Camera", "Back"]
        self.selected_dev_option = 0
        self.viewing_dev = False
        
        # Help options
        self.help_options = ["Controls", "Keybinds", "Back"]
        self.selected_help_option = 0
        self.viewing_help = False
        
        # Mouse interaction rectangles
        self.category_rects = []
        self.camera_rects = []
        self.dev_rects = []
        self.help_rects = []
        
    def render(self, screen):
        screen.fill((0, 0, 20))  # Dark blue background
        
        # Draw title
        title_font = pygame.font.Font(None, 64)
        title = title_font.render(self.title, True, (255, 255, 255))
        title_rect = title.get_rect(center=(screen.get_width() // 2, 80))
        screen.blit(title, title_rect)
        
        if not self.viewing_camera and not self.viewing_dev and not self.viewing_help:
            self._render_main_categories(screen)
        elif self.viewing_camera:
            self._render_camera_settings(screen)
        elif self.viewing_dev:
            self._render_dev_settings(screen)
        elif self.viewing_help:
            self._render_help_settings(screen)
    
    def _render_main_categories(self, screen):
        """Render main settings categories"""
        option_font = pygame.font.Font(None, 48)
        self.category_rects = []  # Reset rectangles
        for i, category in enumerate(self.categories):
            color = (255, 255, 0) if i == self.selected_category else (255, 255, 255)
            text = option_font.render(category, True, color)
            text_rect = text.get_rect(center=(screen.get_width() // 2, 200 + i * 60))
            screen.blit(text, text_rect)
            
            # Store expanded rectangle for mouse interaction
            expanded_rect = text_rect.inflate(40, 20)
            self.category_rects.append(expanded_rect)
    
    def _render_camera_settings(self, screen):
        """Render camera settings submenu"""
        option_font = pygame.font.Font(None, 40)
        small_font = pygame.font.Font(None, 28)
        
        # Draw camera settings title
        subtitle = option_font.render("Camera Settings", True, (200, 200, 255))
        subtitle_rect = subtitle.get_rect(center=(screen.get_width() // 2, 150))
        screen.blit(subtitle, subtitle_rect)
        
        y_offset = 220
        for i, option in enumerate(self.camera_options):
            color = (255, 255, 0) if i == self.selected_camera_option else (255, 255, 255)
            
            if option == "Camera Mode":
                mode_text = f"Camera Mode: {self.settings.camera_mode.value}"
                text = option_font.render(mode_text, True, color)
                # Add description
                desc = small_font.render(self.settings.get_camera_description(), True, (150, 150, 150))
                desc_rect = desc.get_rect(center=(screen.get_width() // 2, y_offset + 25))
                screen.blit(desc, desc_rect)
                y_offset += 25
                
            elif option == "Smoothing":
                if self.settings.camera_mode.name == "SMOOTH":
                    smooth_text = f"Smoothing: {self.settings.camera_smoothing:.2f}"
                    color = color if self.settings.camera_mode.name == "SMOOTH" else (100, 100, 100)
                else:
                    smooth_text = f"Smoothing: {self.settings.camera_smoothing:.2f} (N/A)"
                    color = (100, 100, 100)
                text = option_font.render(smooth_text, True, color)
                
            elif option == "Deadzone":
                if self.settings.camera_mode.name == "DEADZONE":
                    deadzone_text = f"Deadzone: {self.settings.camera_deadzone_radius}px"
                    color = color if self.settings.camera_mode.name == "DEADZONE" else (100, 100, 100)
                else:
                    deadzone_text = f"Deadzone: {self.settings.camera_deadzone_radius}px (N/A)"
                    color = (100, 100, 100)
                text = option_font.render(deadzone_text, True, color)
                
            else:  # Back
                text = option_font.render(option, True, color)
            
            text_rect = text.get_rect(center=(screen.get_width() // 2, y_offset))
            screen.blit(text, text_rect)
            y_offset += 60
        
        # Instructions
        instruction_font = pygame.font.Font(None, 24)
        instructions = "Use LEFT/RIGHT to change values, ENTER to select, ESC to go back"
        instr_text = instruction_font.render(instructions, True, (150, 150, 150))
        instr_rect = instr_text.get_rect(center=(screen.get_width() // 2, screen.get_height() - 40))
        screen.blit(instr_text, instr_rect)
    
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.viewing_camera:
                    self.viewing_camera = False
                elif self.viewing_dev:
                    self.viewing_dev = False
                elif self.viewing_help:
                    self.viewing_help = False
                else:
                    self.game.change_state(GameStates.MAIN_MENU)
            elif not self.viewing_camera and not self.viewing_dev and not self.viewing_help:
                self._handle_main_input(event)
            elif self.viewing_camera:
                self._handle_camera_input(event)
            elif self.viewing_dev:
                self._handle_dev_input(event)
            elif self.viewing_help:
                self._handle_help_input(event)
        elif event.type == pygame.MOUSEMOTION:
            # Check for mouse hover on options
            mouse_pos = pygame.mouse.get_pos()
            if not self.viewing_camera and not self.viewing_dev and not self.viewing_help:
                for i, rect in enumerate(self.category_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected_category = i
                        break
            elif self.viewing_help:
                for i, rect in enumerate(self.help_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected_help_option = i
                        break
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = pygame.mouse.get_pos()
                if not self.viewing_camera and not self.viewing_dev and not self.viewing_help:
                    for i, rect in enumerate(self.category_rects):
                        if rect.collidepoint(mouse_pos):
                            self.selected_category = i
                            self._select_main_option()
                            break
                elif self.viewing_help:
                    for i, rect in enumerate(self.help_rects):
                        if rect.collidepoint(mouse_pos):
                            self.selected_help_option = i
                            self._select_help_option()
                            break
    
    def _handle_main_input(self, event):
        """Handle input for main settings categories"""
        if event.key == pygame.K_UP:
            self.selected_category = (self.selected_category - 1) % len(self.categories)
        elif event.key == pygame.K_DOWN:
            self.selected_category = (self.selected_category + 1) % len(self.categories)
        elif event.key == pygame.K_RETURN:
            self._select_main_option()
    
    def _select_main_option(self):
        """Handle main option selection"""
        if self.selected_category == 0:  # Camera
            self.viewing_camera = True
            self.selected_camera_option = 0
        elif self.selected_category == 1:  # Display (future feature)
            pass  # TODO: Implement display settings
        elif self.selected_category == 2:  # Dev View
            self.viewing_dev = True
            self.selected_dev_option = 0
        elif self.selected_category == 3:  # Help
            self.viewing_help = True
            self.selected_help_option = 0
        elif self.selected_category == 4:  # Back
            self.game.change_state(GameStates.MAIN_MENU)
    
    def _handle_camera_input(self, event):
        """Handle input for camera settings"""
        from ..settings import CameraMode
        
        if event.key == pygame.K_UP:
            self.selected_camera_option = (self.selected_camera_option - 1) % len(self.camera_options)
        elif event.key == pygame.K_DOWN:
            self.selected_camera_option = (self.selected_camera_option + 1) % len(self.camera_options)
        elif event.key == pygame.K_LEFT:
            self._adjust_camera_setting(-1)
        elif event.key == pygame.K_RIGHT:
            self._adjust_camera_setting(1)
        elif event.key == pygame.K_RETURN:
            if self.selected_camera_option == 3:  # Back
                self.viewing_camera = False
    
    def _adjust_camera_setting(self, direction):
        """Adjust camera setting values"""
        from ..settings import CameraMode
        
        if self.selected_camera_option == 0:  # Camera Mode
            modes = list(CameraMode)
            current_index = modes.index(self.settings.camera_mode)
            new_index = (current_index + direction) % len(modes)
            self.settings.camera_mode = modes[new_index]
            self.settings.save()
            
        elif self.selected_camera_option == 1:  # Smoothing
            if self.settings.camera_mode.name == "SMOOTH":
                self.settings.camera_smoothing = max(0.01, min(1.0, 
                    self.settings.camera_smoothing + direction * 0.05))
                self.settings.save()
                
        elif self.selected_camera_option == 2:  # Deadzone
            if self.settings.camera_mode.name == "DEADZONE":
                self.settings.camera_deadzone_radius = max(10, min(200, 
                    self.settings.camera_deadzone_radius + direction * 10))
                self.settings.save()
    
    def _render_dev_settings(self, screen):
        """Render dev view settings submenu"""
        option_font = pygame.font.Font(None, 40)
        small_font = pygame.font.Font(None, 28)
        
        # Draw dev settings title
        subtitle = option_font.render("Dev View Settings", True, (200, 200, 255))
        subtitle_rect = subtitle.get_rect(center=(screen.get_width() // 2, 150))
        screen.blit(subtitle, subtitle_rect)
        
        y_offset = 220
        for i, option in enumerate(self.dev_options):
            color = (255, 255, 0) if i == self.selected_dev_option else (255, 255, 255)
            
            if option == "Enable Dev View":
                dev_text = f"Enable Dev View: {'ON' if self.settings.dev_view_enabled else 'OFF'}"
                text = option_font.render(dev_text, True, color)
            elif option == "Show FPS":
                fps_text = f"Show FPS: {'ON' if self.settings.dev_show_fps else 'OFF'}"
                enabled_color = color if self.settings.dev_view_enabled else (100, 100, 100)
                text = option_font.render(fps_text, True, enabled_color)
            elif option == "Show Ship Pos":
                ship_text = f"Show Ship Position: {'ON' if self.settings.dev_show_ship_pos else 'OFF'}"
                enabled_color = color if self.settings.dev_view_enabled else (100, 100, 100)
                text = option_font.render(ship_text, True, enabled_color)
            elif option == "Show Docking":
                dock_text = f"Show Docking: {'ON' if self.settings.dev_show_docking else 'OFF'}"
                enabled_color = color if self.settings.dev_view_enabled else (100, 100, 100)
                text = option_font.render(dock_text, True, enabled_color)
            elif option == "Show Stations":
                station_text = f"Show Stations: {'ON' if self.settings.dev_show_stations else 'OFF'}"
                enabled_color = color if self.settings.dev_view_enabled else (100, 100, 100)
                text = option_font.render(station_text, True, enabled_color)
            elif option == "Show Camera":
                camera_text = f"Show Camera: {'ON' if self.settings.dev_show_camera else 'OFF'}"
                enabled_color = color if self.settings.dev_view_enabled else (100, 100, 100)
                text = option_font.render(camera_text, True, enabled_color)
            else:  # Back
                text = option_font.render(option, True, color)
            
            text_rect = text.get_rect(center=(screen.get_width() // 2, y_offset))
            screen.blit(text, text_rect)
            y_offset += 50
        
        # Instructions
        instruction_font = pygame.font.Font(None, 24)
        instructions = "Use LEFT/RIGHT to toggle, ENTER to select, ESC to go back"
        instr_text = instruction_font.render(instructions, True, (150, 150, 150))
        instr_rect = instr_text.get_rect(center=(screen.get_width() // 2, screen.get_height() - 40))
        screen.blit(instr_text, instr_rect)
        
        # Dev view status
        if self.settings.dev_view_enabled:
            status_text = "Press F4 in-game to toggle Dev View"
            status_surface = small_font.render(status_text, True, (150, 255, 150))
            status_rect = status_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() - 70))
            screen.blit(status_surface, status_rect)
    
    def _handle_dev_input(self, event):
        """Handle input for dev view settings"""
        if event.key == pygame.K_UP:
            self.selected_dev_option = (self.selected_dev_option - 1) % len(self.dev_options)
        elif event.key == pygame.K_DOWN:
            self.selected_dev_option = (self.selected_dev_option + 1) % len(self.dev_options)
        elif event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
            self._toggle_dev_setting()
        elif event.key == pygame.K_RETURN:
            if self.selected_dev_option == len(self.dev_options) - 1:  # Back
                self.viewing_dev = False
            else:
                self._toggle_dev_setting()
    
    def _toggle_dev_setting(self):
        """Toggle the selected dev view setting"""
        if self.selected_dev_option == 0:  # Enable Dev View
            self.settings.dev_view_enabled = not self.settings.dev_view_enabled
        elif self.selected_dev_option == 1 and self.settings.dev_view_enabled:  # Show FPS
            self.settings.dev_show_fps = not self.settings.dev_show_fps
        elif self.selected_dev_option == 2 and self.settings.dev_view_enabled:  # Show Ship Pos
            self.settings.dev_show_ship_pos = not self.settings.dev_show_ship_pos
        elif self.selected_dev_option == 3 and self.settings.dev_view_enabled:  # Show Docking
            self.settings.dev_show_docking = not self.settings.dev_show_docking
        elif self.selected_dev_option == 4 and self.settings.dev_view_enabled:  # Show Stations
            self.settings.dev_show_stations = not self.settings.dev_show_stations
        elif self.selected_dev_option == 5 and self.settings.dev_view_enabled:  # Show Camera
            self.settings.dev_show_camera = not self.settings.dev_show_camera
        
        self.settings.save()
    
    def _handle_help_input(self, event):
        """Handle input for help settings"""
        if event.key == pygame.K_UP:
            self.selected_help_option = (self.selected_help_option - 1) % len(self.help_options)
        elif event.key == pygame.K_DOWN:
            self.selected_help_option = (self.selected_help_option + 1) % len(self.help_options)
        elif event.key == pygame.K_RETURN:
            self._select_help_option()
    
    def _select_help_option(self):
        """Handle help option selection"""
        if self.selected_help_option == 2:  # Back
            self.viewing_help = False
    
    def _render_help_settings(self, screen):
        """Render help settings submenu"""
        option_font = pygame.font.Font(None, 40)
        text_font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 20)
        
        # Draw help settings title
        subtitle = option_font.render("Help & Controls", True, (200, 200, 255))
        subtitle_rect = subtitle.get_rect(center=(screen.get_width() // 2, 150))
        screen.blit(subtitle, subtitle_rect)
        
        y_offset = 220
        self.help_rects = []  # Reset rectangles
        for i, option in enumerate(self.help_options):
            color = (255, 255, 0) if i == self.selected_help_option else (255, 255, 255)
            text = option_font.render(option, True, color)
            text_rect = text.get_rect(center=(screen.get_width() // 2, y_offset))
            screen.blit(text, text_rect)
            
            # Store expanded rectangle for mouse interaction
            expanded_rect = text_rect.inflate(40, 20)
            self.help_rects.append(expanded_rect)
            y_offset += 60
        
        # Show help content based on selected option
        if self.selected_help_option == 0:  # Controls
            self._render_controls_help(screen, text_font, small_font)
        elif self.selected_help_option == 1:  # Keybinds
            self._render_keybinds_help(screen, text_font, small_font)
        
        # Instructions
        instruction_font = pygame.font.Font(None, 24)
        instructions = "Use UP/DOWN to navigate, ENTER to select, ESC to go back"
        instr_text = instruction_font.render(instructions, True, (150, 150, 150))
        instr_rect = instr_text.get_rect(center=(screen.get_width() // 2, screen.get_height() - 40))
        screen.blit(instr_text, instr_rect)
    
    def _render_controls_help(self, screen, text_font, small_font):
        """Render general controls help"""
        y_offset = 400
        help_text = [
            "MOVEMENT:",
            "  Arrow Keys / WASD - Move ship",
            "  Shift - Boost/Thrust",
            "",
            "NAVIGATION:",
            "  TAB - Open/Close large map",
            "  M - Open/Close large map (alt)",
            "  ESC - Pause game",
            "",
            "DOCKING:",
            "  D - Manual dock when near station",
            "  X - Undock from station"
        ]
        
        for text in help_text:
            if text == "":
                y_offset += 15
                continue
            
            color = (255, 255, 0) if text.endswith(":") else (255, 255, 255)
            font = text_font if text.endswith(":") else small_font
            surface = font.render(text, True, color)
            screen.blit(surface, (50, y_offset))
            y_offset += 20
    
    def _render_keybinds_help(self, screen, text_font, small_font):
        """Render keybinds help"""
        y_offset = 400
        keybinds = [
            "GENERAL KEYBINDS:",
            "  F4 - Toggle developer view",
            "  F11 - Toggle fullscreen",
            "  F12 - Toggle FPS display",
            "",
            "DOCKED ACTIONS:",
            "  T - Open trading interface",
            "  U - Open ship upgrades",
            "  M - Open mission board",
            "",
            "MAP CONTROLS:",
            "  Mouse Wheel - Zoom in/out",
            "  Right Click + Drag - Pan map",
            "  Left Click - Select location",
            "  HOME - Reset map view",
            "  +/- - Zoom in/out (keyboard)"
        ]
        
        for text in keybinds:
            if text == "":
                y_offset += 15
                continue
            
            color = (255, 255, 0) if text.endswith(":") else (255, 255, 255)
            font = text_font if text.endswith(":") else small_font
            surface = font.render(text, True, color)
            screen.blit(surface, (50, y_offset))
            y_offset += 20

class PlayingState(State):
    def __init__(self, game):
        super().__init__(game)
        # Initialize enhanced HUD
        from ..ui.hud.enhanced_hud import EnhancedHUD
        from ..ui.large_map import LargeMap
        self.enhanced_hud = EnhancedHUD(game.WINDOW_SIZE[0], game.WINDOW_SIZE[1])
        self.large_map = LargeMap(game.WINDOW_SIZE[0], game.WINDOW_SIZE[1])

    def update(self, delta_time):
        # Handle ship movement only if not docked
        if not self.game.docking_manager.is_docked():
            self.game.ship.handle_input(delta_time)
            self.game.ship.update(delta_time)

        # Update camera position to follow ship
        self.game.camera.follow(self.game.ship, delta_time)
        
        # Generate new chunks as ship moves
        self.game.universe.ensure_chunks_around_position(self.game.ship.position)
        
        # Update docking system
        self.game.docking_manager.update(
            self.game.ship, 
            self.game.universe.stations, 
            delta_time
        )
        
        # Update enhanced HUD
        self.enhanced_hud.update(delta_time, self.game)
        
        # Update repair system
        is_docked = self.game.docking_manager.is_docked()
        repair_system.update(delta_time, self.game.ship, is_docked)
        
        # Check collisions after movement (only if not docking/docked)
        if not self.game.docking_manager.is_docking_in_progress() and not self.game.docking_manager.is_docked():
            for station in self.game.universe.stations:
                if self.game.ship.check_collision_detailed(station):
                    logger.info("Collision detected in PlayingState")
            
            # Check planet collisions
            for planet in self.game.universe.planets:
                if self.game.ship.check_collision_detailed(planet):
                    logger.info("Planet collision detected in PlayingState")
            
            # Check debris collisions
            for debris in self.game.universe.debris:
                if self.game.ship.check_collision_detailed(debris):
                    logger.info("Debris collision detected in PlayingState")

    def render(self, screen):
        """Render the playing state"""

        # Clear the screen
        screen.fill((0, 0, 20))  # Dark blue background

        # Get camera offset
        camera_offset = self.game.camera.get_offset()

        # Draw starfield first (so it's in background)
        self.game.starfield.draw(screen, camera_offset)

        # Debug visualization removed for cleaner visuals

        # Draw all stations
        for station in self.game.universe.stations:
            screen_pos = self.game.camera.world_to_screen(station.position)
            # Only draw if on screen (with buffer for station size)
            buffer = station.size + 50  # Add buffer for station size and potential visual elements
            if (-buffer <= screen_pos.x <= self.game.WINDOW_SIZE[0] + buffer and 
                -buffer <= screen_pos.y <= self.game.WINDOW_SIZE[1] + buffer):
                station.draw(screen, camera_offset)
                
                # Draw docking zones and feedback
                self._draw_docking_feedback(screen, station, camera_offset)

    def _draw_docking_feedback(self, screen, station, camera_offset):
        """Draw docking zones and visual feedback for stations."""
        screen_pos = station.position - camera_offset
        docking_manager = self.game.docking_manager
        
        # Draw approach detection zone (light blue, dotted)
        approach_radius = station.size + docking_manager.approach_detection_range
        if docking_manager.get_docking_state().value in ['approaching', 'docking', 'docked']:
            if docking_manager.get_target_station() == station:
                pygame.draw.circle(screen, (100, 150, 255), 
                                 (int(screen_pos.x), int(screen_pos.y)),
                                 int(approach_radius), 2)
        
        # Draw docking zone
        docking_radius = station.size + self.game.ship.size + docking_manager.docking_range_buffer
        distance = (self.game.ship.position - station.position).length()
        
        # Color based on docking status
        if distance <= docking_radius:
            ship_speed = self.game.ship.velocity.length()
            if ship_speed <= docking_manager.max_docking_speed:
                # Green - can dock
                zone_color = (0, 255, 0)
                zone_width = 3
            else:
                # Yellow - too fast
                zone_color = (255, 255, 0)
                zone_width = 2
        else:
            # Red - too far
            zone_color = (255, 100, 100)
            zone_width = 1
            
        # Only draw docking zone if approaching or nearby
        if (distance <= approach_radius or 
            docking_manager.get_target_station() == station):
            pygame.draw.circle(screen, zone_color,
                             (int(screen_pos.x), int(screen_pos.y)),
                             int(docking_radius), zone_width)
        
        # Draw status text for target station
        if docking_manager.get_target_station() == station:
            font = pygame.font.Font(None, 24)
            status_message = docking_manager.get_status_message()
            if status_message:
                text_surface = font.render(status_message, True, (255, 255, 255))
                text_rect = text_surface.get_rect()
                text_rect.centerx = int(screen_pos.x)
                text_rect.y = int(screen_pos.y - station.size - 40)
                
                # Draw background for text
                bg_rect = text_rect.inflate(10, 4)
                pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect)
                screen.blit(text_surface, text_rect)
                
        # Draw docking state indicator
        if docking_manager.is_docked() and docking_manager.get_target_station() == station:
            # Draw "DOCKED" indicator
            font = pygame.font.Font(None, 32)
            docked_text = font.render("DOCKED", True, (0, 255, 0))
            text_rect = docked_text.get_rect()
            text_rect.centerx = int(screen_pos.x)
            text_rect.y = int(screen_pos.y + station.size + 10)
            screen.blit(docked_text, text_rect)

        # Draw all planets
        for planet in self.game.universe.planets:
            screen_pos = self.game.camera.world_to_screen(planet.position)
            # Only draw if on screen (with buffer for planet size)
            buffer = planet.size + 50  # Add buffer for planet size
            if (-buffer <= screen_pos.x <= self.game.WINDOW_SIZE[0] + buffer and 
                -buffer <= screen_pos.y <= self.game.WINDOW_SIZE[1] + buffer):
                planet.draw(screen, camera_offset)

        # Draw debris
        for debris in self.game.universe.debris:
            screen_pos = self.game.camera.world_to_screen(debris.position)
            # Only draw if on screen (with buffer for debris size)
            buffer = debris.size + 50  # Add buffer for debris size
            if (-buffer <= screen_pos.x <= self.game.WINDOW_SIZE[0] + buffer and 
                -buffer <= screen_pos.y <= self.game.WINDOW_SIZE[1] + buffer):
                debris.draw(screen, camera_offset)
        
        # Draw combat entities (asteroids and bandits)
        from ..combat.combat_manager import combat_manager
        combat_manager.draw_entities(screen, camera_offset)
        
        # Draw ship
        self.game.ship.draw(screen, camera_offset)
        
        # Draw combat effects (explosions, etc.)
        combat_manager.draw_combat_effects(screen, camera_offset)
        
        # Draw minimap last (so it's on top)
        self.game.minimap.draw(screen, self.game.ship,
                             self.game.universe.stations,
                             self.game.universe.planets)
        
        # Draw enhanced HUD (on top of everything)
        self.enhanced_hud.render(screen, self.game)
        
        # Draw large map overlay if visible (should be on top of everything)
        self.large_map.draw(screen, self.game.ship, self.game.universe.stations, self.game.universe.planets)
        
        # Draw respawn UI if ship is destroyed
        from ..systems.respawn_system import respawn_system
        respawn_system.draw_respawn_ui(screen)
        
        # Draw repair UI if docked and ship needs repair
        if self.game.docking_manager.is_docked():
            station = self.game.docking_manager.get_target_station()
            repair_system.draw_repair_ui(screen, self.game.ship, station)
        

    def _draw_debug_info(self, screen, camera_offset):
        """Draw debug information for object positions"""
        font = pygame.font.Font(None, 24)
        y_offset = 30

        # Draw FPS
        fps = self.game.clock.get_fps()
        fps_text = font.render(f"FPS: {int(fps)}", True, (255, 255, 255))
        screen.blit(fps_text, (10, y_offset))
        y_offset += 20

        # Draw ship info
        ship_pos = self.game.ship.position
        ship_speed = self.game.ship.velocity.length()
        ship_text = font.render(
            f"Ship Pos: ({int(ship_pos.x)}, {int(ship_pos.y)}) Speed: {int(ship_speed)}", 
            True, (255, 255, 255))
        screen.blit(ship_text, (10, y_offset))
        y_offset += 20
        
        # Draw docking info
        docking_state = self.game.docking_manager.get_docking_state()
        target_station = self.game.docking_manager.get_target_station()
        docking_text = font.render(
            f"Docking: {docking_state.value}" + 
            (f" -> {target_station.name}" if target_station else ""), 
            True, (255, 255, 255))
        screen.blit(docking_text, (10, y_offset))
        y_offset += 20

    
        # Draw station positions with proper camera offset
        for i, station in enumerate(self.game.universe.stations):
            screen_pos = station.position - camera_offset
            # Create station text for each station
            station_text = font.render(
                f"Station {i}: ({int(station.position.x)}, {int(station.position.y)})", 
                True, (255, 255, 255))
            
            if 0 <= screen_pos.x <= screen.get_width() and 0 <= screen_pos.y <= screen.get_height():
                screen.blit(station_text, (10, y_offset))
                y_offset += 20

                # Draw station position indicator
                pygame.draw.circle(screen, (255, 0, 0), 
                                 (int(screen_pos.x), int(screen_pos.y)), 5)
    
        # Draw camera info
        camera_text = font.render(
            f"Camera: ({int(camera_offset.x)}, {int(camera_offset.y)})", 
            True, (255, 255, 255))
        screen.blit(camera_text, (10, y_offset))
    
        # Debug info (commented out to reduce console spam)
        # print(f"Number of stations: {len(self.game.universe.stations)}")
        # print(f"Ship position: {self.game.ship.position}")
        # print(f"Camera offset: {camera_offset}")

    def handle_input(self, event):
        # Let large map handle input first (if it's visible)
        if self.large_map.handle_input(event, self.game.ship.position):
            return
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameStates.PAUSED)
            elif event.key == pygame.K_TAB:  # Large map toggle
                self.large_map.toggle_visibility()
                # Center the map on the player when opened
                if self.large_map.visible:
                    self.large_map.center_on_ship(self.game.ship.position)
            elif event.key == pygame.K_d:  # Manual docking
                result = self.game.docking_manager.attempt_manual_docking(
                    self.game.ship, 
                    self.game.universe.stations
                )
                if result != DockingResult.SUCCESS:
                    logger.info(f"Docking failed: {result.value}")
            elif event.key == pygame.K_t:  # Trading
                if self.game.docking_manager.is_docked():
                    station = self.game.docking_manager.get_target_station()
                    self.game.change_state(GameStates.TRADING, station)
            elif event.key == pygame.K_u:  # Upgrades
                if self.game.docking_manager.is_docked():
                    station = self.game.docking_manager.get_target_station()
                    # Check if station offers upgrades
                    station_type = station.station_type.value.lower()
                    if station_type in ["shipyard", "research station", "military base"]:
                        self.game.change_state(GameStates.UPGRADES, station)
                    else:
                        logger.info(f"Station {station.name} does not offer upgrades")
            elif event.key == pygame.K_m:  # Missions
                if self.game.docking_manager.is_docked():
                    station = self.game.docking_manager.get_target_station()
                    self.game.change_state(GameStates.MISSIONS, station)
            elif event.key == pygame.K_x:  # Undocking (changed from U to X to avoid conflict)
                if self.game.docking_manager.is_docked():
                    result = self.game.docking_manager.attempt_undocking(self.game.ship)
                    if result != DockingResult.SUCCESS:
                        logger.info(f"Undocking failed: {result.value}")
            elif event.key == pygame.K_c:  # Cloaking
                effective_stats = self.game.ship.get_effective_stats()
                cloaking_system.handle_input(event, effective_stats)
            elif event.key == pygame.K_r:  # Repair
                if self.game.docking_manager.is_docked():
                    station = self.game.docking_manager.get_target_station()
                    repair_system.handle_input(event, self.game.ship, station)
                else:
                    # Emergency repair when not docked
                    repair_system.handle_input(event, self.game.ship, None)

class PausedState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pause_options = ["Resume", "Save Game", "Settings", "Main Menu"]
        self.selected_option = 0
        self.option_rects = []

    def render(self, screen):
        # First render the game state in the background
        self.game.states[GameStates.PLAYING].render(screen)
        
        # Get screen dimensions
        width, height = screen.get_size()
        
        # Draw pause overlay (full screen)
        s = pygame.Surface((width, height))
        s.set_alpha(128)
        s.fill((0, 0, 0))
        screen.blit(s, (0, 0))
        
        # Title
        title_font = pygame.font.Font(None, 74)
        title_text = title_font.render("PAUSED", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(width // 2, height // 4))
        screen.blit(title_text, title_rect)
        
        # Menu options
        option_font = pygame.font.Font(None, 48)
        y_offset = height // 2 - 50
        self.option_rects = []  # Reset rectangles
        for i, option in enumerate(self.pause_options):
            color = (255, 255, 0) if i == self.selected_option else (255, 255, 255)
            option_text = option_font.render(option, True, color)
            option_rect = option_text.get_rect(center=(width // 2, y_offset))
            screen.blit(option_text, option_rect)
            
            # Store expanded rectangle for mouse interaction
            expanded_rect = option_rect.inflate(40, 20)
            self.option_rects.append(expanded_rect)
            y_offset += 50
        
        # Instructions
        instruction_font = pygame.font.Font(None, 24)
        instructions = instruction_font.render("Use UP/DOWN to navigate, ENTER to select, ESC to resume", True, (150, 150, 150))
        instruction_rect = instructions.get_rect(center=(width // 2, height - 100))
        screen.blit(instructions, instruction_rect)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameStates.PLAYING)
            elif event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.pause_options)
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.pause_options)
            elif event.key == pygame.K_RETURN:
                self._select_option()
        elif event.type == pygame.MOUSEMOTION:
            # Check if mouse is over any option
            mouse_pos = pygame.mouse.get_pos()
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected_option = i
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = pygame.mouse.get_pos()
                for i, rect in enumerate(self.option_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected_option = i
                        self._select_option()
                        break
    
    def _select_option(self):
        """Handle option selection"""
        if self.selected_option == 0:  # Resume
            self.game.change_state(GameStates.PLAYING)
        elif self.selected_option == 1:  # Save Game
            self.game.change_state(GameStates.SAVE_GAME)
        elif self.selected_option == 2:  # Settings
            self.game.change_state(GameStates.SETTINGS)
        elif self.selected_option == 3:  # Main Menu
            self.game.change_state(GameStates.MAIN_MENU)

class TradingState(State):
    def __init__(self, game, station=None):
        super().__init__(game)
        self.station = station
        self.selected_commodity_index = 0
        self.viewing_cargo = False  # False = station market, True = ship cargo
        self.transaction_quantity = 1
        self.message = ""
        self.message_timer = 0
        
        # Get ship and market references
        self.ship = game.ship
        self.market = station.market if station else None
        
        # Get available commodities
        self.available_commodities = self.market.get_available_commodities() if self.market else []
        
    def update(self, delta_time):
        # Update message timer
        if self.message_timer > 0:
            self.message_timer -= delta_time
            if self.message_timer <= 0:
                self.message = ""
        
    def render(self, screen):
        # Clear screen with dark background
        screen.fill((20, 20, 30))
        
        # Fonts
        title_font = pygame.font.Font(None, 48)
        header_font = pygame.font.Font(None, 36)
        text_font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 20)
        
        # Screen dimensions
        width, height = screen.get_size()
        
        # Title
        station_name = self.station.name if self.station else "Unknown Station"
        station_type = self.station.station_type.value if self.station else "Unknown"
        title_text = f"TRADING - {station_name} ({station_type})"
        title_surface = title_font.render(title_text, True, (255, 255, 255))
        title_rect = title_surface.get_rect(centerx=width//2, y=20)
        screen.blit(title_surface, title_rect)
        
        # Credits and cargo info
        credits_text = f"Credits: {self.ship.credits:,}"
        cargo_summary = self.ship.cargo_hold.get_cargo_summary()
        cargo_text = f"Cargo: {cargo_summary}"
        
        credits_surface = text_font.render(credits_text, True, (255, 255, 0))
        cargo_surface = text_font.render(cargo_text, True, (255, 255, 0))
        
        screen.blit(credits_surface, (20, 80))
        screen.blit(cargo_surface, (width - cargo_surface.get_width() - 20, 80))
        
        # Divider line
        pygame.draw.line(screen, (100, 100, 100), (0, 120), (width, 120), 2)
        
        # Split screen layout
        left_width = width // 2 - 10
        right_width = width // 2 - 10
        content_y = 140
        
        # Left panel - Station Market
        market_header = header_font.render("STATION MARKET", True, (200, 200, 200))
        screen.blit(market_header, (20, content_y))
        
        # Right panel - Ship Cargo
        cargo_header = header_font.render("YOUR CARGO", True, (200, 200, 200))
        screen.blit(cargo_header, (width//2 + 20, content_y))
        
        # Market commodities list
        self._render_market_list(screen, 20, content_y + 40, left_width, text_font, small_font)
        
        # Ship cargo list  
        self._render_cargo_list(screen, width//2 + 20, content_y + 40, right_width, text_font, small_font)
        
        # Controls and instructions
        self._render_controls(screen, height, small_font)
        
        # Transaction message
        if self.message:
            msg_surface = text_font.render(self.message, True, (255, 255, 0))
            msg_rect = msg_surface.get_rect(centerx=width//2, y=height - 80)
            screen.blit(msg_surface, msg_rect)
    
    def _render_market_list(self, screen, x, y, width, text_font, small_font):
        """Render the station's market commodity list."""
        if not self.market:
            return
            
        current_y = y
        line_height = 30
        
        for i, commodity in enumerate(self.available_commodities):
            # Highlight selected item if viewing market
            if not self.viewing_cargo and i == self.selected_commodity_index:
                pygame.draw.rect(screen, (50, 50, 100), (x-5, current_y-5, width, line_height))
            
            # Commodity name
            name_surface = text_font.render(commodity.name, True, (255, 255, 255))
            screen.blit(name_surface, (x, current_y))
            
            # Prices
            buy_price = self.market.get_buy_price(commodity.id)
            sell_price = self.market.get_sell_price(commodity.id)
            
            price_text = f"Buy: {buy_price}  Sell: {sell_price}"
            price_surface = small_font.render(price_text, True, (200, 200, 200))
            screen.blit(price_surface, (x + 20, current_y + 18))
            
            current_y += line_height + 10
    
    def _render_cargo_list(self, screen, x, y, width, text_font, small_font):
        """Render the ship's cargo list."""
        current_y = y
        line_height = 30
        
        cargo_items = self.ship.cargo_hold.get_cargo_items()
        
        if not cargo_items:
            empty_surface = text_font.render("Cargo hold empty", True, (150, 150, 150))
            screen.blit(empty_surface, (x, current_y))
            return
        
        for i, (commodity, quantity) in enumerate(cargo_items):
            # Highlight selected item if viewing cargo
            if self.viewing_cargo and i == self.selected_commodity_index:
                pygame.draw.rect(screen, (50, 100, 50), (x-5, current_y-5, width, line_height))
            
            # Commodity name and quantity
            name_text = f"{commodity.name}"
            quantity_text = f"x{quantity}"
            
            name_surface = text_font.render(name_text, True, (255, 255, 255))
            quantity_surface = text_font.render(quantity_text, True, (200, 200, 200))
            
            screen.blit(name_surface, (x, current_y))
            screen.blit(quantity_surface, (x + width - quantity_surface.get_width(), current_y))
            
            # Value
            if self.market:
                sell_price = self.market.get_sell_price(commodity.id)
                if sell_price:
                    value = sell_price * quantity
                    value_text = f"Value: {value}"
                    value_surface = small_font.render(value_text, True, (200, 200, 200))
                    screen.blit(value_surface, (x + 20, current_y + 18))
            
            current_y += line_height + 10
    
    def _render_controls(self, screen, height, font):
        """Render control instructions."""
        controls = [
            "ARROW KEYS: Navigate",
            "TAB: Switch between Market/Cargo",
            "B: Buy selected commodity",
            "S: Sell selected commodity", 
            "ESC: Exit trading"
        ]
        
        current_y = height - 140
        for control in controls:
            surface = font.render(control, True, (180, 180, 180))
            screen.blit(surface, (20, current_y))
            current_y += 20
        
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameStates.PLAYING)
                
            elif event.key == pygame.K_TAB:
                self.viewing_cargo = not self.viewing_cargo
                self.selected_commodity_index = 0
                
            elif event.key == pygame.K_UP:
                self._move_selection(-1)
                
            elif event.key == pygame.K_DOWN:
                self._move_selection(1)
                
            elif event.key == pygame.K_b:
                self._attempt_buy()
                
            elif event.key == pygame.K_s:
                self._attempt_sell()
    
    def _move_selection(self, direction):
        """Move the selection cursor up or down."""
        if self.viewing_cargo:
            max_items = len(self.ship.cargo_hold.get_cargo_items())
        else:
            max_items = len(self.available_commodities)
        
        if max_items > 0:
            self.selected_commodity_index = (self.selected_commodity_index + direction) % max_items
    
    def _attempt_buy(self):
        """Attempt to buy the selected commodity from the station."""
        if self.viewing_cargo or not self.available_commodities:
            self._show_message("Select a commodity from the station market to buy")
            return
        
        if self.selected_commodity_index >= len(self.available_commodities):
            return
            
        commodity = self.available_commodities[self.selected_commodity_index]
        buy_price = self.market.get_buy_price(commodity.id)
        
        # Check if player has enough credits
        if self.ship.credits < buy_price:
            self._show_message("Insufficient credits")
            return
            
        # Check if ship has cargo space
        if not self.ship.cargo_hold.can_add(commodity.id, 1):
            self._show_message("Insufficient cargo space")
            return
            
        # Check if station has stock
        if not self.market.can_buy_from_station(commodity.id, 1):
            self._show_message("Station out of stock")
            return
            
        # Execute transaction
        if self.market.buy_from_station(commodity.id, 1):
            if self.ship.cargo_hold.add_cargo(commodity.id, 1):
                self.ship.credits -= buy_price
                self._show_message(f"Bought {commodity.name} for {buy_price} credits")
            else:
                # Rollback market transaction if cargo add failed
                self.market.sell_to_station(commodity.id, 1)
                self._show_message("Transaction failed - cargo error")
        else:
            self._show_message("Transaction failed")
    
    def _attempt_sell(self):
        """Attempt to sell the selected commodity to the station."""
        if not self.viewing_cargo:
            self._show_message("Select a commodity from your cargo to sell")
            return
            
        cargo_items = self.ship.cargo_hold.get_cargo_items()
        if not cargo_items or self.selected_commodity_index >= len(cargo_items):
            return
            
        commodity, quantity = cargo_items[self.selected_commodity_index]
        sell_price = self.market.get_sell_price(commodity.id)
        
        # Check if station will buy this commodity
        if not self.market.can_sell_to_station(commodity.id, 1):
            self._show_message("Station not buying this commodity")
            return
        
        # Execute transaction  
        if self.ship.cargo_hold.remove_cargo(commodity.id, 1):
            if self.market.sell_to_station(commodity.id, 1):
                self.ship.credits += sell_price
                self._show_message(f"Sold {commodity.name} for {sell_price} credits")
            else:
                # Rollback cargo transaction if market transaction failed
                self.ship.cargo_hold.add_cargo(commodity.id, 1)
                self._show_message("Transaction failed - market error")
        else:
            self._show_message("Transaction failed")
    
    def _show_message(self, message):
        """Display a temporary message to the player."""
        self.message = message
        self.message_timer = 3.0  # Show for 3 seconds


class UpgradeState(State):
    def __init__(self, game, station=None):
        super().__init__(game)
        self.station = station
        self.selected_upgrade_index = 0
        self.selected_category_index = 0
        self.viewing_categories = True  # True = category list, False = upgrade list
        self.message = ""
        self.message_timer = 0
        
        # Get ship and upgrade system references
        self.ship = game.ship
        
        # Import upgrade system
        try:
            from ..upgrades.upgrade_definitions import UpgradeCategory, upgrade_registry
            from ..upgrades.upgrade_system import upgrade_system
        except ImportError:
            from upgrades.upgrade_definitions import UpgradeCategory, upgrade_registry
            from upgrades.upgrade_system import upgrade_system
        
        self.UpgradeCategory = UpgradeCategory
        self.upgrade_registry = upgrade_registry
        self.upgrade_system = upgrade_system
        
        # Get available upgrades for this station
        station_type = station.station_type.value if station else "Shipyard"
        self.available_upgrades = upgrade_system.get_available_upgrades_for_station(
            self.ship.upgrades,
            station_type,
            self.ship.credits
        )
        
        # Group upgrades by category
        self.upgrades_by_category = {}
        for category in UpgradeCategory:
            category_upgrades = [u for u in self.available_upgrades if u.category == category]
            if category_upgrades:
                self.upgrades_by_category[category] = category_upgrades
        
        self.categories = list(self.upgrades_by_category.keys())
        
    def update(self, delta_time):
        # Update message timer
        if self.message_timer > 0:
            self.message_timer -= delta_time
            if self.message_timer <= 0:
                self.message = ""
    
    def render(self, screen):
        # Clear screen with dark background
        screen.fill((20, 30, 20))
        
        # Fonts
        title_font = pygame.font.Font(None, 48)
        header_font = pygame.font.Font(None, 36)
        text_font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 20)
        
        # Screen dimensions
        width, height = screen.get_size()
        
        # Title
        station_name = self.station.name if self.station else "Unknown Station"
        station_type = self.station.station_type.value if self.station else "Unknown"
        title_text = f"SHIP UPGRADES - {station_name} ({station_type})"
        title_surface = title_font.render(title_text, True, (255, 255, 255))
        title_rect = title_surface.get_rect(centerx=width//2, y=20)
        screen.blit(title_surface, title_rect)
        
        # Credits and ship info
        ship_info = self.ship.get_ship_info()
        credits_text = f"Credits: {ship_info['credits']:,}"
        ship_text = f"Ship: Modified Trader (Upgrades: {ship_info['total_upgrade_value']:,} cr)"
        
        credits_surface = text_font.render(credits_text, True, (255, 255, 0))
        ship_surface = text_font.render(ship_text, True, (200, 200, 200))
        
        screen.blit(credits_surface, (20, 80))
        screen.blit(ship_surface, (width - ship_surface.get_width() - 20, 80))
        
        # Divider line
        pygame.draw.line(screen, (100, 100, 100), (0, 120), (width, 120), 2)
        
        # Split screen layout
        left_width = width // 2 - 10
        right_width = width // 2 - 10
        content_y = 140
        
        # Left panel - Current Ship Stats
        stats_header = header_font.render("CURRENT SHIP STATS", True, (200, 200, 200))
        screen.blit(stats_header, (20, content_y))
        
        # Right panel - Available Upgrades
        upgrades_header = header_font.render("AVAILABLE UPGRADES", True, (200, 200, 200))
        screen.blit(upgrades_header, (width//2 + 20, content_y))
        
        # Ship stats list
        self._render_ship_stats(screen, 20, content_y + 40, left_width, text_font, small_font)
        
        # Upgrades list
        self._render_upgrades_list(screen, width//2 + 20, content_y + 40, right_width, text_font, small_font)
        
        # Controls and instructions
        self._render_controls(screen, height, small_font)
        
        # Transaction message
        if self.message:
            msg_surface = text_font.render(self.message, True, (255, 255, 0))
            msg_rect = msg_surface.get_rect(centerx=width//2, y=height - 80)
            screen.blit(msg_surface, msg_rect)
    
    def _render_ship_stats(self, screen, x, y, width, text_font, small_font):
        """Render current ship statistics."""
        ship_info = self.ship.get_ship_info()
        effective_stats = self.ship.get_effective_stats()
        
        current_y = y
        line_height = 25
        
        # Cargo
        cargo_text = f"Cargo: {ship_info['cargo_used']}/{ship_info['cargo_capacity']} units"
        cargo_surface = text_font.render(cargo_text, True, (255, 255, 255))
        screen.blit(cargo_surface, (x, current_y))
        current_y += line_height
        
        # Speed
        speed_text = f"Max Speed: {ship_info['max_speed']:.0f} u/s"
        speed_surface = text_font.render(speed_text, True, (255, 255, 255))
        screen.blit(speed_surface, (x, current_y))
        current_y += line_height
        
        # Thrust
        thrust_text = f"Thrust: {ship_info['thrust_force']:.0f} N"
        thrust_surface = text_font.render(thrust_text, True, (255, 255, 255))
        screen.blit(thrust_surface, (x, current_y))
        current_y += line_height
        
        # Hull
        hull_text = f"Hull: {ship_info['hull_current']:.0f}/{ship_info['hull_max']:.0f} HP"
        hull_surface = text_font.render(hull_text, True, (255, 255, 255))
        screen.blit(hull_surface, (x, current_y))
        current_y += line_height
        
        # Scanner
        scanner_text = f"Scanner: {ship_info['scanner_range']:.0f} range"
        scanner_surface = text_font.render(scanner_text, True, (255, 255, 255))
        screen.blit(scanner_surface, (x, current_y))
        current_y += line_height * 2
        
        # Installed upgrades
        upgrade_header = small_font.render("Installed Upgrades:", True, (200, 200, 200))
        screen.blit(upgrade_header, (x, current_y))
        current_y += 20
        
        for category, upgrade_name in ship_info['upgrade_summary'].items():
            upgrade_text = f"{category}: {upgrade_name}"
            upgrade_surface = small_font.render(upgrade_text, True, (150, 150, 150))
            screen.blit(upgrade_surface, (x + 10, current_y))
            current_y += 18
    
    def _render_upgrades_list(self, screen, x, y, width, text_font, small_font):
        """Render available upgrades list."""
        if not self.categories:
            no_upgrades_surface = text_font.render("No upgrades available", True, (150, 150, 150))
            screen.blit(no_upgrades_surface, (x, y))
            return
        
        current_y = y
        line_height = 35
        
        if self.viewing_categories:
            # Show categories
            for i, category in enumerate(self.categories):
                # Highlight selected category
                if i == self.selected_category_index:
                    pygame.draw.rect(screen, (50, 100, 50), (x-5, current_y-5, width, line_height))
                
                # Category name
                category_text = f"► {category.value}"
                category_surface = text_font.render(category_text, True, (255, 255, 255))
                screen.blit(category_surface, (x, current_y))
                
                # Number of upgrades in category
                upgrade_count = len(self.upgrades_by_category[category])
                count_text = f"({upgrade_count} upgrades)"
                count_surface = small_font.render(count_text, True, (200, 200, 200))
                screen.blit(count_surface, (x + 20, current_y + 18))
                
                current_y += line_height + 10
        else:
            # Show upgrades in selected category
            if self.selected_category_index < len(self.categories):
                selected_category = self.categories[self.selected_category_index]
                category_upgrades = self.upgrades_by_category[selected_category]
                
                for i, upgrade in enumerate(category_upgrades):
                    # Highlight selected upgrade
                    if i == self.selected_upgrade_index:
                        pygame.draw.rect(screen, (100, 50, 50), (x-5, current_y-5, width, line_height))
                    
                    # Upgrade name
                    name_surface = text_font.render(upgrade.name, True, (255, 255, 255))
                    screen.blit(name_surface, (x, current_y))
                    
                    # Price and details
                    station_type = self.station.station_type.value if self.station else "Shipyard"
                    discounted_price = self.upgrade_system.get_discounted_price(upgrade, station_type)
                    
                    price_text = f"{discounted_price:,} credits"
                    if discounted_price < upgrade.cost:
                        price_text += f" (was {upgrade.cost:,})"
                    
                    price_surface = small_font.render(price_text, True, (255, 255, 0))
                    screen.blit(price_surface, (x + 20, current_y + 18))
                    
                    current_y += line_height + 5
    
    def _render_controls(self, screen, height, font):
        """Render control instructions."""
        if self.viewing_categories:
            controls = [
                "ARROW KEYS: Navigate categories",
                "ENTER: View category upgrades",
                "ESC: Exit upgrades"
            ]
        else:
            controls = [
                "ARROW KEYS: Navigate upgrades",
                "ENTER: Purchase upgrade",
                "BACKSPACE: Back to categories",
                "ESC: Exit upgrades"
            ]
        
        current_y = height - 120
        for control in controls:
            surface = font.render(control, True, (180, 180, 180))
            screen.blit(surface, (20, current_y))
            current_y += 20
    
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameStates.PLAYING)
                
            elif event.key == pygame.K_UP:
                self._move_selection(-1)
                
            elif event.key == pygame.K_DOWN:
                self._move_selection(1)
                
            elif event.key == pygame.K_RETURN:
                if self.viewing_categories:
                    self._enter_category()
                else:
                    self._attempt_purchase()
                    
            elif event.key == pygame.K_BACKSPACE:
                if not self.viewing_categories:
                    self.viewing_categories = True
                    self.selected_upgrade_index = 0
    
    def _move_selection(self, direction):
        """Move the selection cursor up or down."""
        if self.viewing_categories:
            max_items = len(self.categories)
            if max_items > 0:
                self.selected_category_index = (self.selected_category_index + direction) % max_items
        else:
            if self.selected_category_index < len(self.categories):
                selected_category = self.categories[self.selected_category_index]
                category_upgrades = self.upgrades_by_category[selected_category]
                max_items = len(category_upgrades)
                if max_items > 0:
                    self.selected_upgrade_index = (self.selected_upgrade_index + direction) % max_items
    
    def _enter_category(self):
        """Enter the selected category to view upgrades."""
        if self.selected_category_index < len(self.categories):
            self.viewing_categories = False
            self.selected_upgrade_index = 0
    
    def _attempt_purchase(self):
        """Attempt to purchase the selected upgrade."""
        if (self.selected_category_index >= len(self.categories) or 
            self.viewing_categories):
            return
        
        selected_category = self.categories[self.selected_category_index]
        category_upgrades = self.upgrades_by_category[selected_category]
        
        if self.selected_upgrade_index >= len(category_upgrades):
            return
        
        upgrade = category_upgrades[self.selected_upgrade_index]
        
        # Get discounted price
        station_type = self.station.station_type.value if self.station else "Shipyard"
        discounted_price = self.upgrade_system.get_discounted_price(upgrade, station_type)
        
        # Check if player can afford it
        if self.ship.credits < discounted_price:
            self._show_message("Insufficient credits")
            return
        
        # Attempt purchase with discounted price
        # Temporarily modify the upgrade cost for this transaction
        original_cost = upgrade.cost
        upgrade.cost = discounted_price
        
        try:
            result, remaining_credits = self.upgrade_system.purchase_upgrade(
                self.ship.upgrades, upgrade.id, self.ship.credits
            )
            
            if result.success:
                self.ship.credits = remaining_credits
                self.ship._update_cargo_capacity()  # Update cargo capacity
                self._show_message(f"Installed {upgrade.name}")
                
                # Refresh available upgrades
                self._refresh_available_upgrades()
            else:
                self._show_message(result.message)
        finally:
            # Restore original cost
            upgrade.cost = original_cost
    
    def _refresh_available_upgrades(self):
        """Refresh the list of available upgrades."""
        station_type = self.station.station_type.value if self.station else "Shipyard"
        self.available_upgrades = self.upgrade_system.get_available_upgrades_for_station(
            self.ship.upgrades,
            station_type,
            self.ship.credits
        )
        
        # Rebuild categories
        self.upgrades_by_category = {}
        for category in self.UpgradeCategory:
            category_upgrades = [u for u in self.available_upgrades if u.category == category]
            if category_upgrades:
                self.upgrades_by_category[category] = category_upgrades
        
        self.categories = list(self.upgrades_by_category.keys())
        
        # Reset selection if needed
        if self.selected_category_index >= len(self.categories):
            self.selected_category_index = 0
            self.viewing_categories = True
    
    def _show_message(self, message):
        """Display a temporary message to the player."""
        self.message = message
        self.message_timer = 3.0  # Show for 3 seconds


class GameOverState(State):
    def __init__(self, game):
        super().__init__(game)
        
    def render(self, screen):
        # Render game over screen
        pass
        
    def handle_input(self, event):
        pass


class SaveGameState(State):
    def __init__(self, game):
        super().__init__(game)
        from ..save_system import save_system
        self.save_system = save_system
        self.title = "Save Game"
        self.save_name = ""
        self.editing_name = True
        self.message = ""
        self.message_timer = 0.0
        self.existing_saves = self.save_system.get_save_list()
        self.selected_save_index = 0
        
    def update(self, delta_time):
        if self.message_timer > 0:
            self.message_timer -= delta_time
            if self.message_timer <= 0:
                self.message = ""
    
    def render(self, screen):
        screen.fill((0, 0, 20))  # Dark blue background
        
        # Draw title
        title_font = pygame.font.Font(None, 64)
        title = title_font.render(self.title, True, (255, 255, 255))
        title_rect = title.get_rect(center=(screen.get_width() // 2, 80))
        screen.blit(title, title_rect)
        
        # Draw input field
        input_font = pygame.font.Font(None, 36)
        name_label = input_font.render("Save Name:", True, (200, 200, 200))
        screen.blit(name_label, (50, 150))
        
        # Input box
        input_box = pygame.Rect(50, 180, 400, 40)
        input_color = (255, 255, 255) if self.editing_name else (150, 150, 150)
        pygame.draw.rect(screen, input_color, input_box, 2)
        
        # Current save name text
        name_text = input_font.render(self.save_name, True, (255, 255, 255))
        screen.blit(name_text, (input_box.x + 5, input_box.y + 8))
        
        # Draw existing saves
        saves_label = input_font.render("Existing Saves:", True, (200, 200, 200))
        screen.blit(saves_label, (50, 250))
        
        save_font = pygame.font.Font(None, 28)
        y_offset = 280
        for i, save_meta in enumerate(self.existing_saves[:8]):  # Show up to 8 saves
            color = (255, 255, 0) if i == self.selected_save_index and not self.editing_name else (255, 255, 255)
            save_text = f"{save_meta.save_name} - {save_meta.credits} credits - {save_meta.location}"
            text = save_font.render(save_text, True, color)
            screen.blit(text, (70, y_offset))
            y_offset += 30
        
        # Draw instructions
        instruction_font = pygame.font.Font(None, 24)
        instructions = [
            "Type save name and press ENTER to save",
            "Use UP/DOWN to select existing save to overwrite",
            "Press TAB to switch between input and save list",
            "Press ESC to go back"
        ]
        
        y_offset = screen.get_height() - 120
        for instruction in instructions:
            instr_text = instruction_font.render(instruction, True, (150, 150, 150))
            screen.blit(instr_text, (50, y_offset))
            y_offset += 25
        
        # Draw message if any
        if self.message:
            message_font = pygame.font.Font(None, 36)
            msg_color = (0, 255, 0) if "success" in self.message.lower() else (255, 100, 100)
            msg_text = message_font.render(self.message, True, msg_color)
            msg_rect = msg_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
            pygame.draw.rect(screen, (0, 0, 0), msg_rect.inflate(20, 10))
            screen.blit(msg_text, msg_rect)
    
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameStates.PAUSED)
            elif event.key == pygame.K_TAB:
                self.editing_name = not self.editing_name
            elif self.editing_name:
                self._handle_name_input(event)
            else:
                self._handle_save_list_input(event)
    
    def _handle_name_input(self, event):
        """Handle text input for save name."""
        if event.key == pygame.K_RETURN:
            self._save_game()
        elif event.key == pygame.K_BACKSPACE:
            self.save_name = self.save_name[:-1]
        else:
            if len(self.save_name) < 30:  # Limit save name length
                char = event.unicode
                if char.isprintable() and char not in ['<', '>', ':', '"', '|', '?', '*', '/', '\\']:
                    self.save_name += char
    
    def _handle_save_list_input(self, event):
        """Handle navigation of existing saves list."""
        if event.key == pygame.K_UP and self.existing_saves:
            self.selected_save_index = (self.selected_save_index - 1) % len(self.existing_saves)
        elif event.key == pygame.K_DOWN and self.existing_saves:
            self.selected_save_index = (self.selected_save_index + 1) % len(self.existing_saves)
        elif event.key == pygame.K_RETURN and self.existing_saves:
            # Overwrite selected save
            selected_save = self.existing_saves[self.selected_save_index]
            self.save_name = selected_save.save_name
            self._save_game()
    
    def _save_game(self):
        """Save the current game."""
        if not self.save_name.strip():
            self.message = "Please enter a save name"
            self.message_timer = 2.0
            return
        
        success = self.save_system.save_game(self.game, self.save_name.strip())
        if success:
            self.message = "Game saved successfully!"
            self.message_timer = 2.0
            # Refresh save list
            self.existing_saves = self.save_system.get_save_list()
        else:
            self.message = "Save failed!"
            self.message_timer = 2.0


class LoadGameState(State):
    def __init__(self, game):
        super().__init__(game)
        from ..save_system import save_system
        self.save_system = save_system
        self.title = "Load Game"
        self.existing_saves = self.save_system.get_save_list()
        self.selected_save_index = 0
        self.message = ""
        self.message_timer = 0.0
        
    def update(self, delta_time):
        if self.message_timer > 0:
            self.message_timer -= delta_time
            if self.message_timer <= 0:
                self.message = ""
    
    def render(self, screen):
        screen.fill((0, 0, 20))  # Dark blue background
        
        # Draw title
        title_font = pygame.font.Font(None, 64)
        title = title_font.render(self.title, True, (255, 255, 255))
        title_rect = title.get_rect(center=(screen.get_width() // 2, 80))
        screen.blit(title, title_rect)
        
        if not self.existing_saves:
            # No saves found
            no_saves_font = pygame.font.Font(None, 48)
            no_saves_text = no_saves_font.render("No saved games found", True, (200, 200, 200))
            no_saves_rect = no_saves_text.get_rect(center=(screen.get_width() // 2, 300))
            screen.blit(no_saves_text, no_saves_rect)
        else:
            # Draw save list with details
            save_font = pygame.font.Font(None, 32)
            detail_font = pygame.font.Font(None, 24)
            
            y_offset = 150
            for i, save_meta in enumerate(self.existing_saves):
                is_selected = i == self.selected_save_index
                color = (255, 255, 0) if is_selected else (255, 255, 255)
                detail_color = (200, 200, 0) if is_selected else (150, 150, 150)
                
                # Save name
                name_text = save_font.render(save_meta.save_name, True, color)
                screen.blit(name_text, (50, y_offset))
                
                # Save details
                from datetime import datetime
                try:
                    save_date = datetime.fromisoformat(save_meta.save_date)
                    date_str = save_date.strftime("%Y-%m-%d %H:%M")
                except:
                    date_str = save_meta.save_date
                
                details = f"Credits: {save_meta.credits} | Location: {save_meta.location} | Date: {date_str}"
                detail_text = detail_font.render(details, True, detail_color)
                screen.blit(detail_text, (70, y_offset + 25))
                
                # Selection highlight
                if is_selected:
                    pygame.draw.rect(screen, (50, 50, 100), 
                                   pygame.Rect(40, y_offset - 5, screen.get_width() - 80, 50), 2)
                
                y_offset += 70
        
        # Draw instructions
        instruction_font = pygame.font.Font(None, 24)
        instructions = [
            "Use UP/DOWN to select save",
            "Press ENTER to load selected save",
            "Press DELETE to delete selected save",
            "Press ESC to go back"
        ]
        
        y_offset = screen.get_height() - 120
        for instruction in instructions:
            instr_text = instruction_font.render(instruction, True, (150, 150, 150))
            screen.blit(instr_text, (50, y_offset))
            y_offset += 25
        
        # Draw message if any
        if self.message:
            message_font = pygame.font.Font(None, 36)
            msg_color = (0, 255, 0) if "success" in self.message.lower() else (255, 100, 100)
            msg_text = message_font.render(self.message, True, msg_color)
            msg_rect = msg_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
            pygame.draw.rect(screen, (0, 0, 0), msg_rect.inflate(20, 10))
            screen.blit(msg_text, msg_rect)
    
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameStates.MAIN_MENU)
            elif not self.existing_saves:
                return  # No saves to interact with
            elif event.key == pygame.K_UP:
                self.selected_save_index = (self.selected_save_index - 1) % len(self.existing_saves)
            elif event.key == pygame.K_DOWN:
                self.selected_save_index = (self.selected_save_index + 1) % len(self.existing_saves)
            elif event.key == pygame.K_RETURN:
                self._load_game()
            elif event.key == pygame.K_DELETE:
                self._delete_save()
    
    def _load_game(self):
        """Load the selected game."""
        if not self.existing_saves:
            return
        
        selected_save = self.existing_saves[self.selected_save_index]
        success = self.save_system.load_game(selected_save.save_name, self.game)
        
        if success:
            self.message = "Game loaded successfully!"
            self.message_timer = 1.0
            # Transition to playing state immediately
            self.game.change_state(GameStates.PLAYING)
        else:
            self.message = "Load failed!"
            self.message_timer = 2.0
    
    def _delete_save(self):
        """Delete the selected save."""
        if not self.existing_saves:
            return
        
        selected_save = self.existing_saves[self.selected_save_index]
        success = self.save_system.delete_save(selected_save.save_name)
        
        if success:
            self.message = "Save deleted"
            self.message_timer = 1.5
            # Refresh save list
            self.existing_saves = self.save_system.get_save_list()
            if self.selected_save_index >= len(self.existing_saves):
                self.selected_save_index = max(0, len(self.existing_saves) - 1)
        else:
            self.message = "Delete failed!"
            self.message_timer = 2.0


class MissionBoardState(State):
    def __init__(self, game, station=None):
        super().__init__(game)
        from ..missions.mission_manager import mission_manager
        self.mission_manager = mission_manager
        self.station = station
        self.title = "Mission Board"
        self.selected_mission_index = 0
        self.viewing_details = False
        self.current_tab = "available"  # "available", "active"
        self.message = ""
        self.message_timer = 0.0
        
        # Generate missions for this station if it's the first visit
        if self.station:
            self.mission_manager.generate_missions_for_station(self.station, self.game)
        
        # Get missions for this station
        self.refresh_missions()
    
    def refresh_missions(self):
        """Refresh the mission lists."""
        if self.station:
            self.available_missions = self.mission_manager.get_available_missions_for_station(self.station.name)
        else:
            self.available_missions = self.mission_manager.available_missions
        
        self.active_missions = self.mission_manager.active_missions
        
        # Reset selection if needed
        if self.current_tab == "available" and self.selected_mission_index >= len(self.available_missions):
            self.selected_mission_index = max(0, len(self.available_missions) - 1)
        elif self.current_tab == "active" and self.selected_mission_index >= len(self.active_missions):
            self.selected_mission_index = max(0, len(self.active_missions) - 1)
    
    def update(self, delta_time):
        if self.message_timer > 0:
            self.message_timer -= delta_time
            if self.message_timer <= 0:
                self.message = ""
    
    def render(self, screen):
        screen.fill((20, 20, 40))  # Dark blue background
        
        # Fonts
        title_font = pygame.font.Font(None, 64)
        tab_font = pygame.font.Font(None, 48)
        header_font = pygame.font.Font(None, 36)
        text_font = pygame.font.Font(None, 28)
        small_font = pygame.font.Font(None, 20)
        
        width, height = screen.get_size()
        
        # Title
        station_name = self.station.name if self.station else "Mission Central"
        title_text = f"MISSION BOARD - {station_name}"
        title_surface = title_font.render(title_text, True, (255, 255, 255))
        title_rect = title_surface.get_rect(centerx=width//2, y=20)
        screen.blit(title_surface, title_rect)
        
        # Tab navigation
        tab_y = 80
        tab_width = 150
        available_color = (255, 255, 0) if self.current_tab == "available" else (200, 200, 200)
        active_color = (255, 255, 0) if self.current_tab == "active" else (200, 200, 200)
        
        available_tab = tab_font.render("Available", True, available_color)
        active_tab = tab_font.render("Active", True, active_color)
        
        screen.blit(available_tab, (50, tab_y))
        screen.blit(active_tab, (50 + tab_width, tab_y))
        
        # Mission count
        if self.current_tab == "available":
            count_text = f"({len(self.available_missions)} missions)"
            missions_to_show = self.available_missions
        else:
            count_text = f"({len(self.active_missions)} missions)"
            missions_to_show = self.active_missions
        
        count_surface = small_font.render(count_text, True, (150, 150, 150))
        screen.blit(count_surface, (50, tab_y + 40))
        
        # Divider line
        pygame.draw.line(screen, (100, 100, 100), (0, 140), (width, 140), 2)
        
        if not self.viewing_details:
            self._render_mission_list(screen, missions_to_show, text_font, small_font)
        else:
            self._render_mission_details(screen, missions_to_show, header_font, text_font, small_font)
        
        # Instructions
        instruction_y = height - 80
        if not self.viewing_details:
            instructions = [
                "TAB: Switch tabs | UP/DOWN: Navigate | ENTER: View details",
                "A: Accept mission | ESC: Back"
            ]
        else:
            instructions = [
                "A: Accept mission | X: Abandon (if active) | ESC: Back to list"
            ]
        
        instruction_font = pygame.font.Font(None, 20)
        for i, instruction in enumerate(instructions):
            instr_text = instruction_font.render(instruction, True, (150, 150, 150))
            screen.blit(instr_text, (20, instruction_y + i * 20))
        
        # Draw message if any
        if self.message:
            message_font = pygame.font.Font(None, 36)
            msg_color = (0, 255, 0) if "success" in self.message.lower() else (255, 100, 100)
            msg_text = message_font.render(self.message, True, msg_color)
            msg_rect = msg_text.get_rect(center=(width // 2, height // 2))
            pygame.draw.rect(screen, (0, 0, 0), msg_rect.inflate(20, 10))
            screen.blit(msg_text, msg_rect)
    
    def _render_mission_list(self, screen, missions, text_font, small_font):
        """Render the list of missions."""
        if not missions:
            no_missions_text = text_font.render("No missions available", True, (150, 150, 150))
            screen.blit(no_missions_text, (50, 200))
            return
        
        start_y = 160
        mission_height = 100
        
        # Show up to 5 missions at a time
        start_index = max(0, self.selected_mission_index - 2)
        end_index = min(len(missions), start_index + 5)
        
        for i in range(start_index, end_index):
            mission = missions[i]
            y = start_y + (i - start_index) * mission_height
            
            # Highlight selected mission
            is_selected = i == self.selected_mission_index
            if is_selected:
                pygame.draw.rect(screen, (50, 50, 100), 
                               pygame.Rect(40, y - 5, screen.get_width() - 80, mission_height - 10))
            
            # Mission title and type
            title_color = (255, 255, 0) if is_selected else (255, 255, 255)
            title_text = text_font.render(mission.title, True, title_color)
            screen.blit(title_text, (50, y))
            
            # Mission type and priority
            type_text = f"{mission.mission_type.value} | {mission.priority.value}"
            type_color = self._get_priority_color(mission.priority)
            type_surface = small_font.render(type_text, True, type_color)
            screen.blit(type_surface, (50, y + 25))
            
            # Reward
            reward_text = f"Reward: {mission.reward.credits:,} credits"
            reward_surface = small_font.render(reward_text, True, (0, 255, 0))
            screen.blit(reward_surface, (50, y + 45))
            
            # Destination info (if available)
            if hasattr(mission, 'destination_station_id') and mission.destination_station_id:
                dest_coords = self.mission_manager.get_station_coordinates(
                    mission.destination_station_id, 
                    self.game.universe.stations
                )
                if dest_coords:
                    dest_text = f"Destination: {mission.destination_station_id} - {dest_coords}"
                    dest_surface = small_font.render(dest_text, True, (150, 200, 255))
                    screen.blit(dest_surface, (50, y + 65))
            
            # Time remaining (if applicable)
            time_remaining = mission.get_formatted_time_remaining()
            if time_remaining != "No time limit":
                time_color = (255, 0, 0) if "EXPIRED" in time_remaining else (255, 255, 0)
                time_surface = small_font.render(f"Time: {time_remaining}", True, time_color)
                screen.blit(time_surface, (350, y + 45))
            
            # Status (for active missions)
            if self.current_tab == "active":
                status_text = f"Status: {mission.status.value} ({mission.completion_percentage:.0%})"
                status_surface = small_font.render(status_text, True, (150, 200, 255))
                screen.blit(status_surface, (50, y + 65))
    
    def _render_mission_details(self, screen, missions, header_font, text_font, small_font):
        """Render detailed view of selected mission."""
        if not missions or self.selected_mission_index >= len(missions):
            return
        
        mission = missions[self.selected_mission_index]
        
        start_y = 160
        line_height = 25
        current_y = start_y
        
        # Mission title
        title_text = header_font.render(mission.title, True, (255, 255, 255))
        screen.blit(title_text, (50, current_y))
        current_y += 40
        
        # Mission details
        details = [
            f"Type: {mission.mission_type.value}",
            f"Priority: {mission.priority.value}",
            f"Status: {mission.status.value}",
            f"Reward: {mission.reward.credits:,} credits",
            f"Time Limit: {mission.get_formatted_time_remaining()}",
            "",
            "Description:",
            mission.description,
            ""
        ]
        
        # Add location information if available
        if hasattr(mission, 'origin_station_id') and mission.origin_station_id:
            origin_coords = self.mission_manager.get_station_coordinates(
                mission.origin_station_id, 
                self.game.universe.stations
            )
            if origin_coords:
                details.append(f"Origin: {mission.origin_station_id} - {origin_coords}")
        
        if hasattr(mission, 'destination_station_id') and mission.destination_station_id:
            dest_coords = self.mission_manager.get_station_coordinates(
                mission.destination_station_id, 
                self.game.universe.stations
            )
            if dest_coords:
                details.append(f"Destination: {mission.destination_station_id} - {dest_coords}")
        
        # Add trading station for trading contracts
        if hasattr(mission, 'station_id') and mission.station_id and not hasattr(mission, 'origin_station_id'):
            station_coords = self.mission_manager.get_station_coordinates(
                mission.station_id, 
                self.game.universe.stations
            )
            if station_coords:
                details.append(f"Trading Station: {mission.station_id} - {station_coords}")
        
        details.extend(["", "Objectives:"])
        
        for detail in details:
            if detail == "":
                current_y += line_height // 2
                continue
            
            color = (255, 255, 255)
            if "Priority:" in detail:
                color = self._get_priority_color(mission.priority)
            elif "Reward:" in detail:
                color = (0, 255, 0)
            elif "Time Limit:" in detail and "EXPIRED" in detail:
                color = (255, 0, 0)
            
            text_surface = text_font.render(detail, True, color)
            screen.blit(text_surface, (50, current_y))
            current_y += line_height
        
        # Objectives
        for i, objective in enumerate(mission.objectives):
            obj_color = (0, 255, 0) if objective.completed else (255, 255, 255)
            status = "✓" if objective.completed else "○"
            obj_text = f"  {status} {objective.description}"
            obj_surface = small_font.render(obj_text, True, obj_color)
            screen.blit(obj_surface, (70, current_y))
            current_y += line_height
        
        # Requirements
        if mission.requirements.min_reputation > 0 or mission.requirements.min_cargo_capacity > 0:
            current_y += line_height
            req_header = text_font.render("Requirements:", True, (255, 255, 255))
            screen.blit(req_header, (50, current_y))
            current_y += line_height
            
            if mission.requirements.min_reputation > 0:
                req_text = f"  Minimum Reputation: {mission.requirements.min_reputation}"
                req_surface = small_font.render(req_text, True, (255, 255, 255))
                screen.blit(req_surface, (70, current_y))
                current_y += line_height
            
            if mission.requirements.min_cargo_capacity > 0:
                req_text = f"  Minimum Cargo Space: {mission.requirements.min_cargo_capacity}"
                req_surface = small_font.render(req_text, True, (255, 255, 255))
                screen.blit(req_surface, (70, current_y))
                current_y += line_height
    
    def _get_priority_color(self, priority):
        """Get color for mission priority."""
        from ..missions.mission_types import MissionPriority
        
        priority_colors = {
            MissionPriority.LOW: (150, 150, 150),
            MissionPriority.MEDIUM: (255, 255, 255),
            MissionPriority.HIGH: (255, 200, 0),
            MissionPriority.URGENT: (255, 0, 0)
        }
        return priority_colors.get(priority, (255, 255, 255))
    
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.viewing_details:
                    self.viewing_details = False
                else:
                    self.game.change_state(GameStates.PLAYING)
            
            elif not self.viewing_details:
                self._handle_list_input(event)
            else:
                self._handle_details_input(event)
    
    def _handle_list_input(self, event):
        """Handle input when viewing mission list."""
        missions = self.available_missions if self.current_tab == "available" else self.active_missions
        
        if event.key == pygame.K_TAB:
            # Switch tabs
            self.current_tab = "active" if self.current_tab == "available" else "available"
            self.selected_mission_index = 0
            self.refresh_missions()
        
        elif event.key == pygame.K_UP and missions:
            self.selected_mission_index = (self.selected_mission_index - 1) % len(missions)
        
        elif event.key == pygame.K_DOWN and missions:
            self.selected_mission_index = (self.selected_mission_index + 1) % len(missions)
        
        elif event.key == pygame.K_RETURN and missions:
            self.viewing_details = True
        
        elif event.key == pygame.K_a and missions:
            # Accept mission
            self._accept_mission()
    
    def _handle_details_input(self, event):
        """Handle input when viewing mission details."""
        missions = self.available_missions if self.current_tab == "available" else self.active_missions
        
        if event.key == pygame.K_a and missions:
            # Accept mission
            self._accept_mission()
        
        elif event.key == pygame.K_x and self.current_tab == "active" and missions:
            # Abandon mission
            self._abandon_mission()
    
    def _accept_mission(self):
        """Accept the currently selected mission."""
        missions = self.available_missions if self.current_tab == "available" else self.active_missions
        
        if not missions or self.selected_mission_index >= len(missions):
            return
        
        mission = missions[self.selected_mission_index]
        
        if self.current_tab != "available":
            self.message = "Can only accept available missions"
            self.message_timer = 2.0
            return
        
        success, message = self.mission_manager.accept_mission(mission.id, self.game.ship, self.game)
        
        self.message = message
        self.message_timer = 2.0
        
        if success:
            self.refresh_missions()
            # Switch to active tab to show the accepted mission
            self.current_tab = "active"
            self.selected_mission_index = 0
    
    def _abandon_mission(self):
        """Abandon the currently selected active mission."""
        if self.current_tab != "active" or not self.active_missions:
            return
        
        if self.selected_mission_index >= len(self.active_missions):
            return
        
        mission = self.active_missions[self.selected_mission_index]
        success, message = self.mission_manager.abandon_mission(mission.id, self.game.ship)
        
        self.message = message
        self.message_timer = 2.0
        
        if success:
            self.refresh_missions()