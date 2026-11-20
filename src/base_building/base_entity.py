"""
Player bases: a command center on a grid, plus modules the player builds.

A base is paid for with the ship's credits and with goods taken from the base's
own storage (the player hauls them there). Modules take real time to build,
draw power, and the production modules turn goods into other goods on their own.
Goods are the game's real commodities, keyed by commodity id.
"""

import pygame
from pygame import Vector2
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field


class ModuleType(Enum):
    """Types of base modules."""
    COMMAND_CENTER = "command_center"
    POWER_GENERATOR = "power_generator"
    STORAGE = "storage"
    MINING_FACILITY = "mining_facility"
    REFINERY = "refinery"
    FACTORY = "factory"


# What the player can build, in the order of the number keys
BUILDABLE = [
    ModuleType.POWER_GENERATOR,
    ModuleType.STORAGE,
    ModuleType.MINING_FACILITY,
    ModuleType.REFINERY,
    ModuleType.FACTORY,
]

CORE_POWER = 60            # the command center runs on its own reactor
GRID_SIZE = 50             # pixels per grid cell
MAX_GRID = 20              # the grid is 20 x 20 cells around the command center
MAX_CYCLES_PER_UPDATE = 500


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


class BaseModule:
    """One module of a base."""

    MODULE_DEFINITIONS = {
        ModuleType.COMMAND_CENTER: ModuleStats(
            label="Command Center", short="CMD", power_consumption=20, power_generation=CORE_POWER,
            storage_capacity=40, size=2, blurb="The heart of the base. It cannot be removed."),
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
            recipe=Recipe({"electronics": 2, "metal_ore": 1}, {"machinery": 1}, 25.0),
            blurb="Turns 2 electronics and 1 metal ore into 1 machinery."),
    }

    COLORS = {
        ModuleType.COMMAND_CENTER: (100, 150, 255),
        ModuleType.POWER_GENERATOR: (255, 230, 100),
        ModuleType.STORAGE: (190, 195, 205),
        ModuleType.MINING_FACILITY: (190, 120, 70),
        ModuleType.REFINERY: (255, 150, 100),
        ModuleType.FACTORY: (170, 120, 255),
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

    # State ------------------------------------------------------------------------------

    @property
    def construction_progress(self) -> float:
        if self.is_constructed or self.stats.build_time <= 0:
            return 1.0
        return min(1.0, self.construction_time_elapsed / self.stats.build_time)

    @property
    def is_operational(self) -> bool:
        return self.is_constructed and self.efficiency > 0

    @property
    def is_powered(self) -> bool:
        return self.is_operational

    def update(self, delta_time: float) -> None:
        """Advance construction."""
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
        # Status light: green running, amber waiting or blocked, red without power
        if not self.is_operational:
            light = (255, 80, 70)
        elif self.blocked or self.waiting_for:
            light = (255, 200, 70)
        else:
            light = (90, 235, 130)
        pygame.draw.circle(screen, light, (rect.left + 6, rect.top + 6), 3)


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
        return sum(m.stats.storage_capacity for m in self.unique_modules() if m.is_constructed)

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

        self.power_generation = sum(m.stats.power_generation for m in modules if m.is_constructed)
        self.power_consumption = sum(m.stats.power_consumption for m in modules if m.is_constructed)
        self.power_ratio = 1.0 if self.power_consumption <= 0 else min(
            1.0, self.power_generation / self.power_consumption)
        for module in modules:
            module.efficiency = self.power_ratio if module.is_constructed else 0.0

        if delta_time > 0:
            for module in modules:
                if module.is_operational and module.stats.recipe is not None:
                    self._run_production(module, delta_time)

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

        font = pygame.font.Font(None, 24)
        name = font.render(self.name, True, (235, 240, 250))
        top = centre.y + min(m.grid_position.y for m in self.unique_modules()) * self.grid_size
        screen.blit(name, name.get_rect(midbottom=(centre.x, top - 6)))
        ok = self.power_ratio >= 1.0
        power = font.render(f"Power {self.power_generation}/{self.power_consumption}", True,
                            (110, 235, 140) if ok else (255, 205, 90))
        bottom = centre.y + max(m.grid_position.y + m.stats.size for m in self.unique_modules()) * self.grid_size
        screen.blit(power, power.get_rect(midtop=(centre.x, bottom + 6)))
