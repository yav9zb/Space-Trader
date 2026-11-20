"""A hint used to load its font and re-render its text on every frame it was
on screen, which is the first thing a new player sees."""

import pygame

import src.ui.onboarding_hints as hints


def test_hint_text_is_rendered_once_not_every_frame():
    first = hints._line_surfaces(["Thrust to fly", "Fire to shoot"])
    again = hints._line_surfaces(["Thrust to fly", "Fire to shoot"])
    assert [id(s) for s in first] == [id(s) for s in again]
    assert hints._line_surfaces(["Something else"])[0] is not first[0]


def test_changed_text_is_rendered_again():
    # Key names can change while a hint is queued, so the text is the cache key
    a = hints._line_surfaces(["Press W"])[0]
    b = hints._line_surfaces(["Press UP"])[0]
    assert a is not b and a.get_width() != b.get_width()


def test_a_hint_still_draws_into_the_screen():
    screen = pygame.Surface((800, 600))
    manager = hints.OnboardingHints()
    manager.active_hint = next(iter(hints.HINTS))
    manager.timer = 2.0
    before = pygame.image.tostring(screen, "RGB")
    manager.render(screen)
    assert pygame.image.tostring(screen, "RGB") != before
