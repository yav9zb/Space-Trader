"""Moving goods between the ship's hold and a base's storage."""

from typing import Dict

from ..trading.commodity import commodity_registry


def commodity_name(commodity_id: str) -> str:
    try:
        return commodity_registry.get_commodity(commodity_id).name
    except KeyError:
        return commodity_id


def depositable(ship) -> Dict[str, int]:
    """What the ship may put into a base: its cargo, less anything a mission is carrying."""
    hold = ship.cargo_hold
    goods = {}
    for commodity_id, amount in hold.items.items():
        free = amount - hold.get_mission_quantity(commodity_id)
        if free > 0:
            goods[commodity_id] = free
    return goods


def deposit(ship, base, commodity_id: str, amount: int) -> int:
    """Move up to `amount` from the hold into the base. Returns how many moved."""
    wanted = min(int(amount), depositable(ship).get(commodity_id, 0))
    moved = base.add_resource(commodity_id, wanted)
    if moved:
        ship.cargo_hold.remove_cargo(commodity_id, moved)
    return moved


def withdraw(ship, base, commodity_id: str, amount: int) -> int:
    """Move up to `amount` from the base into the hold. Returns how many moved."""
    try:
        volume = max(1, commodity_registry.get_commodity(commodity_id).volume)
    except KeyError:
        return 0
    room = ship.cargo_hold.get_available_capacity() // volume
    wanted = min(int(amount), base.get_resource_amount(commodity_id), room)
    if wanted <= 0 or not ship.cargo_hold.add_cargo(commodity_id, wanted):
        return 0
    return base.remove_resource(commodity_id, wanted)
