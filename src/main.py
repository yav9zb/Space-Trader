import pygame
import sys
from pygame.locals import *
from entities.ship import Ship


class GameEngine:
    def __init__(self):
        pygame.init()
        self.WINDOW_SIZE = (800, 600)
        self.screen = pygame.display.set_mode(self.WINDOW_SIZE)
        pygame.display.set_caption('Space Trading Simulator')
        self.clock = pygame.time.Clock()
        self.running = True
        self.ship - Ship(400, 300) # Initialize the ship at the center of the screen

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False

    def update(self):
        # Game logic will go here
        self.ship.handle_input()
        self.ship.update()

    def render(self):
        self.screen.fill((0, 0, 20))  # Dark blue background
        self.ship.draw(self.screen)  # Draw the ship on the screen
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)  # 60 FPS

        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    game = GameEngine()
    game.run()