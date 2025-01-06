import pygame
from enum import Enum, auto


class GameStates(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()

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
        # Draw menu
        font = pygame.font.Font(None, 74)
        title = font.render(self.title, True, (255, 255, 255))
        screen.blit(title, (400 - title.get_width() // 2, 100))

        # Draw menu options
        font = pygame.font.Font(None, 36)
        for i, option in enumerate(self.menu_options):
            color = (255, 255, 0) if i == self.selected_option else (255, 255, 255)
            text = font.render(option, True, color)
            screen.blit(text, (400 - text.get_width() // 2, 300 + i * 50))

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
        self.game.ship.handle_input(delta_time)
        self.game.ship.update(delta_time)

    def render(self, screen):
        # Draw all game objects
        for station in self.game.stations:
            station.draw(screen)
        self.game.ship.draw(screen)
        self.game.minimap.draw(screen, self.game.ship, self.game.stations)

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