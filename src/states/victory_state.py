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
    from ..ui import menu_kit
    from ..ui.menu_style import (
        MenuBackground, wrap_text,
        ACCENT_BLUE, ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM,
    )
except ImportError:
    from states.game_state import State, GameStates
    from legacy import PERKS, legacy
    from missions.rank_system import get_rank_name
    from story.endings import build_ending
    from ui import menu_kit
    from ui.menu_style import (
        MenuBackground, wrap_text,
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
    BODY_SIZES = (23, 20, 17)         # design units; the largest that fits without scrolling is used
    OPTION_ROLE = 24

    def __init__(self, game):
        super().__init__(game)
        self.ending = build_ending(game.story_state.flags)
        self.phase = "ending"            # "ending", then "perk" for New Game+
        self.selected = 0
        self.scroll = 0
        self.option_rects = []
        self.text_overflows = False
        self.background = MenuBackground()
        self._ui = menu_kit.Ui(menu_kit.BASE_SIZE)

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
            point = self._ui.to_px(event.pos)
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(point):
                    self.selected = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = self._ui.to_px(event.pos)
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(point):
                    self.selected = i
                    self.activate(i)
                    break

    # Rendering --------------------------------------------------------------

    def render(self, screen):
        ui = self._ui = menu_kit.ui_for(screen, self.game)
        self.background.draw(screen)
        pad = ui.px(28)

        top = ui.header(screen, self.ending.title.upper(),
                        "Campaign complete" if self.phase == "ending" else "Choose a legacy perk")
        footer_top = ui.footer(screen, "UP / DOWN: choose  |  ENTER: select" + ("  |  ESC: back" if self.phase == "perk" else ""))
        width = ui.content_width(1100)
        panel = pygame.Rect((ui.width - width) // 2, top, width, max(ui.px(120), footer_top - ui.px(6) - top))
        ui.panel(screen, panel)
        inner_w = panel.width - pad * 2

        # The options sit at the bottom of the panel; the text gets the rest
        options = self.options()
        option_font = ui.font(self.OPTION_ROLE)
        option_lh = option_font.get_linesize()
        gap = ui.px(10)
        marker = ui.px(30)
        option_lines = [wrap_text(f"{i + 1}. {text}", option_font, inner_w - marker) for i, text in enumerate(options)]
        options_h = sum(len(lines) * option_lh + gap for lines in option_lines)
        options_top = panel.bottom - pad - options_h

        small = ui.font("small")
        if self.phase == "ending":
            paragraphs = self.ending.paragraphs
            stats = wrap_text("  |  ".join(stats_lines(self.game)), small, inner_w)
        else:
            paragraphs = ["Pick one perk to carry into your next game. It applies once, to "
                          "the new game you are about to start. Your current save is not "
                          "touched."]
            stats = []

        stats_h = (len(stats) * small.get_linesize() + ui.px(12)) if stats else 0
        body_bottom = options_top - stats_h - ui.px(10)
        available = body_bottom - (panel.y + pad)

        # Largest text size that fits without scrolling; the smallest scrolls
        for units in self.BODY_SIZES:
            font = ui.font(units)
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
            ui.text(screen, "PGUP / PGDN: more", "tiny", TEXT_DIM, bottomright=(panel.right - pad, body_bottom))

        y = options_top - stats_h + ui.px(4)
        for line in stats:
            screen.blit(small.render(line, True, TEXT_DIM), (panel.x + pad, y))
            y += small.get_linesize()

        self.option_rects = []
        self.selected = min(self.selected, len(options) - 1)
        y = options_top
        for index, wrapped in enumerate(option_lines):
            height_i = len(wrapped) * option_lh
            rect = pygame.Rect(panel.x + pad - ui.px(8), y - ui.px(4), inner_w + ui.px(16), height_i + ui.px(8))
            self.option_rects.append(rect)
            selected = index == self.selected
            if selected:
                fill = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.rect(fill, (50, 70, 115, 200), fill.get_rect(), border_radius=ui.px(7))
                screen.blit(fill, rect.topleft)
                pygame.draw.rect(screen, ACCENT_BLUE, rect, max(1, ui.px(2)), border_radius=ui.px(7))
                size = max(4, option_lh // 3)
                cx, cy = panel.x + pad + size // 2, y + option_lh // 2
                pygame.draw.polygon(screen, ACCENT_GOLD, [(cx - size // 2, cy - size), (cx + size, cy), (cx - size // 2, cy + size)])
            ly = y
            for line in wrapped:
                screen.blit(option_font.render(line, True, ACCENT_GOLD if selected else TEXT_PRIMARY),
                            (panel.x + pad + marker, ly))
                ly += option_lh
            y += height_i + gap
