"""Logbook screen: Story, Contacts and Factions pages, opened from the pause
menu. Content comes from story.logbook.build_pages; this just lays it out
with the menu kit, so it fits any window and scrolls when a page is long.
"""

import pygame

try:
    from ..states.game_state import State, GameStates
    from ..story.logbook import build_pages, TABS
    from ..ui import menu_kit
    from ..ui.menu_style import MenuBackground, ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM
except ImportError:
    from states.game_state import State, GameStates
    from story.logbook import build_pages, TABS
    from ui import menu_kit
    from ui.menu_style import MenuBackground, ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM

KIND_COLORS = {"heading": ACCENT_GOLD, "body": TEXT_PRIMARY, "dim": TEXT_DIM}
KIND_ROLES = {"heading": 24, "body": "body", "dim": "body"}


class LogbookState(State):
    def __init__(self, game):
        super().__init__(game)
        self.tab = 0
        self.scroll = {name: 0 for name in TABS}
        self.pages = build_pages(game)
        self.background = MenuBackground()
        self.tab_rects = []
        self._ui = menu_kit.Ui(menu_kit.BASE_SIZE)

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = self._ui.to_px(event.pos)
            for index, rect in enumerate(self.tab_rects):
                if rect.collidepoint(point):
                    self.tab = index
            return
        if event.type == pygame.MOUSEWHEEL:
            name = TABS[self.tab]
            self.scroll[name] = max(0, self.scroll[name] - event.y * 2)
            return
        if event.type != pygame.KEYDOWN:
            return
        name = TABS[self.tab]
        if event.key == pygame.K_ESCAPE:
            self.game.change_state(GameStates.PAUSED)
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self.tab = (self.tab - 1) % len(TABS)
        elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_TAB):
            self.tab = (self.tab + 1) % len(TABS)
        elif event.key == pygame.K_UP:
            self.scroll[name] = max(0, self.scroll[name] - 1)
        elif event.key == pygame.K_DOWN:
            self.scroll[name] += 1
        elif event.key == pygame.K_PAGEUP:
            self.scroll[name] = max(0, self.scroll[name] - 8)
        elif event.key == pygame.K_PAGEDOWN:
            self.scroll[name] += 8

    def _lines(self, ui, name, width):
        items = []
        for kind, text in self.pages[name]:
            if kind == "gap":
                items.append(("", "body", TEXT_DIM, 0))
            else:
                items.append((text, KIND_ROLES[kind], KIND_COLORS[kind], 0))
        return menu_kit.build_lines(ui, items, width)

    def render(self, screen):
        ui = self._ui = menu_kit.ui_for(screen, self.game)
        self.background.draw(screen)
        top = ui.header(screen, "LOGBOOK")
        width = ui.content_width(1200)
        left = (ui.width - width) // 2

        # Tabs
        font = ui.font("heading")
        x = left
        self.tab_rects = []
        for index, name in enumerate(TABS):
            selected = index == self.tab
            surface = font.render(name, True, ACCENT_GOLD if selected else TEXT_DIM)
            rect = surface.get_rect(topleft=(x, top))
            screen.blit(surface, rect)
            self.tab_rects.append(rect.inflate(ui.px(16), ui.px(8)))
            if selected:
                pygame.draw.line(screen, ACCENT_GOLD, (rect.left, rect.bottom + ui.px(2)),
                                 (rect.right, rect.bottom + ui.px(2)), max(1, ui.px(2)))
            x = rect.right + ui.px(34)
        top += font.get_linesize() + ui.px(12)

        name = TABS[self.tab]
        footer_hint = "LEFT / RIGHT or click: tab  |  UP / DOWN or wheel: scroll  |  ESC: back"
        footer_top = ui.footer(screen, footer_hint)
        panel = pygame.Rect(left, top, width, max(ui.px(80), footer_top - ui.px(6) - top))
        ui.panel(screen, panel)
        area = panel.inflate(-ui.px(40), -ui.px(32))
        lines = self._lines(ui, name, area.width - ui.px(16))
        self.scroll[name], last, limit = menu_kit.draw_lines(ui, screen, area, lines, self.scroll[name])
        if limit > 0:
            ui.text(screen, f"lines {self.scroll[name] + 1}-{last} of {len(lines)}", "tiny", TEXT_DIM,
                    bottomright=(panel.right - ui.px(14), panel.bottom - ui.px(5)))
