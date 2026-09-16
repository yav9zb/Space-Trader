"""Difficulty levels affecting hazard frequency, damage, and mission parameters."""

from enum import Enum
from dataclasses import dataclass


class DifficultyLevel(Enum):
    PEACEFUL = "peaceful"
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXTREME = "extreme"


@dataclass
class DifficultySettings:
    hazard_frequency_multiplier: float = 1.0
    enemy_spawn_multiplier: float = 1.0
    damage_multiplier: float = 1.0
    mission_time_multiplier: float = 1.0
    mission_reward_multiplier: float = 1.0
    repair_cost_multiplier: float = 1.0
    upgrade_cost_multiplier: float = 1.0
    enemy_aggression_multiplier: float = 1.0
    permadeath: bool = False


class DifficultyManager:
    """Holds the active difficulty and its derived gameplay multipliers."""

    def __init__(self):
        self.current_difficulty = DifficultyLevel.NORMAL
        self.difficulty_settings = self._build_settings()
        self.load_from_settings()

    def _build_settings(self):
        return {
            DifficultyLevel.PEACEFUL: DifficultySettings(
                hazard_frequency_multiplier=0.3,
                enemy_spawn_multiplier=0.0,
                damage_multiplier=0.5,
                mission_time_multiplier=1.5,
                mission_reward_multiplier=1.0,
                repair_cost_multiplier=0.8,
                upgrade_cost_multiplier=0.9,
            ),
            DifficultyLevel.EASY: DifficultySettings(
                hazard_frequency_multiplier=0.7,
                enemy_spawn_multiplier=0.6,
                damage_multiplier=0.8,
                mission_time_multiplier=1.3,
                mission_reward_multiplier=1.1,
                repair_cost_multiplier=0.9,
                upgrade_cost_multiplier=0.95,
            ),
            DifficultyLevel.NORMAL: DifficultySettings(),
            DifficultyLevel.HARD: DifficultySettings(
                hazard_frequency_multiplier=1.4,
                enemy_spawn_multiplier=1.5,
                damage_multiplier=1.3,
                mission_time_multiplier=0.8,
                mission_reward_multiplier=1.2,
                repair_cost_multiplier=1.2,
                upgrade_cost_multiplier=1.1,
                enemy_aggression_multiplier=1.3,
            ),
            DifficultyLevel.EXTREME: DifficultySettings(
                hazard_frequency_multiplier=2.0,
                enemy_spawn_multiplier=2.0,
                damage_multiplier=1.8,
                mission_time_multiplier=0.6,
                mission_reward_multiplier=1.5,
                repair_cost_multiplier=1.5,
                upgrade_cost_multiplier=1.2,
                enemy_aggression_multiplier=1.8,
                permadeath=True,
            ),
        }

    def set_difficulty(self, difficulty: DifficultyLevel):
        """Set the current difficulty level and persist the choice."""
        self.current_difficulty = difficulty
        self.save_to_settings()

    def load_from_settings(self):
        """Load the difficulty level from settings."""
        try:
            from ..settings import game_settings
        except ImportError:
            from settings import game_settings

        try:
            self.current_difficulty = DifficultyLevel(game_settings.difficulty)
        except (ValueError, AttributeError):
            self.current_difficulty = DifficultyLevel.NORMAL

    def save_to_settings(self):
        """Save the current difficulty level to settings."""
        try:
            from ..settings import game_settings
        except ImportError:
            from settings import game_settings

        game_settings.difficulty = self.current_difficulty.value
        game_settings.save()

    def get_settings(self) -> DifficultySettings:
        """Get the current difficulty's multipliers."""
        return self.difficulty_settings[self.current_difficulty]

    def apply_damage_multiplier(self, base_damage: float) -> float:
        """Scale damage the player ship takes by the current difficulty."""
        return base_damage * self.get_settings().damage_multiplier

    def apply_mission_reward_multiplier(self, base_reward: int) -> int:
        """Scale a mission's credit reward by the current difficulty."""
        return int(base_reward * self.get_settings().mission_reward_multiplier)

    def apply_mission_time_multiplier(self, base_time: float) -> float:
        """Scale a mission's time limit by the current difficulty."""
        return base_time * self.get_settings().mission_time_multiplier

    def apply_repair_cost_multiplier(self, base_cost: float) -> float:
        """Scale a repair cost by the current difficulty."""
        return base_cost * self.get_settings().repair_cost_multiplier

    def apply_upgrade_cost_multiplier(self, base_cost: int) -> int:
        """Scale an upgrade cost by the current difficulty."""
        return int(base_cost * self.get_settings().upgrade_cost_multiplier)

    def is_permadeath(self) -> bool:
        """Whether ship destruction should end the game instead of respawning."""
        return self.get_settings().permadeath


# Global difficulty manager instance
difficulty_manager = DifficultyManager()
