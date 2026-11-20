"""
Base Construction State - the base building interface (opened with B).

Laid out with the menu kit, like the other screens: panels, tabs and text are
measured from the window and drawn at the screen's real pixels. The base itself
(its grid and the construction preview) is world drawing, so it is drawn at
point size and scaled up behind the panels, as flight is.
"""

import pygame
from pygame import Vector2
from typing import Optional

try:
    from ..states.game_state import State, GameStates
    from ..base_building.base_manager import base_manager
    from ..base_building.construction_system import ConstructionSystem, ConstructionMode
    from ..base_building.resource_production import ProductionSystem
    from ..ui import menu_kit
    from ..ui.menu_style import MenuBackground, ACCENT_GOLD, ACCENT_BLUE, TEXT_PRIMARY, TEXT_DIM
except ImportError:
    from states.game_state import State, GameStates
    from base_building.base_manager import base_manager
    from base_building.construction_system import ConstructionSystem, ConstructionMode
    from base_building.resource_production import ProductionSystem
    from ui import menu_kit
    from ui.menu_style import MenuBackground, ACCENT_GOLD, ACCENT_BLUE, TEXT_PRIMARY, TEXT_DIM

TABS = [("construction", "Construction"), ("production", "Production"), ("management", "Management")]

GOOD = (120, 230, 150)
WARN = (255, 215, 90)
BAD = (255, 120, 120)

HELP_SECTIONS = [
    ("Construction controls", [
        "1-7: select a module type",
        "Left click: place or remove a module",
        "P: place mode   R: remove mode",
        "Tab: show or hide the grid",
        "Mouse wheel: zoom",
    ]),
    ("Module types", [
        "1 Habitat (crew quarters)",
        "2 Power generator",
        "3 Storage (resources)",
        "4 Refinery (processes materials)",
        "5 Factory (advanced production)",
        "6 Turret (defense)",
        "7 Trade hub (trading)",
    ]),
    ("Tips", [
        "Build power generators first",
        "Monitor resource flows",
        "Plan production chains",
    ]),
]


class BaseConstructionState(State):
    """Game state for base construction and management."""

    def __init__(self, game, base_id: str = None, previous_state=None):
        super().__init__(game)
        self.previous_state = previous_state or GameStates.PLAYING

        # Initialize construction system
        self.construction_system = ConstructionSystem(base_manager)
        self.production_system = ProductionSystem()

        # With no base given, work on the active one, else the nearest to the ship
        self.base_id = base_id or self._default_base_id()

        # UI state
        self.show_base_info = True
        self.show_help = False
        self.selected_tab = "construction"  # construction, production, management

        # View of the base: zoom, and the mouse position in the world
        self.zoom_level = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 2.0
        self.mouse_world_pos = Vector2(0, 0)

        # Layout, set by render and used by clicks and tests
        self.tab_rects = []
        self.help_overflows = False
        self.panel_overflows = False
        self.background = MenuBackground()
        self._ui = menu_kit.Ui(menu_kit.BASE_SIZE)
        self._world = None

        # Activate construction for the base
        if self.base_id:
            self.construction_system.activate_construction(self.base_id)

    # Which base -----------------------------------------------------------------------

    def _ship_position(self) -> Vector2:
        ship = getattr(self.game, "ship", None)
        return Vector2(ship.position) if ship is not None else Vector2(0, 0)

    def _default_base_id(self) -> Optional[str]:
        active = base_manager.get_active_base()
        if active is not None and base_manager.active_base_id in base_manager.bases:
            return base_manager.active_base_id
        nearest = base_manager.get_nearest_base(self._ship_position())
        if nearest:
            return nearest[0]
        return next(iter(base_manager.bases), None)

    def _base(self):
        return base_manager.get_base(self.base_id) if self.base_id else None

    # Update -----------------------------------------------------------------------------

    def update(self, delta_time):
        """Update construction state."""
        base_manager.update(delta_time, self._ship_position())
        self.production_system.update_production(base_manager.bases, delta_time)

        self._update_mouse_world_position()

        if self.construction_system.is_construction_active:
            self.construction_system.update_mouse_position(self.mouse_world_pos)
            self.construction_system.process_build_queue()

    def _view_points(self):
        """The window size in points: what the mouse and the world are measured in."""
        return Vector2(self.game.screen.get_size())

    def _camera_offset(self) -> Vector2:
        """World position of the view's top-left corner: the base sits in the
        middle of the window, whatever the zoom."""
        base = self._base()
        centre = base.position if base is not None else Vector2(0, 0)
        return centre - self._view_points() / (2 * self.zoom_level)

    def _update_mouse_world_position(self):
        """The world position under the mouse."""
        self.mouse_world_pos = self._camera_offset() + Vector2(pygame.mouse.get_pos()) / self.zoom_level

    # Drawing ----------------------------------------------------------------------------

    def render(self, screen):
        """Render the construction interface."""
        ui = self._ui = menu_kit.ui_for(screen, self.game)
        base = self._base()
        if base is not None:
            self._draw_world(ui, screen)
        else:
            self.background.draw(screen)

        top = ui.header(screen, "BASE CONSTRUCTION", subtitle=base.name if base is not None else None)
        footer_top = ui.footer(screen, self._footer_hint(base))
        self.panel_overflows = False

        if base is None:
            self.tab_rects = []
            self._draw_empty(ui, screen, top, footer_top)
        else:
            top = self._draw_tabs(ui, screen, top)
            self._draw_panels(ui, screen, base, top, footer_top)

        if self.show_help:
            self._draw_help(ui, screen)

    def _footer_hint(self, base):
        if base is None:
            return "ESC: back"
        return "Q / W / E or click: tab  |  F1: help  |  F2: base panel  |  TAB: grid  |  1-7: module  |  ESC: leave"

    def _draw_world(self, ui, screen):
        """The base and the construction grid, drawn in points at the current
        zoom and scaled to the screen behind the panels."""
        view = self._view_points() / self.zoom_level
        size = (max(1, int(view.x)), max(1, int(view.y)))
        if self._world is None or self._world.get_size() != size:
            self._world = pygame.Surface(size)
        world = self._world
        world.fill((14, 16, 30))

        camera_offset = self._camera_offset()
        base_manager.draw(world, camera_offset, self._ship_position())
        if self.construction_system.is_construction_active:
            self.construction_system.draw_world(world, camera_offset)

        if world.get_size() == screen.get_size():
            screen.blit(world, (0, 0))
        else:
            pygame.transform.smoothscale(world, screen.get_size(), screen)

    def _draw_empty(self, ui, screen, top, footer_top):
        width = min(ui.content_width(), ui.px(760))
        lines = [
            ("No base to build on", "heading", ACCENT_GOLD),
            ("Base construction is still being connected to the rest of the game, and nothing in a run creates a base yet.", "body", TEXT_PRIMARY),
            ("Claimed outposts earn credits, but they are separate from this screen for now.", "body", TEXT_DIM),
        ]
        inner = width - ui.px(48)
        wrapped = []
        for text, role, color in lines:
            wrapped += [(line, role, color) for line in ui.wrap(text, role, inner)]
            wrapped.append(("", "gap", color))
        height = sum(ui.px(10) if role == "gap" else ui.line_height(role) for _, role, _ in wrapped) + ui.px(48)
        panel = pygame.Rect(0, 0, width, height)
        panel.center = (ui.width // 2, (top + footer_top) // 2)
        ui.panel(screen, panel)
        y = panel.top + ui.px(24)
        for line, role, color in wrapped:
            if role == "gap":
                y += ui.px(10)
                continue
            y = ui.text(screen, line, role, color, topleft=(panel.left + ui.px(24), y)).bottom

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
        side = min(ui.px(420), ui.width // 3)
        margin = ui.margin()

        if self.show_base_info:
            info = pygame.Rect(margin, top, side, bottom - top)
            ui.panel(screen, info)
            self._draw_base_info(ui, screen, base, info.inflate(-ui.px(28), -ui.px(24)))

        panel = pygame.Rect(ui.width - margin - side, top, side, bottom - top)
        ui.panel(screen, panel)
        area = panel.inflate(-ui.px(28), -ui.px(24))
        if self.selected_tab == "construction":
            self._draw_construction(ui, screen, area)
        elif self.selected_tab == "production":
            self._draw_production(ui, screen, base, area)
        else:
            self._draw_management(ui, screen, base, area)

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
        generation, consumption = base.power_generation, base.power_consumption
        powered = generation >= consumption
        items = [
            ("title", base.name),
            ("kv", "Position", f"({base.position.x:.0f}, {base.position.y:.0f})", TEXT_PRIMARY),
            ("kv", "Power", f"{generation} / {consumption}", GOOD if powered else WARN),
        ]
        if consumption > 0:
            items.append(("bar", min(1.0, generation / consumption), GOOD if powered else WARN))
        items += [
            ("kv", "Crew", f"{base.crew_count} / {base.crew_capacity}", TEXT_PRIMARY),
            ("kv", "Modules", len(set(base.modules.values())), TEXT_PRIMARY),
            ("kv", "Defense", base.defense_rating, TEXT_PRIMARY),
            ("gap",),
            ("title", "Resources"),
        ]
        resources = sorted(base.stored_resources.items(), key=lambda entry: entry[1], reverse=True)[:6]
        if resources:
            items += [("kv", name, amount, TEXT_PRIMARY) for name, amount in resources]
        else:
            items.append(("text", "Nothing stored yet.", TEXT_DIM))
        self.panel_overflows |= self._draw_items(ui, screen, area, items)

    def _draw_construction(self, ui, screen, area):
        system = self.construction_system
        items = [("title", "Construction"),
                 ("kv", "Mode", system.construction_mode.value.title(), TEXT_PRIMARY)]
        if system.construction_mode == ConstructionMode.PLACE:
            info = system.get_construction_info()
            name = system.selected_module_type.value.replace("_", " ").title()
            affordable = info.get("can_afford", False)
            items += [("gap",), ("title", name), ("text", "Cost", TEXT_DIM)]
            for resource, amount in info.get("cost", {}).items():
                items.append(("kv", f"  {resource}", amount, GOOD if affordable else BAD))
            items += [("gap",), ("text", "Gives", TEXT_DIM)]
            for label, key in (("Power generated", "power_generation"), ("Power used", "power_consumption"),
                               ("Storage", "storage_capacity"), ("Crew", "crew_capacity"),
                               ("Defense", "defense_rating")):
                if info.get(key, 0) > 0:
                    items.append(("kv", f"  {label}", info[key], TEXT_PRIMARY))
        elif system.construction_mode == ConstructionMode.REMOVE:
            items += [("gap",), ("text", "Click a module to remove it.", TEXT_PRIMARY)]
        items += [("gap",), ("text", "Left click: build or remove.  P: place.  R: remove.  1-7: module type.", TEXT_DIM)]
        self.panel_overflows |= self._draw_items(ui, screen, area, items)

    def _draw_production(self, ui, screen, base, area):
        status = self.production_system.get_production_status(base)
        items = [("title", "Production"),
                 ("kv", "Active", status["active_productions"], GOOD),
                 ("kv", "Idle", status["idle_modules"], WARN), ("gap",)]
        if not status["module_status"]:
            items.append(("text", "No production modules yet. Build a refinery or a factory.", TEXT_DIM))
        for number, module_status in enumerate(status["module_status"].values(), 1):
            if module_status["status"] == "producing":
                progress = module_status["progress"]
                items += [("kv", f"Module {number}", f"Producing {progress:.0%}", GOOD), ("bar", progress, GOOD)]
            else:
                items.append(("kv", f"Module {number}", "Idle", WARN))
        self.panel_overflows |= self._draw_items(ui, screen, area, items)

    def _draw_management(self, ui, screen, base, area):
        items = [("title", "Management")]
        suggestions = self.production_system.optimize_production_chain(base)
        if suggestions:
            items.append(("text", "Suggestions", TEXT_DIM))
            items += [("text", f"- {suggestion}", TEXT_PRIMARY) for suggestion in suggestions[:8]]
        else:
            items.append(("text", "Base is operating efficiently.", GOOD))
        self.panel_overflows |= self._draw_items(ui, screen, area, items)

    def _draw_help(self, ui, screen):
        veil = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 150))
        screen.blit(veil, (0, 0))

        width = min(ui.width - 2 * ui.margin(), ui.px(760))
        height = min(ui.height - 2 * ui.margin(), ui.px(640))
        panel = pygame.Rect(0, 0, width, height)
        panel.center = (ui.width // 2, ui.height // 2)
        ui.panel(screen, panel, border=ACCENT_GOLD, alpha=235)
        ui.text(screen, "Base construction help", "heading", TEXT_PRIMARY, midtop=(panel.centerx, panel.top + ui.px(14)))

        area = pygame.Rect(panel.left + ui.px(24), panel.top + ui.px(64), width - ui.px(48), height - ui.px(100))
        items = []
        for title, lines in HELP_SECTIONS:
            items.append(("title", title))
            items += [("text", line, TEXT_PRIMARY) for line in lines]
            items.append(("gap",))
        self.help_overflows = self._draw_items(ui, screen, area, items)
        ui.text(screen, "F1 or ESC: close", "small", TEXT_DIM, midbottom=(panel.centerx, panel.bottom - ui.px(10)))

    # Input ------------------------------------------------------------------------------

    def _leave(self):
        self.construction_system.deactivate_construction()
        self.game.change_state(self.previous_state)

    def handle_input(self, event):
        """Handle input events."""
        # Leaving and the tabs come first, so a click on a tab never builds
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.show_help:
                self.show_help = False
            else:
                self._leave()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.show_help:
            if self._handle_tab_click(event.pos):
                return

        # Then the construction system
        if not self.show_help and self.construction_system.handle_input(event):
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1:
                self.show_help = not self.show_help
            elif event.key == pygame.K_F2:
                self.show_base_info = not self.show_base_info
            elif event.key == pygame.K_q:
                self.selected_tab = "construction"
            elif event.key == pygame.K_w:
                self.selected_tab = "production"
            elif event.key == pygame.K_e:
                self.selected_tab = "management"

        elif event.type == pygame.MOUSEWHEEL:
            zoom_factor = 1.1 if event.y > 0 else 1.0 / 1.1
            self.zoom_level = max(self.min_zoom, min(self.max_zoom, self.zoom_level * zoom_factor))

    def _handle_tab_click(self, pos) -> bool:
        """Handle a click on the tab row (pos is in window points)."""
        point = self._ui.to_px(pos)
        for (tab_id, _), rect in zip(TABS, self.tab_rects):
            if rect.collidepoint(point):
                self.selected_tab = tab_id
                return True
        return False
