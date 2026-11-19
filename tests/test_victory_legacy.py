import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from types import SimpleNamespace

import pygame
import pytest

from src.legacy import Legacy, PERKS, VETERAN_REPUTATION, FRIENDS_STANDING
from src.states.game_state import GameStates
from src.states.victory_state import VictoryState, ENDING_OPTIONS, stats_lines
from src.story.endings import build_ending, PATHS, SIGNALS, _TITLES
from src.story.story_state import StoryState
from src import legacy as legacy_module


@pytest.fixture(autouse=True)
def pygame_ready():
    pygame.display.init()
    pygame.font.init()
    yield


@pytest.fixture
def tmp_legacy(tmp_path, monkeypatch):
    fresh = Legacy(path=str(tmp_path / "legacy.json"))
    monkeypatch.setattr(legacy_module, "legacy", fresh)
    import src.states.victory_state as victory_module
    monkeypatch.setattr(victory_module, "legacy", fresh)
    return fresh


def make_game(flags=None):
    story = StoryState()
    for name in flags or ():
        story.set_flag(name)
    game = SimpleNamespace(
        story_state=story, play_time=3725.0,
        mission_manager=SimpleNamespace(
            reputation=95, completed_missions=[1, 2, 3],
            faction_standing={"Trade Guild": 0, "Independent": 0, "Pirate Territory": 0}),
        ship=SimpleNamespace(credits=12345),
        changed_to=[], new_universes=0,
    )
    game.story_state.completed_story_missions = ["a", "b"]
    game.change_state = lambda state: game.changed_to.append(state)
    game.create_new_universe = lambda: setattr(game, "new_universes", game.new_universes + 1)
    return game


# --- Endings -----------------------------------------------------------------------

def test_every_path_and_signal_choice_has_its_own_ending():
    seen = set()
    for path in PATHS:
        for signal in SIGNALS:
            flags = {f"path_{path}": True, "signal_open" if signal == "open" else "signal_sealed": True}
            ending = build_ending(flags)
            assert ending.title == _TITLES[(path, signal)]
            assert len(ending.paragraphs) == 3
            seen.add(ending.title)
    assert len(seen) == 6


def test_ending_text_is_ascii_and_reflects_the_choice():
    for path in PATHS:
        for signal in SIGNALS:
            text = " ".join(build_ending({f"path_{path}": True,
                                          f"signal_{signal}": True}).paragraphs)
            assert all(ord(ch) < 128 for ch in text)
    expose = " ".join(build_ending({"path_expose": True, "signal_open": True}).paragraphs)
    join = " ".join(build_ending({"path_join": True, "signal_sealed": True}).paragraphs)
    assert "Hollow Account in front of every station" in expose and "Marrow's seat" in join
    assert "opened the Signal" in expose and "sealed the Signal" in join


def test_a_save_without_choice_flags_still_gets_an_ending():
    assert build_ending({}).title == _TITLES[("independent", "open")]


# --- Legacy perks ----------------------------------------------------------------

def test_a_perk_applies_once_then_is_used_up(tmp_legacy):
    game = make_game()
    tmp_legacy.choose_perk("veteran")
    assert tmp_legacy.apply_pending(game) == "veteran"
    assert game.mission_manager.reputation == 95 + VETERAN_REPUTATION
    assert tmp_legacy.apply_pending(game) is None
    assert game.mission_manager.reputation == 95 + VETERAN_REPUTATION


def test_each_perk_does_what_it_says(tmp_legacy):
    game = make_game()
    game.ship.credits = 1000
    tmp_legacy.choose_perk("old_money")
    tmp_legacy.apply_pending(game)
    assert game.ship.credits == 1200

    tmp_legacy.choose_perk("friends")
    tmp_legacy.apply_pending(game)
    assert set(game.mission_manager.faction_standing.values()) == {FRIENDS_STANDING}


def test_the_perk_survives_restarting_the_game(tmp_legacy):
    tmp_legacy.record_completion("The Open Sky")
    tmp_legacy.choose_perk("friends")

    reloaded = Legacy(path=tmp_legacy.path)
    reloaded.load()
    assert reloaded.pending_perk == "friends"
    assert reloaded.completions == 1 and reloaded.endings == ["The Open Sky"]


def test_a_damaged_or_missing_legacy_file_is_harmless(tmp_path):
    missing = Legacy(path=str(tmp_path / "nope.json"))
    missing.load()
    assert missing.pending_perk is None and missing.completions == 0

    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    damaged = Legacy(path=str(bad))
    damaged.load()
    assert damaged.pending_perk is None

    unknown = tmp_path / "unknown.json"
    unknown.write_text(json.dumps({"pending_perk": "godmode"}))
    odd = Legacy(path=str(unknown))
    odd.load()
    assert odd.pending_perk is None


def test_choosing_an_unknown_perk_is_rejected(tmp_legacy):
    with pytest.raises(ValueError):
        tmp_legacy.choose_perk("godmode")


# --- Victory screen ------------------------------------------------------------------

def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def test_keep_flying_and_main_menu_leave_the_screen(tmp_legacy):
    game = make_game(["path_expose", "signal_open"])
    state = VictoryState(game)
    state.handle_input(key(pygame.K_RETURN))
    assert game.changed_to == [GameStates.PLAYING]

    state = VictoryState(game)
    state.selected = ENDING_OPTIONS.index("Main Menu")
    state.handle_input(key(pygame.K_RETURN))
    assert game.changed_to[-1] == GameStates.MAIN_MENU


def test_new_game_plus_picks_a_perk_then_starts_a_new_game(tmp_legacy):
    game = make_game()
    state = VictoryState(game)
    state.selected = ENDING_OPTIONS.index("Begin New Game+")
    state.handle_input(key(pygame.K_RETURN))
    assert state.phase == "perk" and game.new_universes == 0

    state.selected = list(PERKS).index("friends")
    state.handle_input(key(pygame.K_RETURN))
    assert tmp_legacy.pending_perk == "friends"
    assert game.new_universes == 1
    assert game.changed_to == [GameStates.PLAYING]


def test_escape_or_back_returns_from_the_perk_list_without_starting_anything(tmp_legacy):
    game = make_game()
    state = VictoryState(game)
    state.phase = "perk"
    state.handle_input(key(pygame.K_ESCAPE))
    assert state.phase == "ending"

    state.phase, state.selected = "perk", len(PERKS)
    state.handle_input(key(pygame.K_RETURN))
    assert state.phase == "ending" and game.new_universes == 0 and tmp_legacy.pending_perk is None


def test_stats_summarise_the_run():
    lines = stats_lines(make_game())
    assert "Rank: Captain" in lines
    assert "Credits: 12,345" in lines
    assert "Time: 1h 2m" in lines
    assert any("Story missions: 2 of 16" == line for line in lines)


@pytest.mark.parametrize("size", [(1280, 720), (1024, 768), (800, 600)])
def test_the_screen_renders_at_common_sizes(size, tmp_legacy):
    pygame.display.set_mode((1, 1))
    for phase in ("ending", "perk"):
        state = VictoryState(make_game(["path_join", "signal_sealed"]))
        state.phase = phase
        surface = pygame.Surface(size)
        state.render(surface)
        assert state.option_rects and all(r.bottom <= size[1] for r in state.option_rects)


@pytest.mark.parametrize("size", [(1280, 720), (1024, 768), (924, 668)])
def test_every_ending_fits_without_scrolling_on_normal_windows(size, tmp_legacy):
    """The ending should be readable at once, not hidden behind PGDN."""
    pygame.display.set_mode((1, 1))
    for path in PATHS:
        for signal in SIGNALS:
            state = VictoryState(make_game([f"path_{path}", f"signal_{signal}"]))
            state.render(pygame.Surface(size))
            assert not state.text_overflows, (path, signal, size)


def test_a_very_small_window_scrolls_instead_of_cutting_text(tmp_legacy):
    pygame.display.set_mode((1, 1))
    state = VictoryState(make_game(["path_join", "signal_sealed"]))
    state.render(pygame.Surface((640, 480)))
    assert state.text_overflows
    state.handle_input(key(pygame.K_PAGEDOWN))
    assert state.scroll > 0
