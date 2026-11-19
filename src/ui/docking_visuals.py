"""How docking looks: an animated dashed zone ring around the station, coloured
by whether you can dock right now, and a tractor beam that pulls the ship in
while the docking sequence runs. Pure drawing helpers; the colours' meaning is
decided by the caller from the docking state.
"""

import math

import pygame
from pygame import Vector2

from . import gfx

CAN_DOCK = (60, 255, 110)
TOO_FAST = (255, 215, 60)
TOO_FAR = (255, 110, 100)
APPROACH = (100, 150, 255)


def zone_status(distance: float, docking_radius: float, speed: float, max_speed: float):
    """(colour, name) for the docking zone given where the ship is and how fast."""
    if distance <= docking_radius:
        return (CAN_DOCK, "ready") if speed <= max_speed else (TOO_FAST, "too fast")
    return TOO_FAR, "far"


def dashed_ring(screen: pygame.Surface, center, radius, color, spin_degrees: float,
                dash_degrees: float = 16, gap_degrees: float = 11, width: int = 2):
    """A ring of dashes that can be spun by changing spin_degrees."""
    radius = int(radius)
    if radius < 4:
        return
    rect = pygame.Rect(0, 0, radius * 2, radius * 2)
    rect.center = (int(center[0]), int(center[1]))
    step = dash_degrees + gap_degrees
    angle = spin_degrees % step - step
    while angle < 360:
        start = max(0.0, angle)
        end = min(360.0, angle + dash_degrees)
        if end > start:
            pygame.draw.arc(screen, color, rect, math.radians(start), math.radians(end), width)
        angle += step


def draw_zone(screen: pygame.Surface, center, radius, color, now: float, emphasis: float = 1.0):
    """The docking zone: a glowing ring with slowly turning dashes."""
    gfx.draw_ring_glow(screen, center, radius, 4, color, 0.45 * emphasis)
    dashed_ring(screen, center, radius, color, spin_degrees=now * 25, width=2 if emphasis >= 1 else 1)


def beam_points(start: Vector2, end: Vector2, phase: float, count: int = 7):
    """Positions of light pulses travelling from start to end; phase is any
    increasing number (seconds), each pulse is a fraction 0..1 along the beam."""
    return [start + (end - start) * ((phase * 0.9 + i / count) % 1.0) for i in range(count)]


def draw_tractor_beam(screen: pygame.Surface, start, end, progress: float, now: float,
                      color=(110, 190, 255), reverse: bool = False):
    """Converging beam lines between a station's port and the ship, with
    pulses of light moving along it (toward the ship when undocking)."""
    start, end = Vector2(start), Vector2(end)
    if (end - start).length() < 6:
        return
    along = (end - start).normalize()
    side = Vector2(-along.y, along.x)
    spread = 7 * (1.0 - 0.6 * progress)
    faint = gfx.darken(color, 0.45)
    for offset in (-spread, spread):
        pygame.draw.line(screen, faint, start + side * offset * 0.3, end + side * offset, 1)
    gfx.draw_glow(screen, (start + end) / 2, max(8, int((end - start).length() * 0.35)), color, 0.18)
    for point in beam_points(end if reverse else start, start if reverse else end, now):
        gfx.draw_glow(screen, point, 8, color, 0.9)
        pygame.draw.circle(screen, (235, 245, 255), (int(point.x), int(point.y)), 2)


def draw_progress_arc(screen: pygame.Surface, center, radius, fraction: float, color):
    """An arc around the station that fills as docking completes."""
    fraction = max(0.0, min(1.0, fraction))
    if fraction <= 0 or radius < 6:
        return
    rect = pygame.Rect(0, 0, int(radius) * 2, int(radius) * 2)
    rect.center = (int(center[0]), int(center[1]))
    pygame.draw.arc(screen, color, rect, math.radians(90), math.radians(90 + 360 * fraction), 4)
