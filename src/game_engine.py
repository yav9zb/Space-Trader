import random
import pygame
import logging
from enum import Enum
from pygame.locals import *
from typing import Dict, Optional

from src.states.game_state import GameStates

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
        
        # Game state
        self.running = True
        self.current_state = GameStates.MAIN_MENU
        
        # Resource management
        self.fonts: Dict[str, pygame.font.Font] = {}
        self.images: Dict[str, pygame.Surface] = {}
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        
        # Initialize resources
        self._init_resources()
        
        logger.info("GameEngine initialization complete")

    def _init_resources(self):
        """Initialize game resources like fonts, images, and sounds"""
        try:
            # Initialize fonts
            self.fonts['main'] = pygame.font.Font(None, 36)
            self.fonts['small'] = pygame.font.Font(None, 24)
            
            # Here you would load images and sounds
            # self.images['ship'] = pygame.image.load('assets/ship.png')
            # self.sounds['engine'] = pygame.mixer.Sound('assets/engine.wav')
            
            logger.info("Resources initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing resources: {str(e)}")
            raise

    def handle_events(self) -> None:
        """Process all game events"""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
                
            elif event.type == KEYDOWN:
                self._handle_keydown(event.key)
                
            elif event.type == MOUSEBUTTONDOWN:
                self._handle_mousedown(event.pos)

    def _handle_keydown(self, key: int) -> None:
        """Handle keyboard input based on game state"""
        if key == K_ESCAPE:
            if self.current_state == GameStates.PLAYING:
                self.current_state = GameStates.PAUSED
            elif self.current_state == GameStates.PAUSED:
                self.current_state = GameStates.PLAYING
            else:
                self.running = False

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
        
        if self.current_state == GameStates.PLAYING:
            self._update_playing_state()
        elif self.current_state == GameStates.MAIN_MENU:
            self._update_menu_state()
        elif self.current_state == GameStates.PAUSED:
            self._update_paused_state()

    def _update_playing_state(self) -> None:
        """Update game logic during gameplay"""
        # Add gameplay update logic here
        pass

    def _update_menu_state(self) -> None:
        """Update logic for main menu"""
        # Add menu update logic here
        pass

    def _update_paused_state(self) -> None:
        """Update logic for pause state"""
        # Add pause state update logic here
        pass

    def render(self) -> None:
        """Render the game based on current state"""
        # Clear the screen
        self.screen.fill((0, 0, 20))  # Dark blue background
        
        if self.current_state == GameStates.PLAYING:
            self._render_playing_state()
        elif self.current_state == GameStates.MAIN_MENU:
            self._render_menu_state()
        elif self.current_state == GameStates.PAUSED:
            self._render_paused_state()
        
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
        pygame.quit()

    def change_state(self, new_state: GameStates) -> None:
        """Safely change the game state"""
        logger.info(f"Changing game state from {self.current_state} to {new_state}")
        self.current_state = new_state


class StarField:
    def __init__(self, num_stars, screen_width, screen_height):
        self.stars = []
        for _ in range(num_stars):
            x = random.randint(0, screen_width)
            y = random.randint(0, screen_height)
            brightness = random.randint(100, 255)
            self.stars.append([x, y, brightness])
    
    def draw(self, screen):
        for x, y, brightness in self.stars:
            pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), 1)