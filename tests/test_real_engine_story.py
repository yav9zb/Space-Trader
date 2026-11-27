"""Plays the opening of the campaign through the real GameEngine: real
docking, the real Talk key, the real dialogue screen and number-key choices.
The stub-engine playthrough proves the data; this proves it is wired to the
game the way a player reaches it."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest
from pygame import Vector2

from src.engine.game_engine import GameEngine
from src.input.control_schemes import control_scheme_manager
from src.states.game_state import GameStates
from src.docking.docking_manager import DockingState
from src.story import director


class Clock:
    def get_time(self): return 100
    def tick(self, *a): return 16
    def get_fps(self): return 60.0


@pytest.fixture
def game(tmp_path, monkeypatch):
    from src.legacy import legacy
    monkeypatch.setattr(legacy, "path", str(tmp_path / "legacy.json"))
    monkeypatch.setattr(legacy, "loaded", False)
    engine = GameEngine()
    engine.clock = Clock()
    engine.create_new_universe(seed=31337)
    engine.change_state(GameStates.PLAYING)
    yield engine


def frames(game, count=1, render=True):
    for _ in range(count):
        game.handle_events()
        game.update()
        if render:
            game.render()


def press(game, key):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="", scancode=0))
    frames(game)


def clear_hazards_near(position, radius=3000):
    """Bandits, patrols, asteroids and black holes are random and can knock
    the ship away or shoot it. These tests are about the story wiring, not
    about surviving, so keep the approach quiet."""
    from src.combat.combat_manager import combat_manager
    for group in (combat_manager.active_bandits, combat_manager.active_patrols,
                  combat_manager.active_asteroids, combat_manager.active_black_holes):
        group[:] = [x for x in group if (x.position - position).length() > radius]


def dock_at(game, station):
    """Fly up to a station slowly, the way a player does, and let the real
    docking manager take over. If something nudges the ship away, fly back."""
    assert game.current_state == GameStates.PLAYING
    manager = game.docking_manager
    distance = station.size + game.ship.size + manager.docking_range_buffer - 10
    approach = Vector2(station.position.x - distance, station.position.y)

    # A ship that has just undocked does not auto-dock with that station until it has flown clear
    game.ship.position = Vector2(station.position.x - 1000, station.position.y)
    frames(game, render=False)

    for attempt in range(5):
        clear_hazards_near(station.position)
        game.ship.position = Vector2(approach)
        game.ship.velocity = Vector2(0, 0)
        game.ship.current_hull = game.ship.get_effective_stats().get_effective_hull_points()
        for _ in range(150):
            frames(game, render=False)
            if manager.is_docked():
                return
    raise AssertionError(f"never docked at {station.name}: {manager.get_status_message()!r}")


def undock(game):
    press(game, control_scheme_manager.get_key("undock"))
    for _ in range(600):
        frames(game, render=False)
        if game.docking_manager.docking_state == DockingState.FREE_FLIGHT:
            return
    raise AssertionError("never undocked")


def talk(game, *picks):
    """Press the Talk key and choose by text with the number keys."""
    press(game, control_scheme_manager.get_key("talk"))
    assert game.current_state == GameStates.DIALOGUE, "talking opened nothing"
    for text in picks:
        screen = game.states[GameStates.DIALOGUE]
        offered = [c.text for c in screen.session.visible_choices()]
        assert text in offered, f"'{text}' not offered; got {offered}"
        press(game, pygame.K_1 + offered.index(text))
    return game.current_state


def station(game, name):
    return director.find_station_by_name(name, game.universe)


def test_the_prologue_and_first_contacts_play_through_the_real_game(game):
    story = game.story_state
    hale = station(game, story.npc_stations["hale"])

    # Hale's first conversation, then earning the license
    dock_at(game, hale)
    assert talk(game, "Jessup Vane was your friend?", "What is in the ledger?",
                "I will earn that license.") == GameStates.PLAYING
    assert "prologue_1" in story.active_story_missions
    undock(game)

    game.mission_manager.reputation = 15
    frames(game, 3)
    dock_at(game, hale)
    talk(game, "I have earned my trader's license.", "I will look into it.")
    assert "prologue_2" in story.active_story_missions
    undock(game)

    # The berth: reaching it by real docking is what completes the mission
    berth = story.npc_stations["prologue_2.a"]
    dock_at(game, station(game, berth))
    frames(game, 3)
    assert "prologue_2" in story.completed_story_missions
    assert game.current_state == GameStates.DIALOGUE, "the locker scene should open"
    press(game, pygame.K_1)                                   # Thank you.
    assert game.current_state == GameStates.PLAYING
    undock(game)

    dock_at(game, hale)
    talk(game, "I found Vane's locker.", "I will be careful.")
    undock(game)
    dock_at(game, station(game, story.npc_stations["prologue_3.b"]))
    frames(game, 3)
    assert "prologue_3" in story.completed_story_missions
    press(game, pygame.K_1)                                   # the courier scene
    undock(game)

    dock_at(game, hale)
    talk(game, "I met the courier.", "I will hear them out.")
    assert story.chapter == "act_1"
    undock(game)

    # Act 1: the contacts are now at real stations and can be talked to
    for npc in ("rourke", "voss", "kestrel"):
        assert story.npc_stations.get(npc), f"{npc} not placed"

    voss = station(game, story.npc_stations["voss"])
    dock_at(game, voss)
    talk(game, "What do you want from me?", "I will collect them.", "On my way.")
    assert "act1_2" in story.active_story_missions
    undock(game)

    annex = story.npc_stations["act1_2.a"]
    dock_at(game, station(game, annex))
    frames(game, 3)
    mission = next(m for m in game.mission_manager.active_missions if m.story_id == "act1_2")
    assert mission.stage_index == 1
    assert mission.destination_station_id == voss.name       # the tracker now says: back to Voss
    undock(game)

    dock_at(game, voss)
    talk(game, "I have the manifests.", "I will tell him.")
    frames(game, 3)
    assert "act1_2" in story.completed_story_missions


def test_talking_where_nobody_waits_does_nothing_and_does_not_crash(game):
    spare = game.universe.ensure_station_in_sector(5, 5, None)
    assert spare.name not in game.story_state.npc_stations.values()
    dock_at(game, spare)
    press(game, control_scheme_manager.get_key("talk"))
    assert game.current_state == GameStates.PLAYING
    assert "Nobody here" in game.docking_manager.get_status_message()


def test_docking_at_the_outpost_pays_the_income_through_the_real_game(game):
    from src.story import outpost

    spare = game.universe.ensure_station_in_sector(6, 6, None)
    game.story_state.npc_stations["act3_2.a"] = spare.name
    outpost.claim(game, spare.name)
    game.play_time += 30 * 60                      # half an hour of flying
    before = game.ship.credits

    dock_at(game, spare)

    assert game.ship.credits == before + 30 * outpost.RATE_PER_MINUTE
    assert game.story_state.get_flag(outpost.COLLECTED_AT) >= game.play_time - 1


def differing_pixels(a, b, area):
    return sum(1 for x in range(area.left, area.right) for y in range(area.top, area.bottom)
               if a.get_at((x, y)) != b.get_at((x, y)))


def test_the_real_hud_points_at_the_current_story_objective(game, monkeypatch):
    """The pointer is drawn inside a try/except, so a broken import there would
    fail silently. This renders the game's own frame with and without the
    pointer, with the clock frozen so twinkling stars and flickering glows
    cannot differ, and checks that the pointer is the only change."""
    from src.story.story_missions import start_story_mission
    from src.ui import objective_pointer

    game.story_state.chapter = "act_1"
    director.ensure_npcs_placed(game)
    assert start_story_mission("act1_2", game)
    annex = station(game, game.story_state.npc_stations["act1_2.a"])
    clear_hazards_near(annex.position, 9000)
    game.ship.velocity = Vector2(0, 0)
    frames(game, 2, render=False)                                   # settle, then freeze time
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 5000)

    def still_frame():
        # No hit flash or screen shake left over from other tests' fighting
        game.ship.damage_pulse = 0.0
        game.camera.shake_amount = 0.0
        game.render()
        return game.screen.copy()

    def whole_screen(a, b):
        return differing_pixels(a, b, a.get_rect())

    real_draw = objective_pointer.draw
    game.ship.position = annex.position + Vector2(6000, 0)
    game.ship.velocity = Vector2(0, 0)
    with_pointer = still_frame()
    monkeypatch.setattr(objective_pointer, "draw", lambda *args, **kwargs: None)
    without_pointer = still_frame()
    noise = whole_screen(without_pointer, still_frame())            # stations still turn a hair per draw
    change = whole_screen(with_pointer, without_pointer)
    assert change > 400 and change > noise * 20

    monkeypatch.setattr(objective_pointer, "draw", real_draw)
    game.ship.position = annex.position + Vector2(100, 0)           # arrived: the arrow goes away
    game.ship.velocity = Vector2(0, 0)
    arrived = still_frame()
    monkeypatch.setattr(objective_pointer, "draw", lambda *args, **kwargs: None)
    assert whole_screen(arrived, still_frame()) < 400               # a station turning, not the 1,600-pixel pointer


def test_the_ship_stays_undocked_after_the_undock_key_in_the_real_game(game):
    hale = station(game, game.story_state.npc_stations["hale"])
    dock_at(game, hale)
    undock(game)
    clear_hazards_near(hale.position)
    frames(game, 300, render=False)
    assert game.docking_manager.docking_state != DockingState.DOCKED
    assert not game.docking_manager.is_docked()
