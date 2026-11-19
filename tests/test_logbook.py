import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from types import SimpleNamespace

import pygame
import pytest
from pygame import Vector2

from src.states.game_state import GameStates
from src.states.logbook_state import LogbookState
from src.story import director
from src.story.logbook import build_pages, TABS
from src.story.story_state import StoryState
from src.universe import Universe


@pytest.fixture(autouse=True)
def pygame_ready():
    pygame.display.init()
    pygame.font.init()
    yield


def make_game():
    universe = Universe(seed=77)
    universe.generate_universe()
    game = SimpleNamespace(
        universe=universe,
        world_seed=universe.world_seed,
        story_state=StoryState(),
        mission_manager=SimpleNamespace(
            reputation=0,
            faction_standing={"Trade Guild": 12, "Independent": 0, "Pirate Territory": -30}),
        ship=SimpleNamespace(position=Vector2(0, 0)),
        changed_to=[],
    )
    game.change_state = lambda state: game.changed_to.append(state)
    director.ensure_npcs_placed(game)
    return game


def text_of(lines):
    return "\n".join(text for _, text in lines)


def test_fresh_pages_show_empty_states():
    pages = build_pages(make_game())
    assert set(pages) == set(TABS)
    assert "Prologue" in text_of(pages["Story"])
    assert "Nothing yet" in text_of(pages["Story"])
    assert "have not met anyone" in text_of(pages["Contacts"])


def test_met_contact_and_ledger_entries_appear():
    game = make_game()
    game.story_state.mark_node_seen("hale_intro")
    game.story_state.add_ledger_entry("ledger_cover")
    pages = build_pages(game)
    assert "Dock Master Hale" in text_of(pages["Contacts"])
    assert "Last known:" in text_of(pages["Contacts"])
    assert "The Ledger" in text_of(pages["Story"])


def test_factions_page_shows_signed_standing_and_current_territory():
    text = text_of(build_pages(make_game())["Factions"])
    assert "Trade Guild: +12" in text
    assert "Pirate Territory: -30" in text
    assert "Independent space" in text      # spawn area is always Independent


def test_screen_renders_every_tab_and_scrolling_is_clamped():
    game = make_game()
    state = LogbookState(game)
    screen = pygame.display.set_mode((974, 668))
    for _ in TABS:
        state.render(screen)
        state.handle_input(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    for _ in range(50):
        state.handle_input(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_PAGEDOWN))
    state.render(screen)                    # must not raise or scroll past the end
    assert state.scroll[TABS[state.tab]] < 50 * 8


def test_escape_returns_to_the_pause_menu():
    game = make_game()
    state = LogbookState(game)
    state.handle_input(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert game.changed_to == [GameStates.PAUSED]
