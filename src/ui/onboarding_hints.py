"""Lightweight, dismissible first-time hints.

Each hint shows once ever (tracked in Settings.hints_seen, persisted to
settings.json) - not once per session, and not once per new game. Key
names are pulled live from control_scheme_manager so the text always
matches whatever scheme the player has configured.
"""

import pygame

from ..input.control_schemes import control_scheme_manager

HINT_DURATION = 8.0
FADE_DURATION = 0.6


def _flight_controls_lines():
    k = control_scheme_manager.get_key_name
    return [
        f"{k('thrust')} thrust   {k('rotate_left')}/{k('rotate_right')} turn   {k('fire_weapons')} fire",
        f"Approach a station and press {k('dock')} to dock",
    ]


def _station_services_lines():
    k = control_scheme_manager.get_key_name
    return [
        "Docked! Station services:",
        f"{k('trading')} trade   {k('missions')} missions   {k('upgrades')} upgrades   {k('dock')}/{k('undock')} undock",
    ]


HINTS = {
    "flight_controls": _flight_controls_lines,
    "station_services": _station_services_lines,
}


class OnboardingHints:
    """Shows one hint at a time, auto-dismissed after a few seconds or on key press."""

    def __init__(self):
        self.active_hint = None
        self.timer = 0.0
        self.queue = []

    def trigger(self, hint_id):
        """Show a hint if it hasn't been seen before, queuing it if another
        hint is already showing rather than dropping it. Marks it seen
        immediately (not on dismiss/expiry) so an unclean shutdown mid-hint
        doesn't repeat it."""
        from ..settings import game_settings

        if hint_id not in HINTS:
            return
        if hint_id in game_settings.hints_seen or hint_id in self.queue:
            return

        game_settings.hints_seen.append(hint_id)
        game_settings.save()

        if self.active_hint is None:
            self.active_hint = hint_id
            self.timer = 0.0
        else:
            self.queue.append(hint_id)

    def dismiss(self):
        """Dismiss the active hint immediately (e.g. on a relevant key press)."""
        self._advance()

    def update(self, delta_time):
        if self.active_hint is None:
            return
        self.timer += delta_time
        if self.timer >= HINT_DURATION:
            self._advance()

    def _advance(self):
        """Clear the active hint and show the next queued one, if any."""
        if self.queue:
            self.active_hint = self.queue.pop(0)
            self.timer = 0.0
        else:
            self.active_hint = None
            self.timer = 0.0

    def render(self, screen):
        if self.active_hint is None:
            return

        lines = HINTS[self.active_hint]()
        font = pygame.font.Font(None, 26)
        line_surfaces = [font.render(line, True, (230, 235, 245)) for line in lines]

        padding = 14
        line_spacing = 26
        box_width = max(s.get_width() for s in line_surfaces) + padding * 2
        box_height = len(line_surfaces) * line_spacing + padding * 2 - (line_spacing - font.get_height())

        box_x = (screen.get_width() - box_width) // 2
        box_y = 16

        # Fade in/out at the start and end of the hint's lifetime
        alpha = 255
        if self.timer < FADE_DURATION:
            alpha = int(255 * (self.timer / FADE_DURATION))
        elif self.timer > HINT_DURATION - FADE_DURATION:
            alpha = int(255 * ((HINT_DURATION - self.timer) / FADE_DURATION))
        alpha = max(0, min(255, alpha))

        box_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(box_surface, (10, 14, 30, min(200, alpha)), box_surface.get_rect(), border_radius=8)
        pygame.draw.rect(box_surface, (80, 160, 255, alpha), box_surface.get_rect(), width=2, border_radius=8)

        y = padding
        for line_surface in line_surfaces:
            line_surface.set_alpha(alpha)
            line_rect = line_surface.get_rect(centerx=box_width // 2, y=y)
            box_surface.blit(line_surface, line_rect)
            y += line_spacing

        screen.blit(box_surface, (box_x, box_y))


# Global onboarding hints instance
onboarding_hints = OnboardingHints()
