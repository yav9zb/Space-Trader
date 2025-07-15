import logging
from enum import Enum, auto

import pygame

logger = logging.getLogger(__name__)


class GameStates(Enum):
    MAIN_MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    TRADING = auto()  # Added for market interface
    SETTINGS = auto()  # Added for settings menu
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
        self.menu_options = ["Play", "Settings", "Exit"]
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
                if self.selected_option == 0:  # Play
                    self.game.change_state(GameStates.PLAYING)
                elif self.selected_option == 1:  # Settings
                    self.game.change_state(GameStates.SETTINGS)
                elif self.selected_option == 2:  # Exit
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
        # Handle ship movement
        self.game.ship.handle_input(delta_time)
        self.game.ship.update(delta_time)

        # Update camera position to follow ship
        self.game.camera.follow(self.game.ship, delta_time)
        
        # Generate new chunks as ship moves
        self.game.universe.ensure_chunks_around_position(self.game.ship.position)
        
        # Check collisions after movement
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
            can_dock, distance = self.game.ship.check_docking(station)
            if can_dock:
                screen_pos = station.position - camera_offset
                pygame.draw.circle(screen, (0, 255, 0),
                                 (int(screen_pos.x), int(screen_pos.y)),
                                 station.size + 20,
                                 1)
            
                # Optional: Draw distance indicator
                font = pygame.font.Font(None, 24)
                distance_text = font.render(f"Distance: {int(distance)}", True, (0, 255, 0))
                screen.blit(distance_text, 
                           (int(screen_pos.x - distance_text.get_width()/2),
                            int(screen_pos.y - station.size - 30)))

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
        ship_text = font.render(
            f"Ship Pos: ({int(ship_pos.x)}, {int(ship_pos.y)})", 
            True, (255, 255, 255))
        screen.blit(ship_text, (10, y_offset))
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

class PausedState(State):
    def __init__(self, game):
        super().__init__(game)

    def render(self, screen):
        # First render the game state in the background
        self.game.states[GameStates.PLAYING].render(screen)
        
        # Draw pause overlay
        s = pygame.Surface((800, 600))
        s.set_alpha(128)
        s.fill((0, 0, 0))
        screen.blit(s, (0, 0))
        
        font = pygame.font.Font(None, 74)
        text = font.render("PAUSED", True, (255, 255, 255))
        screen.blit(text, (400 - text.get_width() // 2, 250))
        
        font = pygame.font.Font(None, 36)
        text = font.render("Press ESC to resume or Q to quit", True, (255, 255, 255))
        screen.blit(text, (400 - text.get_width() // 2, 350))

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameStates.PLAYING)
            elif event.key == pygame.K_q:
                self.game.change_state(GameStates.MENU)

class TradingState(State):
    def __init__(self, game):
        super().__init__(game)
        
    def render(self, screen):
        # Render trading interface
        pass
        
    def handle_input(self, event):
        pass

class GameOverState(State):
    def __init__(self, game):
        super().__init__(game)
        
    def render(self, screen):
        # Render game over screen
        pass
        
    def handle_input(self, event):
        pass