import logging
from .engine.game_engine import GameEngine

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='game.log'
)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Starting Space Trading Simulator")
        game = GameEngine()
        game.run()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise
    finally:
        logger.info("Game terminated")

if __name__ == '__main__':
    main()