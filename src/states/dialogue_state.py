"""Dialogue screen: a thin UI wrapper around story.dialogue.DialogueSession.

Shows the current node's text (wrapped, pageable) and the available choices
(wrapped, scrolled to keep the selection visible). All logic - requirement
checks, effects, flags - lives in the session so it can be tested headlessly.
"""

import pygame

try:
    from ..states.game_state import State, GameStates
    from ..story.dialogue import DialogueSession
    from ..ui.menu_style import (
        MenuBackground, draw_title, draw_panel, wrap_text,
        ACCENT_BLUE, ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM,
    )
except ImportError:
    from states.game_state import State, GameStates
    from story.dialogue import DialogueSession
    from ui.menu_style import (
        MenuBackground, draw_title, draw_panel, wrap_text,
        ACCENT_BLUE, ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM,
    )


class DialogueState(State):
    PADDING = 24

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
        self.body_font = pygame.font.Font(None, 30)
        self.choice_font = pygame.font.Font(None, 28)

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
            for index, rect in self.choice_rects:
                if rect.collidepoint(event.pos):
                    self.selected = index
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in self.choice_rects:
                if rect.collidepoint(event.pos):
                    self._choose(index)
                    break

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
        self.background.draw(screen)
        width, height = screen.get_size()
        node = self.session.current
        if node is None:
            return

        title_bottom = draw_title(screen, node.speaker.upper(), y=55)
        panel = pygame.Rect(40, title_bottom + 10, width - 80, height - title_bottom - 70)
        draw_panel(screen, panel)

        pad = self.PADDING
        inner_w = panel.width - pad * 2
        body_lh = self.body_font.get_linesize()

        # Body text, pageable. Takes only the height it needs (up to 55% of
        # the panel) so short lines leave the rest for choices.
        lines = wrap_text(self.session.current_text(), self.body_font, inner_w)
        visible_lines = max(1, min(len(lines), int(panel.height * 0.55) // body_lh))
        body_h = visible_lines * body_lh
        max_scroll = max(0, len(lines) - visible_lines)
        self.body_scroll = min(self.body_scroll, max_scroll)
        y = panel.y + pad
        for line in lines[self.body_scroll:self.body_scroll + visible_lines]:
            screen.blit(self.body_font.render(line, True, TEXT_PRIMARY), (panel.x + pad, y))
            y += body_lh
        if max_scroll > 0:
            hint = "PGUP/PGDN: more text"
            hint_surface = pygame.font.Font(None, 20).render(hint, True, TEXT_DIM)
            screen.blit(hint_surface, (panel.right - pad - hint_surface.get_width(), panel.y + body_h + pad // 2))

        # Choices, scrolled so the selection stays visible
        choices_top = panel.y + body_h + pad + 14
        choices_bottom = panel.bottom - pad // 2
        self._render_choices(screen, panel, choices_top, choices_bottom, inner_w, pad)

        footer = "UP/DOWN or 1-9: choose | ENTER: select | ESC: leave"
        footer_surface = pygame.font.Font(None, 22).render(footer, True, TEXT_DIM)
        screen.blit(footer_surface, (40, height - 42))

        if self.choice_range:
            first, last, total = self.choice_range
            if total > last - first + 1:
                more = pygame.font.Font(None, 22).render(
                    f"Choices {first}-{last} of {total}", True, TEXT_DIM)
                screen.blit(more, (width - 40 - more.get_width(), height - 42))

    def _render_choices(self, screen, panel, top, bottom, inner_w, pad):
        self.choice_rects = []
        self.choice_range = None
        choices = self.session.visible_choices()
        lh = self.choice_font.get_linesize()
        gap = 8
        marker_w = self.choice_font.size("> ")[0]

        if not choices:
            prompt = self.choice_font.render("[ENTER] Continue", True, ACCENT_GOLD)
            screen.blit(prompt, (panel.x + pad, top))
            return

        self.selected = min(self.selected, len(choices) - 1)
        wrapped = [
            wrap_text(f"{i + 1}. {choice.text}", self.choice_font, inner_w - marker_w)
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
            rect = pygame.Rect(panel.x + pad - 8, y - 4, inner_w + 16, heights[index] - gap + 8)
            self.choice_rects.append((index, rect))
            is_selected = index == self.selected
            if is_selected:
                pygame.draw.rect(screen, (40, 55, 90), rect, border_radius=6)
                pygame.draw.rect(screen, ACCENT_BLUE, rect, 2, border_radius=6)
                screen.blit(self.choice_font.render(">", True, ACCENT_GOLD), (panel.x + pad, y))
            color = ACCENT_GOLD if is_selected else TEXT_PRIMARY
            ly = y
            for line in wrapped[index]:
                screen.blit(self.choice_font.render(line, True, color), (panel.x + pad + marker_w, ly))
                ly += lh
            y += heights[index]

        if self.choice_rects:
            self.choice_range = (self.choice_rects[0][0] + 1, self.choice_rects[-1][0] + 1, len(choices))
