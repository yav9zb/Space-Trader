"""The ending screen, shown when the campaign is completed. The text comes
from story.endings (built from the player's choices). From here the player
can keep flying, start New Game+ with a legacy perk, or go to the main menu.
"""

import pygame

try:
    from ..states.game_state import State, GameStates
    from ..legacy import PERKS, legacy
    from ..missions.rank_system import get_rank_name
    from ..story.endings import build_ending
    from ..ui.menu_style import (
        MenuBackground, draw_title, draw_panel, wrap_text,
        ACCENT_BLUE, ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM,
    )
except ImportError:
    from states.game_state import State, GameStates
    from legacy import PERKS, legacy
    from missions.rank_system import get_rank_name
    from story.endings import build_ending
    from ui.menu_style import (
        MenuBackground, draw_title, draw_panel, wrap_text,
        ACCENT_BLUE, ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM,
    )

ENDING_OPTIONS = ["Keep Flying", "Begin New Game+", "Main Menu"]


def stats_lines(game):
    """The run summary shown under the ending."""
    minutes, _ = divmod(int(getattr(game, "play_time", 0.0)), 60)
    hours, minutes = divmod(minutes, 60)
    manager = game.mission_manager
    story = game.story_state
    return [
        f"Rank: {get_rank_name(manager.reputation)}",
        f"Credits: {game.ship.credits:,}",
        f"Missions: {len(manager.completed_missions)}",
        f"Story missions: {len(story.completed_story_missions)} of 16",
        f"Time: {hours}h {minutes}m",
    ]


class VictoryState(State):
    PADDING = 28

    def __init__(self, game):
        super().__init__(game)
        self.ending = build_ending(game.story_state.flags)
        self.phase = "ending"            # "ending", then "perk" for New Game+
        self.selected = 0
        self.scroll = 0
        self.option_rects = []
        self.text_overflows = False
        self.background = MenuBackground()
        self.body_font = pygame.font.Font(None, 30)
        self.option_font = pygame.font.Font(None, 34)
        self.small_font = pygame.font.Font(None, 26)

    # Options ----------------------------------------------------------------

    def options(self):
        if self.phase == "perk":
            return [f"{name}: {desc}" for name, desc in PERKS.values()] + ["Back"]
        return list(ENDING_OPTIONS)

    def activate(self, index):
        if self.phase == "perk":
            perk_ids = list(PERKS)
            if index == len(perk_ids):           # Back
                self.phase, self.selected = "ending", 0
                return
            legacy.choose_perk(perk_ids[index])
            self.game.create_new_universe()
            self.game.change_state(GameStates.PLAYING)
            return

        choice = ENDING_OPTIONS[index]
        if choice == "Keep Flying":
            self.game.change_state(GameStates.PLAYING)
        elif choice == "Begin New Game+":
            self.phase, self.selected = "perk", 0
        else:
            self.game.change_state(GameStates.MAIN_MENU)

    # Input ------------------------------------------------------------------

    def handle_input(self, event):
        options = self.options()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.activate(self.selected)
            elif event.key == pygame.K_ESCAPE and self.phase == "perk":
                self.phase, self.selected = "ending", 0
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll += 3
            elif event.key == pygame.K_PAGEUP:
                self.scroll = max(0, self.scroll - 3)
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll - event.y)
        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    self.activate(i)
                    break

    # Rendering --------------------------------------------------------------

    def render(self, screen):
        self.background.draw(screen)
        width, height = screen.get_size()
        pad = self.PADDING

        title_bottom = draw_title(screen, self.ending.title.upper(),
                                  "Campaign complete" if self.phase == "ending"
                                  else "Choose a legacy perk", y=55)
        panel = pygame.Rect(40, title_bottom + 14, width - 80, height - title_bottom - 70)
        draw_panel(screen, panel)
        inner_w = panel.width - pad * 2

        # The options sit at the bottom of the panel; the text gets the rest
        options = self.options()
        option_lines = [wrap_text(f"{i + 1}. {text}", self.option_font, inner_w - 30)
                        for i, text in enumerate(options)]
        option_lh = self.option_font.get_linesize()
        options_h = sum(len(lines) * option_lh + 10 for lines in option_lines)
        options_top = panel.bottom - pad - options_h

        if self.phase == "ending":
            paragraphs = self.ending.paragraphs
            stats = wrap_text("  |  ".join(stats_lines(self.game)), self.small_font, inner_w)
        else:
            paragraphs = ["Pick one perk to carry into your next game. It applies once, to "
                          "the new game you are about to start. Your current save is not "
                          "touched."]
            stats = []

        stats_h = (len(stats) * self.small_font.get_linesize() + 12) if stats else 0
        body_bottom = options_top - stats_h - 10
        available = body_bottom - (panel.y + pad)

        # Largest text size that fits without scrolling; the smallest scrolls
        for size in (30, 26, 23):
            font = self.body_font if size == 30 else pygame.font.Font(None, size)
            lines = []
            for paragraph in paragraphs:
                lines.extend(wrap_text(paragraph, font, inner_w))
                lines.append("")
            lh = font.get_linesize()
            if len(lines) * lh <= available:
                break
        visible = max(1, available // lh)
        max_scroll = max(0, len(lines) - visible)
        self.scroll = min(self.scroll, max_scroll)
        self.text_overflows = max_scroll > 0

        y = panel.y + pad
        for line in lines[self.scroll:self.scroll + visible]:
            screen.blit(font.render(line, True, TEXT_PRIMARY), (panel.x + pad, y))
            y += lh
        if max_scroll > 0:
            hint = self.small_font.render("PGUP/PGDN: more", True, TEXT_DIM)
            screen.blit(hint, (panel.right - pad - hint.get_width(), body_bottom - 4))

        y = options_top - stats_h + 4
        for line in stats:
            screen.blit(self.small_font.render(line, True, TEXT_DIM), (panel.x + pad, y))
            y += self.small_font.get_linesize()

        self.option_rects = []
        self.selected = min(self.selected, len(options) - 1)
        y = options_top
        for index, wrapped in enumerate(option_lines):
            height_i = len(wrapped) * option_lh
            rect = pygame.Rect(panel.x + pad - 8, y - 4, inner_w + 16, height_i + 8)
            self.option_rects.append(rect)
            selected = index == self.selected
            if selected:
                pygame.draw.rect(screen, (40, 55, 90), rect, border_radius=6)
                pygame.draw.rect(screen, ACCENT_BLUE, rect, 2, border_radius=6)
                screen.blit(self.option_font.render(">", True, ACCENT_GOLD), (panel.x + pad, y))
            ly = y
            for line in wrapped:
                screen.blit(self.option_font.render(line, True, ACCENT_GOLD if selected else TEXT_PRIMARY),
                            (panel.x + pad + 30, ly))
                ly += option_lh
            y += height_i + 10

        footer = "UP/DOWN: choose | ENTER: select" + (" | ESC: back" if self.phase == "perk" else "")
        screen.blit(pygame.font.Font(None, 22).render(footer, True, TEXT_DIM), (40, height - 42))
