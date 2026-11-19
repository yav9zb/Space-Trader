"""Logbook screen: Story, Contacts and Factions pages, opened from the pause
menu. Content comes from story.logbook.build_pages; this just lays it out.
"""

import pygame

try:
    from ..states.game_state import State, GameStates
    from ..story.logbook import build_pages, TABS
    from ..ui.menu_style import (
        MenuBackground, draw_title, draw_panel, wrap_text,
        ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM,
    )
except ImportError:
    from states.game_state import State, GameStates
    from story.logbook import build_pages, TABS
    from ui.menu_style import (
        MenuBackground, draw_title, draw_panel, wrap_text,
        ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM,
    )

KIND_COLORS = {"heading": ACCENT_GOLD, "body": TEXT_PRIMARY, "dim": TEXT_DIM}


class LogbookState(State):
    PADDING = 24

    def __init__(self, game):
        super().__init__(game)
        self.tab = 0
        self.scroll = {name: 0 for name in TABS}
        self.pages = build_pages(game)
        self.background = MenuBackground()
        self.heading_font = pygame.font.Font(None, 34)
        self.body_font = pygame.font.Font(None, 28)
        self.tab_font = pygame.font.Font(None, 40)

    def handle_input(self, event):
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

    def _layout(self, name, inner_w):
        """Wrap a page into (font, color, text, height) rows."""
        rows = []
        for kind, text in self.pages[name]:
            if kind == "gap":
                rows.append((self.body_font, TEXT_DIM, "", self.body_font.get_linesize() // 2))
                continue
            font = self.heading_font if kind == "heading" else self.body_font
            for line in wrap_text(text, font, inner_w):
                rows.append((font, KIND_COLORS[kind], line, font.get_linesize()))
        return rows

    def render(self, screen):
        self.background.draw(screen)
        width, height = screen.get_size()
        title_bottom = draw_title(screen, "LOGBOOK", y=55)

        # Tabs
        x = 50
        tab_y = title_bottom + 12
        for i, name in enumerate(TABS):
            color = ACCENT_GOLD if i == self.tab else TEXT_DIM
            surface = self.tab_font.render(name, True, color)
            screen.blit(surface, (x, tab_y))
            if i == self.tab:
                pygame.draw.line(screen, ACCENT_GOLD, (x, tab_y + surface.get_height() + 2),
                                 (x + surface.get_width(), tab_y + surface.get_height() + 2), 2)
            x += surface.get_width() + 30

        panel = pygame.Rect(40, tab_y + 50, width - 80, height - tab_y - 50 - 60)
        draw_panel(screen, panel)

        pad = self.PADDING
        name = TABS[self.tab]
        rows = self._layout(name, panel.width - pad * 2)
        available = panel.height - pad * 2

        # Largest start row for which everything after it still fits
        max_scroll = len(rows)
        while max_scroll > 0 and sum(r[3] for r in rows[max_scroll - 1:]) <= available:
            max_scroll -= 1
        self.scroll[name] = min(self.scroll[name], max_scroll)

        y = panel.y + pad
        shown_to = self.scroll[name]
        for index in range(self.scroll[name], len(rows)):
            font, color, text, height = rows[index]
            if y + height > panel.bottom - pad:
                break
            if text:
                screen.blit(font.render(text, True, color), (panel.x + pad, y))
            y += height
            shown_to = index + 1

        footer = "LEFT/RIGHT: tab | UP/DOWN: scroll | ESC: back"
        if max_scroll > 0:
            footer += f"   (lines {self.scroll[name] + 1}-{shown_to} of {len(rows)})"
        screen.blit(pygame.font.Font(None, 22).render(footer, True, TEXT_DIM), (40, height - 42))
