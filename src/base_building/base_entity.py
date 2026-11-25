"""
Player bases: a command center on a grid, plus modules the player builds.

A base is paid for with the ship's credits and with goods taken from the base's
own storage (the player hauls them there). Modules take real time to build,
draw power, and the production modules turn goods into other goods on their own.
Goods are the game's real commodities, keyed by commodity id.
"""

import math

import pygame
from pygame import Vector2
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from ..combat.weapons import WeaponSystem, create_weapon


class ModuleType(Enum):
    """Types of base modules."""
    COMMAND_CENTER = "command_center"
    POWER_GENERATOR = "power_generator"
    STORAGE = "storage"
    MINING_FACILITY = "mining_facility"
    REFINERY = "refinery"
    FACTORY = "factory"
    TURRET = "turret"
    SERVICE_BAY = "service_bay"
    TRADE_HUB = "trade_hub"


# What the player can build, in the order of the number keys
BUILDABLE = [
    ModuleType.POWER_GENERATOR,
    ModuleType.STORAGE,
    ModuleType.MINING_FACILITY,
    ModuleType.REFINERY,
    ModuleType.FACTORY,
    ModuleType.TURRET,
    ModuleType.SERVICE_BAY,
    ModuleType.TRADE_HUB,
]

CORE_POWER = 60            # the command center runs on its own reactor
GRID_SIZE = 50             # pixels per grid cell
MAX_GRID = 20              # the grid is 20 x 20 cells around the command center
MAX_CYCLES_PER_UPDATE = 500

TURRET_RANGE = 900.0       # how far a turret shoots
TURRET_DEFENSE = 200       # what one working turret is worth against a raid (see raids.py)
TURRET_MIN_POWER = 0.5     # a turret needs at least this share of full power to fire
REPAIR_RATE = 0.01         # share of its hull a module mends per second, when no raid is on
RESTORE_AT = 0.5           # a knocked-out module works again once it is mended this far

# The service bay: a ship within reach of the base is refuelled and repaired, from the base's own goods
SERVICE_MIN_POWER = 0.5    # a bay needs at least this share of full power
REFUEL_RATE = 8.0          # fuel the bay puts into the ship per second
FUEL_PER_CELL = 10.0       # fuel one fuel cell is worth
HULL_RATE = 5.0            # hull points the bay mends on the ship per second
HULL_PER_MACHINERY = 20.0  # hull points one machinery is worth

# The trade hub: sells the base's goods for credits (see trade.py)
HUB_MIN_POWER = 0.5        # a hub needs at least this share of full power
HUB_RECOVERY = 0.001       # how much of a good's price-drop heals per second


class Shooter:
    """What a turret's shots belong to (it is friendly, so its shots are drawn as one)."""
    friendly = True

    def __init__(self, module):
        self.module = module


class ModuleTarget:
    """A module as something a raider's shots can hit: a position, a radius, and damage."""

    def __init__(self, module, position: Vector2, radius: float):
        self.module = module
        self.position = position
        self.size = radius

    def take_damage(self, damage: float) -> bool:
        return self.module.take_damage(damage)


@dataclass(frozen=True)
class Recipe:
    """Goods in, goods out, and how long one cycle takes (seconds at full power)."""
    inputs: Dict[str, int]
    outputs: Dict[str, int]
    seconds: float


@dataclass(frozen=True)
class ModuleStats:
    label: str = ""
    short: str = ""
    power_consumption: int = 0
    power_generation: int = 0
    storage_capacity: int = 0                 # cargo volume units, like the ship's hold
    cost_credits: int = 0
    cost_goods: Dict[str, int] = field(default_factory=dict)
    build_time: float = 0.0                   # seconds
    size: int = 1                             # grid cells per side
    recipe: Optional[Recipe] = None
    blurb: str = ""
    max_hull: int = 300                       # damage it takes before it is knocked out
    weapon: str = ""                          # a turret's weapon


class BaseModule:
    """One module of a base."""

    MODULE_DEFINITIONS = {
        ModuleType.COMMAND_CENTER: ModuleStats(
            label="Command Center", short="CMD", power_consumption=20, power_generation=CORE_POWER,
            storage_capacity=40, size=2, max_hull=800,
            blurb="The heart of the base. It cannot be removed."),
        ModuleType.POWER_GENERATOR: ModuleStats(
            label="Power Generator", short="PWR", power_generation=100,
            cost_credits=1500, cost_goods={"fuel_cells": 4}, build_time=45.0,
            blurb="Powers the other modules."),
        ModuleType.STORAGE: ModuleStats(
            label="Storage", short="STO", power_consumption=5, storage_capacity=120,
            cost_credits=1200, cost_goods={"metal_ore": 6}, build_time=30.0,
            blurb="Holds more goods."),
        ModuleType.MINING_FACILITY: ModuleStats(
            label="Mining Facility", short="MIN", power_consumption=60, size=2,
            cost_credits=4000, cost_goods={"machinery": 2, "electronics": 4}, build_time=90.0,
            recipe=Recipe({}, {"metal_ore": 1}, 20.0),
            blurb="Digs up metal ore, by itself."),
        ModuleType.REFINERY: ModuleStats(
            label="Refinery", short="REF", power_consumption=80, size=2,
            cost_credits=5000, cost_goods={"metal_ore": 10, "electronics": 4}, build_time=120.0,
            recipe=Recipe({"metal_ore": 2}, {"electronics": 1}, 15.0),
            blurb="Turns 2 metal ore into 1 electronics."),
        ModuleType.FACTORY: ModuleStats(
            label="Factory", short="FAC", power_consumption=60, size=2,
            cost_credits=6500, cost_goods={"metal_ore": 12, "electronics": 8}, build_time=150.0,
            recipe=Recipe({"electronics": 2, "metal_ore": 1}, {"machinery": 2}, 25.0),
            blurb="Turns 2 electronics and 1 metal ore into 2 machinery."),
        ModuleType.TURRET: ModuleStats(
            label="Turret", short="TUR", power_consumption=25,
            cost_credits=2500, cost_goods={"machinery": 2, "electronics": 2}, build_time=40.0,
            max_hull=250, weapon="basic_laser",
            blurb="Shoots raiders. Needs power. A base with none is easy prey."),
        ModuleType.SERVICE_BAY: ModuleStats(
            label="Service Bay", short="SVC", power_consumption=30,
            cost_credits=3500, cost_goods={"machinery": 3, "electronics": 2}, build_time=60.0,
            blurb="Refuels and repairs your ship while you are at the base, using its fuel cells and machinery."),
        ModuleType.TRADE_HUB: ModuleStats(
            label="Trade Hub", short="HUB", power_consumption=40, size=2,
            cost_credits=6000, cost_goods={"electronics": 6, "machinery": 4}, build_time=90.0,
            blurb="Buys the base's goods for credits, so you can sell what it makes without hauling it away."),
    }

    COLORS = {
        ModuleType.COMMAND_CENTER: (100, 150, 255),
        ModuleType.POWER_GENERATOR: (255, 230, 100),
        ModuleType.STORAGE: (190, 195, 205),
        ModuleType.MINING_FACILITY: (190, 120, 70),
        ModuleType.REFINERY: (255, 150, 100),
        ModuleType.FACTORY: (170, 120, 255),
        ModuleType.TURRET: (240, 90, 90),
        ModuleType.SERVICE_BAY: (110, 210, 220),
        ModuleType.TRADE_HUB: (235, 190, 90),
    }

    _label_cache: Dict[tuple, pygame.Surface] = {}

    def __init__(self, module_type: ModuleType, grid_x: int, grid_y: int):
        self.module_type = module_type
        self.grid_position = Vector2(grid_x, grid_y)
        self.stats = self.MODULE_DEFINITIONS[module_type]

        # Construction
        self.construction_time_elapsed = 0.0
        self.is_constructed = False

        # Running: the share of full power it gets, and where the current cycle is
        self.efficiency = 0.0
        self.cycle_progress = 0.0
        self.cycle_running = False
        self.blocked = False                       # a finished cycle with nowhere to put its goods
        self.waiting_for: Dict[str, int] = {}

        # Damage: a module at no hull is knocked out until it has mended
        self.hull = float(self.stats.max_hull)
        self.wrecked = False

        # Turrets
        self.aim = Vector2(0, -1)
        self.weapon_system: Optional[WeaponSystem] = None
        if self.stats.weapon:
            self.weapon_system = WeaponSystem()
            self.weapon_system.add_weapon(create_weapon(self.stats.weapon))
        self.shooter = Shooter(self)

    # State ------------------------------------------------------------------------------

    @property
    def construction_progress(self) -> float:
        if self.is_constructed or self.stats.build_time <= 0:
            return 1.0
        return min(1.0, self.construction_time_elapsed / self.stats.build_time)

    @property
    def is_operational(self) -> bool:
        return self.is_constructed and not self.wrecked and self.efficiency > 0

    @property
    def is_turret(self) -> bool:
        return self.weapon_system is not None

    def take_damage(self, damage: float) -> bool:
        """Returns True if this blow knocked the module out."""
        self.hull = max(0.0, self.hull - damage)
        if self.hull <= 0 and not self.wrecked:
            self.wrecked = True
            return True
        return False

    def mend(self, delta_time: float) -> None:
        """Repair a little. A knocked-out module works again once it is half mended."""
        full = float(self.stats.max_hull)
        self.hull = min(full, self.hull + full * REPAIR_RATE * delta_time)
        if self.wrecked and self.hull >= full * RESTORE_AT:
            self.wrecked = False

    @property
    def is_powered(self) -> bool:
        return self.is_operational

    def update(self, delta_time: float) -> None:
        """Advance construction."""
        if self.weapon_system is not None:
            self.weapon_system.update(delta_time)
        if not self.is_constructed:
            self.construction_time_elapsed += delta_time
            if self.construction_time_elapsed >= self.stats.build_time:
                self.is_constructed = True

    def get_world_position(self, base_position: Vector2, grid_size: float) -> Vector2:
        """The centre of the module in the world."""
        half = self.stats.size * grid_size / 2
        return base_position + Vector2(self.grid_position.x * grid_size + half,
                                       self.grid_position.y * grid_size + half)

    # Drawing ----------------------------------------------------------------------------------

    def _label(self) -> pygame.Surface:
        key = (self.stats.short, self.is_operational)
        surface = self._label_cache.get(key)
        if surface is None:
            font = pygame.font.Font(None, 20)
            color = (20, 24, 36) if self.is_operational else (200, 205, 215)
            surface = self._label_cache[key] = font.render(self.stats.short, True, color)
        return surface

    def draw(self, screen, world_position: Vector2, camera_offset: Vector2, grid_size: float) -> None:
        """Draw the module (world_position is its centre)."""
        centre = world_position - camera_offset
        size = int(grid_size * self.stats.size) - 2
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (int(centre.x), int(centre.y))
        if not screen.get_rect().inflate(size * 2, size * 2).colliderect(rect):
            return

        if not self.is_constructed:
            pygame.draw.rect(screen, (60, 64, 80), rect)
            pygame.draw.rect(screen, (110, 118, 140), rect, 1)
            bar = pygame.Rect(rect.left, rect.bottom - 6, int(rect.width * self.construction_progress), 5)
            pygame.draw.rect(screen, (90, 220, 130), bar)
            return

        color = self.COLORS.get(self.module_type, (128, 128, 128))
        if not self.is_operational:
            color = tuple(int(c * 0.45) for c in color)
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, tuple(min(255, int(c * 1.25)) for c in color), rect, 2)
        label = self._label()
        screen.blit(label, label.get_rect(center=rect.center))
        if self.is_turret:
            tip = Vector2(rect.center) + self.aim * (rect.width * 0.55)
            pygame.draw.line(screen, (255, 210, 200), rect.center, (int(tip.x), int(tip.y)), 3)
        if self.wrecked:
            pygame.draw.rect(screen, (230, 70, 60), rect, 2)
        if self.hull < self.stats.max_hull:
            share = self.hull / self.stats.max_hull
            pygame.draw.rect(screen, (50, 20, 20), (rect.left, rect.top - 6, rect.width, 4))
            pygame.draw.rect(screen, (235, 90, 70) if share < 0.5 else (235, 200, 80),
                             (rect.left, rect.top - 6, int(rect.width * share), 4))
        # Status light: green running, amber waiting or blocked, red without power
        if not self.is_operational:
            light = (255, 80, 70)
        elif self.blocked or self.waiting_for:
            light = (255, 200, 70)
        else:
            light = (90, 235, 130)
        pygame.draw.circle(screen, light, (rect.left + 6, rect.top + 6), 3)


class RaidFocus:
    """What raiders aim for: the base's command center."""
    is_raid_target = True

    def __init__(self, base):
        self.base = base

    @property
    def position(self) -> Vector2:
        return self.base.position + Vector2(self.base.grid_size, self.base.grid_size)

    @property
    def size(self) -> float:
        return self.base.grid_size


class PlayerBase:
    """A player-built base."""

    def __init__(self, x: float, y: float, name: str = "New Base"):
        self.position = Vector2(x, y)
        self.name = name
        self.grid_size = GRID_SIZE
        self.max_grid_size = MAX_GRID
        self.modules: Dict[tuple, BaseModule] = {}    # (grid_x, grid_y) -> module, for every cell it covers
        self.stored_resources: Dict[str, int] = {}    # commodity id -> amount
        self.power_generation = 0
        self.power_consumption = 0
        self.power_ratio = 1.0
        self.base_size = 100

        # Raids (see raids.py): the countdown to the next one, and whether one is on now
        self.raid_timer: Optional[float] = None
        self.under_attack = False
        self.focus = RaidFocus(self)

        # The service bay: goods already turned into fuel or hull that have not gone into the ship yet
        self._fuel_credit = 0.0
        self._hull_credit = 0.0
        self.service_lack: set = set()      # goods the bay ran out of while serving a ship

        # The trade hub: how far each good's price has been pushed down by what was sold (0 to 1)
        self.hub_saturation: Dict[str, float] = {}

        core = BaseModule(ModuleType.COMMAND_CENTER, 0, 0)
        core.is_constructed = True
        self._place(core)
        self.update(0.0)

    # Layout -----------------------------------------------------------------------------------

    def _place(self, module: BaseModule) -> None:
        size = module.stats.size
        gx, gy = int(module.grid_position.x), int(module.grid_position.y)
        for x in range(gx, gx + size):
            for y in range(gy, gy + size):
                self.modules[(x, y)] = module

    def unique_modules(self) -> List[BaseModule]:
        seen, result = set(), []
        for module in self.modules.values():
            if id(module) not in seen:
                seen.add(id(module))
                result.append(module)
        return result

    def is_valid_position(self, grid_x: int, grid_y: int, module_type: ModuleType) -> bool:
        size = BaseModule.MODULE_DEFINITIONS[module_type].size
        half = self.max_grid_size // 2
        if grid_x < -half or grid_y < -half or grid_x + size > half or grid_y + size > half:
            return False
        return not any((x, y) in self.modules
                       for x in range(grid_x, grid_x + size) for y in range(grid_y, grid_y + size))

    # Goods --------------------------------------------------------------------------------------

    @staticmethod
    def _volume(commodity_id: str):
        from ..trading.commodity import commodity_registry
        try:
            return commodity_registry.get_commodity(commodity_id).volume
        except KeyError:
            return None

    @property
    def storage_capacity(self) -> int:
        return sum(m.stats.storage_capacity for m in self.unique_modules()
                   if m.is_constructed and not m.wrecked)

    @property
    def used_capacity(self) -> int:
        return sum((self._volume(c) or 0) * n for c, n in self.stored_resources.items())

    @property
    def free_capacity(self) -> int:
        return max(0, self.storage_capacity - self.used_capacity)

    def add_resource(self, commodity_id: str, amount: int) -> int:
        """Store goods. Returns how many fitted."""
        volume = self._volume(commodity_id)
        if volume is None or amount <= 0:
            return 0
        stored = min(int(amount), self.free_capacity // max(1, volume))
        if stored > 0:
            self.stored_resources[commodity_id] = self.stored_resources.get(commodity_id, 0) + stored
        return stored

    def remove_resource(self, commodity_id: str, amount: int) -> int:
        """Take goods out. Returns how many were taken."""
        have = self.stored_resources.get(commodity_id, 0)
        taken = min(have, max(0, int(amount)))
        if taken:
            if have - taken > 0:
                self.stored_resources[commodity_id] = have - taken
            else:
                del self.stored_resources[commodity_id]
        return taken

    def get_resource_amount(self, commodity_id: str) -> int:
        return self.stored_resources.get(commodity_id, 0)

    def has_resource(self, commodity_id: str, amount: int) -> bool:
        return self.get_resource_amount(commodity_id) >= amount

    # Building -------------------------------------------------------------------------------------

    def shortfall(self, module_type: ModuleType, credits: int = 0) -> Dict[str, int]:
        """What is missing to build a module: {"credits": n, commodity_id: n}. Empty if nothing."""
        stats = BaseModule.MODULE_DEFINITIONS[module_type]
        missing = {}
        if credits < stats.cost_credits:
            missing["credits"] = stats.cost_credits - credits
        for commodity_id, amount in stats.cost_goods.items():
            lacking = amount - self.get_resource_amount(commodity_id)
            if lacking > 0:
                missing[commodity_id] = lacking
        return missing

    def can_afford_module(self, module_type: ModuleType, credits: int = 0) -> bool:
        return not self.shortfall(module_type, credits)

    def add_module(self, module_type: ModuleType, grid_x: int, grid_y: int, wallet=None, free: bool = False) -> bool:
        """Build a module. The cost is taken from `wallet.credits` and the base's storage;
        `free` skips payment. Returns True if it was placed."""
        if module_type == ModuleType.COMMAND_CENTER or not self.is_valid_position(grid_x, grid_y, module_type):
            return False
        stats = BaseModule.MODULE_DEFINITIONS[module_type]
        if not free:
            credits = wallet.credits if wallet is not None else 0
            if self.shortfall(module_type, credits):
                return False
            wallet.credits -= stats.cost_credits
            for commodity_id, amount in stats.cost_goods.items():
                self.remove_resource(commodity_id, amount)
        self._place(BaseModule(module_type, grid_x, grid_y))
        return True

    def remove_module(self, grid_x: int, grid_y: int, wallet=None) -> bool:
        """Take a module down, refunding half its cost. The command center stays."""
        module = self.modules.get((grid_x, grid_y))
        if module is None or module.module_type == ModuleType.COMMAND_CENTER:
            return False
        size = module.stats.size
        gx, gy = int(module.grid_position.x), int(module.grid_position.y)
        for x in range(gx, gx + size):
            for y in range(gy, gy + size):
                self.modules.pop((x, y), None)
        if wallet is not None:
            wallet.credits += module.stats.cost_credits // 2
        for commodity_id, amount in module.stats.cost_goods.items():
            self.add_resource(commodity_id, amount // 2)
        return True

    # Running ------------------------------------------------------------------------------------

    def update(self, delta_time: float) -> None:
        """Advance construction, power and production."""
        modules = self.unique_modules()
        for module in modules:
            module.update(delta_time)
            if not self.under_attack and delta_time > 0 and (module.hull < module.stats.max_hull):
                module.mend(delta_time)

        self.power_generation = sum(m.stats.power_generation for m in modules if m.is_constructed and not m.wrecked)
        self.power_consumption = sum(m.stats.power_consumption for m in modules if m.is_constructed and not m.wrecked)
        self.power_ratio = 1.0 if self.power_consumption <= 0 else min(
            1.0, self.power_generation / self.power_consumption)
        for module in modules:
            module.efficiency = self.power_ratio if module.is_constructed else 0.0

        if delta_time > 0:
            for module in modules:
                if module.is_operational and module.stats.recipe is not None:
                    self._run_production(module, delta_time)
            for commodity_id in list(self.hub_saturation):
                left = self.hub_saturation[commodity_id] - HUB_RECOVERY * delta_time
                if left > 0:
                    self.hub_saturation[commodity_id] = left
                else:
                    del self.hub_saturation[commodity_id]

    def _run_production(self, module: BaseModule, delta_time: float) -> None:
        recipe = module.stats.recipe
        remaining = delta_time * module.efficiency
        module.waiting_for = {}
        for _ in range(MAX_CYCLES_PER_UPDATE):
            if not module.cycle_running:
                lacking = {c: n - self.get_resource_amount(c) for c, n in recipe.inputs.items()
                           if self.get_resource_amount(c) < n}
                if lacking:
                    module.waiting_for = lacking
                    return
                for commodity_id, amount in recipe.inputs.items():
                    self.remove_resource(commodity_id, amount)
                module.cycle_running = True
                module.cycle_progress = 0.0
            step = min(remaining, recipe.seconds - module.cycle_progress)
            module.cycle_progress += step
            remaining -= step
            if module.cycle_progress < recipe.seconds:
                return
            # The cycle is done: the goods need somewhere to go
            volume = sum((self._volume(c) or 0) * n for c, n in recipe.outputs.items())
            if volume > self.free_capacity:
                module.blocked = True
                return
            module.blocked = False
            for commodity_id, amount in recipe.outputs.items():
                self.add_resource(commodity_id, amount)
            module.cycle_running = False
            module.cycle_progress = 0.0
            if remaining <= 0:
                return

    def production_report(self) -> List[dict]:
        """One line per production module: what it is doing now."""
        lines = []
        for module in self.unique_modules():
            recipe = module.stats.recipe
            if recipe is None:
                continue
            if not module.is_constructed:
                state = f"Building {module.construction_progress:.0%}"
            elif module.wrecked:
                state = "Knocked out"
            elif not module.is_operational:
                state = "No power"
            elif module.blocked:
                state = "Storage full"
            elif module.waiting_for:
                from ..trading.commodity import commodity_registry
                needs = ", ".join(f"{n} {commodity_registry.get_commodity(c).name}"
                                  for c, n in module.waiting_for.items())
                state = f"Needs {needs}"
            else:
                state = f"Working {module.cycle_progress / recipe.seconds:.0%}"
            lines.append({"label": module.stats.label, "state": state, "module": module})
        return lines

    # Defense ----------------------------------------------------------------------------------------

    def turrets(self) -> List[BaseModule]:
        return [m for m in self.unique_modules() if m.is_turret]

    def working_turrets(self) -> List[BaseModule]:
        return [m for m in self.turrets() if m.is_operational and m.efficiency >= TURRET_MIN_POWER]

    def defense_rating(self) -> int:
        """What the base can stand against: one working turret is worth TURRET_DEFENSE."""
        return len(self.working_turrets()) * TURRET_DEFENSE

    # Trade --------------------------------------------------------------------------------------------

    def working_hubs(self) -> List[BaseModule]:
        return [m for m in self.unique_modules()
                if m.module_type == ModuleType.TRADE_HUB and m.is_operational and m.efficiency >= HUB_MIN_POWER]

    # Service ------------------------------------------------------------------------------------------

    def service_bays(self) -> List[BaseModule]:
        return [m for m in self.unique_modules() if m.module_type == ModuleType.SERVICE_BAY]

    def working_bays(self) -> List[BaseModule]:
        return [m for m in self.service_bays() if m.is_operational and m.efficiency >= SERVICE_MIN_POWER]

    def serve(self, ship, delta_time: float) -> Dict[str, float]:
        """Refuel and repair a ship that is within reach, out of the base's own goods. Each working
        bay adds its share of the rate. Returns what went into the ship: {"fuel": .., "hull": ..}."""
        given = {"fuel": 0.0, "hull": 0.0}
        bays = len(self.working_bays())
        if bays == 0 or delta_time <= 0:
            return given
        max_hull = ship.get_effective_stats().get_effective_hull_points()
        given["fuel"] = self._serve_one(ship.fuel_capacity - ship.current_fuel, REFUEL_RATE * bays * delta_time,
                                        "fuel_cells", FUEL_PER_CELL, "_fuel_credit", ship.refuel)
        given["hull"] = self._serve_one(max_hull - ship.current_hull, HULL_RATE * bays * delta_time,
                                        "machinery", HULL_PER_MACHINERY, "_hull_credit",
                                        lambda amount: (ship.repair_ship(amount), amount)[1])
        return given

    def _serve_one(self, needed: float, rate_step: float, commodity_id: str, per_unit: float,
                   credit_attr: str, apply) -> float:
        if needed <= 0:
            self.service_lack.discard(commodity_id)
            return 0.0
        amount = min(needed, rate_step)
        credit = getattr(self, credit_attr)
        while credit < amount and self.remove_resource(commodity_id, 1):
            credit += per_unit
        amount = min(amount, credit)
        if amount <= 0:
            self.service_lack.add(commodity_id)
            return 0.0
        self.service_lack.discard(commodity_id)
        setattr(self, credit_attr, credit - amount)
        apply(amount)
        return amount

    def wrecked_count(self) -> int:
        return sum(1 for m in self.unique_modules() if m.wrecked)

    def hit_targets(self) -> List[ModuleTarget]:
        """The parts of the base a raider's shots can hit."""
        return [ModuleTarget(m, m.get_world_position(self.position, self.grid_size),
                             m.stats.size * self.grid_size / 2)
                for m in self.unique_modules() if m.is_constructed]

    def defend(self, targets, now: float) -> List[tuple]:
        """The turrets fire at the nearest of `targets` in range (leading a moving one)
        and return the (projectile, target) pairs that hit."""
        hits = []
        for turret in self.turrets():
            centre = turret.get_world_position(self.position, self.grid_size)
            if turret in self.working_turrets():
                nearest, best = None, TURRET_RANGE * TURRET_RANGE
                for target in targets:
                    d2 = (target.position - centre).length_squared()
                    if d2 < best:
                        nearest, best = target, d2
                if nearest is not None:
                    speed = turret.weapon_system.weapons[0].stats.projectile_speed
                    lead = nearest.position + getattr(nearest, "velocity", Vector2()) * (math.sqrt(best) / speed)
                    aim = lead - centre
                    if aim.length_squared() > 0:
                        turret.aim = aim.normalize()
                        turret.weapon_system.fire_weapons(centre, turret.aim, turret.shooter, now)
            hits += turret.weapon_system.check_hits(targets)
        return hits

    # Drawing --------------------------------------------------------------------------------------

    def draw(self, screen, camera_offset: Vector2) -> None:
        """Draw the base and its modules."""
        centre = self.position - camera_offset
        reach = self.max_grid_size * self.grid_size
        rect = screen.get_rect()
        if (centre.x < -reach or centre.x > rect.width + reach or
                centre.y < -reach or centre.y > rect.height + reach):
            return

        for module in self.unique_modules():
            module.draw(screen, module.get_world_position(self.position, self.grid_size),
                        camera_offset, self.grid_size)
            if module.is_turret:
                module.weapon_system.draw(screen, camera_offset)

        font = pygame.font.Font(None, 24)
        name = font.render(self.name, True, (235, 240, 250))
        top = centre.y + min(m.grid_position.y for m in self.unique_modules()) * self.grid_size
        screen.blit(name, name.get_rect(midbottom=(centre.x, top - 6)))
        ok = self.power_ratio >= 1.0
        power = font.render(f"Power {self.power_generation}/{self.power_consumption}", True,
                            (110, 235, 140) if ok else (255, 205, 90))
        bottom = centre.y + max(m.grid_position.y + m.stats.size for m in self.unique_modules()) * self.grid_size
        screen.blit(power, power.get_rect(midtop=(centre.x, bottom + 6)))
