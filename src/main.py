import pygame
import sys
from pygame.locals import *
from entities.ship import Ship
from entities.station import Station
from entities.commodity import Market
from ui.minimap import Minimap


class GameEngine:
    def __init__(self):
        # Initialize Pygame first
        pygame.init()
        
        # Set up display
        self.WINDOW_SIZE = (800, 600)
        self.screen = pygame.display.set_mode(self.WINDOW_SIZE)
        pygame.display.set_caption('Space Trading Simulator')
        
        # Set up game objects
        self.clock = pygame.time.Clock()
        self.running = True
        self.ship = Ship(400, 300)  # Create ship at center of screen

        # Add stations
        self.stations = [
            Station(200, 200),
            Station(600, 400),
            Station(100, 500)
        ]
        self.minimap = Minimap(self.WINDOW_SIZE[0], self.WINDOW_SIZE[1])

        # Add market
        self.market = Market()

        # Add player inventory
        self.credits = 1000
        self.cargo = {}

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False

    def update(self):
        # Get delta time in seconds
        delta_time = self.clock.get_time() / 1000.0

        self.ship.handle_input(delta_time)
        self.ship.update(delta_time)

    def render(self):
        self.screen.fill((0, 0, 20))  # Dark blue background

        # Draw game objects
        for station in self.stations:
            station.draw(self.screen)

        # Draw ship
        self.ship.draw(self.screen)

        # Draw minimap
        self.minimap.draw(self.screen, self.ship, self.stations)
                
        # Draw UI
        self.draw_ui()
        pygame.display.flip()

    def draw_ui(self):
        # Draw credits
        font = pygame.font.Font(None, 36)
        credits_text = font.render(f'Credits: {self.credits}', True, (255, 255, 255))
        self.screen.blit(credits_text, (10, 10))

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    game = GameEngine()
    game.run()