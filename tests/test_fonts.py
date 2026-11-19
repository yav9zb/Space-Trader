import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from src.ui import fonts


@pytest.fixture(autouse=True)
def pygame_ready():
    pygame.font.init()
    yield


def test_the_bundled_font_and_its_license_are_in_the_repo():
    assert os.path.exists(fonts.font_path())
    assert os.path.getsize(fonts.font_path()) > 100_000
    assert os.path.exists(os.path.join("assets", "licenses", "exo2_OFL.txt"))
    assert "SIL OPEN FONT LICENSE" in open(os.path.join("assets", "licenses", "exo2_OFL.txt")).read().upper()


def test_default_font_requests_get_the_game_font_scaled_and_bold():
    fonts.install()
    font = pygame.font.Font(None, 40)
    reference = _OriginalSized(round(40 * fonts.SIZE_SCALE))
    assert font.get_bold()
    assert font.size("Credits: 12,345") == reference.size("Credits: 12,345")   # Exo at the scaled size
    assert isinstance(font, fonts.ThemedFont)


def _OriginalSized(size):
    ref = fonts._OriginalFont(fonts.font_path(), size)
    ref.set_bold(True)
    return ref


def test_text_widths_stay_close_to_the_builtin_font_so_panels_still_fit():
    """Layouts were drawn around pygame's built-in font; the scale keeps text
    about as wide, so nothing needs re-laying-out."""
    fonts.install()
    samples = ["Credits: 12,345   Hull 100/100", "You have three roads, and I will not pretend",
               "ACTIVE MISSIONS   The Paymaster -> Quarry-882"]
    for size in (20, 24, 28, 36, 48):
        builtin = fonts._OriginalFont(None, size)
        game = pygame.font.Font(None, size)
        for text in samples:
            ratio = game.size(text)[0] / builtin.size(text)[0]
            assert 0.9 < ratio < 1.25, (size, text, ratio)       # the built-in font differs a little between pygame and pygame-ce


def test_fonts_that_name_a_file_are_left_alone():
    fonts.install()
    named = pygame.font.Font(fonts.font_path(), 30)
    assert not named.get_bold()
    assert named.size("Hello")[0] == fonts._OriginalFont(fonts.font_path(), 30).size("Hello")[0]


def test_installing_twice_is_harmless():
    assert fonts.install() is True
    assert fonts.install() is True
    assert pygame.font.Font is fonts.ThemedFont


def test_without_the_font_file_the_game_keeps_pygames_font(monkeypatch):
    fonts.uninstall()
    monkeypatch.setattr(fonts, "font_path", lambda: "/nonexistent/Exo2.ttf")
    try:
        assert fonts.install() is False
        font = pygame.font.Font(None, 30)
        assert font.size("Hello") == fonts._OriginalFont(None, 30).size("Hello")
    finally:
        monkeypatch.undo()
        fonts.install()                       # the rest of the suite runs with the game's font


def test_a_tiny_size_never_collapses_below_a_readable_minimum():
    fonts.install()
    assert pygame.font.Font(None, 4).get_height() >= fonts._OriginalFont(fonts.font_path(), 8).get_height() - 1
