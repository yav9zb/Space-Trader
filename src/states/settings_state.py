"""The settings screens, laid out with the menu kit: a category menu, and one
page per category made of rows (label, value, description) that adjust with
the arrow keys or the mouse. Controls and Help also show a reference panel.
"""

from dataclasses import dataclass
from typing import Callable, List, Optional

import pygame

from ..input.control_schemes import control_scheme_manager
from ..ui import menu_kit
from ..ui.menu_style import ACCENT_BLUE, ACCENT_GOLD, MenuBackground, TEXT_DIM, TEXT_PRIMARY
from .game_state import GameStates, State

DISABLED = (100, 105, 120)
VALUE_COLOR = (150, 205, 255)
WARN = (255, 100, 100)

CATEGORY_PAGES = {
    "Camera": "camera", "Display": "display", "Controls": "controls", "Docking": "docking", "Audio": "audio",
    "Difficulty": "difficulty", "Dev View": "dev", "Help": "help",
}
PAGE_TITLES = {
    "camera": "Camera Settings", "display": "Display Settings", "controls": "Control Settings", "docking": "Docking Settings",
    "audio": "Audio Settings", "difficulty": "Difficulty Settings", "dev": "Dev View Settings",
    "help": "Help & Controls",
}
PAGE_HINTS = {
    "camera": "UP / DOWN choose  |  LEFT / RIGHT change  |  ESC back",
    "display": "UP / DOWN choose  |  LEFT / RIGHT change  |  ESC back",
    "controls": "UP / DOWN choose  |  LEFT / RIGHT or ENTER change the scheme  |  ESC back",
    "docking": "UP / DOWN choose  |  LEFT / RIGHT or ENTER change  |  ESC back",
    "audio": "UP / DOWN choose  |  LEFT / RIGHT adjust volume  |  ESC back",
    "difficulty": "UP / DOWN choose  |  LEFT / RIGHT change  |  ESC back",
    "dev": "UP / DOWN choose  |  LEFT / RIGHT or ENTER toggle  |  ESC back",
    "help": "UP / DOWN choose  |  ESC back",
}
DIFFICULTY_TEXT = {
    "peaceful": "No enemies, reduced hazards - explore and trade in safety",
    "easy": "Fewer enemies, lighter damage - a gentler galaxy",
    "normal": "The intended balance",
    "hard": "More frequent, tougher enemies and higher damage",
    "extreme": "Maximum danger - ship destruction ends the game permanently",
}
HELP_CONTROLS = [
    "MOVEMENT:", "Arrow Keys / WASD - Move ship", "Shift - Boost/Thrust", "",
    "NAVIGATION:", "TAB - Open/Close large map", "M - Open/Close large map (alt)", "ESC - Pause game", "",
    "DOCKING:", "D - Manual dock when near station", "X - Undock from station",
]
HELP_KEYBINDS = [
    "GENERAL KEYBINDS:", "F4 - Toggle developer view", "F11 - Toggle fullscreen", "F12 - Toggle FPS display", "",
    "DOCKED ACTIONS:", "T - Open trading interface", "U - Open ship upgrades", "M - Open mission board", "",
    "MAP CONTROLS:", "Mouse Wheel - Zoom in/out", "Right Click + Drag - Pan map", "Left Click - Select location",
    "HOME - Reset map view", "+/- - Zoom in/out (keyboard)",
]


@dataclass
class Row:
    id: str
    label: str
    value: str = ""
    desc: str = ""
    kind: str = "cycle"            # cycle, slider, toggle or back
    enabled: bool = True
    bar: Optional[float] = None    # 0..1, drawn for volume sliders
    warn: bool = False


class SettingsState(State):
    def __init__(self, game, previous_state=None):
        super().__init__(game)
        from ..settings import game_settings
        self.settings = game_settings
        self.title = "Settings"
        self.categories = ["Camera", "Display", "Controls", "Audio", "Difficulty", "Dev View", "Help", "Back"]
        self.selected_category = 0

        # Track where settings was accessed from to return properly
        self.previous_state = previous_state or GameStates.MAIN_MENU

        self.page: Optional[str] = None
        self.selected = {page: 0 for page in PAGE_TITLES}

        self.background = MenuBackground()
        self.category_menu = menu_kit.MenuList(self.categories)
        self.list = menu_kit.RowList()
        self._ui = menu_kit.Ui(menu_kit.BASE_SIZE)
        self._rows: List[Row] = []

    # Compatibility with the code that asks "which page is open" ------------------------

    @property
    def viewing_camera(self):
        return self.page == "camera"

    @property
    def viewing_display(self):
        return self.page == "display"

    @property
    def viewing_controls(self):
        return self.page == "controls"

    @property
    def viewing_audio(self):
        return self.page == "audio"

    @property
    def viewing_difficulty(self):
        return self.page == "difficulty"

    @property
    def viewing_dev(self):
        return self.page == "dev"

    @property
    def viewing_help(self):
        return self.page == "help"

    # Rows -------------------------------------------------------------------------------

    def rows(self, page: str) -> List[Row]:
        from ..settings import CameraMode, DisplayMode
        s = self.settings
        back = Row("back", "Back", kind="back")
        if page == "camera":
            return [
                Row("camera_mode", "Camera Mode", s.camera_mode.value, s.get_camera_description()),
                Row("smoothing", "Smoothing",
                    f"{s.camera_smoothing:.2f}" + ("" if s.camera_mode == CameraMode.SMOOTH else " (N/A)"),
                    kind="slider", enabled=s.camera_mode == CameraMode.SMOOTH),
                Row("deadzone", "Deadzone",
                    f"{s.camera_deadzone_radius}px" + ("" if s.camera_mode == CameraMode.DEADZONE else " (N/A)"),
                    kind="slider", enabled=s.camera_mode == CameraMode.DEADZONE),
                back]
        if page == "display":
            windowed = s.display_mode == DisplayMode.WINDOWED
            return [
                Row("resolution", "Resolution", f"{s.window_width}x{s.window_height}",
                    "" if windowed else "Matches the desktop in this display mode", enabled=windowed),
                Row("display_mode", "Display Mode", s.display_mode.value),
                Row("hud_scale", "HUD Scale", f"{s.hud_scale:.2f}x",
                    "Scales the flight HUD panels' text and size", kind="slider"),
                back]
        if page == "controls":
            info = control_scheme_manager.get_scheme_info()
            return [Row("control_scheme", "Control Scheme", info["name"], info["description"]), back]
        if page == "docking":
            level = s.docking_speed
            from ..docking.docking_manager import DOCKING_SPEEDS
            return [
                Row("auto_dock", "Auto-Docking", "ON" if s.auto_dock else "OFF",
                    "Dock by yourself when you are close and slow enough. Off: you press the dock key.",
                    kind="toggle"),
                Row("docking_speed", "Docking Speed Limit", f"{level.title()} ({DOCKING_SPEEDS[level]:.0f})",
                    "How fast you may still be going when you dock. Careful is strict, Relaxed forgives."),
                back]
        if page == "audio":
            return [Row(key, label, f"{int(getattr(s, attr) * 100)}%", kind="slider", bar=getattr(s, attr))
                    for key, label, attr in (("master", "Master Volume", "master_volume"),
                                             ("sfx", "SFX Volume", "sfx_volume"),
                                             ("music", "Music Volume", "music_volume"))] + [back]
        if page == "difficulty":
            from ..difficulty.difficulty_manager import difficulty_manager
            level = difficulty_manager.current_difficulty.value
            return [Row("difficulty", "Difficulty", level.upper(), DIFFICULTY_TEXT.get(level, ""),
                        warn=level == "extreme"), back]
        if page == "dev":
            dev_on = s.dev_view_enabled
            flags = (("dev_fps", "Show FPS", s.dev_show_fps), ("dev_ship", "Show Ship Position", s.dev_show_ship_pos),
                     ("dev_dock", "Show Docking", s.dev_show_docking), ("dev_stations", "Show Stations", s.dev_show_stations),
                     ("dev_camera", "Show Camera", s.dev_show_camera))
            rows = [Row("dev_enable", "Enable Dev View", "ON" if dev_on else "OFF", kind="toggle")]
            rows += [Row(key, label, "ON" if value else "OFF", kind="toggle", enabled=dev_on) for key, label, value in flags]
            return rows + [back]
        if page == "help":
            return [Row("help_controls", "Controls", kind="slider"), Row("help_keybinds", "Keybinds", kind="slider"), back]
        return []

    # Drawing -----------------------------------------------------------------------------

    def render(self, screen):
        ui = self._ui = menu_kit.ui_for(screen, self.game)
        self.background.draw(screen)
        if self.page is None:
            self._render_categories(ui, screen)
        else:
            self._render_page(ui, screen)

    def _render_categories(self, ui, screen):
        top = ui.header(screen, "SETTINGS")
        footer_top = ui.footer(screen, "UP / DOWN choose  |  ENTER opens  |  ESC back")
        self.category_menu.selected = self.selected_category
        area = pygame.Rect(0, top, ui.width, max(ui.px(120), footer_top - top))
        self.category_menu.layout(ui, area, row_units=58)
        self.category_menu.draw(ui, screen)

    def _render_page(self, ui, screen):
        page = self.page
        top = ui.header(screen, "SETTINGS", subtitle=PAGE_TITLES[page])
        footer_top = ui.footer(screen, PAGE_HINTS[page])
        self._rows = rows = self.rows(page)
        self.selected[page] = max(0, min(self.selected[page], len(rows) - 1))
        has_detail = page in ("controls", "help")
        bottom = footer_top - ui.px(8)

        if has_detail:
            (rows_panel, rows_inner), (detail_panel, detail_inner) = ui.split_panels(
                screen, top, bottom, [PAGE_TITLES[page].split(" ")[0].upper(), "REFERENCE"], weights=(1, 1) if page == "controls" else (2, 3), widest_units=1300)
        else:
            width = min(ui.px(820), ui.width - 2 * ui.margin())
            needed = len(rows) * ui.px(66) + ui.px(32)
            height = min(bottom - top, needed)
            rows_panel = pygame.Rect((ui.width - width) // 2, top + max(0, (bottom - top - height) // 3), width, height)
            ui.panel(screen, rows_panel)
            rows_inner = rows_panel.inflate(-ui.px(28), -ui.px(28))
            detail_panel = detail_inner = None

        self.list.set_count(len(rows))
        self.list.selected = self.selected[page]
        self.list.layout(ui, rows_inner, row_units=62)
        self.list.draw_chrome(ui, screen)
        for index, rect in self.list.rects.items():
            self._draw_row(ui, screen, rect, rows[index], index == self.selected[page])

        if page == "dev" and self.settings.dev_view_enabled:
            ui.text(screen, "Press F4 in-game to toggle Dev View", "small", (150, 255, 150),
                    midtop=(rows_panel.centerx, rows_panel.bottom + ui.px(8)))
        if page == "controls":
            self._draw_reference(ui, screen, detail_inner, self._control_lines())
        elif page == "help":
            lines = HELP_CONTROLS if self.selected[page] == 0 else HELP_KEYBINDS if self.selected[page] == 1 else []
            self._draw_reference(ui, screen, detail_inner, [(text, "") for text in lines])

    def _draw_row(self, ui, screen, rect, row: Row, selected: bool):
        pad = ui.px(18)
        color = ACCENT_GOLD if selected else TEXT_PRIMARY
        if not row.enabled:
            color = DISABLED
        if row.kind == "back":
            ui.text(screen, row.label, "body", color, center=rect.center)
            return
        label_y = rect.y + ui.px(8) if row.desc else rect.centery
        anchor = {"topleft": (rect.x + pad, label_y)} if row.desc else {"midleft": (rect.x + pad, label_y)}
        ui.text(screen, row.label, 22, color, max_width=rect.width * 4 // 10 - pad, **anchor)
        if row.desc:
            ui.text(screen, row.desc, "small", TEXT_DIM, max_width=rect.width - 2 * pad,
                    bottomleft=(rect.x + pad, rect.bottom - ui.px(8)))
        if not row.value:
            return
        value_color = WARN if row.warn else (VALUE_COLOR if row.enabled else DISABLED)
        arrows = selected and row.enabled
        right = rect.right - pad - (ui.px(18) if arrows else 0)
        value_rect = ui.text(screen, row.value, 22, value_color, max_width=rect.width * 55 // 100 - pad,
                             midright=(right, rect.centery - (ui.px(8) if row.desc else 0)))
        left_edge = value_rect.left
        if row.bar is not None:
            from ..ui import gfx
            bar = pygame.Rect(0, 0, ui.px(150), ui.px(10))
            bar.midright = (value_rect.left - ui.px(14), value_rect.centery)
            gfx.draw_bar(screen, bar, row.bar, (100, 200, 255))
            left_edge = bar.left
        if arrows:
            size, y = ui.px(6), value_rect.centery
            x = left_edge - ui.px(10)
            pygame.draw.polygon(screen, ACCENT_GOLD, [(x - size, y), (x, y - size), (x, y + size)])
            x = value_rect.right + ui.px(10)
            pygame.draw.polygon(screen, ACCENT_GOLD, [(x + size, y), (x, y - size), (x, y + size)])

    def _control_lines(self):
        lines = []
        for section, controls in control_scheme_manager.get_controls_help().items():
            lines.append((section, "head"))
            lines.extend((f"{key}: {description}", "") for key, description in controls.items())
            lines.append(("", ""))
        return lines

    def _draw_reference(self, ui, screen, area, lines):
        """Reference text flowed into as many columns as it needs."""
        if not lines:
            return
        height = ui.line_height("small") + ui.px(3)
        per_column = max(1, area.height // height)
        columns = max(1, -(-len(lines) // per_column))
        columns = min(columns, 3)
        col_width = area.width // columns
        for index, (text, kind) in enumerate(lines[:per_column * columns]):
            column, slot = divmod(index, per_column)
            if not text:
                continue
            heading = kind == "head" or text.endswith(":")
            ui.text(screen, text, "small", (200, 255, 200) if heading else (230, 235, 245),
                    max_width=col_width - ui.px(12), topleft=(area.x + column * col_width, area.y + slot * height))

    # Input ---------------------------------------------------------------------------------

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            self._handle_key(event)
        elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEWHEEL):
            self._handle_mouse(event)

    def _handle_key(self, event):
        if event.key == pygame.K_ESCAPE:
            if self.page is not None:
                self.page = None
            else:
                self.game.change_state(self.previous_state)
            return
        if self.page is None:
            self._handle_main_input(event)
            return
        rows = self.rows(self.page)
        index = self.selected[self.page]
        if event.key == pygame.K_UP:
            self.selected[self.page] = (index - 1) % len(rows)
        elif event.key == pygame.K_DOWN:
            self.selected[self.page] = (index + 1) % len(rows)
        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            self._change(rows[index], -1 if event.key == pygame.K_LEFT else 1)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            row = rows[index]
            if row.kind == "back":
                self.page = None
            elif row.kind in ("cycle", "toggle"):
                self._change(row, 1)

    def _handle_main_input(self, event):
        """Handle input for the category menu"""
        self.category_menu.selected = self.selected_category
        chosen = self.category_menu.handle(event, self._ui, play_sounds=False)
        self.selected_category = self.category_menu.selected
        if chosen is not None:
            self._select_main_option()

    def _select_main_option(self):
        """Open the selected category (or leave settings)"""
        category = self.categories[self.selected_category]
        if category == "Back":
            self.game.change_state(self.previous_state)
        else:
            self.page = CATEGORY_PAGES[category]
            self.selected[self.page] = 0

    def _handle_mouse(self, event):
        if self.page is None:
            self.category_menu.selected = self.selected_category
            chosen = self.category_menu.handle(event, self._ui)
            self.selected_category = self.category_menu.selected
            if chosen is not None:
                self._select_main_option()
            return
        rows = self.rows(self.page)
        if event.type == pygame.MOUSEWHEEL:
            self.selected[self.page] = max(0, min(len(rows) - 1, self.selected[self.page] - event.y))
            return
        index = self.list.index_at(self._ui, event.pos)
        if index is None or index >= len(rows):
            return
        if event.type == pygame.MOUSEMOTION:
            self.selected[self.page] = index
            return
        if event.button != 1:
            return
        self.selected[self.page] = index
        row = rows[index]
        if row.kind == "back":
            self.page = None
            return
        rect = self.list.rects[index]
        self._change(row, -1 if self._ui.to_px(event.pos)[0] < rect.centerx and row.kind in ("cycle", "slider") else 1)

    # Changing values --------------------------------------------------------------------------

    def _change(self, row: Row, direction: int):
        """Apply a change to the setting a row stands for (direction -1 or 1)."""
        if row.kind == "back" or not row.enabled:
            return
        from ..settings import CameraMode, DisplayMode
        s = self.settings
        rid = row.id
        if rid == "camera_mode":
            modes = list(CameraMode)
            s.camera_mode = modes[(modes.index(s.camera_mode) + direction) % len(modes)]
            s.save()
        elif rid == "smoothing":
            s.camera_smoothing = max(0.01, min(1.0, s.camera_smoothing + direction * 0.05))
            s.save()
        elif rid == "deadzone":
            s.camera_deadzone_radius = max(10, min(200, s.camera_deadzone_radius + direction * 10))
            s.save()
        elif rid == "resolution":
            width, height = s.next_resolution(direction)
            s.set_resolution(width, height)
            s.save()
            self.game._update_display()
        elif rid == "display_mode":
            modes = list(DisplayMode)
            s.display_mode = modes[(modes.index(s.display_mode) + direction) % len(modes)]
            s.save()
            self.game._update_display()
        elif rid == "hud_scale":
            s.hud_scale = max(0.75, min(1.75, round(s.hud_scale + direction * 0.1, 2)))
            s.save()
            self.game._update_display()
        elif rid == "auto_dock":
            s.auto_dock = not s.auto_dock
            s.save()
            self.game.docking_manager.apply_settings(s)
        elif rid == "docking_speed":
            levels = ["careful", "standard", "relaxed"]
            s.docking_speed = levels[(levels.index(s.docking_speed) + direction) % len(levels)]
            s.save()
            self.game.docking_manager.apply_settings(s)
        elif rid == "control_scheme":
            self._change_control_scheme(direction)
        elif rid in ("master", "sfx", "music"):
            self._adjust_volume({"master": "master_volume", "sfx": "sfx_volume", "music": "music_volume"}[rid], direction)
        elif rid == "difficulty":
            self._change_difficulty(direction)
        elif rid.startswith("dev_"):
            attr = {"dev_enable": "dev_view_enabled", "dev_fps": "dev_show_fps", "dev_ship": "dev_show_ship_pos",
                    "dev_dock": "dev_show_docking", "dev_stations": "dev_show_stations",
                    "dev_camera": "dev_show_camera"}[rid]
            setattr(s, attr, not getattr(s, attr))
            s.save()

    def _change_control_scheme(self, direction=1):
        """Cycle through available control schemes"""
        from ..input.control_schemes import ControlScheme
        schemes = list(ControlScheme)
        current = schemes.index(control_scheme_manager.get_current_scheme())
        control_scheme_manager.set_scheme(schemes[(current + direction) % len(schemes)])

    def _change_difficulty(self, direction):
        """Cycle through available difficulty levels"""
        from ..difficulty.difficulty_manager import difficulty_manager, DifficultyLevel
        levels = list(DifficultyLevel)
        current = levels.index(difficulty_manager.current_difficulty)
        difficulty_manager.set_difficulty(levels[(current + direction) % len(levels)])

    def _adjust_volume(self, attr, direction):
        from ..audio.sound_manager import sound_manager
        value = max(0.0, min(1.0, getattr(self.settings, attr) + direction * 0.05))
        setattr(self.settings, attr, round(value, 2))
        self.settings.save()
        sound_manager.apply_volumes()
        if attr != "music_volume":
            sound_manager.play("ui_navigate")
