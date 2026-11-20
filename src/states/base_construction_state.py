"""
Base screen (opened with B): found a base where you are, or manage the one
you are next to.

Laid out with the menu kit, like the other screens: panels, tabs, lists and
buttons are measured from the window and drawn at the screen's real pixels. The
base itself (its grid and the placement preview) is world drawing, so it is
drawn at point size and scaled up behind the panels, as flight is.

Tabs: Build (pick a module, click the grid), Storage (move goods between the
ship's hold and the base), Production (what each module is doing).
"""

import pygame
from pygame import Vector2
from typing import Optional

try:
    from ..states.game_state import State, GameStates
    from ..base_building.base_manager import base_manager
    from ..base_building.base_entity import BaseModule, BUILDABLE
    from ..base_building.construction_system import ConstructionSystem, ConstructionMode
    from ..base_building import transfer
    from ..hidpi import make_opaque
    from ..ui import menu_kit
    from ..ui.menu_style import MenuBackground, ACCENT_GOLD, ACCENT_BLUE, TEXT_PRIMARY, TEXT_DIM
except ImportError:
    from states.game_state import State, GameStates
    from base_building.base_manager import base_manager
    from base_building.base_entity import BaseModule, BUILDABLE
    from base_building.construction_system import ConstructionSystem, ConstructionMode
    from base_building import transfer
    from hidpi import make_opaque
    from ui import menu_kit
    from ui.menu_style import MenuBackground, ACCENT_GOLD, ACCENT_BLUE, TEXT_PRIMARY, TEXT_DIM

DEFAULT_ZOOM = 0.8          # a little out, so a whole base fits between the panels

TABS = [("build", "Build"), ("storage", "Storage"), ("production", "Production")]

GOOD = (120, 230, 150)
WARN = (255, 215, 90)
BAD = (255, 120, 120)

HELP_SECTIONS = [
    ("Building", [
        f"1-{len(BUILDABLE)} or click the list: choose a module",
        "Click the grid: build it there (credits from your ship, goods from the base)",
        "R: remove mode (refunds half)   P: place mode",
        "TAB: show or hide the grid   Mouse wheel: zoom",
    ]),
    ("Supplying", [
        "Modules need goods from the base's own storage, so haul them here",
        "Storage tab: RIGHT or ENTER deposits, LEFT withdraws (hold SHIFT for all)",
    ]),
    ("Defending", [
        "Pirates raid bases that have something built, every ten minutes or so",
        "Turrets shoot raiders; each working one stands against a share of a raid",
        "A raid that gets through knocks modules out and steals goods; they mend afterwards",
        "Raiders that find you near the base fight you too",
    ]),
    ("Running it", [
        "Modules take time to build, and need power from generators",
        "Mining makes metal ore; a refinery makes electronics; a factory makes machinery",
        "Production stops when storage is full",
        "Collect what it makes from the Storage tab, and sell it at a station",
    ]),
]


def _goods_text(goods, base=None) -> str:
    return ", ".join(f"{amount} {transfer.commodity_name(commodity_id)}" for commodity_id, amount in goods.items())


class BaseConstructionState(State):
    """Found a base here, or manage the one in reach."""

    def __init__(self, game, base_id: str = None, previous_state=None):
        super().__init__(game)
        self.previous_state = previous_state or GameStates.PLAYING

        self.construction_system = ConstructionSystem(base_manager, wallet=game.ship)
        self.base_id = base_id or self._default_base_id()

        self.show_base_info = True
        self.show_help = False
        self.selected_tab = "build"
        self.status = ""                                 # the last thing that happened, shown in the panel

        self.zoom_level = DEFAULT_ZOOM
        self.min_zoom = 0.5
        self.max_zoom = 2.0
        self.mouse_world_pos = Vector2(0, 0)
        self.view_center = None          # where the base sits on screen, in points (between the panels)

        # Layout, set by render and used by clicks and tests
        self.tab_rects = []
        self.panel_rects = []
        self.help_overflows = False
        self.panel_overflows = False
        self.found_requirements = []
        self.background = MenuBackground()
        self._ui = menu_kit.Ui(menu_kit.BASE_SIZE)
        self._world = None

        # Widgets
        self.module_list = menu_kit.RowList(len(BUILDABLE), wrap_keys=True)
        self.storage_list = menu_kit.RowList(0, wrap_keys=True)
        self.storage_buttons = menu_kit.ButtonBar(["Deposit 1", "Deposit all", "Withdraw 1", "Withdraw all"])
        self.found_buttons = menu_kit.ButtonBar(["Found base", "Cancel"])

        if self.base_id:
            self.construction_system.activate_construction(self.base_id)

    # Which base -----------------------------------------------------------------------------------------

    def _ship_position(self) -> Vector2:
        return Vector2(self.game.ship.position)

    def _default_base_id(self) -> Optional[str]:
        """The base within reach of the ship, if there is one."""
        nearby = base_manager.base_in_range(self._ship_position())
        return nearby[0] if nearby else None

    def _base(self):
        return base_manager.get_base(self.base_id) if self.base_id else None

    def _credits(self) -> int:
        return int(self.game.ship.credits)

    # Update ----------------------------------------------------------------------------------------------

    def update(self, delta_time):
        """The base keeps working while you look at it."""
        base_manager.update(delta_time, self._ship_position())
        self._update_mouse_world_position()
        if self.construction_system.is_construction_active:
            self.construction_system.update_mouse_position(self.mouse_world_pos)

    def _view_points(self):
        return Vector2(self.game.screen.get_size())

    def _camera_offset(self) -> Vector2:
        """World position of the view's top-left corner: the base sits at
        `view_center` (the free space between the panels), whatever the zoom."""
        base = self._base()
        centre = base.position if base is not None else Vector2(0, 0)
        on_screen = self.view_center if self.view_center is not None else self._view_points() / 2
        return centre - Vector2(on_screen) / self.zoom_level

    def _panel_side(self, ui) -> int:
        return min(ui.px(380), int(ui.width / 3.2))

    def _set_view_center(self, ui):
        """Put the base in the middle of the space the panels leave free."""
        margin, side = ui.margin(), self._panel_side(ui)
        left = margin + side if self.show_base_info else margin
        right = ui.width - margin - side
        self.view_center = Vector2((left + right) / 2, ui.height / 2) / ui.ratio

    def _update_mouse_world_position(self):
        self.mouse_world_pos = self._camera_offset() + Vector2(pygame.mouse.get_pos()) / self.zoom_level

    # Drawing -----------------------------------------------------------------------------------------------

    def render(self, screen):
        ui = self._ui = menu_kit.ui_for(screen, self.game)
        base = self._base()
        self.panel_rects = []
        self.panel_overflows = False
        if base is not None:
            self._set_view_center(ui)
            self._draw_world(ui, screen)
        else:
            self.background.draw(screen)

        if base is None:
            top = ui.header(screen, "FOUND A BASE", subtitle="Where you are now")
            footer_top = ui.footer(screen, "ENTER: found it  |  ESC: cancel")
            self.tab_rects = []
            self._draw_found(ui, screen, top, footer_top)
        else:
            top = ui.header(screen, "BASE", subtitle=base.name)
            footer_top = ui.footer(screen, self._footer_hint())
            top = self._draw_tabs(ui, screen, top)
            self._draw_panels(ui, screen, base, top, footer_top)

        if self.show_help:
            self._draw_help(ui, screen)

    def _footer_hint(self):
        if self.selected_tab == "build":
            return f"1-{len(BUILDABLE)}: module  |  click the grid: build  |  R: remove  |  TAB: grid  |  Q / W / E: tabs  |  F1: help  |  ESC: leave"
        if self.selected_tab == "storage":
            return "UP / DOWN: goods  |  RIGHT: deposit  |  LEFT: withdraw  |  SHIFT: all  |  Q / W / E: tabs  |  ESC: leave"
        return "Q / W / E: tabs  |  F1: help  |  ESC: leave"

    def _draw_world(self, ui, screen):
        """The base and its grid, drawn in points at the current zoom and scaled
        to the screen behind the panels."""
        view = self._view_points() / self.zoom_level
        size = (max(1, int(view.x)), max(1, int(view.y)))
        if self._world is None or self._world.get_size() != size:
            self._world = pygame.Surface(size)
        world = self._world
        world.fill((14, 16, 30))

        camera_offset = self._camera_offset()
        base_manager.draw(world, camera_offset, self._ship_position())
        if self.construction_system.is_construction_active and self.selected_tab == "build":
            self.construction_system.draw_world(world, camera_offset)

        if world.get_size() == screen.get_size():
            screen.blit(world, (0, 0))
        else:
            pygame.transform.smoothscale(world, screen.get_size(), screen)
            make_opaque(screen)

    # Found a base -------------------------------------------------------------------------------------------------

    def _founding(self):
        ok, reasons = base_manager.can_found(self._ship_position(), self.game.universe.stations, self._credits())
        return ok, reasons

    def _draw_found(self, ui, screen, top, footer_top):
        ok, reasons = self._founding()
        cost = base_manager.founding_cost
        kit = base_manager.starter_goods

        width = min(ui.content_width(), ui.px(820))
        inner = width - ui.px(48)
        body = [
            ("A base builds, powers itself and produces goods while you fly. You supply it with goods and collect what it makes.", TEXT_PRIMARY),
            (f"Founding one costs {cost:,} credits and comes with a command center and a starter kit: {_goods_text(kit)}.", TEXT_DIM),
        ]
        wrapped = []
        for text, color in body:
            wrapped += [(line, "body", color) for line in ui.wrap(text, "body", inner)] + [("", "gap", color)]
        checks = [(f"Credits: {self._credits():,} of {cost:,}", self._credits() >= cost)]
        for reason in reasons:
            if "credits" not in reason.lower():
                checks.append((reason, False))
        if ok:
            checks.append(("This is a good place for a base.", True))

        height = (sum(ui.px(10) if role == "gap" else ui.line_height(role) for _, role, _ in wrapped)
                  + len(checks) * (ui.line_height("body") + ui.px(4)) + ui.px(56))
        panel = pygame.Rect(0, 0, width, height)
        panel.centerx = ui.width // 2
        panel.top = top + max(0, (footer_top - top - height - ui.px(70)) // 2)
        ui.panel(screen, panel)
        self.panel_rects.append(panel)

        y = panel.top + ui.px(24)
        for line, role, color in wrapped:
            if role == "gap":
                y += ui.px(10)
                continue
            y = ui.text(screen, line, role, color, topleft=(panel.left + ui.px(24), y)).bottom
        for text, good in checks:
            rect = ui.text(screen, text, "body", GOOD if good else BAD, max_width=inner,
                           topleft=(panel.left + ui.px(24), y))
            y = rect.bottom + ui.px(4)
        self.found_requirements = checks

        strip = pygame.Rect(panel.left, panel.bottom + ui.px(12), panel.width, ui.px(50))
        self.found_buttons.enabled = [ok, True]
        self.found_buttons.layout(ui, strip)
        self.found_buttons.draw(ui, screen)

    def found_base(self) -> bool:
        """Found a base at the ship's position, if the rules allow."""
        ship = self.game.ship
        base_id = base_manager.found_base(self._ship_position(), self.game.universe.stations, ship)
        if base_id is None:
            return False
        self.base_id = base_id
        self.construction_system.activate_construction(base_id)
        self.selected_tab = "build"
        self.zoom_level = DEFAULT_ZOOM
        self.status = ""
        from ..ui.notifications import notifications
        notifications.push(f"Base founded: {base_manager.get_base(base_id).name}", duration=6.0, color=(150, 230, 170))
        return True

    # Panels ---------------------------------------------------------------------------------------------------------

    def _draw_tabs(self, ui, screen, top) -> int:
        font = ui.font("heading")
        x = ui.margin()
        self.tab_rects = []
        for tab_id, name in TABS:
            selected = tab_id == self.selected_tab
            surface = font.render(name, True, ACCENT_GOLD if selected else TEXT_DIM)
            rect = surface.get_rect(topleft=(x, top))
            screen.blit(surface, rect)
            self.tab_rects.append(rect.inflate(ui.px(16), ui.px(8)))
            if selected:
                pygame.draw.line(screen, ACCENT_GOLD, (rect.left, rect.bottom + ui.px(2)),
                                 (rect.right, rect.bottom + ui.px(2)), max(1, ui.px(2)))
            x = rect.right + ui.px(34)
        return top + font.get_linesize() + ui.px(14)

    def _draw_panels(self, ui, screen, base, top, bottom):
        bottom = max(top + ui.px(80), bottom)
        side = self._panel_side(ui)
        margin = ui.margin()

        if self.show_base_info:
            info = pygame.Rect(margin, top, side, bottom - top)
            ui.panel(screen, info)
            self.panel_rects.append(info)
            self._draw_base_info(ui, screen, base, info.inflate(-ui.px(28), -ui.px(24)))

        panel = pygame.Rect(ui.width - margin - side, top, side, bottom - top)
        ui.panel(screen, panel)
        self.panel_rects.append(panel)
        area = panel.inflate(-ui.px(28), -ui.px(24))
        if self.selected_tab == "build":
            self._draw_build(ui, screen, base, area)
        elif self.selected_tab == "storage":
            self._draw_storage(ui, screen, base, area)
        else:
            self._draw_production(ui, screen, base, area)

    # A small vertical layout for the panels. Each item is
    # ("title", text), ("kv", label, value, color), ("text", text, color), ("bar", fraction, color),
    # ("gap",). It stops, with an ellipsis, at the bottom of the area.

    def _draw_items(self, ui, screen, area, items, wrap_role="small") -> bool:
        y = area.top
        row = ui.line_height("small") + ui.px(3)
        for item in items:
            kind = item[0]
            if kind == "gap":
                y += ui.px(8)
                continue
            if kind == "title":
                need = ui.line_height("body") + ui.px(6)
            elif kind == "bar":
                need = ui.px(14)
            else:
                need = row
            if y + need > area.bottom:
                ui.text(screen, "...", "small", TEXT_DIM, topleft=(area.left, max(area.top, area.bottom - row)))
                return True
            if kind == "title":
                rect = ui.text(screen, item[1], "body", ACCENT_GOLD, max_width=area.width, topleft=(area.left, y))
                y = rect.bottom + ui.px(6)
            elif kind == "kv":
                _, label, value, color = item
                value_rect = ui.text(screen, str(value), "small", color, max_width=area.width // 2,
                                     topright=(area.right, y))
                ui.text(screen, label, "small", TEXT_DIM, max_width=area.width - value_rect.width - ui.px(10),
                        topleft=(area.left, y))
                y += row
            elif kind == "bar":
                _, fraction, color = item
                trough = pygame.Rect(area.left, y + ui.px(2), area.width, ui.px(8))
                pygame.draw.rect(screen, (40, 46, 66), trough, border_radius=ui.px(3))
                fill = trough.copy()
                fill.width = int(trough.width * max(0.0, min(1.0, fraction)))
                if fill.width:
                    pygame.draw.rect(screen, color, fill, border_radius=ui.px(3))
                y += need
            else:                                                   # text, wrapped
                _, text, color = item
                for line in ui.wrap(text, wrap_role, area.width):
                    if y + row > area.bottom:
                        ui.text(screen, "...", "small", TEXT_DIM,
                                topleft=(area.left, max(area.top, area.bottom - row)))
                        return True
                    ui.text(screen, line, wrap_role, color, topleft=(area.left, y))
                    y += row
        return False

    def _draw_base_info(self, ui, screen, base, area):
        powered = base.power_ratio >= 1.0
        capacity = base.storage_capacity
        used = base.used_capacity
        items = [
            ("title", base.name),
            ("kv", "Power", f"{base.power_generation} / {base.power_consumption}", GOOD if powered else WARN),
            ("bar", min(1.0, base.power_ratio), GOOD if powered else WARN),
            ("kv", "Storage", f"{used} / {capacity}", WARN if capacity and used >= capacity else TEXT_PRIMARY),
            ("bar", used / capacity if capacity else 0.0, ACCENT_BLUE),
            ("kv", "Modules", len(base.unique_modules()), TEXT_PRIMARY),
            *self._defense_items(base),
            ("kv", "Your credits", f"{self._credits():,}", TEXT_PRIMARY),
            ("gap",), ("title", "In storage"),
        ]
        goods = sorted(base.stored_resources.items(), key=lambda entry: transfer.commodity_name(entry[0]))
        if goods:
            items += [("kv", transfer.commodity_name(c), n, TEXT_PRIMARY) for c, n in goods]
        else:
            items.append(("text", "Nothing stored yet.", TEXT_DIM))
        self.panel_overflows |= self._draw_items(ui, screen, area, items)

    def _defense_items(self, base):
        from ..base_building import raids
        threat = raids.threat_of(raids.raid_roster(raids.raid_level(base)))
        rating = base.defense_rating()
        items = []
        if base.under_attack:
            items.append(("text", "UNDER ATTACK", BAD))
        items.append(("kv", "Turrets", f"{len(base.working_turrets())} / {len(base.turrets())}", TEXT_PRIMARY))
        items.append(("kv", "Defense", f"{rating} / {threat}", GOOD if rating >= threat else WARN))
        knocked_out = base.wrecked_count()
        if knocked_out:
            items.append(("kv", "Knocked out", knocked_out, BAD))
        return items

    # Build --------------------------------------------------------------------------------------------------------------

    def _module_row_text(self, base, module_type):
        stats = BaseModule.MODULE_DEFINITIONS[module_type]
        return stats.label, f"{stats.cost_credits:,} cr"

    def _draw_build(self, ui, screen, base, area):
        system = self.construction_system
        ui.text(screen, "Build", "body", ACCENT_GOLD, topleft=area.topleft)
        list_top = area.top + ui.line_height("body") + ui.px(6)
        row_units = 30
        list_height = len(BUILDABLE) * (ui.px(row_units) + ui.px(4))
        # On a short window the list shares the panel with the details below it
        list_height = min(list_height, max(ui.px(row_units), int((area.bottom - list_top) * 0.5)))
        list_area = pygame.Rect(area.left, list_top, area.width, list_height)
        self.module_list.set_count(len(BUILDABLE))
        self.module_list.selected = BUILDABLE.index(system.selected_module_type)
        self.module_list.layout(ui, list_area, row_units)
        self.module_list.draw_chrome(ui, screen)
        credits = self._credits()
        for index, rect in self.module_list.rects.items():
            module_type = BUILDABLE[index]
            label, price = self._module_row_text(base, module_type)
            affordable = base.can_afford_module(module_type, credits)
            color = TEXT_PRIMARY if affordable else (150, 155, 170)
            price_rect = ui.text(screen, price, "small", GOOD if affordable else BAD,
                                 midright=(rect.right - ui.px(10), rect.centery))
            ui.text(screen, f"{index + 1}  {label}", "small", color,
                    max_width=rect.width - price_rect.width - ui.px(30), midleft=(rect.left + ui.px(10), rect.centery))

        detail = pygame.Rect(area.left, self.module_list.area.bottom + ui.px(12), area.width,
                             area.bottom - (self.module_list.area.bottom + ui.px(12)))
        info = system.get_construction_info()
        items = []
        if system.construction_mode == ConstructionMode.REMOVE:
            items += [("title", "Remove mode"), ("text", "Click a module to take it down. Half its cost comes back.", TEXT_PRIMARY),
                      ("text", "P: back to building.", TEXT_DIM)]
        else:
            missing = info["missing"]
            items.append(("title", info["label"]))
            items.append(("text", info["blurb"], TEXT_DIM))
            items.append(("kv", "Credits", f"{info['cost_credits']:,}", BAD if "credits" in missing else GOOD))
            for commodity_id, amount in info["cost_goods"].items():
                have = base.get_resource_amount(commodity_id)
                items.append(("kv", transfer.commodity_name(commodity_id), f"{amount} (base has {have})",
                              BAD if commodity_id in missing else GOOD))
            items.append(("kv", "Build time", f"{info['build_time']:.0f} s", TEXT_PRIMARY))
            if info["power_generation"]:
                items.append(("kv", "Power made", info["power_generation"], TEXT_PRIMARY))
            if info["power_consumption"]:
                items.append(("kv", "Power used", info["power_consumption"], TEXT_PRIMARY))
            if info["storage_capacity"]:
                items.append(("kv", "Storage added", info["storage_capacity"], TEXT_PRIMARY))
            if missing:
                items.append(("text", "Haul the missing goods to this base (Storage tab).", WARN))
            else:
                items.append(("text", "Click the grid to build it.", GOOD))
        if self.status:
            items += [("gap",), ("text", self.status, TEXT_PRIMARY)]
        self.panel_overflows |= self._draw_items(ui, screen, detail, items)

    # Storage -------------------------------------------------------------------------------------------------------------

    def storage_rows(self):
        """[(commodity_id, in the hold, in the base)] for everything in either place."""
        base = self._base()
        ship_goods = transfer.depositable(self.game.ship)
        ids = set(ship_goods) | set(base.stored_resources if base else {})
        rows = [(c, ship_goods.get(c, 0), base.get_resource_amount(c) if base else 0) for c in ids]
        return sorted(rows, key=lambda row: transfer.commodity_name(row[0]))

    def selected_commodity(self):
        rows = self.storage_rows()
        if not rows:
            return None
        return rows[max(0, min(self.storage_list.selected, len(rows) - 1))][0]

    def move_goods(self, direction: int, everything: bool = False) -> int:
        """Deposit (direction > 0) or withdraw (direction < 0) the selected goods. Returns how many moved."""
        base, commodity_id = self._base(), self.selected_commodity()
        if base is None or commodity_id is None:
            return 0
        amount = 10 ** 6 if everything else 1
        if direction > 0:
            moved = transfer.deposit(self.game.ship, base, commodity_id, amount)
            verb = "Deposited"
            if not moved:
                self.status = "Nothing to deposit, or the base is full."
        else:
            moved = transfer.withdraw(self.game.ship, base, commodity_id, amount)
            verb = "Withdrew"
            if not moved:
                self.status = "Nothing to withdraw, or your hold is full."
        if moved:
            self.status = f"{verb} {moved} {transfer.commodity_name(commodity_id)}."
        return moved

    def _draw_storage(self, ui, screen, base, area):
        hold = self.game.ship.cargo_hold
        ui.text(screen, "Storage", "body", ACCENT_GOLD, topleft=area.topleft)
        line = ui.line_height("small")
        y = area.top + ui.line_height("body") + ui.px(4)
        ui.text(screen, f"Hold {hold.get_used_capacity()} / {hold.capacity}", "small", TEXT_PRIMARY,
                topleft=(area.left, y))
        ui.text(screen, f"Base {base.used_capacity} / {base.storage_capacity}", "small", TEXT_PRIMARY,
                topright=(area.right, y))
        y += line + ui.px(8)

        # Column heads
        col = max(ui.px(60), area.width // 5)
        ui.text(screen, "Hold", "tiny", TEXT_DIM, topright=(area.right - col - ui.px(10), y))
        ui.text(screen, "Base", "tiny", TEXT_DIM, topright=(area.right - ui.px(10), y))
        y += ui.line_height("tiny") + ui.px(4)

        button_row = ui.px(36)
        buttons_height = 2 * button_row + ui.px(8)
        status_height = line + ui.px(8)
        list_area = pygame.Rect(area.left, y, area.width, max(ui.px(40), area.bottom - y - buttons_height - status_height - ui.px(8)))
        rows = self.storage_rows()
        self.storage_list.set_count(len(rows))
        self.storage_list.layout(ui, list_area, 28)
        self.storage_list.draw_chrome(ui, screen)
        if not rows:
            ui.text(screen, "Nothing in the hold or the base.", "small", TEXT_DIM, topleft=(list_area.left, list_area.top))
        for index, rect in self.storage_list.rects.items():
            commodity_id, in_hold, in_base = rows[index]
            ui.text(screen, str(in_base), "small", TEXT_PRIMARY, midright=(rect.right - ui.px(10), rect.centery))
            ui.text(screen, str(in_hold), "small", TEXT_PRIMARY, midright=(rect.right - col - ui.px(10), rect.centery))
            ui.text(screen, transfer.commodity_name(commodity_id), "small", TEXT_PRIMARY,
                    max_width=rect.width - 2 * col - ui.px(30), midleft=(rect.left + ui.px(10), rect.centery))
        counter = self.storage_list.counter()
        if counter:
            ui.text(screen, counter, "tiny", TEXT_DIM, bottomright=(area.right, list_area.bottom + ui.px(1)))

        status_top = list_area.bottom + ui.px(6)
        if self.status:
            ui.text(screen, self.status, "small", WARN if "Nothing" in self.status else GOOD, max_width=area.width,
                    topleft=(area.left, status_top))
        selected = self.selected_commodity()
        row = next((r for r in rows if r[0] == selected), (None, 0, 0))
        self.storage_buttons.enabled = [row[1] > 0, row[1] > 0, row[2] > 0, row[2] > 0]
        # Two rows of two: Deposit and Deposit all above Withdraw and Withdraw all
        gap = ui.px(8)
        width = (area.width - gap) // 2
        top = area.bottom - buttons_height
        self.storage_buttons.rects = [
            pygame.Rect(area.left + column * (width + gap), top + line_no * (button_row + ui.px(8)), width, button_row)
            for line_no in range(2) for column in range(2)]
        self.storage_buttons.draw(ui, screen)

    # Production ----------------------------------------------------------------------------------------------------------

    def _draw_production(self, ui, screen, base, area):
        items = [("title", "Production")]
        report = base.production_report()
        if not report:
            items.append(("text", "Nothing here produces goods yet. Build a Mining Facility (3).", TEXT_DIM))
        for line in report:
            module = line["module"]
            working = line["state"].startswith("Working")
            items.append(("kv", line["label"], line["state"],
                          GOOD if working else (WARN if not line["state"].startswith("Building") else TEXT_PRIMARY)))
            recipe = module.stats.recipe
            if module.is_constructed and recipe is not None:
                items.append(("bar", module.cycle_progress / recipe.seconds if module.cycle_running else 0.0, GOOD))
            elif not module.is_constructed:
                items.append(("bar", module.construction_progress, ACCENT_BLUE))
            items.append(("text", self._recipe_text(recipe), TEXT_DIM))
            items.append(("gap",))
        if base.power_ratio < 1.0:
            items.append(("text", f"Not enough power: everything runs at {base.power_ratio:.0%}. Build a Power Generator (1).", WARN))
        self.panel_overflows |= self._draw_items(ui, screen, area, items)

    @staticmethod
    def _recipe_text(recipe) -> str:
        if not recipe.inputs:
            return f"Makes {_goods_text(recipe.outputs)} every {recipe.seconds:.0f} s"
        return f"{_goods_text(recipe.inputs)} -> {_goods_text(recipe.outputs)} every {recipe.seconds:.0f} s"

    # Help ------------------------------------------------------------------------------------------------------------------

    def _draw_help(self, ui, screen):
        veil = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 150))
        screen.blit(veil, (0, 0))

        width = min(ui.width - 2 * ui.margin(), ui.px(820))
        height = min(ui.height - 2 * ui.margin(), ui.px(640))
        panel = pygame.Rect(0, 0, width, height)
        panel.center = (ui.width // 2, ui.height // 2)
        ui.panel(screen, panel, border=ACCENT_GOLD, alpha=235)
        ui.text(screen, "Bases", "heading", TEXT_PRIMARY, midtop=(panel.centerx, panel.top + ui.px(14)))

        area = pygame.Rect(panel.left + ui.px(24), panel.top + ui.px(64), width - ui.px(48), height - ui.px(100))
        items = []
        for title, lines in HELP_SECTIONS:
            items.append(("title", title))
            items += [("text", line, TEXT_PRIMARY) for line in lines]
            items.append(("gap",))
        self.help_overflows = self._draw_items(ui, screen, area, items)
        ui.text(screen, "F1 or ESC: close", "small", TEXT_DIM, midbottom=(panel.centerx, panel.bottom - ui.px(10)))

    # Input ------------------------------------------------------------------------------------------------------------------

    def _leave(self):
        self.construction_system.deactivate_construction()
        self.game.change_state(self.previous_state)

    def _over_panel(self, pos) -> bool:
        point = self._ui.to_px(pos)
        return any(rect.collidepoint(point) for rect in self.panel_rects)

    def handle_input(self, event):
        """Handle input events."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.show_help:
                self.show_help = False
            else:
                self._leave()
            return
        if self.show_help:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                self.show_help = False
            return

        if self._base() is None:
            self._handle_found_input(event)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self._handle_tab_click(event.pos):
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1:
                self.show_help = True
                return
            if event.key == pygame.K_F2:
                self.show_base_info = not self.show_base_info
                return
            tab = {pygame.K_q: "build", pygame.K_w: "storage", pygame.K_e: "production"}.get(event.key)
            if tab:
                self.selected_tab = tab
                return
        if event.type == pygame.MOUSEWHEEL and not self._wheel_over_panel():
            factor = 1.1 if event.y > 0 else 1.0 / 1.1
            self.zoom_level = max(self.min_zoom, min(self.max_zoom, self.zoom_level * factor))
            return

        if self.selected_tab == "build":
            self._handle_build_input(event)
        elif self.selected_tab == "storage":
            self._handle_storage_input(event)

    def _wheel_over_panel(self) -> bool:
        return self._over_panel(pygame.mouse.get_pos())

    def _handle_found_input(self, event):
        ok, _ = self._founding()
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if ok:
                self.found_base()
        elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            clicked = self.found_buttons.handle(event, self._ui)
            if clicked == 0 and ok:
                self.found_base()
            elif clicked == 1:
                self._leave()

    def _handle_build_input(self, event):
        system = self.construction_system
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._over_panel(event.pos):                       # a click on the module list
                index = self.module_list.index_at(self._ui, event.pos)
                if index is not None:
                    system.set_selected_module_type(BUILDABLE[index])
                return
            if system.handle_input(event):                        # a click on the grid
                if system.construction_mode == ConstructionMode.PLACE:
                    label = BaseModule.MODULE_DEFINITIONS[system.selected_module_type].label
                    self.status = f"Building a {label}."
                else:
                    self.status = "Module removed."
            elif system.construction_mode == ConstructionMode.PLACE:
                missing = system.get_construction_info()["missing"]
                if missing:
                    self.status = "You are missing " + ", ".join(
                        "credits" if k == "credits" else transfer.commodity_name(k) for k in missing) + "."
                else:
                    self.status = "It does not fit there."
            return
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_UP, pygame.K_DOWN):
            step = -1 if event.key == pygame.K_UP else 1
            system.set_selected_module_type(BUILDABLE[(BUILDABLE.index(system.selected_module_type) + step) % len(BUILDABLE)])
            return
        system.handle_input(event)

    def _handle_storage_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked = self.storage_buttons.handle(event, self._ui)
            if clicked is not None:
                self.move_goods(1 if clicked < 2 else -1, everything=clicked in (1, 3))
                return
        if event.type == pygame.KEYDOWN:
            mods = getattr(event, "mod", pygame.key.get_mods())
            everything = bool(mods & pygame.KMOD_SHIFT)
            if event.key in (pygame.K_RIGHT, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.move_goods(1, everything)
                return
            if event.key == pygame.K_LEFT:
                self.move_goods(-1, everything)
                return
        if event.type == pygame.MOUSEMOTION:
            self.storage_buttons.handle(event, self._ui)
        self.storage_list.handle(event, self._ui, play_sounds=False)

    def _handle_tab_click(self, pos) -> bool:
        point = self._ui.to_px(pos)
        for (tab_id, _), rect in zip(TABS, self.tab_rects):
            if rect.collidepoint(point):
                self.selected_tab = tab_id
                return True
        return False
