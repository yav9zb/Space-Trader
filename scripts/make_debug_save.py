"""Writes a save file positioned at the start of a campaign act, so the later
story content can be tested without playing everything before it.

    ./venv/bin/python scripts/make_debug_save.py --stage act4 --path join

Then start the game and use Load Game. Stages: act1, act2, act3 (just before
the choice), act4, finale (on the way to the Signal). --path only matters from
act4 on, where the Act 3 choice has already been made. The save is written to
the game's normal saves folder as debug_<stage>_<path>.
"""

import argparse
import os
import sys
import tempfile

# Never open a window or touch the real audio device just to write a file
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def make_save(stage: str, path: str = "independent", seed: int = 2024, name: str = None,
              save_dir: str = None) -> str:
    """Create the save and return its name."""
    from src.engine.game_engine import GameEngine
    from src.legacy import legacy
    from src.save_system import SaveSystem
    from src.story.fast_forward import fast_forward

    # A throwaway legacy file, so a real pending New Game+ perk is not used up
    legacy.path = os.path.join(tempfile.mkdtemp(), "legacy.json")
    legacy.loaded = False

    engine = GameEngine()
    engine.create_new_universe(seed=seed)
    fast_forward(engine, stage, path)

    name = name or f"debug_{stage}_{path}"
    if not SaveSystem(save_dir).save_game(engine, name):
        raise RuntimeError("the save could not be written")
    return name


def main():
    from src.story.fast_forward import STAGES, PATHS

    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument("--path", choices=PATHS, default="independent")
    parser.add_argument("--seed", type=int, default=2024, help="world seed (default 2024)")
    parser.add_argument("--name", help="save name (default debug_<stage>_<path>)")
    args = parser.parse_args()

    name = make_save(args.stage, args.path, args.seed, args.name)
    print(f"Wrote save '{name}'. Start the game and choose Load Game.")


if __name__ == "__main__":
    main()
