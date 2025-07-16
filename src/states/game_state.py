import logging
from enum import Enum, auto

import pygame
from src.docking.docking_state import DockingResult
try:
    from ..trading.commodity import commodity_registry
except ImportError:
    from trading.commodity import commodity_registry

logger = logging.getLogger(__name__)


class GameStates(Enum):
    MAIN_MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    TRADING = auto()  # Added for market interface
    UPGRADES = auto()  # Added for ship upgrade interface
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

    def render(self, screen):
        # Clear screan first
        screen.fill((0, 0, 20)) # Dark blue background

        # Draw title
        title_font = pygame.font.Font(None, 74)
        title = title_font.render(self.title, True, (255, 255, 255))
        title_rect = title.get_rect(center=(screen.get_width() // 2, 100))
        screen.blit(title, title_rect)

        # Draw menu options
        option_font = pygame.font.Font(None, 48)  # Slightly larger font for options
        for i, option in enumerate(self.menu_options):
            color = (255, 255, 0) if i == self.selected_option else (255, 255, 255)
            text = option_font.render(option, True, color)
            # Position each option, centered horizontally and spaced vertically
            text_rect = text.get_rect(center=(screen.get_width() // 2, 300 + i * 60))
            screen.blit(text, text_rect)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.menu_options)
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.menu_options)
            elif event.key == pygame.K_RETURN:
                if self.selected_option == 0:  # New Game
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
        self.categories = ["Camera", "Display", "Back"]
        self.selected_category = 0
        
        # Camera settings options
        self.camera_options = ["Camera Mode", "Smoothing", "Deadzone", "Back"]
        self.selected_camera_option = 0
        self.viewing_camera = False
        
    def render(self, screen):
        screen.fill((0, 0, 20))  # Dark blue background
        
        # Draw title
        title_font = pygame.font.Font(None, 64)
        title = title_font.render(self.title, True, (255, 255, 255))
        title_rect = title.get_rect(center=(screen.get_width() // 2, 80))
        screen.blit(title, title_rect)
        
        if not self.viewing_camera:
            self._render_main_categories(screen)
        else:
            self._render_camera_settings(screen)
    
    def _render_main_categories(self, screen):
        """Render main settings categories"""
        option_font = pygame.font.Font(None, 48)
        for i, category in enumerate(self.categories):
            color = (255, 255, 0) if i == self.selected_category else (255, 255, 255)
            text = option_font.render(category, True, color)
            text_rect = text.get_rect(center=(screen.get_width() // 2, 200 + i * 60))
            screen.blit(text, text_rect)
    
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
                else:
                    self.game.change_state(GameStates.MAIN_MENU)
            elif not self.viewing_camera:
                self._handle_main_input(event)
            else:
                self._handle_camera_input(event)
    
    def _handle_main_input(self, event):
        """Handle input for main settings categories"""
        if event.key == pygame.K_UP:
            self.selected_category = (self.selected_category - 1) % len(self.categories)
        elif event.key == pygame.K_DOWN:
            self.selected_category = (self.selected_category + 1) % len(self.categories)
        elif event.key == pygame.K_RETURN:
            if self.selected_category == 0:  # Camera
                self.viewing_camera = True
                self.selected_camera_option = 0
            elif self.selected_category == 1:  # Display (future feature)
                pass  # TODO: Implement display settings
            elif self.selected_category == 2:  # Back
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

class PlayingState(State):
    def __init__(self, game):
        super().__init__(game)

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

        # Add debug visualization
        pygame.draw.circle(screen, (255, 0, 0), 
                          (int(screen.get_width()/2), int(screen.get_height()/2)), 
                          5)  # Center point reference
    
        # Draw coordinate grid
        grid_size = 100
        for x in range(0, screen.get_width(), grid_size):
            pygame.draw.line(screen, (50, 50, 50), 
                            (x, 0), (x, screen.get_height()))
        for y in range(0, screen.get_height(), grid_size):
            pygame.draw.line(screen, (50, 50, 50),
                            (0, y), (screen.get_width(), y))

        # Draw all stations
        for station in self.game.universe.stations:
            screen_pos = self.game.camera.world_to_screen(station.position)
            # Only draw if on screen
            if (0 <= screen_pos.x <= self.game.WINDOW_SIZE[0] and 
                0 <= screen_pos.y <= self.game.WINDOW_SIZE[1]):
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
            planet.draw(screen, camera_offset)

        # Draw debris
        for debris in self.game.universe.debris:
            debris.draw(screen, camera_offset)
        
        # Draw ship
        self.game.ship.draw(screen, camera_offset)
        
        # Draw minimap last (so it's on top)
        self.game.minimap.draw(screen, self.game.ship,
                             self.game.universe.stations,
                             self.game.universe.planets)
        
        if self.game.debug_mode:
            self._draw_debug_info(screen, camera_offset)

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
    
        # Debug info
        print(f"Number of stations: {len(self.game.universe.stations)}")
        print(f"Ship position: {self.game.ship.position}")
        print(f"Camera offset: {camera_offset}")

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameStates.PAUSED)
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
            elif event.key == pygame.K_x:  # Undocking (changed from U to X to avoid conflict)
                if self.game.docking_manager.is_docked():
                    result = self.game.docking_manager.attempt_undocking(self.game.ship)
                    if result != DockingResult.SUCCESS:
                        logger.info(f"Undocking failed: {result.value}")

class PausedState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pause_options = ["Resume", "Save Game", "Settings", "Main Menu"]
        self.selected_option = 0

    def render(self, screen):
        # First render the game state in the background
        self.game.states[GameStates.PLAYING].render(screen)
        
        # Draw pause overlay
        s = pygame.Surface((800, 600))
        s.set_alpha(128)
        s.fill((0, 0, 0))
        screen.blit(s, (0, 0))
        
        # Title
        title_font = pygame.font.Font(None, 74)
        title_text = title_font.render("PAUSED", True, (255, 255, 255))
        screen.blit(title_text, (400 - title_text.get_width() // 2, 200))
        
        # Menu options
        option_font = pygame.font.Font(None, 48)
        y_offset = 300
        for i, option in enumerate(self.pause_options):
            color = (255, 255, 0) if i == self.selected_option else (255, 255, 255)
            option_text = option_font.render(option, True, color)
            option_rect = option_text.get_rect(center=(400, y_offset))
            screen.blit(option_text, option_rect)
            y_offset += 50
        
        # Instructions
        instruction_font = pygame.font.Font(None, 24)
        instructions = instruction_font.render("Use UP/DOWN to navigate, ENTER to select, ESC to resume", True, (150, 150, 150))
        instruction_rect = instructions.get_rect(center=(400, 550))
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