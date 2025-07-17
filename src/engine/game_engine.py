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
        
        # Load settings and apply display configuration
        from src.settings import game_settings
        self.settings = game_settings
        
        # Display settings
        self.screen = self.settings.apply_display_settings(None)
        self.WINDOW_SIZE = self.screen.get_size()
        pygame.display.set_caption('Space Trading Simulator')
        
        # Game timing
        self.clock = pygame.time.Clock()
        self.FPS = 60
        self.delta_time = 0
                
        # Initialize starfield first
        self.starfield = StarField(100, self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])
        
        # Create universe before creating ship
        self.universe = Universe(seed=None)  # None will generate a random seed
        self.universe.generate_universe()
        self.camera = Camera(self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])
        
        # Store the generated seed for display/saving
        self.world_seed = self.universe.world_seed
        
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
        self.play_time = 0.0  # Total play time in seconds
        
        # Auto-save settings
        self.auto_save_interval = 300.0  # Auto-save every 5 minutes
        self.last_auto_save = 0.0
        
        # Resource management
        self.fonts: Dict[str, pygame.font.Font] = {}
        self.images: Dict[str, pygame.Surface] = {}
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        
        # Initialize resources
        self._init_resources()

        # Initialize mission system
        from src.missions.mission_manager import mission_manager
        self.mission_manager = mission_manager
        
        # Initialize missions for new game
        self.mission_manager.initialize_missions(self)

        # Initialize states
        from src.states.game_state import MenuState, PlayingState, PausedState, SettingsState, TradingState, UpgradeState, SaveGameState, LoadGameState, MissionBoardState
        self.states = {
            GameStates.MAIN_MENU: MenuState(self),
            GameStates.PLAYING: PlayingState(self),
            GameStates.PAUSED: PausedState(self),
            GameStates.SETTINGS: SettingsState(self),
            GameStates.TRADING: None,  # Will be created dynamically with station parameter
            GameStates.UPGRADES: None,  # Will be created dynamically with station parameter
            GameStates.MISSIONS: None,  # Will be created dynamically with station parameter
            GameStates.SAVE_GAME: None,  # Will be created dynamically
            GameStates.LOAD_GAME: LoadGameState(self)
        }
        
        logger.info("GameEngine initialization complete")



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
                if event.key == K_F11:  # F11 to toggle fullscreen
                    self.toggle_fullscreen()
                elif event.key == K_F12:  # F12 to toggle FPS display
                    self.settings.show_fps = not self.settings.show_fps
                elif event.key == K_F4:  # F4 to toggle dev view
                    self.settings.dev_view_enabled = not self.settings.dev_view_enabled
                    self.settings.save()
                    logger.info(f"Dev view: {self.settings.dev_view_enabled}")

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
        
        # Update play time when playing
        if self.current_state == GameStates.PLAYING:
            self.play_time += self.delta_time
            self._check_auto_save()
        
        # Update mission system
        self.mission_manager.update(self)
        
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

    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        self.settings.toggle_fullscreen()
        self.screen = self.settings.apply_display_settings(self.screen)
        self.WINDOW_SIZE = self.screen.get_size()
        
        # Recreate starfield with new dimensions
        self.starfield = StarField(100, self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])
        
        # Update camera with new window size
        self.camera = Camera(self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])
        
        # Update minimap with new window size
        self.minimap = Minimap(self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])
        
        # Update HUD and large map if playing state exists
        if (self.current_state == GameStates.PLAYING and 
            hasattr(self.states[GameStates.PLAYING], 'enhanced_hud')):
            self.states[GameStates.PLAYING].enhanced_hud.resize(self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])
            if hasattr(self.states[GameStates.PLAYING], 'large_map'):
                from ..ui.large_map import LargeMap
                self.states[GameStates.PLAYING].large_map = LargeMap(self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])
        
        logger.info(f"Display mode changed to {self.settings.display_mode.value} ({self.WINDOW_SIZE[0]}x{self.WINDOW_SIZE[1]})")

    def _check_auto_save(self):
        """Check if auto-save should be triggered."""
        if self.play_time - self.last_auto_save >= self.auto_save_interval:
            self._auto_save()
            self.last_auto_save = self.play_time
    
    def _auto_save(self):
        """Perform an auto-save."""
        try:
            from src.save_system import save_system
            success = save_system.save_game(self, "autosave")
            if success:
                logger.info("Auto-save completed successfully")
            else:
                logger.warning("Auto-save failed")
        except Exception as e:
            logger.error(f"Auto-save error: {e}")

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
        elif new_state == GameStates.MISSIONS:
            # Create mission board state with station parameter
            from src.states.game_state import MissionBoardState
            self.states[GameStates.MISSIONS] = MissionBoardState(self, station)
        elif new_state == GameStates.SAVE_GAME:
            # Create save state
            from src.states.game_state import SaveGameState
            self.states[GameStates.SAVE_GAME] = SaveGameState(self)
        elif new_state == GameStates.LOAD_GAME:
            # Refresh load state
            from src.states.game_state import LoadGameState
            self.states[GameStates.LOAD_GAME] = LoadGameState(self)
        elif new_state == GameStates.PLAYING:
            # Resume game
            pass
    
        self.current_state = new_state
    
    def create_new_universe(self, seed=None):
        """Create a new universe with the specified seed"""
        logger.info(f"Creating new universe with seed: {seed}")
        
        # Create new universe
        self.universe = Universe(seed=seed)
        self.universe.generate_universe()
        self.world_seed = self.universe.world_seed
        
        # Reset ship position to first station
        if self.universe.stations:
            first_station = self.universe.stations[0]
            self.ship.position.x = first_station.position.x + 100
            self.ship.position.y = first_station.position.y
        else:
            self.ship.position.x = 400
            self.ship.position.y = 300
        
        # Reset ship velocity
        self.ship.velocity.x = 0
        self.ship.velocity.y = 0
        
        # Reset mission system for new universe
        self.mission_manager.available_missions.clear()
        self.mission_manager.active_missions.clear()
        self.mission_manager.completed_missions.clear()
        self.mission_manager.failed_missions.clear()
        self.mission_manager.last_generation_time = 0
        
        # Initialize missions for new universe
        self.mission_manager.initialize_missions(self)
        
        logger.info(f"New universe created with seed: {self.world_seed}")

class GameError(Exception):
    """Base class for game-related exceptions"""
    pass

class ResourceLoadError(GameError):
    """Raised when a resource fails to load"""
    pass