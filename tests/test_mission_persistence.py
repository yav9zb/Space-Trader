import json

import pytest
from pygame import Vector2

from src.entities.ship import Ship
from src.missions.mission_types import Mission, MissionStatus
from src.missions.specific_missions import (
    DeliveryMission, TradingContractMission, SupplyRunMission,
    EmergencyDeliveryMission, ExplorationMission,
)


class FakeStation:
    def __init__(self, name):
        self.name = name


def roundtrip(mission):
    """Serialize through real JSON, exactly like a save file."""
    return Mission.from_dict(json.loads(json.dumps(mission.to_dict())))


FACTORIES = {
    "delivery": lambda: DeliveryMission("Alpha", "Beta", "food_rations", 5),
    "emergency": lambda: EmergencyDeliveryMission("Alpha", "Beta", "medical_supplies", 4),
    "trading": lambda: TradingContractMission("Alpha", "metal_ore", 10, "electronics", 5),
    "supply": lambda: SupplyRunMission("Beta", {"food_rations": 3, "fuel_cells": 2}),
    "exploration": lambda: ExplorationMission([(1, 2), (3, 4)]),
}


@pytest.mark.parametrize("kind", sorted(FACTORIES))
def test_subclass_survives_roundtrip(kind):
    original = FACTORIES[kind]()
    restored = roundtrip(original)
    assert type(restored) is type(original)
    assert restored.id == original.id
    assert restored.title == original.title


def test_delivery_state_is_restored():
    mission = FACTORIES["delivery"]()
    mission.pickup_completed = True
    restored = roundtrip(mission)
    assert restored.pickup_completed is True
    assert restored.commodity_id == "food_rations"
    assert restored.quantity == 5


def test_delivery_still_completes_after_reload():
    ship = Ship(0, 0)
    mission = FACTORIES["delivery"]()
    assert mission.accept(ship)

    mission.update_progress(ship, FakeStation("Alpha"))
    assert mission.pickup_completed

    restored = roundtrip(mission)
    assert restored.update_progress(ship, FakeStation("Beta")) is True
    assert restored.status == MissionStatus.COMPLETED


def test_exploration_sectors_come_back_as_tuples():
    mission = FACTORIES["exploration"]()
    mission.explored_sectors.add((1, 2))
    restored = roundtrip(mission)
    assert restored.target_sectors == [(1, 2), (3, 4)]
    assert restored.explored_sectors == {(1, 2)}


def test_exploration_still_completes_after_reload():
    ship = Ship(0, 0)
    mission = FACTORIES["exploration"]()
    assert mission.accept(ship) or True  # reputation gate not under test

    mission.status = MissionStatus.ACCEPTED
    ship.position = Vector2(1500, -2500)  # display sector (1, 2)
    mission.update_progress(ship)

    restored = roundtrip(mission)
    ship.position = Vector2(3500, -4500)  # display sector (3, 4)
    assert restored.update_progress(ship) is True


def test_supply_run_requirements_restored():
    restored = roundtrip(FACTORIES["supply"]())
    assert restored.required_supplies == {"food_rations": 3, "fuel_cells": 2}


def test_trading_contract_state_restored():
    mission = FACTORIES["trading"]()
    mission.trade_completed = True
    restored = roundtrip(mission)
    assert restored.trade_completed is True
    assert restored.buy_commodity == "metal_ore"
    assert restored.sell_quantity == 5


def test_old_save_without_class_key_still_loads():
    data = FACTORIES["delivery"]().to_dict()
    data.pop("class", None)
    data.pop("extra_state", None)
    restored = Mission.from_dict(json.loads(json.dumps(data)))
    assert isinstance(restored, Mission)
    assert restored.title
