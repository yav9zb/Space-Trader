"""
Base Management System - the player's bases: founding them, keeping them
running, and saving them.
"""

from pygame import Vector2
from typing import Dict, List, Optional, Any, Tuple

from .base_entity import PlayerBase, BaseModule, ModuleType
from .raids import RaidDirector

SAVE_VERSION = 3


class BaseManager:
    """Owns every player base."""

    def __init__(self):
        self.bases: Dict[str, PlayerBase] = {}
        self.active_base_id: Optional[str] = None
        self.next_base_id = 1

        # Raids: what happened, for the game to tell the player, and the thing that sends them
        self.events: List[Tuple[str, tuple]] = []
        self.raids = RaidDirector(self.events)

        # Rules for founding a base
        self.founding_cost = 4000
        self.max_bases = 3
        self.min_base_distance = 800        # from any other base
        self.min_station_distance = 600     # from any station
        self.interact_range = 500           # how close you must be to use a base

        # Goods a new base starts with: enough for its first generator and storage
        self.starter_goods = {"fuel_cells": 4, "metal_ore": 6}

    def reset(self) -> None:
        """Forget every base (a new game)."""
        self.bases.clear()
        self.active_base_id = None
        self.next_base_id = 1
        self.events.clear()
        self.raids.reset()

    # Founding ---------------------------------------------------------------------------------------

    def can_found(self, position: Vector2, stations, credits: int) -> Tuple[bool, List[str]]:
        """Whether a base can be founded at `position`, and if not, why."""
        position = Vector2(position)
        reasons = []
        if len(self.bases) >= self.max_bases:
            reasons.append(f"You can have at most {self.max_bases} bases.")
        if credits < self.founding_cost:
            reasons.append(f"Needs {self.founding_cost:,} credits (you have {int(credits):,}).")
        if any(position.distance_to(s.position) < self.min_station_distance for s in stations):
            reasons.append(f"Too close to a station (keep {self.min_station_distance} units away).")
        if any(position.distance_to(b.position) < self.min_base_distance for b in self.bases.values()):
            reasons.append(f"Too close to another of your bases (keep {self.min_base_distance} units away).")
        return not reasons, reasons

    def found_base(self, position: Vector2, stations, wallet, name: str = None) -> Optional[str]:
        """Found a base, charging `wallet.credits`. Returns its id, or None (and charges nothing)."""
        ok, _ = self.can_found(position, stations, wallet.credits)
        if not ok:
            return None
        wallet.credits -= self.founding_cost

        base_id = f"base_{self.next_base_id}"
        self.next_base_id += 1
        base = PlayerBase(position.x, position.y, name or f"Frontier Base {len(self.bases) + 1}")
        for commodity_id, amount in self.starter_goods.items():
            base.add_resource(commodity_id, amount)
        self.bases[base_id] = base
        if self.active_base_id is None:
            self.active_base_id = base_id
        return base_id

    # Looking up -------------------------------------------------------------------------------------------

    def get_base(self, base_id: str) -> Optional[PlayerBase]:
        return self.bases.get(base_id)

    def get_active_base(self) -> Optional[PlayerBase]:
        return self.bases.get(self.active_base_id) if self.active_base_id else None

    def set_active_base(self, base_id: str) -> bool:
        if base_id in self.bases:
            self.active_base_id = base_id
            return True
        return False

    def get_nearest_base(self, position: Vector2) -> Optional[Tuple[str, PlayerBase, float]]:
        """(base_id, base, distance) of the nearest base."""
        position = Vector2(position)
        best = None
        for base_id, base in self.bases.items():
            distance = position.distance_to(base.position)
            if best is None or distance < best[2]:
                best = (base_id, base, distance)
        return best

    def base_in_range(self, position: Vector2) -> Optional[Tuple[str, PlayerBase, float]]:
        """The nearest base close enough to use, if any."""
        nearest = self.get_nearest_base(position)
        return nearest if nearest and nearest[2] <= self.interact_range else None

    # Running ----------------------------------------------------------------------------------------------

    def update(self, delta_time: float, player_position: Vector2 = None) -> None:
        """Every base keeps building and producing, wherever the player is."""
        for base in self.bases.values():
            base.update(delta_time)

    def update_defense(self, delta_time: float, player_position: Vector2, combat, now: float) -> list:
        """Raids come and go, and the turrets fire. Returns the turret hits on raiders and other
        bandits, as (projectile, bandit) pairs, for the combat manager to apply."""
        if not self.bases:
            return []
        from ..entities.bandit import BanditState
        self.raids.update(delta_time, self.bases, player_position, combat)
        targets = [b for b in combat.active_bandits
                   if b.state != BanditState.DISABLED and not (b.bounty_id or b.stronghold_id)]
        hits = []
        for base in self.bases.values():
            hits += base.defend(targets, now)
        return hits

    def pop_events(self) -> List[Tuple[str, tuple]]:
        """What happened since the last call."""
        events = list(self.events)
        self.events.clear()
        return events

    def draw(self, screen, camera_offset: Vector2, player_position: Vector2 = None) -> None:
        for base in self.bases.values():
            base.draw(screen, camera_offset)

    # Saving -----------------------------------------------------------------------------------------------

    def save_bases(self) -> Dict[str, Any]:
        bases = {}
        for base_id, base in self.bases.items():
            bases[base_id] = {
                "name": base.name,
                "position": [base.position.x, base.position.y],
                "stored_resources": dict(base.stored_resources),
                "raid_timer": base.raid_timer,
                "core_hull": base.modules[(0, 0)].hull,
                "modules": [{
                    "type": module.module_type.value,
                    "x": int(module.grid_position.x),
                    "y": int(module.grid_position.y),
                    "built": module.construction_time_elapsed,
                    "done": module.is_constructed,
                    "cycle_running": module.cycle_running,
                    "cycle_progress": module.cycle_progress,
                    "hull": module.hull,
                } for module in base.unique_modules() if module.module_type != ModuleType.COMMAND_CENTER],
            }
        return {"version": SAVE_VERSION, "bases": bases, "active_base_id": self.active_base_id,
                "next_base_id": self.next_base_id}

    def load_bases(self, save_data: Dict[str, Any]) -> bool:
        """Restore bases from saved data. On bad data nothing is changed."""
        try:
            loaded: Dict[str, PlayerBase] = {}
            for base_id, data in save_data.get("bases", {}).items():
                x, y = data["position"]
                base = PlayerBase(x, y, data["name"])
                base.stored_resources = {str(c): int(n) for c, n in data.get("stored_resources", {}).items()}
                timer = data.get("raid_timer")
                base.raid_timer = None if timer is None else float(timer)
                core = base.modules[(0, 0)]
                core.hull = max(0.0, min(float(data.get("core_hull", core.hull)), core.stats.max_hull))
                core.wrecked = core.hull <= 0
                for entry in data.get("modules", []):
                    module = BaseModule(ModuleType(entry["type"]), int(entry["x"]), int(entry["y"]))
                    module.construction_time_elapsed = float(entry.get("built", 0.0))
                    module.is_constructed = bool(entry.get("done", False))
                    module.cycle_running = bool(entry.get("cycle_running", False))
                    module.cycle_progress = float(entry.get("cycle_progress", 0.0))
                    module.hull = max(0.0, min(float(entry.get("hull", module.hull)), module.stats.max_hull))
                    module.wrecked = module.hull <= 0
                    base._place(module)
                base.update(0.0)
                loaded[base_id] = base
        except (KeyError, TypeError, ValueError, AttributeError):
            return False
        self.bases = loaded
        active = save_data.get("active_base_id")
        self.active_base_id = active if active in loaded else next(iter(loaded), None)
        self.next_base_id = int(save_data.get("next_base_id", len(loaded) + 1))
        return True


# Global base manager instance
base_manager = BaseManager()
