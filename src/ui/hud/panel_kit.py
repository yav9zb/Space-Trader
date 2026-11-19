"""A small toolkit for HUD panels that are measured, not drawn on a fixed grid.

Rows are added to a Panel; the panel measures them, sizes itself to fit, then
draws a background, a header, and each row. Because the height comes from the
content, panels never leave dead space or spill past their border, and a column
of panels can be stacked with a constant gap.
"""

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import pygame

from .. import gfx
from ..ui_theme import ui_theme, UIElementType

TEXT = (232, 238, 250)
DIM = (140, 152, 175)
AMBER = (240, 190, 60)
RED = (240, 80, 65)
GREEN = (90, 215, 110)
BLUE = (100, 175, 250)

Color = Tuple[int, int, int]


@dataclass
class Metrics:
    """Pixel sizes for one window size."""
    unit: float
    pad: int
    row: int
    gap: int
    bar_h: int
    body: pygame.font.Font
    small: pygame.font.Font
    title: pygame.font.Font
    big: pygame.font.Font
    k: float = 1.0          # pixels per point: 2.0 when drawing at full resolution on a Retina display

    def px(self, n: float) -> int:
        """A fixed size in points, in pixels at this scale."""
        return max(1, round(n * self.k))


def make_metrics(font_scale: float, ratio: float = 1.0) -> Metrics:
    from .. import fonts
    unit = max(0.95, font_scale * 1.15) * ratio
    return Metrics(
        unit=unit,
        pad=max(8, round(9 * unit)),
        row=max(18, round(20 * unit)),
        gap=max(6, round(8 * unit)),
        bar_h=max(14, round(16 * unit)),
        body=fonts.exact(max(13, round(14 * unit))),
        small=fonts.exact(max(11, round(12 * unit))),
        title=fonts.exact(max(14, round(16 * unit))),
        big=fonts.exact(max(18, round(22 * unit))),
        k=ratio,
    )


def level_color(fraction: float, good: Color = GREEN) -> Color:
    """Green while healthy, amber when getting low, red when critical."""
    if fraction < 0.25:
        return RED
    if fraction < 0.5:
        return AMBER
    return good


# ---- icons ------------------------------------------------------------------------

def draw_icon(surface: pygame.Surface, kind: str, center, size: int, color: Color, k: float = 1.0):
    """Tiny glyphs drawn from shapes, since the font has no symbols."""
    cx, cy = int(center[0]), int(center[1])
    r = max(4, size // 2)
    w2, w1 = max(2, round(2 * k)), max(1, round(k))
    if kind == "hull":          # a shield
        pts = [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        pygame.draw.polygon(surface, color, pts, w2)
    elif kind == "cargo":       # a crate
        rect = pygame.Rect(cx - r, cy - r + 1, 2 * r, 2 * r - 2)
        pygame.draw.rect(surface, color, rect, w2)
        pygame.draw.line(surface, color, (cx - r, cy), (cx + r - 1, cy), w1)
    elif kind == "fuel":        # a droplet
        pygame.draw.circle(surface, color, (cx, cy + 2), r - 1, w2)
        pygame.draw.polygon(surface, color, [(cx, cy - r), (cx - r + 2, cy + 1), (cx + r - 2, cy + 1)], 2)
    elif kind == "credits":     # a coin
        pygame.draw.circle(surface, color, (cx, cy), r, w2)
        pygame.draw.circle(surface, color, (cx, cy), max(1, r // 3))
    elif kind == "speed":       # chevrons
        for dx in (-round(3 * k), round(3 * k)):
            pygame.draw.lines(surface, color, False,
                              [(cx + dx - 3, cy - r + 1), (cx + dx + 1, cy), (cx + dx - 3, cy + r - 1)], w2)
    elif kind == "rank":        # a star
        pts = []
        for i in range(10):
            radius = r if i % 2 == 0 else r * 0.45
            angle = math.radians(-90 + i * 36)
            pts.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
        pygame.draw.polygon(surface, color, pts)
    elif kind == "sector":      # a crosshair
        pygame.draw.circle(surface, color, (cx, cy), r - 1, w1)
        pygame.draw.line(surface, color, (cx - r, cy), (cx + r, cy), w1)
        pygame.draw.line(surface, color, (cx, cy - r), (cx, cy + r), w1)
    elif kind == "station":     # a small hub
        pygame.draw.circle(surface, color, (cx, cy), r - 2, w2)
        pygame.draw.circle(surface, color, (cx, cy), w2)


def text_with_shadow(surface: pygame.Surface, font: pygame.font.Font, text: str, color: Color, pos):
    surface.blit(font.render(text, True, (0, 0, 10)), (pos[0] + 1, pos[1] + 1))
    surface.blit(font.render(text, True, color), pos)


def fit_text(font: pygame.font.Font, text: str, max_width: int) -> str:
    """Shorten text with an ellipsis so it never runs past max_width."""
    if font.size(text)[0] <= max_width:
        return text
    while len(text) > 1 and font.size(text + "...")[0] > max_width:
        text = text[:-1]
    return text + "..."


# ---- rows ---------------------------------------------------------------------------

class Row:
    def height(self, m: Metrics, width: int) -> int:
        raise NotImplementedError

    def draw(self, surface: pygame.Surface, m: Metrics, x: int, y: int, width: int):
        raise NotImplementedError


class Stat(Row):
    """A label on the left and its value, brighter, on the right."""

    def __init__(self, label: str, value: str, value_color: Color = TEXT, icon: Optional[str] = None,
                 icon_color: Color = DIM):
        self.label, self.value, self.value_color, self.icon, self.icon_color = label, value, value_color, icon, icon_color

    def height(self, m, width):
        return m.row

    def draw(self, surface, m, x, y, width):
        mid = y + m.row // 2
        left = x
        if self.icon:
            draw_icon(surface, self.icon, (x + m.px(7), mid), m.px(14), self.icon_color, m.k)
            left += m.px(20)
        label = m.small.render(self.label, True, DIM)
        surface.blit(label, (left, mid - label.get_height() // 2))
        room = width - (left - x) - label.get_width() - m.px(8)
        value = m.body.render(fit_text(m.body, self.value, max(20, room)), True, self.value_color)
        surface.blit(value, (x + width - value.get_width(), mid - value.get_height() // 2))


class BarRow(Row):
    """An icon, a label and a bar with the value written on it."""

    def __init__(self, icon: str, label: str, value_text: str, fraction: float, color: Color):
        self.icon, self.label, self.value_text, self.fraction, self.color = icon, label, value_text, fraction, color

    def height(self, m, width):
        return m.bar_h + m.px(6)

    def layout(self, m: Metrics, x: int, y: int, width: int):
        """(bar rectangle, the value text that fits on it)."""
        label_w = max(m.small.size(self.label)[0], m.small.size("FUEL")[0])
        bar_x = x + m.px(20) + label_w + m.px(8)
        bar_w = max(30, x + width - bar_x)
        return pygame.Rect(bar_x, y + m.px(3), bar_w, m.bar_h), fit_text(m.small, self.value_text, bar_w - m.px(6))

    def draw(self, surface, m, x, y, width):
        h = m.bar_h
        mid = y + (h + m.px(6)) // 2
        draw_icon(surface, self.icon, (x + m.px(7), mid), m.px(14), self.color, m.k)
        label = m.small.render(self.label, True, DIM)
        surface.blit(label, (x + m.px(20), mid - label.get_height() // 2))
        bar, text = self.layout(m, x, y, width)
        gfx.draw_bar(surface, bar, self.fraction, self.color)
        rendered = m.small.render(text, True, (255, 255, 255))
        text_with_shadow(surface, m.small, text, (255, 255, 255),
                         (bar.x + (bar.width - rendered.get_width()) // 2,
                          bar.y + (bar.height - rendered.get_height()) // 2))


class Chip(Row):
    """A rounded status tag."""

    def __init__(self, text: str, color: Color, label: Optional[str] = None):
        self.text, self.color, self.label = text, color, label

    def height(self, m, width):
        return m.row + m.px(2)

    def draw(self, surface, m, x, y, width):
        h = m.row
        left = x
        if self.label:
            label = m.small.render(self.label, True, DIM)
            surface.blit(label, (x, y + (h - label.get_height()) // 2 + 1))
            left += label.get_width() + m.px(8)
        room = x + width - left
        text = fit_text(m.small, self.text, room - m.px(14))
        rendered = m.small.render(text, True, self.color)
        rect = pygame.Rect(left, y + 1, min(room, rendered.get_width() + m.px(14)), h)
        if self.label:
            rect.right = x + width
            rect.width = min(rect.width, room)
        back = gfx.darken(self.color, 0.78)
        pygame.draw.rect(surface, back, rect, border_radius=h // 2)
        pygame.draw.rect(surface, gfx.darken(self.color, 0.35), rect, m.px(1), border_radius=h // 2)
        surface.blit(rendered, (rect.centerx - rendered.get_width() // 2,
                                rect.centery - rendered.get_height() // 2))


class Divider(Row):
    def __init__(self, color: Color = (60, 75, 105)):
        self.color = color

    def height(self, m, width):
        return m.gap

    def draw(self, surface, m, x, y, width):
        pygame.draw.line(surface, self.color, (x, y + m.gap // 2), (x + width, y + m.gap // 2), 1)


class Big(Row):
    """A label with a large value beneath, for the thing you glance at most."""

    def __init__(self, label: str, value: str, color: Color = TEXT, icon: Optional[str] = None):
        self.label, self.value, self.color, self.icon = label, value, color, icon

    def height(self, m, width):
        return m.small.get_height() + m.big.get_height() + m.px(4)

    def draw(self, surface, m, x, y, width):
        left = x
        if self.icon:
            draw_icon(surface, self.icon, (x + m.px(7), y + m.small.get_height() // 2 + 1), m.px(14), DIM, m.k)
            left += m.px(20)
        surface.blit(m.small.render(self.label, True, DIM), (left, y))
        value = fit_text(m.big, self.value, width)
        surface.blit(m.big.render(value, True, self.color), (x, y + m.small.get_height() + m.px(2)))


class Grid(Row):
    """Several small gauges side by side: a label, a count and a thin bar."""

    def __init__(self, cells: Sequence[Tuple[str, str, float, Color]], columns: Optional[int] = None):
        self.cells, self.columns = list(cells), columns

    def _cols(self, width: int, m: Metrics) -> int:
        if self.columns:
            return self.columns
        return len(self.cells) if width >= m.px(52) * len(self.cells) else 2

    def height(self, m, width):
        rows = math.ceil(len(self.cells) / self._cols(width, m))
        return rows * (m.small.get_height() + m.body.get_height() + m.px(6)) + (rows - 1) * m.px(4)

    def draw(self, surface, m, x, y, width):
        cols = self._cols(width, m)
        gap = m.px(6)
        cell_w = (width - (cols - 1) * gap) // cols
        cell_h = m.small.get_height() + m.body.get_height() + m.px(6)
        for i, (label, value, fraction, color) in enumerate(self.cells):
            cx = x + (i % cols) * (cell_w + gap)
            cy = y + (i // cols) * (cell_h + m.px(4))
            surface.blit(m.small.render(label, True, DIM), (cx, cy))
            count = m.body.render(fit_text(m.body, value, cell_w), True, TEXT)
            surface.blit(count, (cx, cy + m.small.get_height()))
            gfx.draw_bar(surface, (cx, cy + cell_h - m.px(4), cell_w, m.px(4)), fraction, color, border=(60, 70, 95))


class Entry(Row):
    """A list item: a title with a small value on the right, a subtitle line
    with its own right-hand value, and a thin progress bar."""

    def __init__(self, title: str, right: str, subtitle: str, subtitle_right: str, fraction: float,
                 color: Color = BLUE, right_color: Color = DIM, subtitle_color: Color = BLUE):
        self.title, self.right, self.subtitle, self.subtitle_right = title, right, subtitle, subtitle_right
        self.fraction, self.color, self.right_color, self.subtitle_color = fraction, color, right_color, subtitle_color

    def height(self, m, width):
        lines = m.body.get_height() + (m.small.get_height() if self.subtitle or self.subtitle_right else 0)
        return lines + m.px(10)

    def draw(self, surface, m, x, y, width):
        right = m.small.render(self.right, True, self.right_color) if self.right else None
        room = width - (right.get_width() + m.px(8) if right else 0)
        title = m.body.render(fit_text(m.body, self.title, room), True, TEXT)
        surface.blit(title, (x, y))
        if right:
            surface.blit(right, (x + width - right.get_width(), y + (title.get_height() - right.get_height()) // 2))
        cursor = y + title.get_height()
        if self.subtitle or self.subtitle_right:
            sub_right = m.small.render(self.subtitle_right, True, DIM) if self.subtitle_right else None
            room = width - (sub_right.get_width() + m.px(8) if sub_right else 0)
            sub = m.small.render(fit_text(m.small, self.subtitle, room), True, self.subtitle_color)
            surface.blit(sub, (x, cursor))
            if sub_right:
                surface.blit(sub_right, (x + width - sub_right.get_width(), cursor))
            cursor += sub.get_height()
        gfx.draw_bar(surface, (x, cursor + m.px(3), width, m.px(5)), self.fraction, self.color, border=(60, 70, 95))


class Note(Row):
    def __init__(self, text: str, color: Color = DIM):
        self.text, self.color = text, color

    def height(self, m, width):
        return m.small.get_height() + m.px(2)

    def draw(self, surface, m, x, y, width):
        surface.blit(m.small.render(fit_text(m.small, self.text, width), True, self.color), (x, y))


# ---- the panel ------------------------------------------------------------------------

class Panel:
    HEADER_GAP = 4          # points

    def __init__(self, title: str, element_type: UIElementType, accent: Color, metrics: Metrics, width: int):
        self.title, self.element_type, self.accent = title, element_type, accent
        self.m, self.width = metrics, width
        self.rows: List[Row] = []

    # builders (each returns the panel so calls can chain)
    def add(self, row: Row) -> "Panel":
        self.rows.append(row)
        return self

    def stat(self, *args, **kwargs):
        return self.add(Stat(*args, **kwargs))

    def bar(self, *args, **kwargs):
        return self.add(BarRow(*args, **kwargs))

    def chip(self, *args, **kwargs):
        return self.add(Chip(*args, **kwargs))

    def divider(self):
        return self.add(Divider())

    def big(self, *args, **kwargs):
        return self.add(Big(*args, **kwargs))

    def grid(self, *args, **kwargs):
        return self.add(Grid(*args, **kwargs))

    def note(self, *args, **kwargs):
        return self.add(Note(*args, **kwargs))

    def entry(self, *args, **kwargs):
        return self.add(Entry(*args, **kwargs))

    @property
    def inner_width(self) -> int:
        return self.width - 2 * self.m.pad

    def header_height(self) -> int:
        return self.m.title.get_height() + self.m.px(self.HEADER_GAP) + self.m.px(4)

    def height(self) -> int:
        body = sum(row.height(self.m, self.inner_width) + self.m.px(2) for row in self.rows)
        return self.m.pad + self.header_height() + body + self.m.pad - self.m.px(2)

    def draw(self, surface: pygame.Surface, x: int, y: int) -> pygame.Rect:
        """Draw at (x, y); returns the rectangle used."""
        m = self.m
        rect = pygame.Rect(x, y, self.width, self.height())
        # The shared theme draws the frame; tell it the pixel scale for this panel
        saved = (ui_theme.pixel_ratio, ui_theme.base_scale)
        ui_theme.pixel_ratio, ui_theme.base_scale = m.k, max(saved[1], m.k)
        try:
            ui_theme.draw_panel_background(surface, rect, 190)
            ui_theme.draw_border(surface, rect, self.element_type)
        finally:
            ui_theme.pixel_ratio, ui_theme.base_scale = saved

        title = m.title.render(self.title, True, self.accent)
        surface.blit(title, (x + m.pad, y + m.pad))
        line_y = y + m.pad + m.title.get_height() + m.px(self.HEADER_GAP)
        pygame.draw.line(surface, gfx.darken(self.accent, 0.45), (x + m.pad, line_y),
                         (x + self.width - m.pad, line_y), 1)
        pygame.draw.line(surface, self.accent, (x + m.pad, line_y), (x + m.pad + m.px(26), line_y), m.px(2))

        cursor = y + m.pad + self.header_height()
        for row in self.rows:
            row.draw(surface, m, x + m.pad, cursor, self.inner_width)
            cursor += row.height(m, self.inner_width) + m.px(2)
        return rect


def stack(panels: Sequence[Panel], x: int, y: int, gap: int) -> List[pygame.Rect]:
    """Rectangles for panels stacked top to bottom with a constant gap; the
    caller draws each at its rectangle's top-left."""
    rects, cursor = [], y
    for panel in panels:
        rects.append(pygame.Rect(x, cursor, panel.width, panel.height()))
        cursor += panel.height() + gap
    return rects
