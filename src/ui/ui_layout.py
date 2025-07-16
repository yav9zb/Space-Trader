"""
UI Layout helper for responsive positioning and sizing.
"""
import pygame
from typing import Tuple, Optional
from enum import Enum


class Anchor(Enum):
    """Anchor points for UI elements."""
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


class UILayout:
    """Responsive UI layout helper."""
    
    def __init__(self, screen_width: int, screen_height: int, base_scale: float = 1.0):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.base_scale = base_scale
        
        # Calculate responsive margins based on screen size
        self.margin_x = max(10, int(screen_width * 0.01))  # 1% of screen width, min 10px
        self.margin_y = max(10, int(screen_height * 0.01))  # 1% of screen height, min 10px
        
        # Calculate responsive padding
        self.padding = max(5, int(min(screen_width, screen_height) * 0.005))  # 0.5% of smallest dimension
        
        # Font scaling based on screen resolution
        self.font_scale = self._calculate_font_scale()
        
        # Reserved areas for UI elements (to prevent overlap)
        self.reserved_areas = []
        
        # Hover tracking for interactive elements
        self.hover_states = {}
    
    def _calculate_font_scale(self) -> float:
        """Calculate font scaling based on screen resolution."""
        # Base resolution: 1920x1080
        base_width, base_height = 1920, 1080
        
        # Calculate scale based on screen size
        width_scale = self.screen_width / base_width
        height_scale = self.screen_height / base_height
        
        # Use smaller scale to ensure text fits
        scale = min(width_scale, height_scale) * self.base_scale
        
        # Clamp between reasonable bounds
        return max(0.7, min(2.0, scale))
    
    def get_font_size(self, base_size: int) -> int:
        """Get scaled font size with bounds checking."""
        scaled_size = int(base_size * self.font_scale)
        return max(12, min(72, scaled_size))  # Clamp between 12px and 72px
    
    def get_position(self, anchor: Anchor, width: int, height: int, 
                    offset_x: int = 0, offset_y: int = 0) -> Tuple[int, int]:
        """Get position based on anchor point and dimensions."""
        x, y = 0, 0
        
        if anchor == Anchor.TOP_LEFT:
            x, y = self.margin_x, self.margin_y
        elif anchor == Anchor.TOP_CENTER:
            x, y = (self.screen_width - width) // 2, self.margin_y
        elif anchor == Anchor.TOP_RIGHT:
            x, y = self.screen_width - width - self.margin_x, self.margin_y
        elif anchor == Anchor.CENTER_LEFT:
            x, y = self.margin_x, (self.screen_height - height) // 2
        elif anchor == Anchor.CENTER:
            x, y = (self.screen_width - width) // 2, (self.screen_height - height) // 2
        elif anchor == Anchor.CENTER_RIGHT:
            x, y = self.screen_width - width - self.margin_x, (self.screen_height - height) // 2
        elif anchor == Anchor.BOTTOM_LEFT:
            x, y = self.margin_x, self.screen_height - height - self.margin_y
        elif anchor == Anchor.BOTTOM_CENTER:
            x, y = (self.screen_width - width) // 2, self.screen_height - height - self.margin_y
        elif anchor == Anchor.BOTTOM_RIGHT:
            x, y = self.screen_width - width - self.margin_x, self.screen_height - height - self.margin_y
        
        return x + offset_x, y + offset_y
    
    def get_panel_size(self, base_width: int, base_height: int, 
                      max_width_percent: float = 0.4, max_height_percent: float = 0.6) -> Tuple[int, int]:
        """Get responsive panel size based on screen dimensions."""
        # Calculate scaled dimensions
        scaled_width = int(base_width * self.font_scale)
        scaled_height = int(base_height * self.font_scale)
        
        # Apply maximum percentage constraints
        max_width = int(self.screen_width * max_width_percent)
        max_height = int(self.screen_height * max_height_percent)
        
        # Clamp to maximum values
        width = min(scaled_width, max_width)
        height = min(scaled_height, max_height)
        
        return width, height
    
    def reserve_area(self, x: int, y: int, width: int, height: int, name: str = ""):
        """Reserve an area to prevent UI overlap."""
        self.reserved_areas.append({
            'x': x, 'y': y, 'width': width, 'height': height, 'name': name
        })
    
    def find_non_overlapping_position(self, width: int, height: int, 
                                    preferred_anchor: Anchor = Anchor.TOP_LEFT) -> Tuple[int, int]:
        """Find a position that doesn't overlap with reserved areas."""
        # Try preferred position first
        x, y = self.get_position(preferred_anchor, width, height)
        
        if not self._overlaps_reserved_area(x, y, width, height):
            return x, y
        
        # Try other positions
        for anchor in Anchor:
            if anchor == preferred_anchor:
                continue
            
            x, y = self.get_position(anchor, width, height)
            if not self._overlaps_reserved_area(x, y, width, height):
                return x, y
        
        # If no non-overlapping position found, use preferred with warning
        return self.get_position(preferred_anchor, width, height)
    
    def _overlaps_reserved_area(self, x: int, y: int, width: int, height: int) -> bool:
        """Check if a rectangle overlaps with any reserved area."""
        for area in self.reserved_areas:
            if (x < area['x'] + area['width'] and 
                x + width > area['x'] and
                y < area['y'] + area['height'] and
                y + height > area['y']):
                return True
        return False
    
    def clear_reserved_areas(self):
        """Clear all reserved areas."""
        self.reserved_areas.clear()
    
    def resize(self, screen_width: int, screen_height: int):
        """Update layout for new screen dimensions."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Recalculate responsive values
        self.margin_x = max(10, int(screen_width * 0.01))
        self.margin_y = max(10, int(screen_height * 0.01))
        self.padding = max(5, int(min(screen_width, screen_height) * 0.005))
        self.font_scale = self._calculate_font_scale()
        
        # Clear reserved areas since screen changed
        self.clear_reserved_areas()
        
        # Clear hover states on resize
        self.hover_states.clear()
    
    def get_responsive_spacing(self, base_spacing: int) -> int:
        """Get responsive spacing based on screen size."""
        return max(base_spacing, int(base_spacing * self.font_scale))
    
    def update_hover_state(self, element_id: str, mouse_pos: Tuple[int, int], element_rect: pygame.Rect) -> bool:
        """Update hover state for an element and return if it's being hovered."""
        is_hovering = element_rect.collidepoint(mouse_pos)
        self.hover_states[element_id] = is_hovering
        return is_hovering
    
    def is_hovering(self, element_id: str) -> bool:
        """Check if an element is being hovered."""
        return self.hover_states.get(element_id, False)