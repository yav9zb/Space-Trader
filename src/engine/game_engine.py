import os
import pygame
import logging
from pygame.locals import *
from typing import Dict
from src.camera import Camera
from src.universe import Universe
from src.docking.docking_manager import DockingManager
from src.settings import DisplayMode
from src.combat.combat_manager import combat_manager
from src.paths import get_user_data_path, get_resource_path

from ..states.game_state import GameStates
from ..entities.ship import Ship
from ..entities.station import Station
from ..ui.minimap import Minimap
from ..entities.starfield import StarField


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=get_user_data_path('game.log')
)
logger = logging.getLogger(__name__)

# Menu screens are laid out with ui/menu_kit.py: they measure themselves from the
# window and draw at its real pixels (a Retina display's physical pixels when
# available), so they need no scaling. Flight is drawn the same way; the pause
# menu is a menu drawn over the flight view.
NATIVE_STATES = frozenset({
    GameStates.MAIN_MENU, GameStates.GAME_OVER, GameStates.SAVE_GAME, GameStates.LOAD_GAME,
    GameStates.TRADING, GameStates.UPGRADES, GameStates.SETTINGS, GameStates.MISSIONS,
    GameStates.DIALOGUE, GameStates.LOGBOOK, GameStates.VICTORY, GameStates.BASE_CONSTRUCTION,
})


FADE_SECONDS = 0.22
# Switching between flight and its pause menu should feel instant
NO_FADE = {frozenset({GameStates.PLAYING, GameStates.PAUSED})}


class GameEngine:

    def __init__(self):
        """Initialize the game engine with basic settings and states"""
        logger.info("Initializing GameEngine")
        
        # Initialize Pygame
        pygame.init()

        # The game's font (Exo 2); must come before any screen creates a font
        from src.ui import fonts
        fonts.install()

        # Initialize Steamworks if running under Steam - safe no-op otherwise
        from src.steam.steam_manager import steam_manager
        self.steam_manager = steam_manager

        # Load settings and apply display configuration
        from src.settings import game_settings
        self.settings = game_settings
        
        # Display settings
        self.screen = self.settings.apply_display_settings(None)
        self.WINDOW_SIZE = self.screen.get_size()
        pygame.display.set_caption('Space Trading Simulator')

        try:
            icon_path = get_resource_path(os.path.join('assets', 'icon', 'icon_64.png'))
            icon = pygame.image.load(icon_path)
            pygame.display.set_icon(icon)
            if self.presenter is not None and hasattr(self.presenter.window, "set_icon"):
                self.presenter.window.set_icon(icon)        # the high-density window has its own
        except (pygame.error, FileNotFoundError) as e:
            logger.warning(f"Failed to load window icon: {e}")
        
        # Game timing
        self.clock = pygame.time.Clock()
        self.FPS = 60
        self.delta_time = 0
                
        # Initialize starfield first
        from src import display as _display
        self.starfield = StarField(_display.star_count(self.WINDOW_SIZE), self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])
        
        # Create universe before creating ship
        self.universe = Universe(seed=None)  # None will generate a random seed
        self.universe.generate_universe()
        self.camera = Camera(self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])
        
        # Store the generated seed for display/saving
        self.world_seed = self.universe.world_seed

        from src.economy_events import economy_events
        economy_events.world_seed = self.world_seed
        economy_events.reset()
        
        # Initialize docking system
        self.docking_manager = DockingManager()
        self.docking_manager.refusal_check = self._docking_refusal
        self.docking_manager.inspection_hook = self._on_docked
        self.docking_manager.apply_settings(self.settings)

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

        from src.story.story_state import story_state
        self.story_state = story_state
        self.pending_dialogue = None
        self.fade_remaining = 0.0
        
        # Initialize missions for new game
        self.mission_manager.initialize_missions(self)

        # Initialize states
        from src.states.game_state import MenuState, PlayingState, PausedState, SettingsState, TradingState, UpgradeState, SaveGameState, LoadGameState, MissionBoardState, GameOverState
        from src.states.base_construction_state import BaseConstructionState
        self.states = {
            GameStates.MAIN_MENU: MenuState(self),
            GameStates.PLAYING: PlayingState(self),
            GameStates.PAUSED: PausedState(self),
            GameStates.SETTINGS: SettingsState(self),
            GameStates.TRADING: None,  # Will be created dynamically with station parameter
            GameStates.UPGRADES: None,  # Will be created dynamically with station parameter
            GameStates.MISSIONS: None,  # Will be created dynamically with station parameter
            GameStates.BASE_CONSTRUCTION: None,  # Will be created dynamically
            GameStates.DIALOGUE: None,  # Will be created dynamically with a start node
            GameStates.LOGBOOK: None,  # Created fresh each time it is opened
            GameStates.VICTORY: None,  # Created when the campaign is completed
            GameStates.SAVE_GAME: None,  # Will be created dynamically
            GameStates.LOAD_GAME: LoadGameState(self),
            GameStates.GAME_OVER: GameOverState(self)
        }

        from src.story.director import ensure_npcs_placed
        ensure_npcs_placed(self)
        
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
            elif event.type in (pygame.VIDEORESIZE, pygame.WINDOWSIZECHANGED, pygame.WINDOWRESIZED):
                # The window changed size (dragged, zoomed, or macOS fullscreen).
                # pygame has already resized the surface; just re-lay-out.
                self._on_window_resized()
            
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
        self.fade_remaining = max(0.0, getattr(self, "fade_remaining", 0.0) - self.delta_time)
        
        # Update play time when playing
        if self.current_state == GameStates.PLAYING:
            self.play_time += self.delta_time
            self._check_auto_save()
        
        # Update mission system
        self.mission_manager.update(self)

        if self.current_state != GameStates.MAIN_MENU:
            from src.achievements import achievements
            achievements.tick(self.delta_time, self)
        
        # Update combat system
        combat_manager.update(self.delta_time, self)
        
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
        if self.current_state in NATIVE_STATES:
            presenter = self.presenter
            if presenter is not None:
                self.screen.fill((0, 0, 0))
                presenter.queue(lambda pixels, ratio: current_state.render(pixels))
            else:
                current_state.render(self.screen)
        else:
            current_state.render(self.screen)

        self._draw_fade()
        self._present()



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

        self.steam_manager.shutdown()
        pygame.quit()

    def _docking_refusal(self, station):
        """Why this station won't let the player dock, if their standing with
        its faction has fallen far enough."""
        from src.factions import get_station_faction, docking_refusal
        faction = get_station_faction(station, self.world_seed)
        return docking_refusal(faction, self.mission_manager.faction_standing.get(faction, 0))

    def _on_docked(self, station):
        """Everything that happens when docking completes."""
        self._inspect_cargo(station)
        from src.story.outpost import collect
        collect(self, station)

    def _inspect_cargo(self, station):
        """Guild inspection on docking, if the player carries contraband."""
        from src.smuggling import inspect
        from src.ui.notifications import notifications
        result = inspect(self.ship, station, self)
        if result:
            notifications.push(result.message(), duration=7.0, color=(255, 120, 120))

    def start_dialogue(self, start_id: str) -> None:
        """Open a conversation at the given dialogue node."""
        self.pending_dialogue = start_id
        self.change_state(GameStates.DIALOGUE)

    def start_victory(self) -> None:
        """The campaign is complete: remember it and show the ending."""
        from src.legacy import legacy
        from src.story.endings import build_ending

        self.story_state.record_event("campaign_completed")
        legacy.record_completion(build_ending(self.story_state.flags).title)

        from src.achievements import achievements
        achievements.check(self)
        self.change_state(GameStates.VICTORY)

    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        self.settings.toggle_fullscreen()
        self._update_display()
    
    @property
    def presenter(self):
        """The high-density presenter, or None on the standard display path."""
        from .. import hidpi
        return hidpi.get_presenter()

    def _present(self):
        """Show the finished frame."""
        presenter = self.presenter
        if presenter is not None:
            presenter.present()
        else:
            pygame.display.flip()

    def _draw_fade(self):
        """Fade in from black right after switching screens."""
        remaining = getattr(self, "fade_remaining", 0.0)
        if remaining <= 0:
            return
        presenter = self.presenter
        if presenter is not None:
            # the veil covers the upscaled frame and every sharp layer
            presenter.veil_alpha = max(presenter.veil_alpha, int(255 * min(1.0, remaining / FADE_SECONDS)))
            return
        size = self.screen.get_size()
        if getattr(self, "_fade_surface", None) is None or self._fade_surface.get_size() != size:
            self._fade_surface = pygame.Surface(size)
            self._fade_surface.fill((0, 0, 0))
        self._fade_surface.set_alpha(int(255 * min(1.0, remaining / FADE_SECONDS)))
        self.screen.blit(self._fade_surface, (0, 0))

    def _on_window_resized(self):
        """React to the window having a new size without re-creating it
        (re-creating on every resize event flickers and fights macOS's own
        fullscreen). Remembers the size for next time in windowed mode."""
        presenter = self.presenter
        surface = presenter.sync() if presenter is not None else pygame.display.get_surface()
        if surface is None or surface.get_size() == self.WINDOW_SIZE:
            return
        self.screen = surface
        if self.settings.display_mode == DisplayMode.WINDOWED:
            self.settings.window_width, self.settings.window_height = surface.get_size()
        self._relayout()

    def _update_display(self):
        """Apply the display settings (creating or resizing the window) and re-lay-out."""
        self.screen = self.settings.apply_display_settings(self.screen)
        self._relayout()

    def _relayout(self):
        """Rebuild everything that depends on the window size."""
        from .. import display
        old_size = self.WINDOW_SIZE
        self.WINDOW_SIZE = self.screen.get_size()
        logger.info(f"Display updated: {old_size[0]}x{old_size[1]} -> {self.WINDOW_SIZE[0]}x{self.WINDOW_SIZE[1]}")

        # Recreate starfield with new dimensions (more stars on bigger windows)
        self.starfield = StarField(display.star_count(self.WINDOW_SIZE), self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])

        # Update camera with new window size
        self.camera = Camera(self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])

        # Update minimap with new window size
        self.minimap.resize(self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])

        # Update all state UI components
        for state in self.states.values():
            if hasattr(state, 'enhanced_hud'):
                state.enhanced_hud.resize(self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])
            if hasattr(state, 'large_map'):
                from ..ui.large_map import LargeMap
                state.large_map = LargeMap(self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])

        logger.info(f"Display mode: {self.settings.display_mode.value} ({self.WINDOW_SIZE[0]}x{self.WINDOW_SIZE[1]})")

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
        if new_state != self.current_state and frozenset({self.current_state, new_state}) not in NO_FADE:
            self.fade_remaining = FADE_SECONDS
    
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
        elif new_state == GameStates.SETTINGS:
            # Create settings state with previous state tracking
            from src.states.game_state import SettingsState
            self.states[GameStates.SETTINGS] = SettingsState(self, self.current_state)
        elif new_state == GameStates.DIALOGUE:
            # Create a dialogue screen for the node set by start_dialogue()
            from src.states.dialogue_state import DialogueState
            self.states[GameStates.DIALOGUE] = DialogueState(self, self.pending_dialogue)
        elif new_state == GameStates.VICTORY:
            from src.states.victory_state import VictoryState
            self.states[GameStates.VICTORY] = VictoryState(self)
        elif new_state == GameStates.LOGBOOK:
            from src.states.logbook_state import LogbookState
            self.states[GameStates.LOGBOOK] = LogbookState(self)
        elif new_state == GameStates.BASE_CONSTRUCTION:
            # Create base construction state
            from src.states.base_construction_state import BaseConstructionState
            self.states[GameStates.BASE_CONSTRUCTION] = BaseConstructionState(self, previous_state=self.current_state)
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

        from src.economy_events import economy_events
        economy_events.world_seed = self.world_seed
        economy_events.reset()
        
        self.play_time = 0.0
        self.last_auto_save = 0.0

        # Nothing from the old universe may follow the player into the new one
        from src.combat.combat_manager import combat_manager
        combat_manager.clear_all()
        from src.base_building.base_manager import base_manager
        base_manager.reset()

        # A new game starts with a new ship. It is re-initialised in place so
        # everything already holding a reference to it stays valid.
        self.ship.__init__(self.ship.position.x, self.ship.position.y)

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
        self.mission_manager.reputation = 0
        for faction in self.mission_manager.faction_standing:
            self.mission_manager.faction_standing[faction] = 0
        self.story_state.reset()

        from src.legacy import legacy, PERKS
        from src.ui.notifications import notifications
        perk = legacy.apply_pending(self)
        if perk:
            notifications.push(f"Legacy perk applied: {PERKS[perk][0]}", duration=8.0,
                               color=(255, 215, 120))

        from src.story.director import ensure_npcs_placed
        ensure_npcs_placed(self)
        
        # Initialize missions for new universe
        self.mission_manager.initialize_missions(self)
        
        logger.info(f"New universe created with seed: {self.world_seed}")

class GameError(Exception):
    """Base class for game-related exceptions"""
    pass

class ResourceLoadError(GameError):
    """Raised when a resource fails to load"""
    pass