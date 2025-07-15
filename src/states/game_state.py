import logging
from enum import Enum, auto

import pygame

logger = logging.getLogger(__name__)


class GameStates(Enum):
    MAIN_MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    TRADING = auto()  # Added for market interface
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
        self.menu_options = ["Play", "Exit"]
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
                elif self.selected_option == 1:  # Exit
                    self.game.running = False

class PlayingState(State):
    def __init__(self, game):
        super().__init__(game)

    def update(self, delta_time):
        # Handle ship movement
        self.game.ship.handle_input(delta_time)
        self.game.ship.update(delta_time)

        # Update camera position to follow ship
        self.game.camera.follow(self.game.ship)
        
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
                station.draw(screen, screen_pos)
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
        
        # Draw ship at center
        ship_screen_pos = pygame.Vector2(self.game.WINDOW_SIZE[0]/2, 
                                 self.game.WINDOW_SIZE[1]/2)
        self.game.ship.draw(screen, ship_screen_pos)
        
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