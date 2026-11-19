"""Dialogue screen: a thin UI wrapper around story.dialogue.DialogueSession.

Shows the current node's text (wrapped, pageable) and the available choices
(wrapped, scrolled to keep the selection visible). All logic - requirement
checks, effects, flags - lives in the session so it can be tested headlessly.
"""

import pygame

try:
    from ..states.game_state import State, GameStates
    from ..story.dialogue import DialogueSession
    from ..ui import menu_kit
    from ..ui.menu_style import (
        MenuBackground, wrap_text,
        ACCENT_BLUE, ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM,
    )
except ImportError:
    from states.game_state import State, GameStates
    from story.dialogue import DialogueSession
    from ui import menu_kit
    from ui.menu_style import (
        MenuBackground, wrap_text,
        ACCENT_BLUE, ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM,
    )


class DialogueState(State):
    BODY_ROLE = 23
    CHOICE_ROLE = 21

    def __init__(self, game, start_id, nodes=None, return_state=None):
        super().__init__(game)
        if nodes is None:
            from ..story.dialogue_data import NODES
            nodes = NODES
        self.session = DialogueSession(nodes, start_id, game)
        self.return_state = return_state or GameStates.PLAYING
        self.selected = 0
        self.body_scroll = 0
        self.choice_scroll = 0
        self.choice_rects = []
        self.choice_range = None
        self.background = MenuBackground()
        self._ui = menu_kit.Ui(menu_kit.BASE_SIZE)

    # Input ----------------------------------------------------------------

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._leave()
                return
            choices = self.session.visible_choices()
            if not choices:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._leave()
                return
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(choices)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(choices)
            elif event.key == pygame.K_PAGEUP:
                self.body_scroll = max(0, self.body_scroll - 3)
            elif event.key == pygame.K_PAGEDOWN:
                self.body_scroll += 3
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._choose(self.selected)
            elif pygame.K_1 <= event.key <= pygame.K_9:
                index = event.key - pygame.K_1
                if index < len(choices):
                    self._choose(index)
        elif event.type == pygame.MOUSEMOTION:
            point = self._ui.to_px(event.pos)
            for index, rect in self.choice_rects:
                if rect.collidepoint(point):
                    self.selected = index
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = self._ui.to_px(event.pos)
            for index, rect in self.choice_rects:
                if rect.collidepoint(point):
                    self._choose(index)
                    break
        elif event.type == pygame.MOUSEWHEEL:
            self.body_scroll = max(0, self.body_scroll - event.y)

    def _choose(self, index):
        if not self.session.choose(index):
            self._leave()
            return
        self.selected = 0
        self.body_scroll = 0
        self.choice_scroll = 0

    def _leave(self):
        # An effect may already have moved the game on (the ending, or a scene
        # that opened another conversation); do not drag it back.
        current = getattr(self.game, "current_state", GameStates.DIALOGUE)
        registered = getattr(self.game, "states", {}).get(GameStates.DIALOGUE, self)
        if current != GameStates.DIALOGUE or registered is not self:
            return
        self.game.change_state(self.return_state)

    # Rendering -------------------------------------------------------------

    def render(self, screen):
        ui = self._ui = menu_kit.ui_for(screen, self.game)
        self.background.draw(screen)
        node = self.session.current
        if node is None:
            return

        top = ui.header(screen, node.speaker.upper())
        footer_top = ui.footer(screen, "UP / DOWN or 1-9: choose  |  ENTER: select  |  ESC: leave")
        width = ui.content_width(1100)
        panel = pygame.Rect((ui.width - width) // 2, top, width, max(ui.px(120), footer_top - ui.px(6) - top))
        ui.panel(screen, panel)

        pad = ui.px(24)
        inner_w = panel.width - pad * 2
        body_font = ui.font(self.BODY_ROLE)
        body_lh = body_font.get_linesize()

        # Body text, pageable. Takes only the height it needs (up to 55% of
        # the panel) so short lines leave the rest for choices.
        lines = wrap_text(self.session.current_text(), body_font, inner_w)
        visible_lines = max(1, min(len(lines), int(panel.height * 0.55) // body_lh))
        body_h = visible_lines * body_lh
        max_scroll = max(0, len(lines) - visible_lines)
        self.body_scroll = min(self.body_scroll, max_scroll)
        y = panel.y + pad
        for line in lines[self.body_scroll:self.body_scroll + visible_lines]:
            screen.blit(body_font.render(line, True, TEXT_PRIMARY), (panel.x + pad, y))
            y += body_lh
        if max_scroll > 0:
            ui.text(screen, "PGUP / PGDN: more text", "tiny", TEXT_DIM,
                    topright=(panel.right - pad, panel.y + body_h + pad // 2))

        # Choices, scrolled so the selection stays visible
        choices_top = panel.y + body_h + pad + ui.px(24)
        choices_bottom = panel.bottom - pad // 2
        self._render_choices(ui, screen, panel, choices_top, choices_bottom, inner_w, pad)

        if self.choice_range:
            first, last, total = self.choice_range
            if total > last - first + 1:
                ui.text(screen, f"Choices {first}-{last} of {total}", "tiny", TEXT_DIM,
                        bottomright=(panel.right - ui.px(14), panel.bottom - ui.px(4)))

    def _render_choices(self, ui, screen, panel, top, bottom, inner_w, pad):
        self.choice_rects = []
        self.choice_range = None
        choices = self.session.visible_choices()
        font = ui.font(self.CHOICE_ROLE)
        lh = font.get_linesize()
        gap = ui.px(8)
        marker_w = ui.px(22)

        if not choices:
            ui.text(screen, "[ENTER] Continue", self.CHOICE_ROLE, ACCENT_GOLD, topleft=(panel.x + pad, top))
            return

        self.selected = min(self.selected, len(choices) - 1)
        wrapped = [
            wrap_text(f"{i + 1}. {choice.text}", font, inner_w - marker_w)
            for i, choice in enumerate(choices)
        ]
        heights = [len(w) * lh + gap for w in wrapped]

        # Move the window start until the selected choice fits
        self.choice_scroll = min(self.choice_scroll, self.selected)
        while (sum(heights[self.choice_scroll:self.selected + 1]) > bottom - top
               and self.choice_scroll < self.selected):
            self.choice_scroll += 1

        y = top
        for index in range(self.choice_scroll, len(choices)):
            if y + heights[index] - gap > bottom:
                break
            rect = pygame.Rect(panel.x + pad - ui.px(8), y - ui.px(4), inner_w + ui.px(16), heights[index] - gap + ui.px(8))
            self.choice_rects.append((index, rect))
            is_selected = index == self.selected
            if is_selected:
                fill = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.rect(fill, (50, 70, 115, 200), fill.get_rect(), border_radius=ui.px(7))
                screen.blit(fill, rect.topleft)
                pygame.draw.rect(screen, ACCENT_BLUE, rect, max(1, ui.px(2)), border_radius=ui.px(7))
                size = max(4, lh // 3)
                cx, cy = panel.x + pad + size // 2, y + lh // 2
                pygame.draw.polygon(screen, ACCENT_GOLD, [(cx - size // 2, cy - size), (cx + size, cy), (cx - size // 2, cy + size)])
            color = ACCENT_GOLD if is_selected else TEXT_PRIMARY
            ly = y
            for line in wrapped[index]:
                screen.blit(font.render(line, True, color), (panel.x + pad + marker_w, ly))
                ly += lh
            y += heights[index]

        if self.choice_rects:
            self.choice_range = (self.choice_rects[0][0] + 1, self.choice_rects[-1][0] + 1, len(choices))
