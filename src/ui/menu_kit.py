"""Layout toolkit for the menu screens.

The older screens were drawn on a fixed pixel grid (a title at y=70, options
every 60 pixels) and then scaled up as a bitmap, which is soft on a Retina
display and wastes space on a wide window. A screen built with this kit
measures instead: every size comes from one continuous scale derived from the
window, text is rendered at its exact pixel size (so it is sharp at any
size, and at a Retina display's real pixels), and lists fit their spacing to
the room they are given.

Units: a "design unit" is one pixel on a 1280x800 window. `Ui.px(n)` turns design
units into surface pixels for the surface being drawn on, so the same code
produces a correct layout at 1024x640, 1512x945, 3440x1440, or on a surface
with twice the pixels of the window.
"""

from typing import Dict, List, Optional, Sequence, Tuple

import pygame

from . import fonts, gfx
from .menu_style import (ACCENT_BLUE, ACCENT_GOLD, TEXT_DIM, TEXT_PRIMARY,
                         draw_panel, wrap_text)

BASE_SIZE = (1280, 800)
MIN_SCALE = 0.72
MAX_SCALE = 2.4

# Text sizes in design units (pixels at the base window size)
ROLES: Dict[str, int] = {
    "display": 56,
    "title": 44,
    "heading": 28,
    "option": 32,
    "body": 20,
    "small": 16,
    "tiny": 13,
}

COLOR_SELECTED = ACCENT_GOLD
COLOR_NORMAL = (220, 225, 235)
COLOR_WARN = (255, 120, 120)
COLOR_GOOD = (120, 230, 150)
HOVER_FILL = (80, 160, 255, 34)

_fonts: Dict[int, pygame.font.Font] = {}


def scale_for(points: Tuple[int, int]) -> float:
    """The design-unit to point scale for a window size in points."""
    width, height = points
    scale = min(width / BASE_SIZE[0], height / BASE_SIZE[1])
    return max(MIN_SCALE, min(MAX_SCALE, scale))


def _font(pixels: int) -> pygame.font.Font:
    font = _fonts.get(pixels)
    if font is None:
        if len(_fonts) > 64:
            _fonts.clear()
        font = _fonts[pixels] = fonts.exact(pixels)
    return font


class Ui:
    """Measurements for one surface: how big a design unit is, the fonts, and
    helpers that draw text and standard screen furniture."""

    def __init__(self, size: Tuple[int, int], ratio: float = 1.0):
        self.size = (int(size[0]), int(size[1]))
        self.ratio = float(ratio) if ratio else 1.0
        self.points = (self.size[0] / self.ratio, self.size[1] / self.ratio)
        self.scale = scale_for(self.points)
        self.unit = self.scale * self.ratio              # surface pixels per design unit

    # Measuring ----------------------------------------------------------------------

    def px(self, units: float) -> int:
        return max(1, round(units * self.unit)) if units else 0

    def font(self, role="body") -> pygame.font.Font:
        units = ROLES[role] if isinstance(role, str) else role
        return _font(max(8, round(units * self.unit)))

    def to_px(self, pos) -> Tuple[int, int]:
        """A mouse position in window points as a position on this surface."""
        return int(pos[0] * self.ratio), int(pos[1] * self.ratio)

    @property
    def width(self) -> int:
        return self.size[0]

    @property
    def height(self) -> int:
        return self.size[1]

    def screen_rect(self) -> pygame.Rect:
        return pygame.Rect(0, 0, *self.size)

    # Text ---------------------------------------------------------------------------

    def text(self, screen, text: str, role="body", color=TEXT_PRIMARY, max_width: Optional[int] = None,
             **anchor) -> pygame.Rect:
        """Draw text placed by a rect anchor (`center=`, `topleft=`, `midtop=`...).
        With max_width, text that would be wider is shortened with "..."."""
        font = self.font(role)
        if max_width is not None:
            text = fit_text(text, font, max_width)
        surface = font.render(text, True, color)
        rect = surface.get_rect(**anchor)
        screen.blit(surface, rect)
        return rect

    def wrap(self, text: str, role, width: int) -> List[str]:
        return wrap_text(text, self.font(role), width)

    def line_height(self, role="body") -> int:
        return self.font(role).get_linesize()

    # Furniture ----------------------------------------------------------------------

    def margin(self) -> int:
        return self.px(48)

    def content_width(self, widest_units: int = 1180) -> int:
        """The width screens lay content out in: the window less margins, but
        never so wide that rows become hard to follow on an ultrawide window."""
        return min(self.width - 2 * self.margin(), self.px(widest_units))

    def header(self, screen, title: str, subtitle: Optional[str] = None, role="title") -> int:
        """Title with an accent underline (and subtitle). Returns the y just
        below the header, for the content that follows."""
        top = self.px(34)
        font = self.font(role)
        surface = font.render(title, True, TEXT_PRIMARY)
        rect = surface.get_rect(midtop=(self.width // 2, top))
        shadow = font.render(title, True, (0, 0, 12))
        screen.blit(shadow, rect.move(self.px(2), self.px(2)))
        gfx.draw_glow(screen, rect.center, max(30, rect.height), ACCENT_BLUE, 0.12)
        screen.blit(surface, rect)
        line_y = rect.bottom + self.px(6)
        pygame.draw.line(screen, ACCENT_BLUE, (rect.left, line_y), (rect.right, line_y), max(1, self.px(2)))
        bottom = line_y + self.px(4)
        if subtitle:
            sub = self.text(screen, subtitle, "small", TEXT_DIM, max_width=self.width - 2 * self.margin(),
                            midtop=(self.width // 2, bottom + self.px(6)))
            bottom = sub.bottom
        return bottom + self.px(14)

    def footer(self, screen, hint: str, color=TEXT_DIM) -> int:
        """A line of key hints along the bottom edge. Returns its top y."""
        rect = self.text(screen, hint, "small", color, max_width=self.width - 2 * self.margin(),
                         midbottom=(self.width // 2, self.height - self.px(16)))
        return rect.top - self.px(10)

    def panel(self, screen, rect, border=ACCENT_BLUE, alpha=190):
        draw_panel(screen, pygame.Rect(rect), border_color=border, bg_alpha=alpha,
                   border_width=max(1, self.px(2)), radius=self.px(10))

    def message(self, screen, text: str, color=ACCENT_GOLD):
        """A short notice boxed in the middle of the screen."""
        font = self.font("heading")
        surface = font.render(fit_text(text, font, self.width - 4 * self.margin()), True, color)
        rect = surface.get_rect(center=(self.width // 2, self.height // 2))
        self.panel(screen, rect.inflate(self.px(40), self.px(24)), border=color, alpha=235)
        screen.blit(surface, rect)


def fit_text(text: str, font: pygame.font.Font, max_width: int) -> str:
    """The text, shortened with "..." if it is wider than max_width."""
    if max_width <= 0 or font.size(text)[0] <= max_width:
        return text
    ellipsis = "..."
    while text and font.size(text + ellipsis)[0] > max_width:
        text = text[:-1]
    return text.rstrip() + ellipsis


def ui_for(screen: pygame.Surface, game) -> Ui:
    """A Ui for a surface the engine handed to a screen: on the high-density
    path the surface has more pixels than the window has points."""
    ratio = 1.0
    presenter = getattr(game, "presenter", None)
    if presenter is not None:
        points = tuple(game.WINDOW_SIZE)
        if points[0]:
            ratio = screen.get_width() / points[0]
    return Ui(screen.get_size(), ratio)


# Lists ------------------------------------------------------------------------------

def scroll_window(count: int, selected: int, rows: int, offset: int = 0) -> int:
    """The first visible row of a list that keeps `selected` in view, moving as
    little as possible from the previous `offset`."""
    rows = max(1, rows)
    if count <= rows:
        return 0
    offset = max(0, min(offset, count - rows))
    if selected < offset:
        offset = selected
    elif selected >= offset + rows:
        offset = selected - rows + 1
    return max(0, min(offset, count - rows))


class MenuList:
    """A vertical list of choices: arrow keys and the mouse move the highlight,
    Enter or a click activates. Spacing shrinks to fit the room it is given, and
    a list too long to fit scrolls."""

    def __init__(self, items: Sequence[str], role="option", min_row_units: int = 30, wrap_keys: bool = True):
        self.items = list(items)
        self.selected = 0
        self.role = role
        self.min_row_units = min_row_units
        self.wrap_keys = wrap_keys
        self.rects: Dict[int, pygame.Rect] = {}        # visible index -> hit rectangle
        self.offset = 0
        self.rows_visible = len(self.items)

    # Layout -------------------------------------------------------------------------

    def layout(self, ui: Ui, area: pygame.Rect, row_units: int = 62, width_units: Optional[int] = None,
               align_top: bool = False) -> pygame.Rect:
        """Place the rows in area. Returns the rectangle the list occupies."""
        area = pygame.Rect(area)
        count = len(self.items)
        row = ui.px(row_units)
        smallest = ui.px(self.min_row_units)
        if count * row > area.height:
            row = max(smallest, area.height // max(1, count))
        self.rows_visible = max(1, min(count, area.height // max(1, row)))
        self.offset = scroll_window(count, self.selected, self.rows_visible, self.offset)
        shown = min(count, self.rows_visible)
        total = shown * row
        top = area.top if align_top else area.top + max(0, (area.height - total) // 2)
        font = ui.font(self.role)
        widest = max((font.size(item)[0] for item in self.items), default=0)
        width = ui.px(width_units) if width_units else widest + ui.px(110)
        width = min(max(width, ui.px(280)), area.width)
        self.rects = {}
        for slot in range(shown):
            index = self.offset + slot
            self.rects[index] = pygame.Rect(area.centerx - width // 2, top + slot * row, width, row)
        self.row_height = row
        return pygame.Rect(area.centerx - width // 2, top, width, total)

    # Drawing ------------------------------------------------------------------------

    def draw(self, ui: Ui, screen, hovered: Optional[int] = None):
        font = ui.font(self.role)
        for index, rect in self.rects.items():
            selected = index == self.selected
            if selected or index == hovered:
                fill = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.rect(fill, HOVER_FILL if selected else (80, 160, 255, 16),
                                 fill.get_rect(), border_radius=ui.px(8))
                screen.blit(fill, rect.topleft)
            color = COLOR_SELECTED if selected else COLOR_NORMAL
            label = font.render(fit_text(self.items[index], font, rect.width - ui.px(70)), True, color)
            label_rect = label.get_rect(center=rect.center)
            screen.blit(label, label_rect)
            if selected:
                size = max(4, rect.height // 5)
                x = rect.left + ui.px(22)
                pygame.draw.polygon(screen, COLOR_SELECTED, [
                    (x, rect.centery - size), (x + size, rect.centery), (x, rect.centery + size)])
        if self.offset > 0:
            self._arrow(ui, screen, up=True)
        if self.offset + self.rows_visible < len(self.items):
            self._arrow(ui, screen, up=False)

    def _arrow(self, ui: Ui, screen, up: bool):
        if not self.rects:
            return
        rects = list(self.rects.values())
        anchor = rects[0] if up else rects[-1]
        size = ui.px(7)
        x = anchor.centerx
        y = anchor.top - size - ui.px(2) if up else anchor.bottom + size + ui.px(2)
        tip = -size if up else size
        pygame.draw.polygon(screen, TEXT_DIM, [(x - size, y), (x + size, y), (x, y + tip)])

    # Input --------------------------------------------------------------------------

    def index_at(self, ui: Ui, pos) -> Optional[int]:
        point = ui.to_px(pos)
        for index, rect in self.rects.items():
            if rect.collidepoint(point):
                return index
        return None

    def handle(self, event, ui: Optional[Ui] = None, play_sounds: bool = True) -> Optional[int]:
        """Feed an event in. Returns the activated index, or None."""
        ui = ui or Ui((1, 1))
        count = len(self.items)
        if not count:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_DOWN):
                step = -1 if event.key == pygame.K_UP else 1
                if self.wrap_keys:
                    self.selected = (self.selected + step) % count
                else:
                    self.selected = max(0, min(count - 1, self.selected + step))
                self.offset = scroll_window(count, self.selected, self.rows_visible, self.offset)
                self._sound("ui_navigate", play_sounds)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._sound("ui_confirm", play_sounds)
                return self.selected
        elif event.type == pygame.MOUSEMOTION:
            index = self.index_at(ui, event.pos)
            if index is not None:
                self.selected = index
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            index = self.index_at(ui, event.pos)
            if index is not None:
                self.selected = index
                self._sound("ui_confirm", play_sounds)
                return index
        elif event.type == pygame.MOUSEWHEEL and self.rows_visible < count:
            self.selected = max(0, min(count - 1, self.selected - event.y))
            self.offset = scroll_window(count, self.selected, self.rows_visible, self.offset)
        return None

    @staticmethod
    def _sound(name: str, enabled: bool):
        if enabled:
            from ..audio.sound_manager import sound_manager
            sound_manager.play(name)


class RowList:
    """A scrolling list whose rows the screen draws itself (a save with its
    details, a mission, a market line). The list owns the geometry: how many
    rows fit, which are visible, hit rectangles, scrolling and the mouse."""

    def __init__(self, count: int = 0, wrap_keys: bool = True):
        self.count = count
        self.selected = 0
        self.offset = 0
        self.wrap_keys = wrap_keys
        self.rects: Dict[int, pygame.Rect] = {}
        self.rows_visible = 1
        self.area = pygame.Rect(0, 0, 0, 0)

    def set_count(self, count: int):
        self.count = count
        self.selected = max(0, min(self.selected, count - 1))
        self.offset = scroll_window(count, self.selected, self.rows_visible, self.offset)

    def layout(self, ui: Ui, area: pygame.Rect, row_units: int, gap_units: int = 4):
        """Fit as many rows of row_units as the area holds, scrolled to keep
        the selection in view."""
        self.area = pygame.Rect(area)
        row, gap = ui.px(row_units), ui.px(gap_units)
        self.rows_visible = max(1, (self.area.height + gap) // (row + gap))
        self.offset = scroll_window(self.count, self.selected, self.rows_visible, self.offset)
        self.rects = {}
        for slot in range(min(self.count, self.rows_visible)):
            index = self.offset + slot
            self.rects[index] = pygame.Rect(self.area.left, self.area.top + slot * (row + gap), self.area.width, row)

    def draw_chrome(self, ui: Ui, screen, hovered: Optional[int] = None, fill_selected: bool = True):
        """Highlight under the selected (and hovered) rows, and scroll arrows."""
        for index, rect in self.rects.items():
            if index == self.selected and fill_selected:
                fill = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.rect(fill, (60, 70, 110, 190), fill.get_rect(), border_radius=ui.px(7))
                screen.blit(fill, rect.topleft)
                pygame.draw.rect(screen, ACCENT_BLUE, rect, max(1, ui.px(2)), border_radius=ui.px(7))
            elif index == hovered:
                fill = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.rect(fill, (80, 160, 255, 22), fill.get_rect(), border_radius=ui.px(7))
                screen.blit(fill, rect.topleft)
        if self.offset > 0:
            self._arrow(ui, screen, self.area.top - ui.px(2), up=True)
        if self.offset + self.rows_visible < self.count:
            self._arrow(ui, screen, self.area.bottom + ui.px(2), up=False)

    def counter(self) -> str:
        if self.count <= self.rows_visible:
            return ""
        first = self.offset + 1
        return f"{first}-{min(self.count, self.offset + self.rows_visible)} of {self.count}"

    def _arrow(self, ui: Ui, screen, y: int, up: bool):
        size = ui.px(6)
        x = self.area.centerx
        tip = -size if up else size
        base = y
        pygame.draw.polygon(screen, TEXT_DIM, [(x - size, base), (x + size, base), (x, base + tip)])

    def index_at(self, ui: Ui, pos) -> Optional[int]:
        point = ui.to_px(pos)
        for index, rect in self.rects.items():
            if rect.collidepoint(point):
                return index
        return None

    def handle(self, event, ui: Ui, activate_on_click: bool = False, play_sounds: bool = True) -> Optional[int]:
        """Navigation by arrows, wheel and mouse. Returns an index when a row
        is activated (Enter, or a click if activate_on_click)."""
        if not self.count:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_DOWN):
                step = -1 if event.key == pygame.K_UP else 1
                if self.wrap_keys:
                    self.selected = (self.selected + step) % self.count
                else:
                    self.selected = max(0, min(self.count - 1, self.selected + step))
                self.offset = scroll_window(self.count, self.selected, self.rows_visible, self.offset)
                MenuList._sound("ui_navigate", play_sounds)
            elif event.key in (pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                step = -self.rows_visible if event.key == pygame.K_PAGEUP else self.rows_visible
                self.selected = max(0, min(self.count - 1, self.selected + step))
                self.offset = scroll_window(self.count, self.selected, self.rows_visible, self.offset)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self.selected
        elif event.type == pygame.MOUSEMOTION:
            index = self.index_at(ui, event.pos)
            if index is not None:
                self.selected = index
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            index = self.index_at(ui, event.pos)
            if index is not None:
                self.selected = index
                MenuList._sound("ui_navigate", play_sounds)
                return index if activate_on_click else None
        elif event.type == pygame.MOUSEWHEEL:
            self.selected = max(0, min(self.count - 1, self.selected - event.y))
            self.offset = scroll_window(self.count, self.selected, self.rows_visible, self.offset)
        return None


def draw_background(background, screen):
    """The drifting starfield every menu sits on."""
    background.draw(screen)
