import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest
from pygame import Vector2

from src.ui import gfx
from src.ui.floating_text import floating_texts, FloatingTexts, LIFETIME


@pytest.fixture(autouse=True)
def pygame_ready():
    pygame.display.init()
    pygame.font.init()
    gfx.clear_caches()
    floating_texts.clear()
    yield
    floating_texts.clear()


def blank(w=300, h=300):
    s = pygame.Surface((w, h))
    s.fill((0, 0, 0))
    return s


def lit(surface, threshold=30, area=None):
    area = area or surface.get_rect()
    return sum(1 for x in range(area.left, area.right) for y in range(area.top, area.bottom)
               if sum(surface.get_at((x, y))[:3]) > threshold)


# --- the player's ship ---------------------------------------------------------------

def test_the_hull_has_wings_and_stays_close_to_the_ships_collision_size():
    from src.entities.ship import Ship

    ship = Ship(150, 150)
    ship.size = 30
    s = blank()
    ship.draw(s, Vector2(0, 0))
    xs = [x for x in range(300) for y in range(300) if sum(s.get_at((x, y))[:3]) > 250 and 100 < y < 220]
    assert max(xs) - min(xs) > ship.size * 1.4                               # wings spread wider than the fuselage
    far = lit(s, 40, pygame.Rect(0, 0, 300, 300)) - lit(s, 40, pygame.Rect(150 - 56, 150 - 56, 112, 112))
    assert far < 40                                                          # only faint glow beyond ~1.9x size


def test_the_hull_is_lit_on_the_left_and_shadowed_on_the_right():
    from src.entities.ship import Ship

    ship = Ship(150, 150)
    ship.size = 40
    s = blank()
    ship.draw(s, Vector2(0, 0))
    left = sum(sum(s.get_at((x, y))[:3]) for x in range(115, 148) for y in range(150, 200))
    right = sum(sum(s.get_at((x, y))[:3]) for x in range(153, 186) for y in range(150, 200))
    assert left > right * 1.05


def test_the_wings_are_filled_and_the_left_wing_is_lit_more_than_the_right():
    from src.entities.ship import Ship

    ship = Ship(150, 150)
    ship.size = 40
    s = blank()
    ship.draw(s, Vector2(0, 0))
    # wing boxes, either side of the fuselage, below the middle of the hull
    left_box = pygame.Rect(150 - 37, 150 + 22, 12, 14)                       # outboard of the engine pods
    right_box = pygame.Rect(150 + 25, 150 + 22, 12, 14)
    brightness = lambda box: sum(sum(s.get_at((x, y))[:3]) for x in range(box.left, box.right)
                                 for y in range(box.top, box.bottom))
    assert lit(s, 120, left_box) > 25 and lit(s, 120, right_box) > 15       # solid, not just an outline
    assert brightness(left_box) > brightness(right_box) * 1.05


@pytest.mark.parametrize("rotation", [0, 45, 90, 135, 180, 270, 359])
def test_the_ship_draws_at_any_heading_and_thrusting(rotation):
    from src.entities.ship import Ship

    ship = Ship(150, 150)
    ship.rotation, ship.thrusting = rotation, True
    s = blank()
    ship.draw(s, Vector2(0, 0))
    assert lit(s) > 120


# --- cloaking ---------------------------------------------------------------------------

def test_cloak_effects_only_draw_while_cloaked_and_ripples_spread_over_time():
    from src.systems.cloaking_system import CloakingSystem

    system = CloakingSystem()
    off = blank()
    system.draw_cloak_effects(off, Vector2(150, 150), Vector2(0, 0))
    assert lit(off) == 0

    system.is_cloaked = True
    radii = []
    for timer in (0.0, 0.2, 0.4):
        system.shimmer_timer = timer
        s = blank()
        system.draw_cloak_effects(s, Vector2(150, 150), Vector2(0, 0))
        assert lit(s) > 100
        brightest = max(range(5, 100), key=lambda r: sum(s.get_at((150 + r, 150))[:3]))
        radii.append(brightest)
    assert pygame.image.tostring(off, "RGB") != pygame.image.tostring(s, "RGB")
    assert len(set(radii)) > 1                                               # the ripple moves


# --- floating text -------------------------------------------------------------------------

def test_floating_text_rises_holds_then_fades_and_expires():
    texts = FloatingTexts()
    texts.add(Vector2(150, 200), "+150 cr")
    early, late = blank(), blank()
    texts.draw(early, Vector2(0, 0))
    texts.update(LIFETIME * 0.9)
    texts.draw(late, Vector2(0, 0))

    def top_row(surface):
        rows = [y for y in range(300) if any(sum(surface.get_at((x, y))[:3]) > 80 for x in range(100, 200))]
        return min(rows) if rows else None

    assert top_row(early) is not None and top_row(late) is not None
    assert top_row(late) < top_row(early)                                    # it rose
    assert lit(late) < lit(early)                                            # and is fading
    texts.update(LIFETIME)
    assert texts.items == []


def test_floating_text_follows_the_camera_and_is_capped():
    texts = FloatingTexts()
    texts.add(Vector2(1000, 1000), "+5 cr")
    on_screen, off_screen = blank(), blank()
    texts.draw(on_screen, Vector2(900, 900))
    texts.draw(off_screen, Vector2(0, 0))
    assert lit(on_screen) > 0 and lit(off_screen) == 0
    for i in range(100):
        texts.add(Vector2(i, i), "x")
    assert len(texts.items) <= 24


def test_destroying_a_bandit_pops_its_reward_where_it_died():
    from types import SimpleNamespace
    from src.combat.combat_manager import CombatManager
    from src.entities.bandit import BanditShip, BanditType

    manager = CombatManager()
    bandit = BanditShip(Vector2(500, 600), BanditType.FIGHTER)
    ship = SimpleNamespace(credits=0)
    manager._handle_bandit_destroyed(bandit, ship)
    assert ship.credits == bandit.credits_reward
    assert len(floating_texts.items) == 1
    position, text, _, _ = floating_texts.items[0]
    assert text == f"+{bandit.credits_reward} cr" and position == Vector2(500, 600)


def test_clearing_combat_clears_floating_text():
    from src.combat.combat_manager import CombatManager
    floating_texts.add(Vector2(0, 0), "+1 cr")
    CombatManager().clear_all()
    assert floating_texts.items == []


# --- screen fades ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    from src.engine.game_engine import GameEngine

    class Clock:
        def get_time(self): return 16
        def tick(self, *a): return 16
        def get_fps(self): return 60.0

    game = GameEngine()
    game.clock = Clock()
    return game


def test_switching_screens_fades_in_but_flight_and_pause_swap_instantly(engine):
    from src.states.game_state import GameStates
    from src.engine.game_engine import FADE_SECONDS

    engine.change_state(GameStates.MAIN_MENU)
    engine.fade_remaining = 0
    engine.change_state(GameStates.SETTINGS)
    assert engine.fade_remaining == FADE_SECONDS

    engine.create_new_universe(seed=4)
    engine.change_state(GameStates.PLAYING)
    engine.fade_remaining = 0
    engine.change_state(GameStates.PAUSED)
    assert engine.fade_remaining == 0
    engine.change_state(GameStates.PLAYING)
    assert engine.fade_remaining == 0

    engine.change_state(GameStates.PLAYING)                                    # same state again: no fade
    assert engine.fade_remaining == 0


def test_the_fade_starts_dark_and_is_gone_after_its_duration(engine):
    from src.states.game_state import GameStates
    from src.engine.game_engine import FADE_SECONDS

    engine.change_state(GameStates.MAIN_MENU)
    engine.fade_remaining = FADE_SECONDS
    engine.render()
    start = sum(engine.screen.get_at((x, y))[0] + engine.screen.get_at((x, y))[1] + engine.screen.get_at((x, y))[2]
                for x in range(0, engine.screen.get_width(), 9) for y in range(0, engine.screen.get_height(), 9))

    for _ in range(30):
        engine.update()                                                      # 16 ms frames
    assert engine.fade_remaining == 0
    engine.render()
    end = sum(engine.screen.get_at((x, y))[0] + engine.screen.get_at((x, y))[1] + engine.screen.get_at((x, y))[2]
              for x in range(0, engine.screen.get_width(), 9) for y in range(0, engine.screen.get_height(), 9))
    assert start < end * 0.5                                                  # much darker at the start
