"""The trade hub: a base with a working hub buys its own goods for credits.

The hub pays a share of a commodity's standard price, less than a station would,
because it saves the haul. Every unit sold pushes that good's price down a little
and the drop heals with time (see PlayerBase.update), so a flood of one good fetches
less than a steady trickle.
"""

from typing import Tuple

from ..trading.commodity import commodity_registry

HUB_RATE = 0.7              # the share of the standard price the hub pays
IMPACT_PER_UNIT = 0.01      # price drop per unit sold
MAX_DROP = 0.5              # the price never falls below half the hub's rate


def is_open(base) -> bool:
    return bool(base.working_hubs())


def _base_price(commodity_id: str):
    try:
        return commodity_registry.get_commodity(commodity_id).base_price
    except KeyError:
        return None


def quote(base, commodity_id: str) -> int:
    """What the hub pays for one unit now (0 if it cannot buy it)."""
    price = _base_price(commodity_id)
    if price is None or not is_open(base):
        return 0
    drop = min(MAX_DROP, base.hub_saturation.get(commodity_id, 0.0))
    return max(1, int(price * HUB_RATE * (1.0 - drop)))


def sell(base, wallet, commodity_id: str, amount: int) -> Tuple[int, int]:
    """Sell up to `amount` of the base's goods. Each unit is priced as it goes, so the drop
    applies within a sale. Returns (units sold, credits paid), and puts the credits in the wallet."""
    sold, paid = 0, 0
    available = base.get_resource_amount(commodity_id)
    while sold < min(int(amount), available):
        price = quote(base, commodity_id)
        if price <= 0:
            break
        sold += 1
        paid += price
        base.hub_saturation[commodity_id] = min(MAX_DROP, base.hub_saturation.get(commodity_id, 0.0) + IMPACT_PER_UNIT)
    if sold:
        base.remove_resource(commodity_id, sold)
        wallet.credits += paid
    return sold, paid
