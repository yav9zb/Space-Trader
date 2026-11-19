"""Starting a new game from the main menu must give a fresh ship."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

from src.engine.game_engine import GameEngine


@pytest.fixture(scope="module")
def engine():
    return GameEngine()


@pytest.fixture(autouse=True)
def isolated_legacy(tmp_path, monkeypatch):
    """Never read or consume a developer's real legacy perk."""
    from src.legacy import legacy
    monkeypatch.setattr(legacy, "path", str(tmp_path / "legacy.json"))
    monkeypatch.setattr(legacy, "loaded", False)
    monkeypatch.setattr(legacy, "pending_perk", None)
    monkeypatch.setattr(legacy, "completions", 0)
    monkeypatch.setattr(legacy, "endings", [])
    monkeypatch.setattr(legacy, "achievements", [])


def test_a_new_game_does_not_keep_the_old_ships_wealth_or_upgrades(engine):
    ship = engine.ship
    ship.credits = 250_000
    ship.cargo_hold.add_cargo("food", 5)
    engine.mission_manager.reputation = 90
    held = engine.ship

    engine.create_new_universe()

    assert engine.ship is held                    # states keep their reference
    assert engine.ship.credits == 1000
    assert engine.ship.cargo_hold.items == {}
    assert engine.mission_manager.reputation == 0


def test_a_new_game_clears_ships_left_over_from_the_old_universe(engine):
    from pygame import Vector2
    from src.combat.combat_manager import combat_manager
    from src.entities.bandit import BanditShip, BanditType

    combat_manager.add_bandit(BanditShip(Vector2(50, 50), BanditType.FIGHTER))
    assert combat_manager.active_bandits

    engine.create_new_universe()

    assert combat_manager.active_bandits == []
    assert combat_manager.active_traders == []
    assert combat_manager.active_patrols == []


def test_the_ending_starts_victory_and_the_perk_applies_to_the_next_game(engine):
    from src.legacy import legacy
    from src.states.game_state import GameStates

    engine.create_new_universe()
    engine.story_state.set_flag("path_expose")
    engine.story_state.set_flag("signal_open")
    engine.story_state.set_flag("campaign_complete")

    engine.start_victory()
    assert "signal" in legacy.achievements        # unlocked at once, not on the next tick

    assert engine.current_state == GameStates.VICTORY
    assert engine.story_state.count_events("campaign_completed") == 1
    assert legacy.completions == 1 and legacy.endings == ["The Open Sky"]

    legacy.choose_perk("veteran")
    engine.create_new_universe()
    assert engine.mission_manager.reputation == 15
    assert legacy.pending_perk is None
    engine.change_state(GameStates.PLAYING)
