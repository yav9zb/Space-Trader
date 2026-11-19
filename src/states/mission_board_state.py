"""The mission board: a list of missions with tabs for Available and Active,
and a details view that scrolls when a mission's text is long. Laid out with
the menu kit, so it fits any window and draws at the window's real pixels.
"""

import pygame

from ..ui import menu_kit
from ..ui.menu_style import ACCENT_BLUE, ACCENT_GOLD, MenuBackground, TEXT_DIM, TEXT_PRIMARY
from .game_state import GameStates, State

GOOD = (120, 230, 140)
BAD = (255, 90, 90)
INFO = (150, 200, 255)


class MissionBoardState(State):
    def __init__(self, game, station=None):
        super().__init__(game)
        from ..missions.mission_manager import mission_manager
        self.mission_manager = mission_manager
        self.station = station
        self.title = "Mission Board"
        self.selected_mission_index = 0
        self.viewing_details = False
        self.current_tab = "available"  # "available", "active"
        self.message = ""
        self.message_timer = 0.0
        self.detail_scroll = 0
        self._clicked_once = None          # a second click on the same card opens its details

        # Generate missions for this station if it's the first visit
        if self.station:
            self.mission_manager.generate_missions_for_station(self.station, self.game)

        # Get missions for this station
        self.refresh_missions()

        self.background = MenuBackground()
        self.list = menu_kit.RowList()
        self.list_buttons = menu_kit.ButtonBar(["Details  (ENTER)", "Accept  (A)", "Switch tab  (TAB)", "Leave  (ESC)"])
        self.detail_buttons = menu_kit.ButtonBar(["Accept  (A)", "Abandon  (X)", "Back  (ESC)"])
        self.tab_rects = {}
        self._ui = menu_kit.Ui(menu_kit.BASE_SIZE)
        self._detail_rows_visible = 1
        self._detail_line_count = 0

    def refresh_missions(self):
        """Refresh the mission lists."""
        if self.station:
            self.available_missions = self.mission_manager.get_available_missions_for_station(self.station.name)
        else:
            self.available_missions = self.mission_manager.available_missions

        self.active_missions = self.mission_manager.active_missions

        # Reset selection if needed
        if self.current_tab == "available" and self.selected_mission_index >= len(self.available_missions):
            self.selected_mission_index = max(0, len(self.available_missions) - 1)
        elif self.current_tab == "active" and self.selected_mission_index >= len(self.active_missions):
            self.selected_mission_index = max(0, len(self.active_missions) - 1)

    @property
    def missions(self):
        return self.available_missions if self.current_tab == "available" else self.active_missions

    def update(self, delta_time):
        if self.message_timer > 0:
            self.message_timer -= delta_time
            if self.message_timer <= 0:
                self.message = ""

    # Drawing ---------------------------------------------------------------------------------

    def render(self, screen):
        ui = self._ui = menu_kit.ui_for(screen, self.game)
        self.background.draw(screen)

        station_name = self.station.name if self.station else "Mission Central"
        top = ui.header(screen, "MISSION BOARD", subtitle=station_name)
        width = ui.content_width(1300)
        left = (ui.width - width) // 2

        top = self._draw_tabs_and_standing(ui, screen, left, width, top)

        footer_text = ("UP / DOWN scroll  |  A accept  |  X abandon (active)  |  ESC back to list" if self.viewing_details
                       else "TAB switch tabs  |  UP / DOWN navigate  |  ENTER details  |  A accept  |  ESC back")
        footer_top = ui.footer(screen, footer_text)
        buttons = pygame.Rect(0, footer_top - ui.px(40), ui.width, ui.px(40))
        panel = pygame.Rect(left, top, width, max(ui.px(80), buttons.top - ui.px(8) - top))
        ui.panel(screen, panel)

        if self.viewing_details:
            self._render_details(ui, screen, panel.inflate(-ui.px(28), -ui.px(24)))
            self.detail_buttons.enabled = [self.current_tab == "available" and bool(self.missions),
                                           self.current_tab == "active" and bool(self.missions), True]
            bar = self.detail_buttons
        else:
            self._render_list(ui, screen, panel)
            self.list_buttons.enabled = [bool(self.missions), self.current_tab == "available" and bool(self.missions),
                                         True, True]
            bar = self.list_buttons
        bar.layout(ui, buttons)
        bar.draw(ui, screen)

        if self.message:
            ui.message(screen, self.message, ACCENT_GOLD if "success" in self.message.lower() else (255, 120, 120))

    def _draw_tabs_and_standing(self, ui, screen, left, width, top):
        """Tabs, reputation and per-faction standing. Returns the y where the panel starts."""
        from ..missions.rank_system import get_rank_name
        font = ui.font("heading")
        x = left
        self.tab_rects = {}
        for key, label, count in (("available", "Available", len(self.available_missions)),
                                  ("active", "Active", len(self.active_missions))):
            selected = self.current_tab == key
            surface = font.render(f"{label} ({count})", True, ACCENT_GOLD if selected else TEXT_DIM)
            rect = surface.get_rect(topleft=(x, top))
            screen.blit(surface, rect)
            self.tab_rects[key] = rect.inflate(ui.px(16), ui.px(8))
            if selected:
                pygame.draw.line(screen, ACCENT_GOLD, (rect.left, rect.bottom + ui.px(2)),
                                 (rect.right, rect.bottom + ui.px(2)), max(1, ui.px(2)))
            x = rect.right + ui.px(34)
        reputation = self.mission_manager.reputation
        rep_rect = ui.text(screen, f"Reputation: {reputation} ({get_rank_name(reputation)})", "small", ACCENT_GOLD,
                           max_width=width - (x - left), topright=(left + width, top + ui.px(4)))
        y = top + font.get_linesize() + ui.px(8)

        # Who specifically trusts (or resents) the player
        standing_x = left
        for faction_name, value in self.mission_manager.faction_standing.items():
            color = GOOD if value > 0 else BAD if value < 0 else TEXT_DIM
            text = f"{faction_name}: {value:+d}"
            surface = ui.font("small").render(text, True, color)
            if standing_x + surface.get_width() > left + width:
                break
            screen.blit(surface, (standing_x, y))
            standing_x += surface.get_width() + ui.px(22)
        return y + ui.line_height("small") + ui.px(8)

    def _render_list(self, ui, screen, panel):
        missions = self.missions
        inner = panel.inflate(-ui.px(24), -ui.px(24))
        if not missions:
            ui.text(screen, "No missions available", "body", TEXT_DIM, topleft=(inner.x + ui.px(4), inner.y + ui.px(4)))
            self.list.set_count(0)
            self.list.rects = {}
            return
        self.list.set_count(len(missions))
        self.list.selected = min(self.selected_mission_index, len(missions) - 1)
        room = pygame.Rect(inner)
        room.height -= ui.px(16)                                     # room for the "1-4 of 9" counter
        self.list.layout(ui, room, row_units=78)
        self.list.draw_chrome(ui, screen)
        for index, rect in self.list.rects.items():
            self._draw_card(ui, screen, rect, missions[index], index == self.selected_mission_index)
        counter = self.list.counter()
        if counter:
            ui.text(screen, counter, "tiny", TEXT_DIM, bottomright=(panel.right - ui.px(16), panel.bottom - ui.px(8)))

    def _draw_card(self, ui, screen, rect, mission, selected):
        pad = ui.px(16)
        inner_width = rect.width - 2 * pad
        time_remaining = mission.get_formatted_time_remaining()
        right_x = rect.right - pad
        title_max = inner_width
        if time_remaining != "No time limit":
            color = BAD if "EXPIRED" in time_remaining else ACCENT_GOLD
            time_rect = ui.text(screen, f"Time: {time_remaining}", "small", color, topright=(right_x, rect.y + ui.px(9)))
            title_max = inner_width - time_rect.width - ui.px(16)
        ui.text(screen, mission.title, 22, ACCENT_GOLD if selected else TEXT_PRIMARY, max_width=title_max,
                topleft=(rect.x + pad, rect.y + ui.px(6)))

        reward = ui.text(screen, f"Reward: {mission.reward.credits:,} credits", "small", GOOD,
                         midright=(right_x, rect.y + ui.px(40)))
        ui.text(screen, f"{mission.mission_type.value} | {mission.priority.value}", "small",
                self._get_priority_color(mission.priority), max_width=inner_width - reward.width - ui.px(16),
                midleft=(rect.x + pad, rect.y + ui.px(40)))

        line = ""
        if self.current_tab == "active":
            line = f"Status: {mission.status.value} ({mission.completion_percentage:.0%})"
        elif getattr(mission, "destination_station_id", None):
            coords = self.mission_manager.get_station_coordinates(mission.destination_station_id, self.game.universe.stations)
            if coords:
                line = f"Destination: {mission.destination_station_id} - {coords}"
        if line:
            ui.text(screen, line, "small", INFO, max_width=inner_width, midleft=(rect.x + pad, rect.bottom - ui.px(15)))

    def _detail_lines(self, ui, mission, width):
        """The mission's full description as (text, role, color, indent) lines, wrapped to width."""
        lines = []

        def add(text, role="body", color=TEXT_PRIMARY, indent=0):
            if text == "":
                lines.append(("", role, color, 0))
                return
            for piece in ui.wrap(text, role, width - ui.px(indent)):
                lines.append((piece, role, color, indent))

        add(mission.title, 26)
        lines.append(("", "small", TEXT_DIM, 0))
        add(f"Type: {mission.mission_type.value}")
        add(f"Priority: {mission.priority.value}", color=self._get_priority_color(mission.priority))
        add(f"Status: {mission.status.value}")
        add(f"Reward: {mission.reward.credits:,} credits", color=GOOD)
        remaining = mission.get_formatted_time_remaining()
        add(f"Time Limit: {remaining}", color=BAD if "EXPIRED" in remaining else TEXT_PRIMARY)
        add("")
        add("Description:", color=ACCENT_GOLD)
        add(mission.description, "body", (215, 220, 232), 12)
        add("")

        stations = self.game.universe.stations
        for attr, label in (("origin_station_id", "Origin"), ("destination_station_id", "Destination")):
            station_id = getattr(mission, attr, None)
            if station_id:
                coords = self.mission_manager.get_station_coordinates(station_id, stations)
                if coords:
                    add(f"{label}: {station_id} - {coords}")
        # Trading contracts name a single trading station
        if getattr(mission, "station_id", None) and not hasattr(mission, "origin_station_id"):
            coords = self.mission_manager.get_station_coordinates(mission.station_id, stations)
            if coords:
                add(f"Trading Station: {mission.station_id} - {coords}")

        add("")
        add("Objectives:", color=ACCENT_GOLD)
        for objective in mission.objectives:
            add(f"[{'X' if objective.completed else ' '}] {objective.description}", "small",
                GOOD if objective.completed else TEXT_PRIMARY, 16)

        req = mission.requirements
        if req.min_reputation > 0 or req.min_cargo_capacity > 0:
            add("")
            add("Requirements:", color=ACCENT_GOLD)
            if req.min_reputation > 0:
                text = f"Minimum Reputation: {req.min_reputation}"
                # min_faction_standing is set equal to min_reputation at generation time
                # (see mission_manager.py), so the faction is noted inline rather than
                # repeating the same number on a second line
                if req.min_faction_standing > 0:
                    faction = self.mission_manager.resolve_mission_faction(mission, self.game)
                    if faction:
                        text += f" (also requires {faction} standing)"
                add(text, "small", TEXT_PRIMARY, 16)
            if req.min_cargo_capacity > 0:
                add(f"Minimum Cargo Space: {req.min_cargo_capacity}", "small", TEXT_PRIMARY, 16)
        return lines

    def _render_details(self, ui, screen, area):
        missions = self.missions
        if not missions or self.selected_mission_index >= len(missions):
            return
        lines = self._detail_lines(ui, missions[self.selected_mission_index], area.width - ui.px(16))
        heights = [ui.line_height(role) + ui.px(3) for _, role, _, _ in lines]
        # How many lines fit from the current scroll position
        self._detail_line_count = len(lines)
        max_scroll = self._max_scroll(lines, heights, area.height)
        self.detail_scroll = max(0, min(self.detail_scroll, max_scroll))
        y = area.top
        shown = 0
        for index in range(self.detail_scroll, len(lines)):
            text, role, color, indent = lines[index]
            if y + heights[index] > area.bottom + ui.px(2):
                break
            if text:
                ui.text(screen, text, role, color, topleft=(area.x + ui.px(indent), y))
            y += heights[index]
            shown += 1
        self._detail_rows_visible = max(1, shown)
        if self.detail_scroll > 0:
            self._scroll_arrow(ui, screen, area.right, area.top, up=True)
        if self.detail_scroll < max_scroll:
            self._scroll_arrow(ui, screen, area.right, area.bottom, up=False)

    def _max_scroll(self, lines, heights, available):
        """The largest first line that still lets the last line be visible."""
        total = 0
        start = len(lines)
        while start > 0 and total + heights[start - 1] <= available:
            start -= 1
            total += heights[start]
        return start

    @staticmethod
    def _scroll_arrow(ui, screen, x, y, up):
        size = ui.px(6)
        tip = -size if up else size
        pygame.draw.polygon(screen, TEXT_DIM, [(x - size * 2, y), (x - size * 2 + size * 2, y), (x - size, y + tip)])

    def _get_priority_color(self, priority):
        """Get color for mission priority."""
        from ..missions.mission_types import MissionPriority

        priority_colors = {
            MissionPriority.LOW: (150, 150, 150),
            MissionPriority.MEDIUM: (255, 255, 255),
            MissionPriority.HIGH: (255, 200, 0),
            MissionPriority.URGENT: (255, 0, 0)
        }
        return priority_colors.get(priority, (255, 255, 255))

    # Input -------------------------------------------------------------------------------------

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.viewing_details:
                    self.viewing_details = False
                else:
                    self.game.change_state(GameStates.PLAYING)
            elif not self.viewing_details:
                self._handle_list_input(event)
            else:
                self._handle_details_input(event)
        elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEWHEEL):
            self._handle_mouse(event)

    def _switch_tab(self, tab=None):
        self._clicked_once = None
        self.current_tab = tab or ("active" if self.current_tab == "available" else "available")
        self.selected_mission_index = 0
        self.detail_scroll = 0
        self.refresh_missions()

    def _handle_list_input(self, event):
        """Handle input when viewing mission list."""
        missions = self.missions

        if event.key == pygame.K_TAB:
            self._switch_tab()
        elif event.key == pygame.K_UP and missions:
            self.selected_mission_index = (self.selected_mission_index - 1) % len(missions)
        elif event.key == pygame.K_DOWN and missions:
            self.selected_mission_index = (self.selected_mission_index + 1) % len(missions)
        elif event.key == pygame.K_RETURN and missions:
            self._open_details()
        elif event.key == pygame.K_a and missions:
            self._accept_mission()

    def _open_details(self):
        self.viewing_details = True
        self.detail_scroll = 0

    def _handle_details_input(self, event):
        """Handle input when viewing mission details."""
        if event.key == pygame.K_a and self.missions:
            self._accept_mission()
        elif event.key == pygame.K_x and self.current_tab == "active" and self.missions:
            self._abandon_mission()
        elif event.key == pygame.K_UP:
            self.detail_scroll = max(0, self.detail_scroll - 1)
        elif event.key == pygame.K_DOWN:
            self.detail_scroll += 1                                      # clamped when drawn
        elif event.key == pygame.K_PAGEUP:
            self.detail_scroll = max(0, self.detail_scroll - self._detail_rows_visible)
        elif event.key == pygame.K_PAGEDOWN:
            self.detail_scroll += self._detail_rows_visible

    def _handle_mouse(self, event):
        ui = self._ui
        if self.viewing_details:
            if event.type == pygame.MOUSEWHEEL:
                self.detail_scroll = max(0, self.detail_scroll - event.y * 2)
                return
            pressed = self.detail_buttons.handle(event, ui)
            if pressed == 0:
                self._accept_mission()
            elif pressed == 1:
                self._abandon_mission()
            elif pressed == 2:
                self.viewing_details = False
            return

        if event.type == pygame.MOUSEWHEEL:
            if self.missions:
                self.selected_mission_index = max(0, min(len(self.missions) - 1, self.selected_mission_index - event.y))
            return
        pressed = self.list_buttons.handle(event, ui)
        if pressed is not None:
            if pressed == 0 and self.missions:
                self._open_details()
            elif pressed == 1:
                self._accept_mission()
            elif pressed == 2:
                self._switch_tab()
            elif pressed == 3:
                self.game.change_state(GameStates.PLAYING)
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = ui.to_px(event.pos)
            for tab, rect in self.tab_rects.items():
                if rect.collidepoint(point):
                    if tab != self.current_tab:
                        self._switch_tab(tab)
                    return
            index = self.list.index_at(ui, event.pos)
            if index is not None and index < len(self.missions):
                if index == self._clicked_once:
                    self._open_details()
                self._clicked_once = index
                self.selected_mission_index = index

    # Actions -------------------------------------------------------------------------------------

    def _accept_mission(self):
        """Accept the currently selected mission."""
        missions = self.missions

        if not missions or self.selected_mission_index >= len(missions):
            return

        mission = missions[self.selected_mission_index]

        if self.current_tab != "available":
            self.message = "Can only accept available missions"
            self.message_timer = 2.0
            return

        success, message = self.mission_manager.accept_mission(mission.id, self.game.ship, self.game)

        self.message = message
        self.message_timer = 2.0

        if success:
            self.refresh_missions()
            # Switch to active tab to show the accepted mission
            self.current_tab = "active"
            self.selected_mission_index = 0
            self.detail_scroll = 0

    def _abandon_mission(self):
        """Abandon the currently selected active mission."""
        if self.current_tab != "active" or not self.active_missions:
            return

        if self.selected_mission_index >= len(self.active_missions):
            return

        mission = self.active_missions[self.selected_mission_index]
        success, message = self.mission_manager.abandon_mission(mission.id, self.game.ship, self.game)

        self.message = message
        self.message_timer = 2.0

        if success:
            self.refresh_missions()
