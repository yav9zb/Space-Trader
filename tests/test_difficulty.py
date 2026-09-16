"""Tests for the difficulty level system."""

import pytest
from src.difficulty.difficulty_manager import DifficultyManager, DifficultyLevel


def test_default_difficulty_is_normal():
    manager = DifficultyManager()
    assert manager.current_difficulty == DifficultyLevel.NORMAL


def test_normal_difficulty_has_no_multipliers():
    manager = DifficultyManager()
    settings = manager.get_settings()
    assert settings.hazard_frequency_multiplier == 1.0
    assert settings.enemy_spawn_multiplier == 1.0
    assert settings.damage_multiplier == 1.0
    assert settings.permadeath == False


def test_peaceful_disables_enemy_spawns():
    manager = DifficultyManager()
    manager.set_difficulty(DifficultyLevel.PEACEFUL)
    assert manager.get_settings().enemy_spawn_multiplier == 0.0


def test_extreme_is_permadeath():
    manager = DifficultyManager()
    manager.set_difficulty(DifficultyLevel.EXTREME)
    assert manager.is_permadeath() == True

    manager.set_difficulty(DifficultyLevel.HARD)
    assert manager.is_permadeath() == False


def test_apply_damage_multiplier():
    manager = DifficultyManager()

    manager.set_difficulty(DifficultyLevel.EASY)
    assert manager.apply_damage_multiplier(100) == 80.0

    manager.set_difficulty(DifficultyLevel.HARD)
    assert manager.apply_damage_multiplier(100) == pytest.approx(130.0)


def test_apply_mission_reward_multiplier():
    manager = DifficultyManager()

    manager.set_difficulty(DifficultyLevel.HARD)
    assert manager.apply_mission_reward_multiplier(1000) == 1200

    manager.set_difficulty(DifficultyLevel.NORMAL)
    assert manager.apply_mission_reward_multiplier(1000) == 1000


def test_apply_repair_cost_multiplier():
    manager = DifficultyManager()

    manager.set_difficulty(DifficultyLevel.PEACEFUL)
    assert manager.apply_repair_cost_multiplier(100) == pytest.approx(80.0)


def test_apply_upgrade_cost_multiplier():
    manager = DifficultyManager()

    manager.set_difficulty(DifficultyLevel.EXTREME)
    assert manager.apply_upgrade_cost_multiplier(1000) == 1200


def test_difficulty_persists_to_settings():
    from src.settings import Settings

    manager = DifficultyManager()
    settings = Settings()
    manager.set_difficulty(DifficultyLevel.HARD)

    # set_difficulty saves to the global game_settings singleton
    from src.settings import game_settings
    assert game_settings.difficulty == "hard"

    # Reset to normal so this test doesn't leak state into other tests
    manager.set_difficulty(DifficultyLevel.NORMAL)
