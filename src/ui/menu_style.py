"""Shared visual style for menu/screen states (Settings, Trading, Missions,
Upgrades, Save/Load) - a drifting starfield background, consistent title
treatment, and rounded accent-bordered panels, matching the polish already
applied to the main menu and HUD panels (src/ui/ui_theme.py).
"""

import pygame
from pygame import Vector2

ACCENT_BLUE = (80, 160, 255)
ACCENT_GOLD = (255, 220, 80)
TEXT_PRIMARY = (230, 235, 245)
TEXT_DIM = (140, 150, 170)
PANEL_BG = (10, 14, 30)
PANEL_RADIUS = 10


class MenuBackground:
    """Drifting starfield background, lazily sized to the screen. Each
    state that wants this background owns one instance (created once in
    __init__, drawn every render() call)."""

    def __init__(self):
        self.starfield = None
        self.start_ticks = pygame.time.get_ticks()

    def draw(self, screen, bg_color=(2, 2, 16)):
        from ..entities.starfield import StarField

        screen.fill(bg_color)
        if self.starfield is None or self.starfield.screen_width != screen.get_width():
            self.starfield = StarField(120, screen.get_width(), screen.get_height())
        drift = (pygame.time.get_ticks() - self.start_ticks) * 0.015
        self.starfield.draw(screen, Vector2(drift, drift * 0.35))


def draw_title(screen, title, subtitle=None, y=70):
    """Consistent screen title with an accent underline, matching the main menu.
    Returns the y-coordinate just below the title block, for laying out content."""
    title_font = pygame.font.Font(None, 64)
    title_surface = title_font.render(title, True, TEXT_PRIMARY)
    title_rect = title_surface.get_rect(center=(screen.get_width() // 2, y))
    screen.blit(title_surface, title_rect)

    pygame.draw.line(
        screen, ACCENT_BLUE,
        (title_rect.left, title_rect.bottom + 6),
        (title_rect.right, title_rect.bottom + 6), 2
    )

    bottom = title_rect.bottom + 10
    if subtitle:
        subtitle_font = pygame.font.Font(None, 26)
        subtitle_surface = subtitle_font.render(subtitle, True, TEXT_DIM)
        subtitle_rect = subtitle_surface.get_rect(center=(screen.get_width() // 2, bottom + 16))
        screen.blit(subtitle_surface, subtitle_rect)
        bottom = subtitle_rect.bottom

    return bottom


def draw_panel(screen, rect, border_color=ACCENT_BLUE, bg_alpha=190, border_width=2):
    """Rounded, semi-transparent panel with an accent border."""
    panel_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surface, (*PANEL_BG, bg_alpha), panel_surface.get_rect(), border_radius=PANEL_RADIUS)
    screen.blit(panel_surface, rect.topleft)
    pygame.draw.rect(screen, border_color, rect, border_width, border_radius=PANEL_RADIUS)
