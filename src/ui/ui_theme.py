"""
UI Theme system for consistent styling across the interface.
"""
import pygame
from enum import Enum
from typing import Tuple, Dict, Optional


class UIElementType(Enum):
    """Types of UI elements for theming."""
    SHIP_STATUS = "ship_status"
    NAVIGATION = "navigation"
    MISSION_TRACKER = "mission_tracker"
    DEV_VIEW = "dev_view"
    MINIMAP = "minimap"
    LARGE_MAP = "large_map"
    STATUS_BAR = "status_bar"
    SELECTION_HIGHLIGHT = "selection_highlight"
    INPUT_BOX = "input_box"
    BUTTON = "button"
    DIALOG = "dialog"


class UIState(Enum):
    """UI element states for dynamic styling."""
    NORMAL = "normal"
    HOVER = "hover"
    ACTIVE = "active"
    DISABLED = "disabled"
    FOCUSED = "focused"


class UITheme:
    """Centralized UI theme system for consistent styling."""
    
    def __init__(self, base_scale: float = 1.0):
        self.base_scale = base_scale
        self.alpha_enabled = True
        
        # Color palette
        self.colors = {
            # Primary colors
            'primary_blue': (100, 150, 200),
            'primary_green': (100, 200, 100),
            'primary_orange': (200, 150, 100),
            'primary_purple': (150, 100, 200),
            
            # Secondary colors
            'secondary_blue': (80, 120, 160),
            'secondary_green': (80, 160, 80),
            'secondary_orange': (160, 120, 80),
            'secondary_purple': (120, 80, 160),
            
            # Neutral colors
            'light_gray': (150, 150, 150),
            'medium_gray': (100, 100, 100),
            'dark_gray': (60, 60, 60),
            'darker_gray': (40, 40, 40),
            
            # Accent colors
            'white': (255, 255, 255),
            'light_blue': (180, 220, 255),
            'light_green': (180, 255, 180),
            'light_orange': (255, 220, 180),
            'warning_yellow': (255, 255, 0),
            'error_red': (255, 100, 100),
            'success_green': (100, 255, 100),
            
            # Background colors
            'panel_bg': (0, 0, 0),
            'panel_bg_transparent': (0, 0, 0, 180),
        }
        
        # Border styles for different UI elements
        self.border_styles = {
            UIElementType.SHIP_STATUS: {
                UIState.NORMAL: {
                    'color': 'primary_blue',
                    'thickness': 2,
                    'alpha': 255
                },
                UIState.HOVER: {
                    'color': 'light_blue',
                    'thickness': 2,
                    'alpha': 255
                }
            },
            UIElementType.NAVIGATION: {
                UIState.NORMAL: {
                    'color': 'primary_green',
                    'thickness': 2,
                    'alpha': 255
                },
                UIState.HOVER: {
                    'color': 'light_green',
                    'thickness': 2,
                    'alpha': 255
                }
            },
            UIElementType.MISSION_TRACKER: {
                UIState.NORMAL: {
                    'color': 'primary_orange',
                    'thickness': 2,
                    'alpha': 255
                },
                UIState.HOVER: {
                    'color': 'light_orange',
                    'thickness': 2,
                    'alpha': 255
                }
            },
            UIElementType.DEV_VIEW: {
                UIState.NORMAL: {
                    'color': 'primary_purple',
                    'thickness': 2,
                    'alpha': 200
                }
            },
            UIElementType.MINIMAP: {
                UIState.NORMAL: {
                    'color': 'medium_gray',
                    'thickness': 2,
                    'alpha': 255
                }
            },
            UIElementType.LARGE_MAP: {
                UIState.NORMAL: {
                    'color': 'primary_purple',
                    'thickness': 3,
                    'alpha': 255
                }
            },
            UIElementType.STATUS_BAR: {
                UIState.NORMAL: {
                    'color': 'dark_gray',
                    'thickness': 1,
                    'alpha': 255
                }
            },
            UIElementType.SELECTION_HIGHLIGHT: {
                UIState.NORMAL: {
                    'color': 'secondary_blue',
                    'thickness': 2,
                    'alpha': 255
                },
                UIState.ACTIVE: {
                    'color': 'primary_blue',
                    'thickness': 3,
                    'alpha': 255
                }
            },
            UIElementType.INPUT_BOX: {
                UIState.NORMAL: {
                    'color': 'light_gray',
                    'thickness': 2,
                    'alpha': 255
                },
                UIState.FOCUSED: {
                    'color': 'white',
                    'thickness': 2,
                    'alpha': 255
                }
            },
            UIElementType.BUTTON: {
                UIState.NORMAL: {
                    'color': 'medium_gray',
                    'thickness': 2,
                    'alpha': 255
                },
                UIState.HOVER: {
                    'color': 'light_gray',
                    'thickness': 2,
                    'alpha': 255
                },
                UIState.ACTIVE: {
                    'color': 'white',
                    'thickness': 2,
                    'alpha': 255
                }
            }
        }
    
    def get_color(self, color_name: str) -> Tuple[int, int, int]:
        """Get a color from the theme palette."""
        return self.colors.get(color_name, (255, 255, 255))
    
    def get_border_style(self, element_type: UIElementType, state: UIState = UIState.NORMAL) -> Dict:
        """Get border style for a UI element in a specific state."""
        element_styles = self.border_styles.get(element_type, {})
        style = element_styles.get(state, element_styles.get(UIState.NORMAL, {}))
        
        if not style:
            # Fallback to default style
            style = {
                'color': 'medium_gray',
                'thickness': 2,
                'alpha': 255
            }
        
        return {
            'color': self.get_color(style['color']),
            'thickness': max(1, int(style['thickness'] * self.base_scale)),
            'alpha': style['alpha']
        }
    
    def draw_border(self, surface: pygame.Surface, rect: pygame.Rect, 
                   element_type: UIElementType, state: UIState = UIState.NORMAL):
        """Draw a border around a rectangle with theme styling."""
        style = self.get_border_style(element_type, state)
        
        # Create a surface for the border if alpha is needed
        if style['alpha'] < 255 and self.alpha_enabled:
            border_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(border_surface, (*style['color'], style['alpha']), 
                           (0, 0, rect.width, rect.height), style['thickness'])
            surface.blit(border_surface, rect.topleft)
        else:
            pygame.draw.rect(surface, style['color'], rect, style['thickness'])
    
    def draw_panel_background(self, surface: pygame.Surface, rect: pygame.Rect, 
                            alpha: int = 180):
        """Draw a standard panel background."""
        if alpha < 255 and self.alpha_enabled:
            panel_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            panel_surface.fill((*self.colors['panel_bg'], alpha))
            surface.blit(panel_surface, rect.topleft)
        else:
            pygame.draw.rect(surface, self.colors['panel_bg'], rect)
    
    def get_text_color(self, element_type: UIElementType, state: UIState = UIState.NORMAL) -> Tuple[int, int, int]:
        """Get appropriate text color for a UI element."""
        text_colors = {
            UIElementType.SHIP_STATUS: (200, 200, 255),
            UIElementType.NAVIGATION: (200, 255, 200),
            UIElementType.MISSION_TRACKER: (255, 200, 100),
            UIElementType.DEV_VIEW: (255, 255, 255),
            UIElementType.MINIMAP: (255, 255, 255),
            UIElementType.LARGE_MAP: (255, 255, 255),
            UIElementType.STATUS_BAR: (255, 255, 255),
            UIElementType.SELECTION_HIGHLIGHT: (255, 255, 255),
            UIElementType.INPUT_BOX: (255, 255, 255),
            UIElementType.BUTTON: (255, 255, 255)
        }
        
        base_color = text_colors.get(element_type, (255, 255, 255))
        
        # Modify color based on state
        if state == UIState.HOVER:
            return tuple(min(255, c + 30) for c in base_color)
        elif state == UIState.DISABLED:
            return tuple(max(50, c - 100) for c in base_color)
        
        return base_color
    
    def update_scale(self, new_scale: float):
        """Update the base scale for responsive design."""
        self.base_scale = new_scale
    
    def set_alpha_enabled(self, enabled: bool):
        """Enable or disable alpha blending for performance."""
        self.alpha_enabled = enabled


# Global theme instance
ui_theme = UITheme()