import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

from src.entities.ship import Ship
from src.missions.mission_manager import MissionManager
from src.missions.mission_types import MissionStatus
from src.missions.specific_missions import ExplorationMission, SupplyRunMission


def make_supply_run():
    return SupplyRunMission("Beta", {"food_rations": 2})


def make_exploration():
    return ExplorationMission([(1, 2)])


@pytest.mark.parametrize("make", [make_supply_run, make_exploration])
def test_player_with_enough_reputation_can_accept_a_gated_mission(make):
    """accept() re-ran can_accept() with the default reputation of 0, so a
    mission with min_reputation > 0 could never be accepted, however much
    reputation the player had."""
    manager = MissionManager()
    mission = make()
    manager.available_missions.append(mission)
    manager.reputation = mission.requirements.min_reputation

    success, message = manager.accept_mission(mission.id, Ship(0, 0))
    assert success, message
    assert mission.status == MissionStatus.ACCEPTED
    assert mission in manager.active_missions


@pytest.mark.parametrize("make", [make_supply_run, make_exploration])
def test_player_below_the_requirement_is_still_refused_with_the_reputation_reason(make):
    manager = MissionManager()
    mission = make()
    manager.available_missions.append(mission)
    manager.reputation = mission.requirements.min_reputation - 1

    success, message = manager.accept_mission(mission.id, Ship(0, 0))
    assert not success
    assert "reputation" in message.lower()
    assert mission in manager.available_missions
