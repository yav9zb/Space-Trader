import random
import pygame
import logging
from enum import Enum
from pygame.locals import *
from typing import Dict, Optional
from src.camera import Camera
from src.universe import Universe
from src.docking.docking_manager import DockingManager

from ..states.game_state import GameStates
from ..entities.ship import Ship
from ..entities.station import Station
from ..entities.commodity import Market
from ..ui.minimap import Minimap
from ..entities.starfield import StarField
from ..universe import Universe


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='game.log'
)
logger = logging.getLogger(__name__)

class GameEngine:

    def __init__(self):
        """Initialize the game engine with basic settings and states"""
        logger.info("Initializing GameEngine")
        
        # Initialize Pygame
        pygame.init()
        
        # Display settings
        self.WINDOW_SIZE = (800, 600)
        self.screen = pygame.display.set_mode(self.WINDOW_SIZE)
        pygame.display.set_caption('Space Trading Simulator')
        
        # Game timing
        self.clock = pygame.time.Clock()
        self.FPS = 60
        self.delta_time = 0
                
        # Initialize starfield first
        self.starfield = StarField(100, self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])
        
        # Create universe before creating ship
        self.universe = Universe()
        self.universe.generate_universe()
        self.camera = Camera(self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])
        
        # Initialize docking system
        self.docking_manager = DockingManager()

        # Game objects
        self.ship = Ship(400, 300)
        self.stations = [
            Station(200, 200),
            Station(600, 400),
            Station(100, 500)
        ]
        self.minimap = Minimap(self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])
        self.market = Market()
    
        # Place ship at first station
        if self.universe.stations:
            first_station = self.universe.stations[0]
            self.ship = Ship(first_station.position.x + 100,
                        first_station.position.y)
        else:
            self.ship = Ship(400, 300)
        
        # Player data
        self.credits = 1000
        self.cargo = {}
        
        # Game state
        self.running = True
        self.current_state = GameStates.MAIN_MENU
        
        # Resource management
        self.fonts: Dict[str, pygame.font.Font] = {}
        self.images: Dict[str, pygame.Surface] = {}
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        
        # Initialize resources
        self._init_resources()

        # Initialize states
        from src.states.game_state import MenuState, PlayingState, PausedState, SettingsState, TradingState, UpgradeState
        self.states = {
            GameStates.MAIN_MENU: MenuState(self),
            GameStates.PLAYING: PlayingState(self),
            GameStates.PAUSED: PausedState(self),
            GameStates.SETTINGS: SettingsState(self),
            GameStates.TRADING: None,  # Will be created dynamically with station parameter
            GameStates.UPGRADES: None  # Will be created dynamically with station parameter
        }
        
        logger.info("GameEngine initialization complete")

        self.debug_mode = True


    def _init_resources(self):
        """Initialize game resources like fonts, images, and sounds"""
        try:
            # Initialize fonts
            self.fonts['main'] = pygame.font.Font(None, 36)
            if not self.fonts['main']:
                raise ResourceLoadError("Failed to load main font")
            
            self.fonts['small'] = pygame.font.Font(None, 24)
            if not self.fonts['small']:
                raise ResourceLoadError("Failed to load small font")
            
            # Here you would load images and sounds
            # self.images['ship'] = pygame.image.load('assets/ship.png')
            # self.sounds['engine'] = pygame.mixer.Sound('assets/engine.wav')
            
            logger.info("Resources initialized successfully")
        except ResourceLoadError as e:
            logger.error(f"Resource loading error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading resources: {str(e)}")
            raise GameError(f"Failed to initialize resources: {str(e)}")

    def handle_events(self) -> None:
        """Process all game events"""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
                return
            # Let the current state handle the event first
            current_state = self.states[self.current_state]
            current_state.handle_input(event)

            # Handle other keys globally (ESC is handled by individual states)
            if event.type == KEYDOWN and event.key != K_ESCAPE:
                self._handle_keydown(event.key)
                
            if event.type == MOUSEBUTTONDOWN:
                self._handle_mousedown(event.pos)

            # Debug controls
            if event.type == KEYDOWN:
                if event.key == K_F3:  # F3 to toggle debug mode
                    self.debug_mode = not self.debug_mode
                    logger.info(f"Debug mode: {self.debug_mode}")

    def _handle_keydown(self, key: int) -> None:
        """Handle keyboard input based on game state"""
        # Add more key handling based on game state
        if self.current_state == GameStates.PLAYING:
            self._handle_playing_keys(key)

    def _handle_playing_keys(self, key: int) -> None:
        """Handle keyboard input during gameplay"""
        # Add specific gameplay key handling here
        pass

    def _handle_mousedown(self, pos: tuple) -> None:
        """Handle mouse input based on game state"""
        if self.current_state == GameStates.MAIN_MENU:
            self._handle_menu_click(pos)

    def _handle_menu_click(self, pos: tuple) -> None:
        """Handle mouse clicks in the main menu"""
        # Add menu click handling here
        pass

    def update(self) -> None:
        """Update game logic based on current state"""
        self.delta_time = self.clock.get_time() / 1000.0  # Convert to seconds
        
        # Update current state
        current_state = self.states[self.current_state]
        current_state.update(self.delta_time)

        # If we're in playing state, check collisions
        if self.current_state == GameStates.PLAYING:
            self._check_collisions()  # Add this new method call
    
    def _check_collisions(self):
        """Handle all collision checks"""
        # Check ship collision with each station
        for station in self.stations:
            if self.ship.check_collision_detailed(station):
                logger.info("Collision detected with station")

    def _update_playing_state(self):
        """Update game logic during gameplay"""
        # Update ship first
        self.ship.update(self.delta_time)

        # Check collisions with stations
        collision_occurred = False
        for station in self.stations:
            if self.ship.check_collision_detailed(station):
                collision_occurred = True
                logger.info(f"Collision detected with station at {station.position}")
                
                # Check if we should dock (low velocity near station)
                if self.ship.velocity.length() < 50:
                    # Optional: Check if we're in docking range
                    dock_distance = (station.position - self.ship.position).length()
                    if dock_distance < station.size + self.ship.size + 10:
                        logger.info("Docking conditions met")
                        self.change_state(GameStates.TRADING)
                        break

    def _update_menu_state(self) -> None:
        """Update logic for main menu"""
        # Add menu update logic here
        pass

    def _update_paused_state(self) -> None:
        """Update logic for pause state"""
        # Add pause state update logic here
        pass

    def render(self):
        """Render the game based on current state"""
        
        # Get current state and render it
        current_state = self.states[self.current_state]
        current_state.render(self.screen)
        
        pygame.display.flip()

        # Debug rendering
        if self.debug_mode and self.current_state == GameStates.PLAYING:
            self._render_debug()

    def _render_debug(self):
        """Render debug information"""
        # Draw collision circles for stations
        for station in self.stations:
            pygame.draw.circle(self.screen, (0, 255, 0),
                             (int(station.position.x), int(station.position.y)),
                             station.size + self.ship.size,
                             1)  # Draw combined collision radius

    def _render_playing_state(self) -> None:
        """Render the game during gameplay"""
        # Add gameplay rendering here
        pass

    def _render_menu_state(self) -> None:
        """Render the main menu"""
        title = self.fonts['main'].render('Space Trading Simulator', True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.WINDOW_SIZE[0] // 2, 100))
        self.screen.blit(title, title_rect)

    def _render_paused_state(self) -> None:
        """Render the pause screen"""
        # First render the game state
        self._render_playing_state()
        
        # Add pause overlay
        pause_text = self.fonts['main'].render('PAUSED', True, (255, 255, 255))
        pause_rect = pause_text.get_rect(center=(self.WINDOW_SIZE[0] // 2, self.WINDOW_SIZE[1] // 2))
        self.screen.blit(pause_text, pause_rect)

    def run(self) -> None:
        """Main game loop"""
        logger.info("Starting game loop")
        
        try:
            while self.running:
                self.handle_events()
                self.update()
                self.render()
                self.clock.tick(self.FPS)
        
        except Exception as e:
            logger.error(f"Error in game loop: {str(e)}")
            raise
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Clean up resources and quit the game"""
        logger.info("Cleaning up and shutting down")

        # Clean up resources
        for sound in self.sounds.values():
            sound.stop()
        self.sounds.clear()
    
        # Clear other resources
        self.fonts.clear()
        self.images.clear()
    
        # Reset game objects
        self.universe = None
        self.ship = None
        self.camera = None
        
        pygame.quit()

    def change_state(self, new_state: GameStates, station=None) -> None:
        """Safely change the game state"""
        logger.info(f"Changing game state from {self.current_state} to {new_state}")
    
        # Handle cleanup of old state
        if self.current_state == GameStates.TRADING:
            # Save market state
            pass
        elif self.current_state == GameStates.PLAYING:
            # Save game state
            pass
    
        # Handle initialization of new state
        if new_state == GameStates.TRADING:
            # Create trading state with station parameter
            from src.states.game_state import TradingState
            self.states[GameStates.TRADING] = TradingState(self, station)
        elif new_state == GameStates.UPGRADES:
            # Create upgrade state with station parameter
            from src.states.game_state import UpgradeState
            self.states[GameStates.UPGRADES] = UpgradeState(self, station)
        elif new_state == GameStates.PLAYING:
            # Resume game
            pass
    
        self.current_state = new_state

class GameError(Exception):
    """Base class for game-related exceptions"""
    pass

class ResourceLoadError(GameError):
    """Raised when a resource fails to load"""
    pass