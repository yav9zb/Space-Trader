"""Sounds made far from the player are quieter, and silent far enough away."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest
from pygame import Vector2

from src.audio import sound_manager as sm


class FakeChannel:
    def __init__(self):
        self.volume = None

    def set_volume(self, volume):
        self.volume = volume


class FakeSound:
    def __init__(self):
        self.channels = []

    def play(self):
        self.channels.append(FakeChannel())
        return self.channels[-1]


@pytest.fixture
def manager():
    m = sm.SoundManager()
    m.enabled = True
    m.sfx = {"boom": FakeSound()}
    m.listener = Vector2(0, 0)
    return m


def test_loudness_falls_from_full_to_nothing_with_distance():
    assert sm.loudness(0) == 1.0 and sm.loudness(sm.HEARD_FULL) == 1.0
    assert sm.loudness(sm.HEARD_FAR) == 0.0 and sm.loudness(sm.HEARD_FAR * 3) == 0.0
    middle = sm.loudness((sm.HEARD_FULL + sm.HEARD_FAR) / 2)
    assert 0.4 < middle < 0.6
    assert sm.loudness(1000) > sm.loudness(2000)


def test_a_near_sound_plays_at_full_volume(manager):
    manager.play("boom", Vector2(100, 0))
    assert len(manager.sfx["boom"].channels) == 1 and manager.sfx["boom"].channels[0].volume is None


def test_a_far_sound_plays_quieter(manager):
    manager.play("boom", Vector2(1600, 0))
    volume = manager.sfx["boom"].channels[0].volume
    assert volume is not None and 0 < volume < 1


def test_a_very_far_sound_is_not_played(manager):
    manager.play("boom", Vector2(sm.HEARD_FAR + 500, 0))
    assert manager.sfx["boom"].channels == []


def test_a_sound_without_a_position_or_without_a_listener_is_always_full(manager):
    manager.play("boom")
    manager.listener = None
    manager.play("boom", Vector2(10 ** 6, 0))
    assert len(manager.sfx["boom"].channels) == 2 and all(c.volume is None for c in manager.sfx["boom"].channels)


def test_a_weapon_passes_where_it_fired_from(monkeypatch):
    from src.combat.weapons import WeaponSystem, create_weapon

    heard = []
    monkeypatch.setattr(sm.sound_manager, "play", lambda name, position=None: heard.append(position))
    system = WeaponSystem()
    system.add_weapon(create_weapon("basic_laser"))
    system.fire_weapons(Vector2(500, 600), Vector2(1, 0), type("O", (), {})(), 100.0)
    assert heard and heard[0] == Vector2(500, 600)


def test_the_game_loop_keeps_the_listener_on_the_ship():
    from src.engine.game_engine import GameEngine
    from src.states.game_state import GameStates

    class Clock:
        def get_time(self): return 16
        def tick(self, *a): return 16
        def get_fps(self): return 60.0

    game = GameEngine()
    game.clock = Clock()
    game.create_new_universe(seed=4)
    game.change_state(GameStates.PLAYING)
    game.fade_remaining = 0
    game.ship.position = Vector2(1234, 567)
    game.states[GameStates.PLAYING].update(0.016)
    assert sm.sound_manager.listener is not None
    assert (sm.sound_manager.listener - game.ship.position).length() < 5
