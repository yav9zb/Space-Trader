"""Keep the test suite away from the developer's own data. Several tests run
the real engine, which autosaves every few minutes of play time into the
saves folder and reads and writes the legacy (New Game+ and achievements) file;
without this they overwrite a real autosave and could use up a real perk."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest


@pytest.fixture(autouse=True, scope="session")
def isolated_user_data(tmp_path_factory):
    from pathlib import Path

    from src.legacy import legacy
    from src.save_system import save_system

    root = tmp_path_factory.mktemp("user_data")
    saves = root / "saves"
    saves.mkdir()

    original = (save_system.save_directory, legacy.path, legacy.loaded)
    save_system.save_directory = Path(saves)
    legacy.path = str(root / "legacy.json")
    legacy.loaded = False
    yield root
    save_system.save_directory, legacy.path, legacy.loaded = original


@pytest.fixture(autouse=True, scope="session")
def game_font():
    """Tests run with the game's real font, as the game does, so layout checks
    (text fitting, wrapping) mean what they say."""
    import pygame
    pygame.font.init()
    from src.ui import fonts
    fonts.install()
    yield
