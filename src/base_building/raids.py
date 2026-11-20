"""
Raids: pirates come for a base that is worth taking.

Each base that has something built has a countdown to its next raid. When it
runs out:

  - if the player is near, the raiders are real ships: they fly in, the turrets
    and the player fight them, and what they shoot is the base itself;
  - if the player is away, the raid is settled on the spot, by comparing the
    raiders' strength with what the base's working turrets can stand against.

Either way a base that holds loses goods and has modules knocked out, and a
base with enough turrets loses nothing. Knocked-out modules mend by themselves
once the shooting stops.
"""

import math
import random
from typing import Dict, List, Optional, Tuple

from pygame import Vector2

from .base_entity import PlayerBase

RAID_INTERVAL = (600.0, 900.0)      # seconds between raids on one base
LIVE_RANGE = 3000.0                 # the player this close sees the raid happen
ABANDON_RANGE = 6000.0              # the player this far gone: a live raid is settled unseen
SPAWN_DISTANCE = 1600.0             # raiders come in from this far out
WITHDRAW_AFTER = 240.0              # raiders still alive after this long give up
MAX_LEVEL = 8

MAX_THEFT = 0.3                     # the most of any stock a raid takes
THEFT_PER_BREACH = 0.1              # per module knocked out in a live raid
DAMAGE_PER_SHORTFALL = 5.0          # hull damage per point of threat the turrets could not cover

RED = (255, 130, 110)
GREEN = (140, 235, 160)
AMBER = (255, 205, 100)


def _threat_table():
    from ..entities.bandit import BanditType
    return {BanditType.SCOUT: 40, BanditType.FIGHTER: 90, BanditType.HEAVY: 180, BanditType.BOSS: 300}


def raid_level(base: PlayerBase) -> int:
    """How big a raid the base draws: more built, more worth taking."""
    built = sum(1 for m in base.unique_modules() if m.is_constructed and m.module_type.value != "command_center")
    return max(1, min(MAX_LEVEL, 1 + built // 2))


def raid_roster(level: int):
    """The raiders of a raid of this level."""
    from ..entities.bandit import BanditType as B
    rosters = {
        1: [B.SCOUT, B.SCOUT],
        2: [B.SCOUT, B.SCOUT, B.SCOUT],
        3: [B.FIGHTER, B.SCOUT, B.SCOUT],
        4: [B.FIGHTER, B.FIGHTER, B.SCOUT, B.SCOUT],
        5: [B.HEAVY, B.FIGHTER, B.SCOUT, B.SCOUT],
        6: [B.HEAVY, B.FIGHTER, B.FIGHTER, B.SCOUT, B.SCOUT],
        7: [B.HEAVY, B.HEAVY, B.FIGHTER, B.SCOUT, B.SCOUT],
        8: [B.BOSS, B.HEAVY, B.FIGHTER, B.FIGHTER, B.SCOUT],
    }
    return list(rosters[max(1, min(MAX_LEVEL, level))])


def threat_of(bandit_types) -> int:
    table = _threat_table()
    return sum(table[t] for t in bandit_types)


def is_worth_raiding(base: PlayerBase) -> bool:
    """A base with only its command center has nothing to take yet."""
    return any(m.is_constructed and m.module_type.value != "command_center" for m in base.unique_modules())


class LiveRaid:
    def __init__(self, base_id: str, bandits: list, wrecked_before: int):
        self.base_id = base_id
        self.bandits = bandits
        self.wrecked_before = wrecked_before
        self.age = 0.0


class RaidDirector:
    """Counts the raids down, sends them, and settles them."""

    def __init__(self, events: list, rng=None):
        self.events = events                         # (text, color) the game turns into notifications
        self.live: Dict[str, LiveRaid] = {}
        self.rng = rng or random

    def reset(self) -> None:
        self.live.clear()

    def _say(self, text: str, color=AMBER) -> None:
        self.events.append((text, color))

    # Driving it -----------------------------------------------------------------------------------

    def update(self, delta_time: float, bases: Dict[str, PlayerBase], player_position: Vector2, combat) -> None:
        for base_id, base in bases.items():
            raid = self.live.get(base_id)
            if raid is not None:
                self._update_live(raid, base, delta_time, player_position, combat)
                continue
            if not is_worth_raiding(base):
                continue
            if base.raid_timer is None:
                base.raid_timer = self.rng.uniform(*RAID_INTERVAL)
            base.raid_timer -= delta_time
            if base.raid_timer <= 0:
                base.raid_timer = self.rng.uniform(*RAID_INTERVAL)
                self.launch(base_id, base, player_position, combat)
        for base_id in [b for b in self.live if b not in bases]:      # a base that is gone
            self.live.pop(base_id)

    def launch(self, base_id: str, base: PlayerBase, player_position: Vector2, combat) -> None:
        roster = raid_roster(raid_level(base))
        if (Vector2(player_position) - base.position).length() <= LIVE_RANGE:
            self._start_live(base_id, base, roster, combat)
        else:
            self._settle_unseen(base, threat_of(roster))

    # Live raids ------------------------------------------------------------------------------------

    def _start_live(self, base_id: str, base: PlayerBase, roster, combat) -> None:
        from ..entities.bandit import BanditShip, BanditState

        angle = self.rng.uniform(0, 2 * math.pi)
        origin = base.position + Vector2(math.cos(angle), math.sin(angle)) * SPAWN_DISTANCE
        bandits = []
        for index, bandit_type in enumerate(roster):
            spread = Vector2(self.rng.uniform(-150, 150), self.rng.uniform(-150, 150))
            bandit = BanditShip(origin + spread, bandit_type)
            bandit.raid_base = base
            bandit.patrol_center = Vector2(base.position)
            bandit.state = BanditState.HUNTING
            combat.add_bandit(bandit)
            bandits.append(bandit)
        base.under_attack = True
        self.live[base_id] = LiveRaid(base_id, bandits, base.wrecked_count())
        self._say(f"Raiders are attacking {base.name}!", RED)

    def _update_live(self, raid: LiveRaid, base: PlayerBase, delta_time: float,
                     player_position: Vector2, combat) -> None:
        from ..entities.bandit import BanditState

        raid.age += delta_time
        alive = [b for b in raid.bandits if b.state != BanditState.DISABLED and b in combat.active_bandits]
        if not alive:
            self._finish_live(raid, base, "held")
            return
        if (Vector2(player_position) - base.position).length() > ABANDON_RANGE:
            # Out of sight: the rest of the fight is settled on numbers
            for bandit in alive:
                combat.remove_bandit(bandit)
            self._end_live(raid, base)
            self._settle_unseen(base, threat_of(b.bandit_type for b in alive))
            return
        if raid.age >= WITHDRAW_AFTER:
            for bandit in alive:
                combat.remove_bandit(bandit)
            self._finish_live(raid, base, "withdrew")

    def _end_live(self, raid: LiveRaid, base: PlayerBase) -> None:
        base.under_attack = False
        self.live.pop(raid.base_id, None)

    def _finish_live(self, raid: LiveRaid, base: PlayerBase, how: str) -> None:
        knocked_out = max(0, base.wrecked_count() - raid.wrecked_before)
        self._end_live(raid, base)
        if knocked_out == 0:
            self._say(f"{base.name} drove off the raiders.", GREEN)
            return
        stolen = self._steal(base, min(MAX_THEFT, THEFT_PER_BREACH * knocked_out))
        self._say(f"{base.name} was raided: {knocked_out} module(s) knocked out{self._stolen_text(stolen)}.", RED)

    # Settling a raid without the player there -----------------------------------------------------

    def _settle_unseen(self, base: PlayerBase, threat: int) -> None:
        defense = base.defense_rating()
        if defense >= threat:
            self._say(f"{base.name} repelled a raid.", GREEN)
            return
        shortfall = threat - defense
        knocked_out = self._wreck(base, shortfall * DAMAGE_PER_SHORTFALL)
        stolen = self._steal(base, max(0.05, min(MAX_THEFT, 0.5 * shortfall / threat)))
        self._say(f"{base.name} was raided while you were away: {knocked_out} module(s) knocked out"
                  f"{self._stolen_text(stolen)}.", RED)

    def _wreck(self, base: PlayerBase, budget: float) -> int:
        """Spend `budget` hull damage on random modules, one after another. Returns how many were knocked out."""
        modules = [m for m in base.unique_modules() if m.is_constructed and not m.wrecked]
        self.rng.shuffle(modules)
        knocked_out = 0
        for module in modules:
            if budget <= 0:
                break
            blow = min(budget, module.hull)
            budget -= blow
            knocked_out += 1 if module.take_damage(blow) else 0
        base.update(0.0)
        return knocked_out

    def _steal(self, base: PlayerBase, fraction: float) -> Dict[str, int]:
        stolen = {}
        for commodity_id, amount in list(base.stored_resources.items()):
            take = int(amount * fraction + 0.5)
            if take > 0:
                stolen[commodity_id] = base.remove_resource(commodity_id, take)
        return stolen

    @staticmethod
    def _stolen_text(stolen: Dict[str, int]) -> str:
        if not stolen:
            return ""
        from ..trading.commodity import commodity_registry
        parts = [f"{n} {commodity_registry.get_commodity(c).name}" for c, n in sorted(stolen.items())]
        return ", and stole " + ", ".join(parts)
