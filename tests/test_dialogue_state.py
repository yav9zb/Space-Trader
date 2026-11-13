import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from types import SimpleNamespace

import pygame
import pytest

from src.states.game_state import GameStates
from src.states.dialogue_state import DialogueState, wrap_text
from src.story.dialogue import Choice, Node
from src.story.story_state import StoryState


@pytest.fixture(autouse=True)
def pygame_ready():
    pygame.display.init()
    pygame.font.init()
    yield


def make_game():
    game = SimpleNamespace(
        mission_manager=SimpleNamespace(
            reputation=0,
            faction_standing={"Trade Guild": 0, "Independent": 0, "Pirate Territory": 0},
        ),
        ship=SimpleNamespace(credits=0),
        story_state=StoryState(),
        changed_to=[],
    )
    game.change_state = lambda state: game.changed_to.append(state)
    return game


NODES = {
    "start": Node("start", "Hale", "Hello there.", choices=[
        Choice("Ask more.", next="more"),
        Choice("Goodbye.", next=None),
    ]),
    "more": Node("more", "Hale", "There is more.", choices=[Choice("Thanks.", next=None)]),
}


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def test_wrap_text_respects_width_and_newlines():
    font = pygame.font.Font(None, 28)
    lines = wrap_text("one two three four five six seven eight nine ten", font, 120)
    assert len(lines) > 1
    assert all(font.size(line)[0] <= 120 for line in lines)
    assert wrap_text("a\n\nb", font, 500) == ["a", "", "b"]


def test_overlong_single_word_does_not_loop_forever():
    font = pygame.font.Font(None, 28)
    assert wrap_text("x" * 200, font, 50) == ["x" * 200]


def test_selection_wraps_and_enter_advances():
    game = make_game()
    state = DialogueState(game, "start", nodes=NODES)
    state.handle_input(key(pygame.K_UP))          # wraps to the last choice
    assert state.selected == 1
    state.handle_input(key(pygame.K_DOWN))        # wraps back
    assert state.selected == 0
    state.handle_input(key(pygame.K_RETURN))
    assert state.session.current.id == "more"
    assert game.changed_to == []


def test_number_keys_choose_directly_and_ending_returns_to_play():
    game = make_game()
    state = DialogueState(game, "start", nodes=NODES)
    state.handle_input(key(pygame.K_2))           # "Goodbye." ends it
    assert game.changed_to == [GameStates.PLAYING]


def test_escape_leaves_at_any_time():
    game = make_game()
    state = DialogueState(game, "start", nodes=NODES)
    state.handle_input(key(pygame.K_ESCAPE))
    assert game.changed_to == [GameStates.PLAYING]


def test_render_draws_without_error_and_records_clickable_choices():
    game = make_game()
    state = DialogueState(game, "start", nodes=NODES)
    screen = pygame.display.set_mode((974, 668))
    state.render(screen)
    assert len(state.choice_rects) == 2


def test_long_text_and_many_choices_stay_within_the_panel():
    long_text = " ".join(["word"] * 400)
    nodes = {"start": Node("start", "Hale", long_text, choices=[
        Choice(f"Choice number {i} with some extra words to force wrapping " * 2, next=None)
        for i in range(12)
    ])}
    game = make_game()
    state = DialogueState(game, "start", nodes=nodes)
    screen = pygame.display.set_mode((974, 668))
    state.selected = 11
    state.render(screen)
    # The selected (last) choice must be one of the drawn, clickable ones
    assert any(index == 11 for index, _ in state.choice_rects)
    assert all(rect.bottom <= 668 for _, rect in state.choice_rects)
