import logging
from enum import Enum, auto

import pygame
from src.docking.docking_state import DockingResult
try:
    from ..trading.commodity import commodity_registry
    from ..systems.cloaking_system import cloaking_system
    from ..systems.repair_system import repair_system
    from ..input.control_schemes import control_scheme_manager
except ImportError:
    from trading.commodity import commodity_registry
    from systems.cloaking_system import cloaking_system
    from systems.repair_system import repair_system
    from input.control_schemes import control_scheme_manager

logger = logging.getLogger(__name__)


class GameStates(Enum):
    MAIN_MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    TRADING = auto()  # Added for market interface
    UPGRADES = auto()  # Added for ship upgrade interface
    MISSIONS = auto()  # Added for mission board
    SETTINGS = auto()  # Added for settings menu
    SAVE_GAME = auto()  # Added for save menu
    LOAD_GAME = auto()  # Added for load menu
    BASE_CONSTRUCTION = auto()  # Added for base building
    GAME_OVER = auto()
    DIALOGUE = auto()  # Added for story/NPC conversations
    LOGBOOK = auto()  # Added for the story/contacts/factions logbook
    VICTORY = auto()  # Campaign complete

class State:
    def __init__(self, game):
        self.game = game

    def update(self, delta_time):
        pass

    def render(self, screen):
        pass

    def handle_input(self, event):
        pass

class MenuState(State):
    def __init__(self, game):
        super().__init__(game)
        from ..ui.menu_kit import MenuList, Ui, BASE_SIZE
        from ..ui.menu_style import MenuBackground
        self.title = "Space Trading Simulator"
        self.tagline = "Trade. Explore. Survive."
        self.menu = MenuList(["New Game", "Load Game", "Settings", "Exit"])
        self.background = MenuBackground()
        self._ui = Ui(BASE_SIZE)

    @property
    def menu_options(self):
        return self.menu.items

    @property
    def selected_option(self):
        return self.menu.selected

    @selected_option.setter
    def selected_option(self, value):
        self.menu.selected = value

    @property
    def option_rects(self):
        return [self.menu.rects[i] for i in sorted(self.menu.rects)]

    def render(self, screen):
        from ..ui.menu_kit import ui_for
        from ..ui.menu_style import ACCENT_BLUE
        from ..ui import gfx

        ui = self._ui = ui_for(screen, self.game)
        self.background.draw(screen)

        # Title with a soft accent underline, tagline beneath
        title_font = ui.font("display")
        title = title_font.render(self.title, True, (235, 240, 255))
        title_rect = title.get_rect(midtop=(ui.width // 2, max(ui.px(40), round(ui.height * 0.13))))
        gfx.draw_glow(screen, title_rect.center, max(40, title_rect.height * 2), ACCENT_BLUE, 0.10)
        screen.blit(title, title_rect)
        line_y = title_rect.bottom + ui.px(10)
        pygame.draw.line(screen, ACCENT_BLUE, (title_rect.left, line_y), (title_rect.right, line_y), max(1, ui.px(2)))
        tagline = ui.text(screen, self.tagline, "heading", (140, 170, 220),
                          midtop=(ui.width // 2, line_y + ui.px(14)))

        # The options share what is left of the screen below the title
        area = pygame.Rect(0, tagline.bottom + ui.px(30), ui.width, 0)
        area.height = max(ui.px(120), ui.height - ui.px(80) - area.top)
        self.menu.layout(ui, area, row_units=64)
        self.menu.draw(ui, screen)

        ui.footer(screen, "UP / DOWN to choose, ENTER to select")

        # Current world seed in the bottom right
        if hasattr(self.game, 'world_seed') and self.game.world_seed is not None:
            ui.text(screen, f"World Seed: {self.game.world_seed}", "small", (110, 120, 140),
                    bottomright=(ui.width - ui.px(14), ui.height - ui.px(12)))

    def handle_input(self, event):
        chosen = self.menu.handle(event, self._ui)
        if chosen is not None:
            self._select_option()

    def _select_option(self):
        """Handle option selection"""
        if self.selected_option == 0:  # New Game
            self.game.create_new_universe()  # Create a new universe with random seed
            self.game.change_state(GameStates.PLAYING)
        elif self.selected_option == 1:  # Load Game
            self.game.change_state(GameStates.LOAD_GAME)
        elif self.selected_option == 2:  # Settings
            self.game.change_state(GameStates.SETTINGS)
        elif self.selected_option == 3:  # Exit
            self.game.running = False

class GameOverState(State):
    """Permadeath end screen, shown when the ship is destroyed on Extreme difficulty."""
    def __init__(self, game):
        super().__init__(game)
        from ..ui.menu_kit import MenuList, Ui, BASE_SIZE
        self.title = "GAME OVER"
        self.menu = MenuList(["Return to Main Menu", "Exit"])
        self._ui = Ui(BASE_SIZE)

    @property
    def menu_options(self):
        return self.menu.items

    @property
    def selected_option(self):
        return self.menu.selected

    @property
    def option_rects(self):
        return [self.menu.rects[i] for i in sorted(self.menu.rects)]

    def render(self, screen):
        from ..ui.menu_kit import ui_for
        ui = self._ui = ui_for(screen, self.game)
        screen.fill((20, 0, 0))  # Dark red background
        cx = ui.width // 2

        title = ui.text(screen, self.title, "display", (220, 40, 40),
                        midtop=(cx, max(ui.px(40), round(ui.height * 0.12))))
        subtitle = ui.text(screen, "Your ship was destroyed. Extreme difficulty offers no second chances.",
                           "body", (200, 150, 150), max_width=ui.width - 2 * ui.margin(),
                           midtop=(cx, title.bottom + ui.px(16)))

        # Run stats
        credits = self.game.ship.credits if getattr(self.game, 'ship', None) else 0
        play_time = getattr(self.game, 'play_time', 0.0)
        minutes, seconds = divmod(int(play_time), 60)
        y = subtitle.bottom + ui.px(34)
        for line in (f"Final Credits: {credits}", f"Time Survived: {minutes}m {seconds}s"):
            rect = ui.text(screen, line, "heading", (220, 220, 220), midtop=(cx, y))
            y = rect.bottom + ui.px(8)

        area = pygame.Rect(0, y + ui.px(24), ui.width, 0)
        area.height = max(ui.px(110), ui.height - ui.px(50) - area.top)
        self.menu.layout(ui, area, row_units=64)
        self.menu.draw(ui, screen)

    def handle_input(self, event):
        chosen = self.menu.handle(event, self._ui, play_sounds=False)
        if chosen is not None:
            self._select_option()

    def _select_option(self):
        if self.selected_option == 0:  # Return to Main Menu
            self.game.change_state(GameStates.MAIN_MENU)
        elif self.selected_option == 1:  # Exit
            self.game.running = False


class SettingsState(State):
    def __init__(self, game, previous_state=None):
        super().__init__(game)
        from ..settings import game_settings, CameraMode
        self.settings = game_settings
        self.title = "Settings"
        self.categories = ["Camera", "Display", "Controls", "Audio", "Difficulty", "Dev View", "Help", "Back"]
        self.selected_category = 0

        # Track where settings was accessed from to return properly
        self.previous_state = previous_state or GameStates.MAIN_MENU

        # Camera settings options
        self.camera_options = ["Camera Mode", "Smoothing", "Deadzone", "Back"]
        self.selected_camera_option = 0
        self.viewing_camera = False

        # Display settings options
        self.display_options = ["Resolution", "Display Mode", "HUD Scale", "Back"]
        self.selected_display_option = 0
        self.viewing_display = False
        self.display_rects = []

        # Control scheme settings options
        self.control_options = ["Control Scheme", "Show Controls", "Back"]
        self.selected_control_option = 0
        self.viewing_controls = False

        # Difficulty settings options
        self.difficulty_options = ["Difficulty Level", "Back"]
        self.selected_difficulty_option = 0
        self.viewing_difficulty = False
        self.difficulty_rects = []

        # Audio settings options
        self.audio_options = ["Master Volume", "SFX Volume", "Music Volume", "Back"]
        self.selected_audio_option = 0
        self.viewing_audio = False
        self.audio_rects = []
        
        # Dev view settings options
        self.dev_options = ["Enable Dev View", "Show FPS", "Show Ship Pos", "Show Docking", "Show Stations", "Show Camera", "Back"]
        self.selected_dev_option = 0
        self.viewing_dev = False
        
        # Help options
        self.help_options = ["Controls", "Keybinds", "Back"]
        self.selected_help_option = 0
        self.viewing_help = False
        
        # Mouse interaction rectangles
        self.category_rects = []
        self.camera_rects = []
        self.control_rects = []
        self.dev_rects = []
        self.help_rects = []

        from ..ui.menu_style import MenuBackground
        self.background = MenuBackground()

    def render(self, screen):
        from ..ui.menu_style import draw_title

        self.background.draw(screen)
        draw_title(screen, self.title.upper(), y=70)

        if not self.viewing_camera and not self.viewing_dev and not self.viewing_controls and not self.viewing_help and not self.viewing_difficulty and not self.viewing_audio and not self.viewing_display:
            self._render_main_categories(screen)
        elif self.viewing_camera:
            self._render_camera_settings(screen)
        elif self.viewing_display:
            self._render_display_settings(screen)
        elif self.viewing_controls:
            self._render_control_settings(screen)
        elif self.viewing_audio:
            self._render_audio_settings(screen)
        elif self.viewing_difficulty:
            self._render_difficulty_settings(screen)
        elif self.viewing_dev:
            self._render_dev_settings(screen)
        elif self.viewing_help:
            self._render_help_settings(screen)
    
    def _render_main_categories(self, screen):
        """Render main settings categories"""
        option_font = pygame.font.Font(None, 48)
        self.category_rects = []  # Reset rectangles
        for i, category in enumerate(self.categories):
            color = (255, 255, 0) if i == self.selected_category else (255, 255, 255)
            text = option_font.render(category, True, color)
            text_rect = text.get_rect(center=(screen.get_width() // 2, 200 + i * 60))
            screen.blit(text, text_rect)
            
            # Store expanded rectangle for mouse interaction
            expanded_rect = text_rect.inflate(40, 20)
            self.category_rects.append(expanded_rect)
    
    def _render_camera_settings(self, screen):
        """Render camera settings submenu"""
        option_font = pygame.font.Font(None, 40)
        small_font = pygame.font.Font(None, 28)
        
        # Draw camera settings title
        subtitle = option_font.render("Camera Settings", True, (200, 200, 255))
        subtitle_rect = subtitle.get_rect(center=(screen.get_width() // 2, 150))
        screen.blit(subtitle, subtitle_rect)
        
        y_offset = 220
        for i, option in enumerate(self.camera_options):
            color = (255, 255, 0) if i == self.selected_camera_option else (255, 255, 255)
            extra_spacing = 0

            if option == "Camera Mode":
                mode_text = f"Camera Mode: {self.settings.camera_mode.value}"
                text = option_font.render(mode_text, True, color)

            elif option == "Smoothing":
                if self.settings.camera_mode.name == "SMOOTH":
                    smooth_text = f"Smoothing: {self.settings.camera_smoothing:.2f}"
                    color = color if self.settings.camera_mode.name == "SMOOTH" else (100, 100, 100)
                else:
                    smooth_text = f"Smoothing: {self.settings.camera_smoothing:.2f} (N/A)"
                    color = (100, 100, 100)
                text = option_font.render(smooth_text, True, color)

            elif option == "Deadzone":
                if self.settings.camera_mode.name == "DEADZONE":
                    deadzone_text = f"Deadzone: {self.settings.camera_deadzone_radius}px"
                    color = color if self.settings.camera_mode.name == "DEADZONE" else (100, 100, 100)
                else:
                    deadzone_text = f"Deadzone: {self.settings.camera_deadzone_radius}px (N/A)"
                    color = (100, 100, 100)
                text = option_font.render(deadzone_text, True, color)

            else:  # Back
                text = option_font.render(option, True, color)

            text_rect = text.get_rect(center=(screen.get_width() // 2, y_offset))
            screen.blit(text, text_rect)

            if option == "Camera Mode":
                # Add description below the option, without overlapping the next one
                desc = small_font.render(self.settings.get_camera_description(), True, (150, 150, 150))
                desc_rect = desc.get_rect(center=(screen.get_width() // 2, y_offset + 25))
                screen.blit(desc, desc_rect)
                extra_spacing = 25

            y_offset += 60 + extra_spacing
        
        # Instructions
        instruction_font = pygame.font.Font(None, 24)
        instructions = "Use LEFT/RIGHT to change values, ENTER to select, ESC to go back"
        instr_text = instruction_font.render(instructions, True, (150, 150, 150))
        instr_rect = instr_text.get_rect(center=(screen.get_width() // 2, screen.get_height() - 40))
        screen.blit(instr_text, instr_rect)
    
    def _render_control_settings(self, screen):
        """Render control scheme settings submenu"""
        option_font = pygame.font.Font(None, 40)
        small_font = pygame.font.Font(None, 28)
        
        # Draw control settings title
        subtitle = option_font.render("Control Settings", True, (200, 200, 255))
        subtitle_rect = subtitle.get_rect(center=(screen.get_width() // 2, 150))
        screen.blit(subtitle, subtitle_rect)
        
        y_offset = 220
        self.control_rects = []  # Reset rectangles
        
        for i, option in enumerate(self.control_options):
            color = (255, 255, 0) if i == self.selected_control_option else (255, 255, 255)
            extra_spacing = 0

            if option == "Control Scheme":
                scheme_info = control_scheme_manager.get_scheme_info()
                scheme_text = f"Control Scheme: {scheme_info['name']}"
                text = option_font.render(scheme_text, True, color)

            elif option == "Show Controls":
                text = option_font.render("Show Current Controls", True, color)

            else:  # Back
                text = option_font.render(option, True, color)

            text_rect = text.get_rect(center=(screen.get_width() // 2, y_offset))
            screen.blit(text, text_rect)

            if option == "Control Scheme":
                # Add description below the option, without overlapping the next one
                desc = small_font.render(scheme_info['description'], True, (150, 150, 150))
                desc_rect = desc.get_rect(center=(screen.get_width() // 2, y_offset + 25))
                screen.blit(desc, desc_rect)
                extra_spacing = 25

            # Store expanded rectangle for mouse interaction
            expanded_rect = text_rect.inflate(40, 20)
            self.control_rects.append(expanded_rect)
            y_offset += 60 + extra_spacing
        
        # Show current control scheme bindings
        if self.control_options[self.selected_control_option] == "Show Controls":
            self._render_current_controls(screen, y_offset + 40)
        
        # Instructions
        instruction_font = pygame.font.Font(None, 24)
        instructions = "Use LEFT/RIGHT to change control scheme, ENTER to select, ESC to go back"
        instr_text = instruction_font.render(instructions, True, (150, 150, 150))
        instr_rect = instr_text.get_rect(center=(screen.get_width() // 2, screen.get_height() - 40))
        screen.blit(instr_text, instr_rect)
    
    def _render_current_controls(self, screen, start_y):
        """Render current control scheme bindings"""
        small_font = pygame.font.Font(None, 24)
        controls_help = control_scheme_manager.get_controls_help()
        
        x_left = screen.get_width() // 2 - 200
        x_right = screen.get_width() // 2 + 200
        
        y_offset = start_y
        for section_name, controls in controls_help.items():
            # Section header
            section_text = small_font.render(section_name, True, (200, 255, 200))
            section_rect = section_text.get_rect(center=(x_left if len(controls_help) > 3 else screen.get_width() // 2, y_offset))
            screen.blit(section_text, section_rect)
            y_offset += 25
            
            # Controls in section
            for key, description in controls.items():
                control_text = f"{key}: {description}"
                control_surface = small_font.render(control_text, True, (255, 255, 255))
                control_rect = control_surface.get_rect(center=(x_left if len(controls_help) > 3 else screen.get_width() // 2, y_offset))
                screen.blit(control_surface, control_rect)
                y_offset += 20
            
            y_offset += 10  # Extra spacing between sections
    
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.viewing_camera:
                    self.viewing_camera = False
                elif self.viewing_display:
                    self.viewing_display = False
                elif self.viewing_controls:
                    self.viewing_controls = False
                elif self.viewing_audio:
                    self.viewing_audio = False
                elif self.viewing_difficulty:
                    self.viewing_difficulty = False
                elif self.viewing_dev:
                    self.viewing_dev = False
                elif self.viewing_help:
                    self.viewing_help = False
                else:
                    self.game.change_state(self.previous_state)
            elif not self.viewing_camera and not self.viewing_controls and not self.viewing_audio and not self.viewing_difficulty and not self.viewing_dev and not self.viewing_help and not self.viewing_display:
                self._handle_main_input(event)
            elif self.viewing_camera:
                self._handle_camera_input(event)
            elif self.viewing_display:
                self._handle_display_input(event)
            elif self.viewing_controls:
                self._handle_control_input(event)
            elif self.viewing_audio:
                self._handle_audio_input(event)
            elif self.viewing_difficulty:
                self._handle_difficulty_input(event)
            elif self.viewing_dev:
                self._handle_dev_input(event)
            elif self.viewing_help:
                self._handle_help_input(event)
        elif event.type == pygame.MOUSEMOTION:
            # Check for mouse hover on options
            mouse_pos = pygame.mouse.get_pos()
            if not self.viewing_camera and not self.viewing_controls and not self.viewing_audio and not self.viewing_difficulty and not self.viewing_dev and not self.viewing_help and not self.viewing_display:
                for i, rect in enumerate(self.category_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected_category = i
                        break
            elif self.viewing_display:
                for i, rect in enumerate(self.display_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected_display_option = i
                        break
            elif self.viewing_controls:
                for i, rect in enumerate(self.control_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected_control_option = i
                        break
            elif self.viewing_audio:
                for i, rect in enumerate(self.audio_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected_audio_option = i
                        break
            elif self.viewing_difficulty:
                for i, rect in enumerate(self.difficulty_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected_difficulty_option = i
                        break
            elif self.viewing_help:
                for i, rect in enumerate(self.help_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected_help_option = i
                        break
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = pygame.mouse.get_pos()
                if not self.viewing_camera and not self.viewing_controls and not self.viewing_audio and not self.viewing_difficulty and not self.viewing_dev and not self.viewing_help and not self.viewing_display:
                    for i, rect in enumerate(self.category_rects):
                        if rect.collidepoint(mouse_pos):
                            self.selected_category = i
                            self._select_main_option()
                            break
                elif self.viewing_display:
                    for i, rect in enumerate(self.display_rects):
                        if rect.collidepoint(mouse_pos):
                            self.selected_display_option = i
                            self._select_display_option()
                            break
                elif self.viewing_controls:
                    for i, rect in enumerate(self.control_rects):
                        if rect.collidepoint(mouse_pos):
                            self.selected_control_option = i
                            self._select_control_option()
                            break
                elif self.viewing_audio:
                    for i, rect in enumerate(self.audio_rects):
                        if rect.collidepoint(mouse_pos):
                            self.selected_audio_option = i
                            self._select_audio_option()
                            break
                elif self.viewing_difficulty:
                    for i, rect in enumerate(self.difficulty_rects):
                        if rect.collidepoint(mouse_pos):
                            self.selected_difficulty_option = i
                            self._select_difficulty_option()
                            break
                elif self.viewing_help:
                    for i, rect in enumerate(self.help_rects):
                        if rect.collidepoint(mouse_pos):
                            self.selected_help_option = i
                            self._select_help_option()
                            break
    
    def _handle_main_input(self, event):
        """Handle input for main settings categories"""
        if event.key == pygame.K_UP:
            self.selected_category = (self.selected_category - 1) % len(self.categories)
        elif event.key == pygame.K_DOWN:
            self.selected_category = (self.selected_category + 1) % len(self.categories)
        elif event.key == pygame.K_RETURN:
            self._select_main_option()
    
    def _select_main_option(self):
        """Handle main option selection"""
        category = self.categories[self.selected_category]
        if category == "Camera":
            self.viewing_camera = True
            self.selected_camera_option = 0
        elif category == "Display":
            self.viewing_display = True
            self.selected_display_option = 0
        elif category == "Controls":
            self.viewing_controls = True
            self.selected_control_option = 0
        elif category == "Audio":
            self.viewing_audio = True
            self.selected_audio_option = 0
        elif category == "Difficulty":
            self.viewing_difficulty = True
            self.selected_difficulty_option = 0
        elif category == "Dev View":
            self.viewing_dev = True
            self.selected_dev_option = 0
        elif category == "Help":
            self.viewing_help = True
            self.selected_help_option = 0
        elif category == "Back":
            self.game.change_state(self.previous_state)
    
    def _handle_camera_input(self, event):
        """Handle input for camera settings"""
        from ..settings import CameraMode
        
        if event.key == pygame.K_UP:
            self.selected_camera_option = (self.selected_camera_option - 1) % len(self.camera_options)
        elif event.key == pygame.K_DOWN:
            self.selected_camera_option = (self.selected_camera_option + 1) % len(self.camera_options)
        elif event.key == pygame.K_LEFT:
            self._adjust_camera_setting(-1)
        elif event.key == pygame.K_RIGHT:
            self._adjust_camera_setting(1)
        elif event.key == pygame.K_RETURN:
            if self.selected_camera_option == 3:  # Back
                self.viewing_camera = False
    
    def _adjust_camera_setting(self, direction):
        """Adjust camera setting values"""
        from ..settings import CameraMode
        
        if self.selected_camera_option == 0:  # Camera Mode
            modes = list(CameraMode)
            current_index = modes.index(self.settings.camera_mode)
            new_index = (current_index + direction) % len(modes)
            self.settings.camera_mode = modes[new_index]
            self.settings.save()
            
        elif self.selected_camera_option == 1:  # Smoothing
            if self.settings.camera_mode.name == "SMOOTH":
                self.settings.camera_smoothing = max(0.01, min(1.0, 
                    self.settings.camera_smoothing + direction * 0.05))
                self.settings.save()
                
        elif self.selected_camera_option == 2:  # Deadzone
            if self.settings.camera_mode.name == "DEADZONE":
                self.settings.camera_deadzone_radius = max(10, min(200,
                    self.settings.camera_deadzone_radius + direction * 10))
                self.settings.save()

    def _render_display_settings(self, screen):
        """Render display settings submenu"""
        from ..settings import DisplayMode

        option_font = pygame.font.Font(None, 40)
        small_font = pygame.font.Font(None, 28)

        subtitle = option_font.render("Display Settings", True, (200, 200, 255))
        subtitle_rect = subtitle.get_rect(center=(screen.get_width() // 2, 150))
        screen.blit(subtitle, subtitle_rect)

        y_offset = 220
        self.display_rects = []
        windowed = self.settings.display_mode == DisplayMode.WINDOWED

        for i, option in enumerate(self.display_options):
            color = (255, 255, 0) if i == self.selected_display_option else (255, 255, 255)
            desc = None

            if option == "Resolution":
                if windowed:
                    res_text = f"Resolution: {self.settings.window_width}x{self.settings.window_height}"
                else:
                    res_text = f"Resolution: {self.settings.window_width}x{self.settings.window_height} (N/A, matches desktop)"
                    color = (100, 100, 100)
                text = option_font.render(res_text, True, color)

            elif option == "Display Mode":
                text = option_font.render(f"Display Mode: {self.settings.display_mode.value}", True, color)

            elif option == "HUD Scale":
                text = option_font.render(f"HUD Scale: {self.settings.hud_scale:.2f}x", True, color)
                desc = "Scales the flight HUD panels' text and size - menus are unaffected"

            else:  # Back
                text = option_font.render(option, True, color)

            text_rect = text.get_rect(center=(screen.get_width() // 2, y_offset))
            screen.blit(text, text_rect)
            self.display_rects.append(text_rect.inflate(40, 20))
            extra_spacing = 0

            if desc:
                desc_surface = small_font.render(desc, True, (150, 150, 150))
                desc_rect = desc_surface.get_rect(center=(screen.get_width() // 2, y_offset + 25))
                screen.blit(desc_surface, desc_rect)
                extra_spacing = 25

            y_offset += 60 + extra_spacing

        instruction_font = pygame.font.Font(None, 24)
        instructions = "Use LEFT/RIGHT to change values, ENTER to select, ESC to go back"
        instr_text = instruction_font.render(instructions, True, (150, 150, 150))
        instr_rect = instr_text.get_rect(center=(screen.get_width() // 2, screen.get_height() - 40))
        screen.blit(instr_text, instr_rect)

    def _handle_display_input(self, event):
        """Handle input for display settings"""
        if event.key == pygame.K_UP:
            self.selected_display_option = (self.selected_display_option - 1) % len(self.display_options)
        elif event.key == pygame.K_DOWN:
            self.selected_display_option = (self.selected_display_option + 1) % len(self.display_options)
        elif event.key == pygame.K_LEFT:
            self._adjust_display_setting(-1)
        elif event.key == pygame.K_RIGHT:
            self._adjust_display_setting(1)
        elif event.key == pygame.K_RETURN:
            self._select_display_option()

    def _select_display_option(self):
        """Handle display option selection"""
        if self.display_options[self.selected_display_option] == "Back":
            self.viewing_display = False

    def _adjust_display_setting(self, direction):
        """Adjust the selected display setting"""
        from ..settings import DisplayMode

        option = self.display_options[self.selected_display_option]

        if option == "Resolution":
            if self.settings.display_mode != DisplayMode.WINDOWED:
                return
            width, height = self.settings.next_resolution(direction)
            self.settings.set_resolution(width, height)
            self.settings.save()
            self.game._update_display()

        elif option == "Display Mode":
            modes = list(DisplayMode)
            current_index = modes.index(self.settings.display_mode)
            new_index = (current_index + direction) % len(modes)
            self.settings.display_mode = modes[new_index]
            self.settings.save()
            self.game._update_display()

        elif option == "HUD Scale":
            new_scale = max(0.75, min(1.75, round(self.settings.hud_scale + direction * 0.1, 2)))
            self.settings.hud_scale = new_scale
            self.settings.save()
            self.game._update_display()

    def _render_dev_settings(self, screen):
        """Render dev view settings submenu"""
        option_font = pygame.font.Font(None, 40)
        small_font = pygame.font.Font(None, 28)
        
        # Draw dev settings title
        subtitle = option_font.render("Dev View Settings", True, (200, 200, 255))
        subtitle_rect = subtitle.get_rect(center=(screen.get_width() // 2, 150))
        screen.blit(subtitle, subtitle_rect)
        
        y_offset = 220
        for i, option in enumerate(self.dev_options):
            color = (255, 255, 0) if i == self.selected_dev_option else (255, 255, 255)
            
            if option == "Enable Dev View":
                dev_text = f"Enable Dev View: {'ON' if self.settings.dev_view_enabled else 'OFF'}"
                text = option_font.render(dev_text, True, color)
            elif option == "Show FPS":
                fps_text = f"Show FPS: {'ON' if self.settings.dev_show_fps else 'OFF'}"
                enabled_color = color if self.settings.dev_view_enabled else (100, 100, 100)
                text = option_font.render(fps_text, True, enabled_color)
            elif option == "Show Ship Pos":
                ship_text = f"Show Ship Position: {'ON' if self.settings.dev_show_ship_pos else 'OFF'}"
                enabled_color = color if self.settings.dev_view_enabled else (100, 100, 100)
                text = option_font.render(ship_text, True, enabled_color)
            elif option == "Show Docking":
                dock_text = f"Show Docking: {'ON' if self.settings.dev_show_docking else 'OFF'}"
                enabled_color = color if self.settings.dev_view_enabled else (100, 100, 100)
                text = option_font.render(dock_text, True, enabled_color)
            elif option == "Show Stations":
                station_text = f"Show Stations: {'ON' if self.settings.dev_show_stations else 'OFF'}"
                enabled_color = color if self.settings.dev_view_enabled else (100, 100, 100)
                text = option_font.render(station_text, True, enabled_color)
            elif option == "Show Camera":
                camera_text = f"Show Camera: {'ON' if self.settings.dev_show_camera else 'OFF'}"
                enabled_color = color if self.settings.dev_view_enabled else (100, 100, 100)
                text = option_font.render(camera_text, True, enabled_color)
            else:  # Back
                text = option_font.render(option, True, color)
            
            text_rect = text.get_rect(center=(screen.get_width() // 2, y_offset))
            screen.blit(text, text_rect)
            y_offset += 50
        
        # Instructions
        instruction_font = pygame.font.Font(None, 24)
        instructions = "Use LEFT/RIGHT to toggle, ENTER to select, ESC to go back"
        instr_text = instruction_font.render(instructions, True, (150, 150, 150))
        instr_rect = instr_text.get_rect(center=(screen.get_width() // 2, screen.get_height() - 40))
        screen.blit(instr_text, instr_rect)
        
        # Dev view status
        if self.settings.dev_view_enabled:
            status_text = "Press F4 in-game to toggle Dev View"
            status_surface = small_font.render(status_text, True, (150, 255, 150))
            status_rect = status_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() - 70))
            screen.blit(status_surface, status_rect)
    
    def _handle_control_input(self, event):
        """Handle input for control scheme settings"""
        if event.key == pygame.K_UP:
            self.selected_control_option = (self.selected_control_option - 1) % len(self.control_options)
        elif event.key == pygame.K_DOWN:
            self.selected_control_option = (self.selected_control_option + 1) % len(self.control_options)
        elif event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
            self._change_control_scheme()
        elif event.key == pygame.K_RETURN:
            self._select_control_option()
    
    def _select_control_option(self):
        """Handle control option selection"""
        if self.selected_control_option == len(self.control_options) - 1:  # Back
            self.viewing_controls = False
        elif self.control_options[self.selected_control_option] == "Control Scheme":
            self._change_control_scheme()
        # "Show Controls" is handled by the rendering method
    
    def _change_control_scheme(self):
        """Cycle through available control schemes"""
        from ..input.control_schemes import ControlScheme
        
        current_scheme = control_scheme_manager.get_current_scheme()
        all_schemes = list(ControlScheme)
        current_index = all_schemes.index(current_scheme)
        
        # Cycle to next scheme
        next_index = (current_index + 1) % len(all_schemes)
        next_scheme = all_schemes[next_index]

        control_scheme_manager.set_scheme(next_scheme)

    def _render_difficulty_settings(self, screen):
        """Render difficulty settings submenu"""
        from ..difficulty.difficulty_manager import difficulty_manager

        option_font = pygame.font.Font(None, 40)
        small_font = pygame.font.Font(None, 26)

        subtitle = option_font.render("Difficulty Settings", True, (200, 200, 255))
        subtitle_rect = subtitle.get_rect(center=(screen.get_width() // 2, 150))
        screen.blit(subtitle, subtitle_rect)

        difficulty_descriptions = {
            "peaceful": "No enemies, reduced hazards - explore and trade in safety",
            "easy": "Fewer enemies, lighter damage - a gentler galaxy",
            "normal": "The intended balance",
            "hard": "More frequent, tougher enemies and higher damage",
            "extreme": "Maximum danger - ship destruction ends the game permanently",
        }

        y_offset = 220
        self.difficulty_rects = []

        for i, option in enumerate(self.difficulty_options):
            color = (255, 255, 0) if i == self.selected_difficulty_option else (255, 255, 255)
            extra_spacing = 0

            if option == "Difficulty Level":
                level_name = difficulty_manager.current_difficulty.value.upper()
                level_color = (255, 80, 80) if difficulty_manager.current_difficulty.value == "extreme" else color
                level_text = f"Difficulty: {level_name}"
                text = option_font.render(level_text, True, level_color)
            else:  # Back
                text = option_font.render(option, True, color)

            text_rect = text.get_rect(center=(screen.get_width() // 2, y_offset))
            screen.blit(text, text_rect)
            self.difficulty_rects.append(text_rect.inflate(40, 20))

            if option == "Difficulty Level":
                # Add description below the option, without overlapping the next one
                desc = small_font.render(
                    difficulty_descriptions.get(difficulty_manager.current_difficulty.value, ""),
                    True, (170, 170, 170)
                )
                desc_rect = desc.get_rect(center=(screen.get_width() // 2, y_offset + 28))
                screen.blit(desc, desc_rect)
                extra_spacing = 28

            y_offset += 60 + extra_spacing

        instruction_font = pygame.font.Font(None, 24)
        instructions = "Use LEFT/RIGHT to change difficulty, ENTER to select, ESC to go back"
        instr_text = instruction_font.render(instructions, True, (150, 150, 150))
        instr_rect = instr_text.get_rect(center=(screen.get_width() // 2, screen.get_height() - 40))
        screen.blit(instr_text, instr_rect)

    def _handle_difficulty_input(self, event):
        """Handle input for difficulty settings"""
        if event.key == pygame.K_UP:
            self.selected_difficulty_option = (self.selected_difficulty_option - 1) % len(self.difficulty_options)
        elif event.key == pygame.K_DOWN:
            self.selected_difficulty_option = (self.selected_difficulty_option + 1) % len(self.difficulty_options)
        elif event.key == pygame.K_LEFT:
            self._change_difficulty(-1)
        elif event.key == pygame.K_RIGHT:
            self._change_difficulty(1)
        elif event.key == pygame.K_RETURN:
            self._select_difficulty_option()

    def _select_difficulty_option(self):
        """Handle difficulty option selection"""
        if self.difficulty_options[self.selected_difficulty_option] == "Back":
            self.viewing_difficulty = False
        elif self.difficulty_options[self.selected_difficulty_option] == "Difficulty Level":
            self._change_difficulty(1)

    def _change_difficulty(self, direction):
        """Cycle through available difficulty levels"""
        from ..difficulty.difficulty_manager import difficulty_manager, DifficultyLevel

        all_levels = list(DifficultyLevel)
        current_index = all_levels.index(difficulty_manager.current_difficulty)
        next_index = (current_index + direction) % len(all_levels)
        difficulty_manager.set_difficulty(all_levels[next_index])

    def _render_audio_settings(self, screen):
        """Render audio settings submenu"""
        option_font = pygame.font.Font(None, 40)

        subtitle = option_font.render("Audio Settings", True, (200, 200, 255))
        subtitle_rect = subtitle.get_rect(center=(screen.get_width() // 2, 150))
        screen.blit(subtitle, subtitle_rect)

        volume_attrs = {
            "Master Volume": "master_volume",
            "SFX Volume": "sfx_volume",
            "Music Volume": "music_volume",
        }

        y_offset = 220
        self.audio_rects = []

        for i, option in enumerate(self.audio_options):
            color = (255, 255, 0) if i == self.selected_audio_option else (255, 255, 255)

            if option in volume_attrs:
                value = getattr(self.settings, volume_attrs[option])
                text = option_font.render(f"{option}: {int(value * 100)}%", True, color)

                # Draw a simple volume bar
                bar_x = screen.get_width() // 2 - 100
                bar_y = y_offset + 30
                pygame.draw.rect(screen, (60, 60, 80), (bar_x, bar_y, 200, 10))
                pygame.draw.rect(screen, (100, 200, 255), (bar_x, bar_y, int(200 * value), 10))
                y_offset += 20
            else:  # Back
                text = option_font.render(option, True, color)

            text_rect = text.get_rect(center=(screen.get_width() // 2, y_offset))
            screen.blit(text, text_rect)
            self.audio_rects.append(text_rect.inflate(40, 20))
            y_offset += 60

        instruction_font = pygame.font.Font(None, 24)
        instructions = "Use LEFT/RIGHT to adjust volume, ENTER to select, ESC to go back"
        instr_text = instruction_font.render(instructions, True, (150, 150, 150))
        instr_rect = instr_text.get_rect(center=(screen.get_width() // 2, screen.get_height() - 40))
        screen.blit(instr_text, instr_rect)

    def _handle_audio_input(self, event):
        """Handle input for audio settings"""
        if event.key == pygame.K_UP:
            self.selected_audio_option = (self.selected_audio_option - 1) % len(self.audio_options)
        elif event.key == pygame.K_DOWN:
            self.selected_audio_option = (self.selected_audio_option + 1) % len(self.audio_options)
        elif event.key == pygame.K_LEFT:
            self._adjust_audio_setting(-1)
        elif event.key == pygame.K_RIGHT:
            self._adjust_audio_setting(1)
        elif event.key == pygame.K_RETURN:
            self._select_audio_option()

    def _select_audio_option(self):
        """Handle audio option selection"""
        if self.audio_options[self.selected_audio_option] == "Back":
            self.viewing_audio = False

    def _adjust_audio_setting(self, direction):
        """Adjust the selected volume slider"""
        from ..audio.sound_manager import sound_manager

        volume_attrs = ["master_volume", "sfx_volume", "music_volume"]
        if self.selected_audio_option >= len(volume_attrs):
            return

        attr = volume_attrs[self.selected_audio_option]
        new_value = max(0.0, min(1.0, getattr(self.settings, attr) + direction * 0.05))
        setattr(self.settings, attr, round(new_value, 2))
        self.settings.save()
        sound_manager.apply_volumes()
        if attr != "music_volume":
            sound_manager.play("ui_navigate")

    def _handle_dev_input(self, event):
        """Handle input for dev view settings"""
        if event.key == pygame.K_UP:
            self.selected_dev_option = (self.selected_dev_option - 1) % len(self.dev_options)
        elif event.key == pygame.K_DOWN:
            self.selected_dev_option = (self.selected_dev_option + 1) % len(self.dev_options)
        elif event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
            self._toggle_dev_setting()
        elif event.key == pygame.K_RETURN:
            if self.selected_dev_option == len(self.dev_options) - 1:  # Back
                self.viewing_dev = False
            else:
                self._toggle_dev_setting()
    
    def _toggle_dev_setting(self):
        """Toggle the selected dev view setting"""
        if self.selected_dev_option == 0:  # Enable Dev View
            self.settings.dev_view_enabled = not self.settings.dev_view_enabled
        elif self.selected_dev_option == 1 and self.settings.dev_view_enabled:  # Show FPS
            self.settings.dev_show_fps = not self.settings.dev_show_fps
        elif self.selected_dev_option == 2 and self.settings.dev_view_enabled:  # Show Ship Pos
            self.settings.dev_show_ship_pos = not self.settings.dev_show_ship_pos
        elif self.selected_dev_option == 3 and self.settings.dev_view_enabled:  # Show Docking
            self.settings.dev_show_docking = not self.settings.dev_show_docking
        elif self.selected_dev_option == 4 and self.settings.dev_view_enabled:  # Show Stations
            self.settings.dev_show_stations = not self.settings.dev_show_stations
        elif self.selected_dev_option == 5 and self.settings.dev_view_enabled:  # Show Camera
            self.settings.dev_show_camera = not self.settings.dev_show_camera
        
        self.settings.save()
    
    def _handle_help_input(self, event):
        """Handle input for help settings"""
        if event.key == pygame.K_UP:
            self.selected_help_option = (self.selected_help_option - 1) % len(self.help_options)
        elif event.key == pygame.K_DOWN:
            self.selected_help_option = (self.selected_help_option + 1) % len(self.help_options)
        elif event.key == pygame.K_RETURN:
            self._select_help_option()
    
    def _select_help_option(self):
        """Handle help option selection"""
        if self.selected_help_option == 2:  # Back
            self.viewing_help = False
    
    def _render_help_settings(self, screen):
        """Render help settings submenu"""
        option_font = pygame.font.Font(None, 40)
        text_font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 20)
        
        # Draw help settings title
        subtitle = option_font.render("Help & Controls", True, (200, 200, 255))
        subtitle_rect = subtitle.get_rect(center=(screen.get_width() // 2, 150))
        screen.blit(subtitle, subtitle_rect)
        
        y_offset = 220
        self.help_rects = []  # Reset rectangles
        for i, option in enumerate(self.help_options):
            color = (255, 255, 0) if i == self.selected_help_option else (255, 255, 255)
            text = option_font.render(option, True, color)
            text_rect = text.get_rect(center=(screen.get_width() // 2, y_offset))
            screen.blit(text, text_rect)
            
            # Store expanded rectangle for mouse interaction
            expanded_rect = text_rect.inflate(40, 20)
            self.help_rects.append(expanded_rect)
            y_offset += 60
        
        # Show help content based on selected option
        if self.selected_help_option == 0:  # Controls
            self._render_controls_help(screen, text_font, small_font)
        elif self.selected_help_option == 1:  # Keybinds
            self._render_keybinds_help(screen, text_font, small_font)
        
        # Instructions
        instruction_font = pygame.font.Font(None, 24)
        instructions = "Use UP/DOWN to navigate, ENTER to select, ESC to go back"
        instr_text = instruction_font.render(instructions, True, (150, 150, 150))
        instr_rect = instr_text.get_rect(center=(screen.get_width() // 2, screen.get_height() - 40))
        screen.blit(instr_text, instr_rect)
    
    def _render_controls_help(self, screen, text_font, small_font):
        """Render general controls help"""
        y_offset = 400
        help_text = [
            "MOVEMENT:",
            "  Arrow Keys / WASD - Move ship",
            "  Shift - Boost/Thrust",
            "",
            "NAVIGATION:",
            "  TAB - Open/Close large map",
            "  M - Open/Close large map (alt)",
            "  ESC - Pause game",
            "",
            "DOCKING:",
            "  D - Manual dock when near station",
            "  X - Undock from station"
        ]
        
        for text in help_text:
            if text == "":
                y_offset += 15
                continue
            
            color = (255, 255, 0) if text.endswith(":") else (255, 255, 255)
            font = text_font if text.endswith(":") else small_font
            surface = font.render(text, True, color)
            screen.blit(surface, (50, y_offset))
            y_offset += 20
    
    def _render_keybinds_help(self, screen, text_font, small_font):
        """Render keybinds help"""
        y_offset = 400
        keybinds = [
            "GENERAL KEYBINDS:",
            "  F4 - Toggle developer view",
            "  F11 - Toggle fullscreen",
            "  F12 - Toggle FPS display",
            "",
            "DOCKED ACTIONS:",
            "  T - Open trading interface",
            "  U - Open ship upgrades",
            "  M - Open mission board",
            "",
            "MAP CONTROLS:",
            "  Mouse Wheel - Zoom in/out",
            "  Right Click + Drag - Pan map",
            "  Left Click - Select location",
            "  HOME - Reset map view",
            "  +/- - Zoom in/out (keyboard)"
        ]
        
        for text in keybinds:
            if text == "":
                y_offset += 15
                continue
            
            color = (255, 255, 0) if text.endswith(":") else (255, 255, 255)
            font = text_font if text.endswith(":") else small_font
            surface = font.render(text, True, color)
            screen.blit(surface, (50, y_offset))
            y_offset += 20

class PlayingState(State):
    def __init__(self, game):
        super().__init__(game)
        # Initialize enhanced HUD
        from ..ui.hud.enhanced_hud import EnhancedHUD
        from ..ui.large_map import LargeMap
        from ..ui.onboarding_hints import onboarding_hints
        self.enhanced_hud = EnhancedHUD(game.WINDOW_SIZE[0], game.WINDOW_SIZE[1])
        self.large_map = LargeMap(game.WINDOW_SIZE[0], game.WINDOW_SIZE[1])
        self.onboarding_hints = onboarding_hints
        self.onboarding_hints.trigger("flight_controls")

    def update(self, delta_time):
        self.onboarding_hints.update(delta_time)
        from ..ui.notifications import notifications
        notifications.update(delta_time)
        from ..economy_events import economy_events
        economy_events.update(self.game)

        if self.game.docking_manager.is_docked():
            from ..story.director import get_contact_at
            if get_contact_at(self.game.docking_manager.get_target_station(), self.game):
                self.onboarding_hints.trigger("station_contact")

        # Handle ship movement only if not docked
        if not self.game.docking_manager.is_docked():
            self.game.ship.handle_input(delta_time)
            self.game.ship.update(delta_time)

        # Update camera position to follow ship
        self.game.camera.follow(self.game.ship, delta_time)
        
        # Generate new chunks as ship moves
        self.game.universe.ensure_chunks_around_position(self.game.ship.position)
        
        # Update universe (debris physics, etc.)
        self.game.universe.update(delta_time, self.game.ship.position)
        
        # Update docking system
        self.game.docking_manager.update(
            self.game.ship, 
            self.game.universe.stations, 
            delta_time
        )
        
        # Update enhanced HUD
        self.enhanced_hud.update(delta_time, self.game)
        
        # Update repair system
        is_docked = self.game.docking_manager.is_docked()
        repair_system.update(delta_time, self.game.ship, is_docked)
        
        # Check collisions after movement (only if not docking/docked)
        if not self.game.docking_manager.is_docking_in_progress() and not self.game.docking_manager.is_docked():
            for station in self.game.universe.stations:
                if self.game.ship.check_collision_detailed(station):
                    logger.info("Collision detected in PlayingState")
            
            # Check planet collisions
            for planet in self.game.universe.planets:
                if self.game.ship.check_collision_detailed(planet):
                    logger.info("Planet collision detected in PlayingState")
            
            # Check debris collisions with enhanced physics
            from ..systems.debris_field_manager import debris_field_manager
            
            # Get nearby debris for collision checking
            nearby_debris = debris_field_manager.get_debris_at_position(
                self.game.ship.position, self.game.ship.size + 50
            )
            
            for debris in nearby_debris:
                if self.game.ship.check_collision_detailed(debris):
                    logger.info(f"Debris collision detected: {debris.debris_type.value}")
                    
                    # Apply debris physics to ship collision
                    self._handle_ship_debris_collision(debris)
            
            # Also check legacy debris (backward compatibility)
            for debris in self.game.universe.debris:
                if debris not in debris_field_manager.debris_list:
                    if self.game.ship.check_collision_detailed(debris):
                        logger.info("Legacy debris collision detected in PlayingState")
    
    def _handle_ship_debris_collision(self, debris):
        """Handle collision between ship and debris with enhanced physics."""
        from ..systems.debris_field_manager import debris_field_manager
        
        # Calculate collision response for ship
        ship = self.game.ship
        
        # Calculate momentum transfer
        ship_momentum = ship.velocity * ship.mass
        debris_momentum = debris.velocity * debris.mass
        
        # Apply momentum transfer to debris
        momentum_transfer = ship_momentum * 0.1  # Ship transfers some momentum to debris
        debris.velocity += momentum_transfer / debris.mass
        
        # Create collision effects
        debris._create_collision_sparks(debris)  # Visual effects
        
        # Apply damage based on debris type and collision speed
        collision_speed = (ship.velocity - debris.velocity).length()
        
        if debris.debris_type.value == "metal":
            # Metal debris does more damage
            damage = max(1, collision_speed * 0.2)
        elif debris.debris_type.value == "ice":
            # Ice debris does less damage but may fragment
            damage = max(0.5, collision_speed * 0.1)
            if collision_speed > 50:
                fragments = debris.fragment(3)
                for fragment in fragments:
                    debris_field_manager.add_debris(fragment)
        else:
            # Standard damage
            damage = max(1, collision_speed * 0.15)
        
        # Apply damage to ship
        ship.take_damage(damage)
        
        # High-speed collisions might cause debris to fragment
        if collision_speed > 40 and debris.size > 10:
            fragments = debris.fragment()
            if fragments:
                # Remove original debris and add fragments
                if debris in debris_field_manager.debris_list:
                    debris_field_manager.debris_list.remove(debris)
                for fragment in fragments:
                    debris_field_manager.add_debris(fragment)

    def render(self, screen):
        """Render the playing state"""

        # Clear the screen
        screen.fill((0, 0, 20))  # Dark blue background

        # Get camera offset
        camera_offset = self.game.camera.get_offset()

        # Draw starfield first (so it's in background)
        self.game.starfield.draw(screen, camera_offset)

        # Debug visualization removed for cleaner visuals

        # Draw all stations
        for station in self.game.universe.stations:
            screen_pos = self.game.camera.world_to_screen(station.position)
            # Only draw if on screen (with buffer for station size)
            buffer = station.size + 50  # Add buffer for station size and potential visual elements
            if (-buffer <= screen_pos.x <= self.game.WINDOW_SIZE[0] + buffer and 
                -buffer <= screen_pos.y <= self.game.WINDOW_SIZE[1] + buffer):
                station.draw(screen, camera_offset)

                # Draw docking zones and feedback
                self._draw_docking_feedback(screen, station, camera_offset)

        # Draw all planets
        for planet in self.game.universe.planets:
            screen_pos = self.game.camera.world_to_screen(planet.position)
            # Only draw if on screen (with buffer for planet size)
            buffer = planet.size + 50  # Add buffer for planet size
            if (-buffer <= screen_pos.x <= self.game.WINDOW_SIZE[0] + buffer and
                -buffer <= screen_pos.y <= self.game.WINDOW_SIZE[1] + buffer):
                planet.draw(screen, camera_offset)

        # Draw debris using debris field manager
        from ..systems.debris_field_manager import debris_field_manager
        debris_field_manager.draw(screen, camera_offset)

        # Draw legacy debris (backward compatibility)
        for debris in self.game.universe.debris:
            if debris not in debris_field_manager.debris_list:
                screen_pos = self.game.camera.world_to_screen(debris.position)
                # Only draw if on screen (with buffer for debris size)
                buffer = debris.size + 50  # Add buffer for debris size
                if (-buffer <= screen_pos.x <= self.game.WINDOW_SIZE[0] + buffer and
                    -buffer <= screen_pos.y <= self.game.WINDOW_SIZE[1] + buffer):
                    debris.draw(screen, camera_offset)

        # Draw combat entities (asteroids and bandits)
        from ..combat.combat_manager import combat_manager
        combat_manager.draw_entities(screen, camera_offset)

        # Draw ship
        self.game.ship.draw(screen, camera_offset)

        # Draw combat effects (explosions, etc.)
        combat_manager.draw_combat_effects(screen, camera_offset)

        presenter = self.game.presenter
        if presenter is None:
            # Draw minimap last (so it's on top)
            from ..ui.minimap import gather_contacts
            self.game.minimap.draw(screen, self.game.ship,
                                 self.game.universe.stations,
                                 self.game.universe.planets,
                                 gather_contacts(self.game, self.game.minimap.view_radius))

        # Red edge flash right after the player is hit
        from ..ui import gfx as _gfx
        _gfx.draw_edge_flash(screen, (255, 40, 30), getattr(self.game.ship, 'damage_pulse', 0.0) * 0.9)

        if presenter is None:
            # Draw enhanced HUD (on top of everything)
            self.enhanced_hud.render(screen, self.game)
        else:
            # On a Retina display the panels, radar and notifications are drawn
            # later at full resolution; what lives in the world stays here
            self.enhanced_hud.render_pointer(screen, self.game)
            self.enhanced_hud.render_overlays(screen, self.game)
            presenter.queue(self._draw_sharp_hud)

        # Draw large map overlay if visible (should be on top of everything)
        objectives = []
        if self.large_map.visible:
            from ..ui.objective_pointer import all_objectives
            objectives = all_objectives(self.game)
        self.large_map.draw(screen, self.game.ship, self.game.universe.stations, self.game.universe.planets,
                            objectives)

        # Draw respawn UI if ship is destroyed
        from ..systems.respawn_system import respawn_system
        respawn_system.draw_respawn_ui(screen)

        # Draw repair UI if docked and ship needs repair
        if self.game.docking_manager.is_docked():
            target_station = self.game.docking_manager.get_target_station()
            repair_system.draw_repair_ui(screen, self.game.ship, target_station)

        if self.game.presenter is None:
            from ..ui.notifications import notifications
            notifications.render(screen)

        # Draw onboarding hints last, on top of everything
        self.onboarding_hints.render(screen)

    def _sharp_ui(self, size, ratio):
        """The full-resolution HUD and radar for the current pixel size,
        rebuilt when the size or ratio changes."""
        from ..ui.minimap import Minimap
        from ..ui.hud.enhanced_hud import EnhancedHUD
        key = (tuple(size), ratio)
        if getattr(self, "_sharp_key", None) != key:
            self._sharp_hud = EnhancedHUD(size[0], size[1], ratio)
            self._sharp_radar = Minimap(size[0], size[1], ratio=ratio)
            self._sharp_hud.minimap = self._sharp_radar
            self._sharp_key = key
        return self._sharp_hud, self._sharp_radar

    def _draw_sharp_hud(self, pixels, ratio):
        """Draw the radar, panels and notifications at the display's real pixels."""
        from ..ui.minimap import gather_contacts
        from ..ui.notifications import notifications
        hud, radar = self._sharp_ui(pixels.get_size(), ratio)
        hud.update(getattr(self.game, 'delta_time', 0.016), self.game)
        radar.set_view_radius(self.game.minimap.view_radius)
        radar.draw(pixels, self.game.ship, self.game.universe.stations, self.game.universe.planets,
                   gather_contacts(self.game, radar.view_radius))
        hud.render_panels(pixels, self.game)
        notifications.render(pixels, ratio)

    def _draw_docking_feedback(self, screen, station, camera_offset):
        """Draw docking zones and visual feedback for stations."""
        screen_pos = station.position - camera_offset
        docking_manager = self.game.docking_manager
        
        from pygame import Vector2
        from ..ui import docking_visuals as dv
        now = pygame.time.get_ticks() / 1000.0
        center = (int(screen_pos.x), int(screen_pos.y))
        state_name = docking_manager.get_docking_state().value
        is_target = docking_manager.get_target_station() == station

        # Approach zone, only for the station being approached
        approach_radius = station.size + docking_manager.approach_detection_range
        if state_name in ['approaching', 'docking', 'docked'] and is_target:
            dv.dashed_ring(screen, center, approach_radius, dv.APPROACH, -now * 15, 10, 14, 1)

        # Docking zone, coloured by whether you can dock right now
        docking_radius = station.size + self.game.ship.size + docking_manager.docking_range_buffer
        distance = (self.game.ship.position - station.position).length()
        zone_color, _ = dv.zone_status(distance, docking_radius, self.game.ship.velocity.length(),
                                       docking_manager.max_docking_speed)
        if distance <= approach_radius or is_target:
            dv.draw_zone(screen, center, docking_radius, zone_color, now,
                         emphasis=1.0 if distance <= docking_radius else 0.5)

        # While the docking sequence runs, pull the ship in along a beam
        if is_target and state_name in ('docking', 'undocking'):
            duration = max(0.001, docking_manager.docking_duration)
            progress = min(1.0, docking_manager.docking_timer / duration)
            port = Vector2(0, -station.size - 10).rotate(station.rotation) + screen_pos
            ship_screen = self.game.ship.position - camera_offset
            dv.draw_tractor_beam(screen, port, ship_screen, progress, now, reverse=state_name == 'undocking')
            dv.draw_progress_arc(screen, center, station.size + 16,
                                 progress if state_name == 'docking' else 1.0 - progress, dv.CAN_DOCK)

        # Draw status text for target station
        if docking_manager.get_target_station() == station:
            font = pygame.font.Font(None, 24)
            status_message = docking_manager.get_status_message()
            if status_message:
                text_surface = font.render(status_message, True, (255, 255, 255))
                text_rect = text_surface.get_rect()
                text_rect.centerx = int(screen_pos.x)
                text_rect.y = int(screen_pos.y - station.size - 40)
                
                # Draw background for text
                bg_rect = text_rect.inflate(10, 4)
                pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect)
                screen.blit(text_surface, text_rect)
                
        # Draw docking state indicator
        if docking_manager.is_docked() and docking_manager.get_target_station() == station:
            # Draw "DOCKED" indicator
            font = pygame.font.Font(None, 32)
            docked_text = font.render("DOCKED", True, (0, 255, 0))
            text_rect = docked_text.get_rect()
            text_rect.centerx = int(screen_pos.x)
            text_rect.y = int(screen_pos.y + station.size + 10)
            screen.blit(docked_text, text_rect)

            # A story contact waiting at this station
            from ..story.director import get_contact_at
            contact = get_contact_at(station, self.game)
            if contact:
                contact_font = pygame.font.Font(None, 24)
                talk_key = control_scheme_manager.get_key_name("talk")
                contact_text = contact_font.render(
                    f"{contact.name} is here - press {talk_key} to talk", True, (255, 220, 80))
                contact_rect = contact_text.get_rect()
                contact_rect.centerx = int(screen_pos.x)
                contact_rect.y = text_rect.bottom + 6
                screen.blit(contact_text, contact_rect)

    def _draw_debug_info(self, screen, camera_offset):
        """Draw debug information for object positions"""
        font = pygame.font.Font(None, 24)
        y_offset = 30

        # Draw FPS
        fps = self.game.clock.get_fps()
        fps_text = font.render(f"FPS: {int(fps)}", True, (255, 255, 255))
        screen.blit(fps_text, (10, y_offset))
        y_offset += 20

        # Draw ship info
        ship_pos = self.game.ship.position
        ship_speed = self.game.ship.velocity.length()
        ship_text = font.render(
            f"Ship Pos: ({int(ship_pos.x)}, {int(ship_pos.y)}) Speed: {int(ship_speed)}", 
            True, (255, 255, 255))
        screen.blit(ship_text, (10, y_offset))
        y_offset += 20
        
        # Draw docking info
        docking_state = self.game.docking_manager.get_docking_state()
        target_station = self.game.docking_manager.get_target_station()
        docking_text = font.render(
            f"Docking: {docking_state.value}" + 
            (f" -> {target_station.name}" if target_station else ""), 
            True, (255, 255, 255))
        screen.blit(docking_text, (10, y_offset))
        y_offset += 20

    
        # Draw station positions with proper camera offset
        for i, station in enumerate(self.game.universe.stations):
            screen_pos = station.position - camera_offset
            # Create station text for each station
            station_text = font.render(
                f"Station {i}: ({int(station.position.x)}, {int(station.position.y)})", 
                True, (255, 255, 255))
            
            if 0 <= screen_pos.x <= screen.get_width() and 0 <= screen_pos.y <= screen.get_height():
                screen.blit(station_text, (10, y_offset))
                y_offset += 20

                # Draw station position indicator
                pygame.draw.circle(screen, (255, 0, 0), 
                                 (int(screen_pos.x), int(screen_pos.y)), 5)
    
        # Draw camera info
        camera_text = font.render(
            f"Camera: ({int(camera_offset.x)}, {int(camera_offset.y)})", 
            True, (255, 255, 255))
        screen.blit(camera_text, (10, y_offset))
    
        # Debug info (commented out to reduce console spam)
        # print(f"Number of stations: {len(self.game.universe.stations)}")
        # print(f"Ship position: {self.game.ship.position}")
        # print(f"Camera offset: {camera_offset}")

    def handle_input(self, event):
        # Let large map handle input first (if it's visible)
        if self.large_map.handle_input(event, self.game.ship.position):
            return
            
        if event.type == pygame.KEYDOWN:
            self.onboarding_hints.dismiss()

            if event.key == control_scheme_manager.get_key("pause"):
                self.game.change_state(GameStates.PAUSED)
            elif event.key == control_scheme_manager.get_key("toggle_map"):
                self.large_map.toggle_visibility()
                # Center the map on the player when opened
                if self.large_map.visible:
                    self.large_map.center_on_ship(self.game.ship.position)
            elif event.key == control_scheme_manager.get_key("dock"):
                result = self.game.docking_manager.attempt_manual_docking(
                    self.game.ship, 
                    self.game.universe.stations
                )
                if result != DockingResult.SUCCESS:
                    logger.info(f"Docking failed: {result.value}")
            elif event.key == control_scheme_manager.get_key("trading"):
                if self.game.docking_manager.is_docked():
                    station = self.game.docking_manager.get_target_station()
                    self.game.change_state(GameStates.TRADING, station)
            elif event.key == control_scheme_manager.get_key("upgrades"):
                if self.game.docking_manager.is_docked():
                    station = self.game.docking_manager.get_target_station()
                    # Check if station offers upgrades
                    station_type = station.station_type.value.lower()
                    if station_type in ["shipyard", "research station", "military base"]:
                        self.game.change_state(GameStates.UPGRADES, station)
                    else:
                        logger.info(f"Station {station.name} does not offer upgrades")
            elif event.key == control_scheme_manager.get_key("missions"):
                if self.game.docking_manager.is_docked():
                    station = self.game.docking_manager.get_target_station()
                    self.game.change_state(GameStates.MISSIONS, station)
            elif event.key == control_scheme_manager.get_key("talk"):
                if self.game.docking_manager.is_docked():
                    from ..story.director import get_contact_at, start_contact_dialogue
                    station = self.game.docking_manager.get_target_station()
                    contact = get_contact_at(station, self.game)
                    if contact:
                        start_contact_dialogue(contact, self.game)
                    else:
                        self.game.docking_manager.last_status_message = "Nobody here wants to talk."
            elif event.key == control_scheme_manager.get_key("hail"):
                from ..combat.combat_manager import combat_manager as backup_combat
                from ..ui.notifications import notifications
                success, message = backup_combat.call_backup(self.game)
                notifications.push(message, color=(120, 230, 140) if success else (255, 120, 120))
            elif event.key == control_scheme_manager.get_key("undock"):
                if self.game.docking_manager.is_docked():
                    result = self.game.docking_manager.attempt_undocking(self.game.ship)
                    if result != DockingResult.SUCCESS:
                        logger.info(f"Undocking failed: {result.value}")
            elif event.key == control_scheme_manager.get_key("cloaking"):
                effective_stats = self.game.ship.get_effective_stats()
                cloaking_system.handle_input(event, effective_stats)
            elif event.key == control_scheme_manager.get_key("repair"):
                if self.game.docking_manager.is_docked():
                    station = self.game.docking_manager.get_target_station()
                    repair_system.handle_input(event, self.game.ship, station)
                else:
                    # Emergency repair when not docked
                    repair_system.handle_input(event, self.game.ship, None)
            elif event.key == control_scheme_manager.get_key("base_construction"):
                # Enter base construction mode
                self.game.change_state(GameStates.BASE_CONSTRUCTION)

class PausedState(State):
    def __init__(self, game):
        super().__init__(game)
        from ..ui.menu_kit import MenuList, Ui, BASE_SIZE
        self.menu = MenuList(["Resume", "Save Game", "Logbook", "Settings", "Main Menu"])
        self._ui = Ui(BASE_SIZE)

    @property
    def pause_options(self):
        return self.menu.items

    @property
    def selected_option(self):
        return self.menu.selected

    @selected_option.setter
    def selected_option(self, value):
        self.menu.selected = value

    @property
    def option_rects(self):
        return [self.menu.rects[i] for i in sorted(self.menu.rects)]

    def render(self, screen):
        # First render the game state in the background
        self.game.states[GameStates.PLAYING].render(screen)

        presenter = self.game.presenter
        if presenter is not None:
            # On a Retina display the veil goes over the finished frame, sharp
            # HUD included, and the menu on top of that at full resolution
            presenter.veil_alpha = 128
            presenter.queue(lambda pixels, ratio: self._draw_menu(pixels), on_top=True)
            return

        veil = pygame.Surface(screen.get_size())
        veil.set_alpha(128)
        veil.fill((0, 0, 0))
        screen.blit(veil, (0, 0))
        self._draw_menu(screen)

    def _draw_menu(self, screen):
        from ..ui.menu_kit import ui_for
        ui = self._ui = ui_for(screen, self.game)
        cx = ui.width // 2

        title = ui.text(screen, "PAUSED", "title", (255, 255, 255),
                        midtop=(cx, max(ui.px(30), round(ui.height * 0.16))))
        footer_top = ui.footer(screen, "UP / DOWN to navigate, ENTER to select, ESC to resume", color=(170, 175, 190))
        area = pygame.Rect(0, title.bottom + ui.px(26), ui.width, 0)
        area.height = max(ui.px(100), footer_top - ui.px(20) - area.top)
        self.menu.layout(ui, area, row_units=56)
        self.menu.draw(ui, screen)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.change_state(GameStates.PLAYING)
            return
        if self.menu.handle(event, self._ui) is not None:
            self._select_option()

    def _select_option(self):
        """Handle option selection"""
        option = self.pause_options[self.selected_option]
        if option == "Resume":
            self.game.change_state(GameStates.PLAYING)
        elif option == "Save Game":
            self.game.change_state(GameStates.SAVE_GAME)
        elif option == "Logbook":
            self.game.change_state(GameStates.LOGBOOK)
        elif option == "Settings":
            self.game.change_state(GameStates.SETTINGS)
        elif option == "Main Menu":
            self.game.change_state(GameStates.MAIN_MENU)

class TradingState(State):
    def __init__(self, game, station=None):
        super().__init__(game)
        self.station = station
        self.selected_commodity_index = 0
        self.viewing_cargo = False  # False = station market, True = ship cargo
        self.transaction_quantity = 1
        self.message = ""
        self.message_timer = 0

        # Get ship and market references
        self.ship = game.ship
        self.market = station.market if station else None

        # Get available commodities
        self.available_commodities = self.market.get_available_commodities() if self.market else []

        from ..ui.menu_kit import ButtonBar, RowList, Ui, BASE_SIZE
        from ..ui.menu_style import MenuBackground
        self.background = MenuBackground()
        self.market_list = RowList()
        self.cargo_list = RowList()
        self.buttons = ButtonBar(["Buy  (B)", "Sell  (S)", "Switch  (TAB)", "Leave  (ESC)"])
        self._ui = Ui(BASE_SIZE)
        
    def update(self, delta_time):
        # Update message timer
        if self.message_timer > 0:
            self.message_timer -= delta_time
            if self.message_timer <= 0:
                self.message = ""
        
    def render(self, screen):
        from ..ui.menu_kit import ui_for
        from ..ui.menu_style import ACCENT_GOLD, TEXT_DIM

        ui = self._ui = ui_for(screen, self.game)
        self.background.draw(screen)

        station_name = self.station.name if self.station else "Unknown Station"
        station_type = self.station.station_type.value if self.station else "Unknown"
        top = ui.header(screen, "TRADING", subtitle=f"{station_name} - {station_type}")
        top = ui.info_row(screen, top, f"Credits: {self.ship.credits:,}",
                          f"Cargo: {self.ship.cargo_hold.get_cargo_summary()}")

        # Stacked from the bottom: key hints, buttons, a message line, then the panels
        footer_top = ui.footer(screen, "ARROWS navigate  |  TAB switch market / cargo  |  B buy  |  S sell  |  ESC leave")
        buttons = pygame.Rect(0, footer_top - ui.px(40), ui.width, ui.px(40))
        message = pygame.Rect(0, buttons.top - ui.px(30), ui.width, ui.px(26))
        panels_bottom = message.top - ui.px(4)

        (market_panel, market_inner), (cargo_panel, cargo_inner) = ui.split_panels(
            screen, top + ui.px(10), panels_bottom, ["STATION MARKET", "YOUR CARGO"],
            active=1 if self.viewing_cargo else 0)

        cargo_items = self.ship.cargo_hold.get_cargo_items()
        for lst, count, inner, active in ((self.market_list, len(self.available_commodities) if self.market else 0,
                                           market_inner, not self.viewing_cargo),
                                          (self.cargo_list, len(cargo_items), cargo_inner, self.viewing_cargo)):
            lst.set_count(count)
            lst.selected = min(self.selected_commodity_index, max(0, count - 1)) if active else 0
            room = pygame.Rect(inner)
            room.height -= ui.px(16)                                  # room for the "1-7 of 9" counter
            lst.layout(ui, room, row_units=54)

        self.market_list.draw_chrome(ui, screen, fill_selected=not self.viewing_cargo, accent=(80, 140, 255))
        self.cargo_list.draw_chrome(ui, screen, fill_selected=self.viewing_cargo, accent=(90, 200, 120))
        self._draw_market_rows(ui, screen)
        self._draw_cargo_rows(ui, screen, cargo_items)
        for lst, panel in ((self.market_list, market_panel), (self.cargo_list, cargo_panel)):
            counter = lst.counter()
            if counter:
                ui.text(screen, counter, "tiny", TEXT_DIM, bottomright=(panel.right - ui.px(16), panel.bottom - ui.px(8)))

        if self.message:
            ui.text(screen, self.message, "body", ACCENT_GOLD, max_width=ui.width - 2 * ui.margin(),
                    center=message.center)
        self.buttons.enabled = [not self.viewing_cargo, self.viewing_cargo, True, True]
        self.buttons.layout(ui, buttons)
        self.buttons.draw(ui, screen)

    def _draw_market_rows(self, ui, screen):
        from ..ui.menu_style import ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM
        if not self.market:
            return
        for index, rect in self.market_list.rects.items():
            commodity = self.available_commodities[index]
            selected = not self.viewing_cargo and index == self.selected_commodity_index
            pad = ui.px(14)
            ui.text(screen, commodity.name, 21, ACCENT_GOLD if selected else TEXT_PRIMARY, max_width=rect.width - 2 * pad,
                    topleft=(rect.x + pad, rect.y + ui.px(6)))
            buy_price = self.market.get_buy_price(commodity.id)
            sell_price = self.market.get_sell_price(commodity.id)
            ui.text(screen, f"Buy: {buy_price}   Sell: {sell_price}", "small", (200, 205, 215) if selected else TEXT_DIM,
                    max_width=rect.width - 2 * pad, bottomleft=(rect.x + pad, rect.bottom - ui.px(6)))

    def _draw_cargo_rows(self, ui, screen, cargo_items):
        from ..ui.menu_style import ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM
        if not cargo_items:
            rect = self.cargo_list.area
            ui.text(screen, "Cargo hold empty", "body", TEXT_DIM, topleft=(rect.x + ui.px(4), rect.y + ui.px(6)))
            return
        for index, rect in self.cargo_list.rects.items():
            commodity, quantity = cargo_items[index]
            selected = self.viewing_cargo and index == self.selected_commodity_index
            pad = ui.px(14)
            quantity_rect = ui.text(screen, f"x{quantity}", 21, (200, 205, 215),
                                    topright=(rect.right - pad, rect.y + ui.px(6)))
            ui.text(screen, commodity.name, 21, ACCENT_GOLD if selected else TEXT_PRIMARY,
                    max_width=rect.width - 3 * pad - quantity_rect.width, topleft=(rect.x + pad, rect.y + ui.px(6)))
            if self.market:
                sell_price = self.market.get_sell_price(commodity.id)
                if sell_price:
                    ui.text(screen, f"Value: {sell_price * quantity}", "small", (200, 205, 215) if selected else TEXT_DIM,
                            bottomleft=(rect.x + pad, rect.bottom - ui.px(6)))

    def _handle_mouse(self, event):
        """Buttons, picking a row in either panel, and the wheel."""
        if event.type == pygame.MOUSEWHEEL:
            self._move_selection(-1 if event.y > 0 else 1)
            return
        pressed = self.buttons.handle(event, self._ui)
        if pressed is not None:
            (self._attempt_buy, self._attempt_sell, self._switch_panel,
             lambda: self.game.change_state(GameStates.PLAYING))[pressed]()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            index = self.market_list.index_at(self._ui, event.pos)
            if index is not None:
                self._select(index, cargo=False)
                return
            index = self.cargo_list.index_at(self._ui, event.pos)
            if index is not None:
                self._select(index, cargo=True)

    def _select(self, index, cargo):
        if cargo != self.viewing_cargo:
            self.viewing_cargo = cargo
        self.selected_commodity_index = index

    def _switch_panel(self):
        self.viewing_cargo = not self.viewing_cargo
        self.selected_commodity_index = 0

    def handle_input(self, event):
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEWHEEL):
            self._handle_mouse(event)
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameStates.PLAYING)
                
            elif event.key == pygame.K_TAB:
                self.viewing_cargo = not self.viewing_cargo
                self.selected_commodity_index = 0
                
            elif event.key == pygame.K_UP:
                self._move_selection(-1)
                
            elif event.key == pygame.K_DOWN:
                self._move_selection(1)
                
            elif event.key == pygame.K_b:
                self._attempt_buy()
                
            elif event.key == pygame.K_s:
                self._attempt_sell()
    
    def _move_selection(self, direction):
        """Move the selection cursor up or down."""
        if self.viewing_cargo:
            max_items = len(self.ship.cargo_hold.get_cargo_items())
        else:
            max_items = len(self.available_commodities)
        
        if max_items > 0:
            self.selected_commodity_index = (self.selected_commodity_index + direction) % max_items
    
    def _attempt_buy(self):
        """Attempt to buy the selected commodity from the station."""
        if self.viewing_cargo or not self.available_commodities:
            self._show_message("Select a commodity from the station market to buy")
            return
        
        if self.selected_commodity_index >= len(self.available_commodities):
            return
            
        commodity = self.available_commodities[self.selected_commodity_index]
        buy_price = self.market.get_buy_price(commodity.id)
        
        # Check if player has enough credits
        if self.ship.credits < buy_price:
            self._show_message("Insufficient credits")
            return
            
        # Check if ship has cargo space
        if not self.ship.cargo_hold.can_add(commodity.id, 1):
            self._show_message("Insufficient cargo space")
            return
            
        # Check if station has stock
        if not self.market.can_buy_from_station(commodity.id, 1):
            self._show_message("Station out of stock")
            return
            
        # Execute transaction
        if self.market.buy_from_station(commodity.id, 1):
            success = False
            
            # Handle special commodities (fuel and ammo)
            if commodity.id in ["ship_fuel", "deuterium"]:
                # Add fuel directly to ship
                fuel_amount = 10.0 if commodity.id == "ship_fuel" else 15.0  # Deuterium is more efficient
                if self.ship.can_add_fuel(fuel_amount):
                    actual_added = self.ship.refuel(fuel_amount)
                    if actual_added > 0:
                        self.ship.credits -= buy_price
                        self._show_message(f"Refueled {actual_added:.1f} units for {buy_price} credits")
                        success = True
                else:
                    self._show_message("Fuel tank is full")
            elif commodity.id in ["laser_cells", "plasma_cartridges", "missiles", "railgun_slugs"]:
                # Add ammo directly to ship
                ammo_amount = 10  # Standard ammo purchase quantity
                if self.ship.can_add_ammo(commodity.id, ammo_amount):
                    actual_added = self.ship.add_ammo(commodity.id, ammo_amount)
                    if actual_added > 0:
                        self.ship.credits -= buy_price
                        self._show_message(f"Bought {actual_added} {commodity.name} for {buy_price} credits")
                        success = True
                else:
                    self._show_message("Ammo storage is full")
            else:
                # Regular commodity - add to cargo
                if self.ship.cargo_hold.add_cargo(commodity.id, 1):
                    self.ship.credits -= buy_price
                    self._show_message(f"Bought {commodity.name} for {buy_price} credits")
                    success = True
                else:
                    self._show_message("Transaction failed - cargo error")
            
            if not success:
                # Rollback market transaction if purchase failed
                self.market.sell_to_station(commodity.id, 1)
        else:
            self._show_message("Transaction failed")
    
    def _attempt_sell(self):
        """Attempt to sell the selected commodity to the station."""
        if not self.viewing_cargo:
            self._show_message("Select a commodity from your cargo to sell")
            return
            
        cargo_items = self.ship.cargo_hold.get_cargo_items()
        if not cargo_items or self.selected_commodity_index >= len(cargo_items):
            return
            
        commodity, quantity = cargo_items[self.selected_commodity_index]
        sell_price = self.market.get_sell_price(commodity.id)
        
        # Check if station will buy this commodity
        if not self.market.can_sell_to_station(commodity.id, 1):
            self._show_message("Station not buying this commodity")
            return
        
        # Execute transaction  
        if self.ship.cargo_hold.remove_cargo(commodity.id, 1):
            if self.market.sell_to_station(commodity.id, 1):
                self.ship.credits += sell_price
                self._show_message(f"Sold {commodity.name} for {sell_price} credits")
            else:
                # Rollback cargo transaction if market transaction failed
                self.ship.cargo_hold.add_cargo(commodity.id, 1)
                self._show_message("Transaction failed - market error")
        else:
            self._show_message("Transaction failed")
    
    def _show_message(self, message):
        """Display a temporary message to the player."""
        self.message = message
        self.message_timer = 3.0  # Show for 3 seconds


class UpgradeState(State):
    def __init__(self, game, station=None):
        super().__init__(game)
        self.station = station
        self.selected_upgrade_index = 0
        self.selected_category_index = 0
        self.viewing_categories = True  # True = category list, False = upgrade list
        self.message = ""
        self.message_timer = 0
        
        # Get ship and upgrade system references
        self.ship = game.ship
        
        # Import upgrade system
        try:
            from ..upgrades.upgrade_definitions import UpgradeCategory, upgrade_registry
            from ..upgrades.upgrade_system import upgrade_system
        except ImportError:
            from upgrades.upgrade_definitions import UpgradeCategory, upgrade_registry
            from upgrades.upgrade_system import upgrade_system
        
        self.UpgradeCategory = UpgradeCategory
        self.upgrade_registry = upgrade_registry
        self.upgrade_system = upgrade_system
        
        # Get available upgrades for this station
        station_type = station.station_type.value if station else "Shipyard"
        self.available_upgrades = upgrade_system.get_available_upgrades_for_station(
            self.ship.upgrades,
            station_type,
            self.ship.credits,
            self.game.mission_manager.reputation
        )

        # Group upgrades by category
        self.upgrades_by_category = {}
        for category in UpgradeCategory:
            category_upgrades = [u for u in self.available_upgrades if u.category == category]
            if category_upgrades:
                self.upgrades_by_category[category] = category_upgrades
        
        self.categories = list(self.upgrades_by_category.keys())

        from ..ui.menu_kit import ButtonBar, RowList, Ui, BASE_SIZE
        from ..ui.menu_style import MenuBackground
        self.background = MenuBackground()
        self.list = RowList()
        self.category_buttons = ButtonBar(["Open  (ENTER)", "Leave  (ESC)"])
        self.upgrade_buttons = ButtonBar(["Buy  (ENTER)", "Back  (BACKSPACE)", "Leave  (ESC)"])
        self._ui = Ui(BASE_SIZE)

    def _get_current_faction_standing(self) -> int:
        """Standing with whichever faction controls this station's sector,
        or 0 if there's no station (e.g. accessed outside normal docking)."""
        if not self.station:
            return 0
        from ..factions import get_station_faction
        faction = get_station_faction(self.station, self.game.world_seed)
        return self.game.mission_manager.faction_standing.get(faction, 0)

    def update(self, delta_time):
        # Update message timer
        if self.message_timer > 0:
            self.message_timer -= delta_time
            if self.message_timer <= 0:
                self.message = ""

    def render(self, screen):
        from ..ui.menu_kit import ui_for
        from ..ui.menu_style import ACCENT_GOLD, TEXT_DIM

        ui = self._ui = ui_for(screen, self.game)
        self.background.draw(screen)

        station_name = self.station.name if self.station else "Unknown Station"
        station_type = self.station.station_type.value if self.station else "Unknown"
        top = ui.header(screen, "SHIP UPGRADES", subtitle=f"{station_name} - {station_type}")
        ship_info = self.ship.get_ship_info()
        top = ui.info_row(screen, top, f"Credits: {ship_info['credits']:,}",
                          f"Upgrades installed: {ship_info['total_upgrade_value']:,} cr", right_color=TEXT_DIM)

        footer_top = ui.footer(screen, "UP / DOWN navigate  |  ENTER " + (
            "opens a category" if self.viewing_categories else "buys the upgrade  |  BACKSPACE goes back") + "  |  ESC leave")
        buttons = pygame.Rect(0, footer_top - ui.px(40), ui.width, ui.px(40))
        message = pygame.Rect(0, buttons.top - ui.px(30), ui.width, ui.px(26))
        panels_bottom = message.top - ui.px(4)

        (stats_panel, stats_inner), (up_panel, up_inner) = ui.split_panels(
            screen, top + ui.px(10), panels_bottom,
            ["CURRENT SHIP STATS", "CATEGORIES" if self.viewing_categories else "UPGRADES"])

        self._draw_ship_stats(ui, screen, stats_inner, ship_info)

        count = self._row_count()
        self.list.set_count(count)
        self.list.selected = min(self.selected_category_index if self.viewing_categories else self.selected_upgrade_index,
                                 max(0, count - 1))
        room = pygame.Rect(up_inner)
        room.height -= ui.px(16)
        self.list.layout(ui, room, row_units=56)
        self.list.draw_chrome(ui, screen, accent=(90, 200, 120) if self.viewing_categories else (80, 140, 255))
        self._draw_upgrade_rows(ui, screen, room)
        counter = self.list.counter()
        if counter:
            ui.text(screen, counter, "tiny", TEXT_DIM, bottomright=(up_panel.right - ui.px(16), up_panel.bottom - ui.px(8)))

        if self.message:
            ui.text(screen, self.message, "body", ACCENT_GOLD, max_width=ui.width - 2 * ui.margin(), center=message.center)
        bar = self.category_buttons if self.viewing_categories else self.upgrade_buttons
        bar.layout(ui, buttons)
        bar.draw(ui, screen)

    def _row_count(self):
        if self.viewing_categories:
            return len(self.categories)
        if self.selected_category_index < len(self.categories):
            return len(self.upgrades_by_category[self.categories[self.selected_category_index]])
        return 0

    def _draw_ship_stats(self, ui, screen, inner, ship_info):
        """Current ship statistics, then what is installed; stops where the panel ends."""
        from ..ui.menu_style import TEXT_PRIMARY, TEXT_DIM
        lines = [
            (f"Cargo: {ship_info['cargo_used']}/{ship_info['cargo_capacity']} units", "body", TEXT_PRIMARY),
            (f"Max Speed: {ship_info['max_speed']:.0f} u/s", "body", TEXT_PRIMARY),
            (f"Thrust: {ship_info['thrust_force']:.0f} N", "body", TEXT_PRIMARY),
            (f"Hull: {ship_info['hull_current']:.0f}/{ship_info['hull_max']:.0f} HP", "body", TEXT_PRIMARY),
            (f"Scanner: {ship_info['scanner_range']:.0f} range", "body", TEXT_PRIMARY),
            ("", "small", TEXT_DIM),
            ("Installed upgrades", "small", (200, 205, 215)),
        ]
        for category, upgrade_name in ship_info['upgrade_summary'].items():
            lines.append((f"{category}: {upgrade_name}", "small", TEXT_DIM))
        y = inner.top
        for text, role, color in lines:
            height = ui.line_height(role) + ui.px(3)
            if y + height > inner.bottom + ui.px(4):
                ui.text(screen, "...", "small", TEXT_DIM, topleft=(inner.x + ui.px(10), min(y, inner.bottom - height)))
                break
            if text:
                ui.text(screen, text, role, color, max_width=inner.width - ui.px(10),
                        topleft=(inner.x + (ui.px(10) if role == "small" and text[0] != "I" else 0), y))
            y += height

    def _draw_upgrade_rows(self, ui, screen, room):
        from ..ui.menu_style import ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM
        if not self.categories:
            ui.text(screen, "No upgrades available", "body", TEXT_DIM, topleft=(room.x + ui.px(4), room.y + ui.px(6)))
            return
        pad = ui.px(14)
        if self.viewing_categories:
            for index, rect in self.list.rects.items():
                category = self.categories[index]
                selected = index == self.selected_category_index
                ui.text(screen, category.value, 21, ACCENT_GOLD if selected else TEXT_PRIMARY,
                        max_width=rect.width - 2 * pad, topleft=(rect.x + pad, rect.y + ui.px(6)))
                n = len(self.upgrades_by_category[category])
                ui.text(screen, f"{n} upgrade" + ("" if n == 1 else "s"), "small", TEXT_DIM,
                        bottomleft=(rect.x + pad, rect.bottom - ui.px(6)))
            return
        category = self.categories[self.selected_category_index]
        station_type = self.station.station_type.value if self.station else "Shipyard"
        standing = self._get_current_faction_standing()
        for index, rect in self.list.rects.items():
            upgrade = self.upgrades_by_category[category][index]
            selected = index == self.selected_upgrade_index
            ui.text(screen, upgrade.name, 21, ACCENT_GOLD if selected else TEXT_PRIMARY,
                    max_width=rect.width - 2 * pad, topleft=(rect.x + pad, rect.y + ui.px(6)))
            price = self.upgrade_system.get_discounted_price(upgrade, station_type, standing)
            text, color = f"{price:,} credits", ACCENT_GOLD
            if price < upgrade.cost:
                text += f" (was {upgrade.cost:,})"
            elif price > upgrade.cost:
                text += f" (base {upgrade.cost:,})"
                color = (255, 120, 120)              # hostile-faction markup warning
            ui.text(screen, text, "small", color, max_width=rect.width - 2 * pad,
                    bottomleft=(rect.x + pad, rect.bottom - ui.px(6)))

    def _handle_mouse(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self._move_selection(-1 if event.y > 0 else 1)
            return
        bar = self.category_buttons if self.viewing_categories else self.upgrade_buttons
        pressed = bar.handle(event, self._ui)
        if pressed is not None:
            if self.viewing_categories:
                (self._enter_category, lambda: self.game.change_state(GameStates.PLAYING))[pressed]()
            else:
                (self._attempt_purchase, self._back_to_categories,
                 lambda: self.game.change_state(GameStates.PLAYING))[pressed]()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            index = self.list.index_at(self._ui, event.pos)
            if index is None:
                return
            if self.viewing_categories:
                self.selected_category_index = index
                self._enter_category()
            else:
                self.selected_upgrade_index = index

    def _back_to_categories(self):
        self.viewing_categories = True
        self.selected_upgrade_index = 0

    def handle_input(self, event):
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEWHEEL):
            self._handle_mouse(event)
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameStates.PLAYING)
                
            elif event.key == pygame.K_UP:
                self._move_selection(-1)
                
            elif event.key == pygame.K_DOWN:
                self._move_selection(1)
                
            elif event.key == pygame.K_RETURN:
                if self.viewing_categories:
                    self._enter_category()
                else:
                    self._attempt_purchase()
                    
            elif event.key == pygame.K_BACKSPACE:
                if not self.viewing_categories:
                    self._back_to_categories()
    
    def _move_selection(self, direction):
        """Move the selection cursor up or down."""
        if self.viewing_categories:
            max_items = len(self.categories)
            if max_items > 0:
                self.selected_category_index = (self.selected_category_index + direction) % max_items
        else:
            if self.selected_category_index < len(self.categories):
                selected_category = self.categories[self.selected_category_index]
                category_upgrades = self.upgrades_by_category[selected_category]
                max_items = len(category_upgrades)
                if max_items > 0:
                    self.selected_upgrade_index = (self.selected_upgrade_index + direction) % max_items
    
    def _enter_category(self):
        """Enter the selected category to view upgrades."""
        if self.selected_category_index < len(self.categories):
            self.viewing_categories = False
            self.selected_upgrade_index = 0
    
    def _attempt_purchase(self):
        """Attempt to purchase the selected upgrade."""
        if (self.selected_category_index >= len(self.categories) or 
            self.viewing_categories):
            return
        
        selected_category = self.categories[self.selected_category_index]
        category_upgrades = self.upgrades_by_category[selected_category]
        
        if self.selected_upgrade_index >= len(category_upgrades):
            return
        
        upgrade = category_upgrades[self.selected_upgrade_index]
        
        # Get discounted price
        station_type = self.station.station_type.value if self.station else "Shipyard"
        discounted_price = self.upgrade_system.get_discounted_price(
            upgrade, station_type, self._get_current_faction_standing()
        )

        # Check if player can afford it
        if self.ship.credits < discounted_price:
            self._show_message("Insufficient credits")
            return
        
        # Attempt purchase with discounted price
        # Temporarily modify the upgrade cost for this transaction
        original_cost = upgrade.cost
        upgrade.cost = discounted_price
        
        try:
            result, remaining_credits = self.upgrade_system.purchase_upgrade(
                self.ship.upgrades, upgrade.id, self.ship.credits,
                self.game.mission_manager.reputation
            )
            
            if result.success:
                self.ship.credits = remaining_credits
                self.ship._update_cargo_capacity()  # Update cargo capacity
                self._show_message(f"Installed {upgrade.name}")
                
                # Refresh available upgrades
                self._refresh_available_upgrades()
            else:
                self._show_message(result.message)
        finally:
            # Restore original cost
            upgrade.cost = original_cost
    
    def _refresh_available_upgrades(self):
        """Refresh the list of available upgrades."""
        station_type = self.station.station_type.value if self.station else "Shipyard"
        self.available_upgrades = self.upgrade_system.get_available_upgrades_for_station(
            self.ship.upgrades,
            station_type,
            self.ship.credits,
            self.game.mission_manager.reputation
        )
        
        # Rebuild categories
        self.upgrades_by_category = {}
        for category in self.UpgradeCategory:
            category_upgrades = [u for u in self.available_upgrades if u.category == category]
            if category_upgrades:
                self.upgrades_by_category[category] = category_upgrades
        
        self.categories = list(self.upgrades_by_category.keys())
        
        # Reset selection if needed
        if self.selected_category_index >= len(self.categories):
            self.selected_category_index = 0
            self.viewing_categories = True
    
    def _show_message(self, message):
        """Display a temporary message to the player."""
        self.message = message
        self.message_timer = 3.0  # Show for 3 seconds


def _draw_save_row(ui, screen, rect, meta, selected):
    """One saved game: its name over a line of details."""
    from ..ui.menu_style import ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM
    from datetime import datetime
    color = ACCENT_GOLD if selected else TEXT_PRIMARY
    detail_color = (230, 200, 110) if selected else TEXT_DIM
    try:
        date_str = datetime.fromisoformat(meta.save_date).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError):
        date_str = str(meta.save_date)
    pad = ui.px(16)
    width = rect.width - 2 * pad
    ui.text(screen, meta.save_name, 22, color, max_width=width, topleft=(rect.x + pad, rect.y + ui.px(7)))
    ui.text(screen, f"Credits: {meta.credits}  |  Location: {meta.location}  |  {date_str}", "small",
            detail_color, max_width=width, bottomleft=(rect.x + pad, rect.bottom - ui.px(7)))


class SaveGameState(State):
    def __init__(self, game):
        super().__init__(game)
        from ..save_system import save_system
        self.save_system = save_system
        self.title = "Save Game"
        self.save_name = ""
        self.editing_name = True
        self.message = ""
        self.message_timer = 0.0
        self.existing_saves = self.save_system.get_save_list()
        self.selected_save_index = 0

        from ..ui.menu_kit import RowList, Ui, BASE_SIZE
        from ..ui.menu_style import MenuBackground
        self.background = MenuBackground()
        self.list = RowList()
        self._ui = Ui(BASE_SIZE)
        self.input_box = pygame.Rect(0, 0, 0, 0)

    def update(self, delta_time):
        if self.message_timer > 0:
            self.message_timer -= delta_time
            if self.message_timer <= 0:
                self.message = ""

    def render(self, screen):
        from ..ui.menu_kit import ui_for
        from ..ui.menu_style import ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM

        ui = self._ui = ui_for(screen, self.game)
        self.background.draw(screen)
        top = ui.header(screen, "SAVE GAME")
        footer_top = ui.footer(
            screen, "Type a name, ENTER saves  |  TAB switches between name and list  |  UP / DOWN pick a save to overwrite  |  ESC back")

        width = ui.content_width(1000)
        left = (ui.width - width) // 2
        ui.text(screen, "Save name", "body", TEXT_PRIMARY, topleft=(left, top))
        self.input_box = pygame.Rect(left, top + ui.px(30), min(width, ui.px(560)), ui.px(46))
        border = ACCENT_GOLD if self.editing_name else (100, 110, 130)
        ui.panel(screen, self.input_box, border=border, alpha=150)
        caret = "|" if self.editing_name and (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        ui.text(screen, self.save_name + caret, "body", TEXT_PRIMARY, max_width=self.input_box.width - ui.px(28),
                midleft=(self.input_box.x + ui.px(14), self.input_box.centery))

        label_y = self.input_box.bottom + ui.px(22)
        ui.text(screen, "Existing saves", "body", TEXT_PRIMARY, topleft=(left, label_y))
        panel = pygame.Rect(left, label_y + ui.px(32), width, max(ui.px(60), footer_top - ui.px(8) - (label_y + ui.px(32))))
        ui.panel(screen, panel)

        self.list.set_count(len(self.existing_saves))
        self.list.selected = self.selected_save_index
        inner = panel.inflate(-ui.px(24), -ui.px(24))
        inner.height -= ui.px(16)                   # room for the "1-7 of 9" counter
        self.list.layout(ui, inner, row_units=60)
        self.list.draw_chrome(ui, screen, fill_selected=not self.editing_name)
        if not self.existing_saves:
            ui.text(screen, "No saves yet", "heading", TEXT_DIM, center=panel.center)
        for index, rect in self.list.rects.items():
            _draw_save_row(ui, screen, rect, self.existing_saves[index],
                           index == self.selected_save_index and not self.editing_name)
        counter = self.list.counter()
        if counter:
            ui.text(screen, counter, "tiny", TEXT_DIM, bottomright=(panel.right - ui.px(16), panel.bottom - ui.px(8)))

        if self.message:
            ui.message(screen, self.message, ACCENT_GOLD if "success" in self.message.lower() else (255, 120, 120))

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = self._ui.to_px(event.pos)
            if self.input_box.collidepoint(point):
                self.editing_name = True
            else:
                index = self.list.index_at(self._ui, event.pos)
                if index is not None:
                    self.selected_save_index = index
                    self.editing_name = False
        elif event.type == pygame.MOUSEWHEEL and self.existing_saves:
            self.selected_save_index = max(0, min(len(self.existing_saves) - 1, self.selected_save_index - event.y))
            self.editing_name = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameStates.PAUSED)
            elif event.key == pygame.K_TAB:
                self.editing_name = not self.editing_name
            elif self.editing_name:
                self._handle_name_input(event)
            else:
                self._handle_save_list_input(event)
    
    def _handle_name_input(self, event):
        """Handle text input for save name."""
        if event.key == pygame.K_RETURN:
            self._save_game()
        elif event.key == pygame.K_BACKSPACE:
            self.save_name = self.save_name[:-1]
        else:
            if len(self.save_name) < 30:  # Limit save name length
                char = event.unicode
                if char.isprintable() and char not in ['<', '>', ':', '"', '|', '?', '*', '/', '\\']:
                    self.save_name += char
    
    def _handle_save_list_input(self, event):
        """Handle navigation of existing saves list."""
        if event.key == pygame.K_UP and self.existing_saves:
            self.selected_save_index = (self.selected_save_index - 1) % len(self.existing_saves)
        elif event.key == pygame.K_DOWN and self.existing_saves:
            self.selected_save_index = (self.selected_save_index + 1) % len(self.existing_saves)
        elif event.key == pygame.K_RETURN and self.existing_saves:
            # Overwrite selected save
            selected_save = self.existing_saves[self.selected_save_index]
            self.save_name = selected_save.save_name
            self._save_game()
    
    def _save_game(self):
        """Save the current game."""
        if not self.save_name.strip():
            self.message = "Please enter a save name"
            self.message_timer = 2.0
            return
        
        success = self.save_system.save_game(self.game, self.save_name.strip())
        if success:
            self.message = "Game saved successfully!"
            self.message_timer = 2.0
            # Refresh save list
            self.existing_saves = self.save_system.get_save_list()
        else:
            self.message = "Save failed!"
            self.message_timer = 2.0


class LoadGameState(State):
    def __init__(self, game):
        super().__init__(game)
        from ..save_system import save_system
        self.save_system = save_system
        self.title = "Load Game"
        self.existing_saves = self.save_system.get_save_list()
        self.selected_save_index = 0
        self.message = ""
        self.message_timer = 0.0

        from ..ui.menu_kit import RowList, Ui, BASE_SIZE
        from ..ui.menu_style import MenuBackground
        self.background = MenuBackground()
        self.list = RowList()
        self._ui = Ui(BASE_SIZE)

    def update(self, delta_time):
        if self.message_timer > 0:
            self.message_timer -= delta_time
            if self.message_timer <= 0:
                self.message = ""

    def render(self, screen):
        from ..ui.menu_kit import ui_for
        from ..ui.menu_style import ACCENT_GOLD, TEXT_DIM

        ui = self._ui = ui_for(screen, self.game)
        self.background.draw(screen)
        top = ui.header(screen, "LOAD GAME")
        footer_top = ui.footer(screen, "UP / DOWN select  |  ENTER or click loads  |  DELETE removes a save  |  ESC back")

        width = ui.content_width(1000)
        panel = pygame.Rect((ui.width - width) // 2, top + ui.px(6), width, max(ui.px(80), footer_top - ui.px(8) - top - ui.px(6)))
        ui.panel(screen, panel)

        self.list.set_count(len(self.existing_saves))
        self.list.selected = self.selected_save_index
        inner = panel.inflate(-ui.px(24), -ui.px(24))
        inner.height -= ui.px(16)                   # room for the "1-7 of 9" counter
        self.list.layout(ui, inner, row_units=62)
        self.list.draw_chrome(ui, screen)
        if not self.existing_saves:
            ui.text(screen, "No saved games found", "heading", TEXT_DIM, center=panel.center)
        for index, rect in self.list.rects.items():
            _draw_save_row(ui, screen, rect, self.existing_saves[index], index == self.selected_save_index)
        counter = self.list.counter()
        if counter:
            ui.text(screen, counter, "tiny", TEXT_DIM, bottomright=(panel.right - ui.px(16), panel.bottom - ui.px(8)))

        if self.message:
            ui.message(screen, self.message, ACCENT_GOLD if "success" in self.message.lower() else (255, 120, 120))

    def handle_input(self, event):
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEWHEEL):
            self.list.selected = self.selected_save_index
            chosen = self.list.handle(event, self._ui, activate_on_click=True)
            self.selected_save_index = self.list.selected
            if chosen is not None:
                self._load_game()
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameStates.MAIN_MENU)
            elif not self.existing_saves:
                return  # No saves to interact with
            elif event.key == pygame.K_UP:
                self.selected_save_index = (self.selected_save_index - 1) % len(self.existing_saves)
            elif event.key == pygame.K_DOWN:
                self.selected_save_index = (self.selected_save_index + 1) % len(self.existing_saves)
            elif event.key == pygame.K_RETURN:
                self._load_game()
            elif event.key == pygame.K_DELETE:
                self._delete_save()
    
    def _load_game(self):
        """Load the selected game."""
        if not self.existing_saves:
            return
        
        selected_save = self.existing_saves[self.selected_save_index]
        success = self.save_system.load_game(selected_save.save_name, self.game)
        
        if success:
            self.message = "Game loaded successfully!"
            self.message_timer = 1.0
            # Transition to playing state immediately
            self.game.change_state(GameStates.PLAYING)
        else:
            self.message = "Load failed!"
            self.message_timer = 2.0
    
    def _delete_save(self):
        """Delete the selected save."""
        if not self.existing_saves:
            return
        
        selected_save = self.existing_saves[self.selected_save_index]
        success = self.save_system.delete_save(selected_save.save_name)
        
        if success:
            self.message = "Save deleted"
            self.message_timer = 1.5
            # Refresh save list
            self.existing_saves = self.save_system.get_save_list()
            if self.selected_save_index >= len(self.existing_saves):
                self.selected_save_index = max(0, len(self.existing_saves) - 1)
        else:
            self.message = "Delete failed!"
            self.message_timer = 2.0


class MissionBoardState(State):
    def __init__(self, game, station=None):
        super().__init__(game)
        from ..missions.mission_manager import mission_manager
        self.mission_manager = mission_manager
        self.station = station
        self.title = "Mission Board"
        self.selected_mission_index = 0
        self.viewing_details = False
        self.current_tab = "available"  # "available", "active"
        self.message = ""
        self.message_timer = 0.0
        
        # Generate missions for this station if it's the first visit
        if self.station:
            self.mission_manager.generate_missions_for_station(self.station, self.game)
        
        # Get missions for this station
        self.refresh_missions()

        from ..ui.menu_style import MenuBackground
        self.background = MenuBackground()

    def refresh_missions(self):
        """Refresh the mission lists."""
        if self.station:
            self.available_missions = self.mission_manager.get_available_missions_for_station(self.station.name)
        else:
            self.available_missions = self.mission_manager.available_missions
        
        self.active_missions = self.mission_manager.active_missions
        
        # Reset selection if needed
        if self.current_tab == "available" and self.selected_mission_index >= len(self.available_missions):
            self.selected_mission_index = max(0, len(self.available_missions) - 1)
        elif self.current_tab == "active" and self.selected_mission_index >= len(self.active_missions):
            self.selected_mission_index = max(0, len(self.active_missions) - 1)
    
    def update(self, delta_time):
        if self.message_timer > 0:
            self.message_timer -= delta_time
            if self.message_timer <= 0:
                self.message = ""
    
    def render(self, screen):
        from ..ui.menu_style import draw_title, draw_panel, ACCENT_BLUE, ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM

        self.background.draw(screen)

        # Fonts
        tab_font = pygame.font.Font(None, 40)
        header_font = pygame.font.Font(None, 36)
        text_font = pygame.font.Font(None, 28)
        small_font = pygame.font.Font(None, 20)

        width, height = screen.get_size()

        # Title
        station_name = self.station.name if self.station else "Mission Central"
        title_bottom = draw_title(screen, "MISSION BOARD", subtitle=station_name, y=50)

        # Tab navigation
        tab_y = title_bottom + 20
        tab_spacing = 30
        available_color = ACCENT_GOLD if self.current_tab == "available" else TEXT_DIM
        active_color = ACCENT_GOLD if self.current_tab == "active" else TEXT_DIM

        available_tab = tab_font.render("Available", True, available_color)
        active_tab = tab_font.render("Active", True, active_color)

        screen.blit(available_tab, (50, tab_y))
        active_tab_x = 50 + available_tab.get_width() + tab_spacing
        screen.blit(active_tab, (active_tab_x, tab_y))

        # Underline whichever tab is selected
        underline_rect = available_tab.get_rect(topleft=(50, tab_y)) if self.current_tab == "available" \
            else active_tab.get_rect(topleft=(active_tab_x, tab_y))
        pygame.draw.line(screen, ACCENT_GOLD, (underline_rect.left, underline_rect.bottom + 2),
                        (underline_rect.right, underline_rect.bottom + 2), 2)

        # Mission count
        if self.current_tab == "available":
            count_text = f"({len(self.available_missions)} missions)"
            missions_to_show = self.available_missions
        else:
            count_text = f"({len(self.active_missions)} missions)"
            missions_to_show = self.active_missions

        count_surface = small_font.render(count_text, True, TEXT_DIM)
        screen.blit(count_surface, (50, tab_y + 42))

        # Reputation (missions above may require a minimum to accept)
        from ..missions.rank_system import get_rank_name
        reputation = self.mission_manager.reputation
        reputation_text = f"Reputation: {reputation} ({get_rank_name(reputation)})"
        reputation_surface = small_font.render(reputation_text, True, ACCENT_GOLD)
        screen.blit(reputation_surface, (width - reputation_surface.get_width() - 50, tab_y + 42))

        # Per-faction standing - who specifically trusts (or resents) you
        faction_parts = []
        for faction_name, value in self.mission_manager.faction_standing.items():
            if value > 0:
                color = (120, 230, 140)
            elif value < 0:
                color = (255, 90, 90)
            else:
                color = TEXT_DIM
            faction_parts.append((f"{faction_name}: {value:+d}", color))

        standing_x = width - 50
        for text, color in reversed(faction_parts):
            surface = small_font.render(text, True, color)
            standing_x -= surface.get_width()
            screen.blit(surface, (standing_x, tab_y + 62))
            standing_x -= 20

        # Panel behind the mission list/details. Details mode only needs one
        # instruction line instead of two, so it gets that 20px back - this
        # view's content (variable-length description/objectives/requirements)
        # runs close to the panel's bottom edge more easily than the list view.
        panel_top = tab_y + 90
        instruction_y = height - 60 if self.viewing_details else height - 80
        panel_rect = pygame.Rect(20, panel_top, width - 40, instruction_y - 20 - panel_top)
        draw_panel(screen, panel_rect)

        if not self.viewing_details:
            self._render_mission_list(screen, missions_to_show, text_font, small_font, instruction_y, panel_rect)
        else:
            self._render_mission_details(screen, missions_to_show, header_font, text_font, small_font, panel_rect)

        if not self.viewing_details:
            instructions = [
                "TAB: Switch tabs | UP/DOWN: Navigate | ENTER: View details",
                "A: Accept mission | ESC: Back"
            ]
        else:
            instructions = [
                "A: Accept mission | X: Abandon (if active) | ESC: Back to list"
            ]

        instruction_font = pygame.font.Font(None, 20)
        for i, instruction in enumerate(instructions):
            instr_text = instruction_font.render(instruction, True, TEXT_DIM)
            screen.blit(instr_text, (20, instruction_y + i * 20))

        # Draw message if any
        if self.message:
            message_font = pygame.font.Font(None, 36)
            msg_color = ACCENT_GOLD if "success" in self.message.lower() else (255, 120, 120)
            msg_text = message_font.render(self.message, True, msg_color)
            msg_rect = msg_text.get_rect(center=(width // 2, height // 2))
            draw_panel(screen, msg_rect.inflate(30, 16), border_color=msg_color)
            screen.blit(msg_text, msg_rect)
    
    def _render_mission_list(self, screen, missions, text_font, small_font, instruction_y=None, panel_rect=None):
        """Render the list of missions, inside panel_rect if given."""
        from ..ui.menu_style import ACCENT_BLUE, ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM

        left = panel_rect.x + 20 if panel_rect else 50
        right = panel_rect.right - 20 if panel_rect else screen.get_width() - 50
        start_y = (panel_rect.y + 16) if panel_rect else 160

        if not missions:
            no_missions_text = text_font.render("No missions available", True, TEXT_DIM)
            screen.blit(no_missions_text, (left, start_y))
            return

        mission_height = 100

        # Show as many missions as fit above the instructions footer
        available_height = (instruction_y - 20 - start_y) if instruction_y else 500
        max_visible = max(1, available_height // mission_height)

        start_index = max(0, self.selected_mission_index - max_visible // 2)
        start_index = min(start_index, max(0, len(missions) - max_visible))
        end_index = min(len(missions), start_index + max_visible)

        for i in range(start_index, end_index):
            mission = missions[i]
            y = start_y + (i - start_index) * mission_height

            # Highlight selected mission
            is_selected = i == self.selected_mission_index
            if is_selected:
                card_rect = pygame.Rect(left - 10, y - 5, right - left + 20, mission_height - 10)
                pygame.draw.rect(screen, (40, 55, 90), card_rect, border_radius=6)
                pygame.draw.rect(screen, ACCENT_BLUE, card_rect, 2, border_radius=6)

            # Mission title and type
            title_color = ACCENT_GOLD if is_selected else TEXT_PRIMARY
            title_text = text_font.render(mission.title, True, title_color)
            screen.blit(title_text, (left, y))

            # Mission type and priority
            type_text = f"{mission.mission_type.value} | {mission.priority.value}"
            type_color = self._get_priority_color(mission.priority)
            type_surface = small_font.render(type_text, True, type_color)
            screen.blit(type_surface, (left, y + 25))

            # Reward
            reward_text = f"Reward: {mission.reward.credits:,} credits"
            reward_surface = small_font.render(reward_text, True, (120, 230, 140))
            screen.blit(reward_surface, (left, y + 45))

            # Destination info (if available)
            if hasattr(mission, 'destination_station_id') and mission.destination_station_id:
                dest_coords = self.mission_manager.get_station_coordinates(
                    mission.destination_station_id,
                    self.game.universe.stations
                )
                if dest_coords:
                    dest_text = f"Destination: {mission.destination_station_id} - {dest_coords}"
                    dest_surface = small_font.render(dest_text, True, (150, 200, 255))
                    screen.blit(dest_surface, (left, y + 65))

            # Time remaining (if applicable)
            time_remaining = mission.get_formatted_time_remaining()
            if time_remaining != "No time limit":
                time_color = (255, 90, 90) if "EXPIRED" in time_remaining else ACCENT_GOLD
                time_surface = small_font.render(f"Time: {time_remaining}", True, time_color)
                screen.blit(time_surface, (left + 300, y + 45))

            # Status (for active missions)
            if self.current_tab == "active":
                status_text = f"Status: {mission.status.value} ({mission.completion_percentage:.0%})"
                status_surface = small_font.render(status_text, True, (150, 200, 255))
                screen.blit(status_surface, (left, y + 65))
    
    def _render_mission_details(self, screen, missions, header_font, text_font, small_font, panel_rect=None):
        """Render detailed view of selected mission, clipped to panel_rect if given."""
        if not missions or self.selected_mission_index >= len(missions):
            return

        from ..ui.menu_style import TEXT_PRIMARY

        mission = missions[self.selected_mission_index]

        left = panel_rect.x + 20 if panel_rect else 50
        start_y = (panel_rect.y + 16) if panel_rect else 160
        line_height = 25
        current_y = start_y

        original_clip = screen.get_clip()
        if panel_rect:
            screen.set_clip(panel_rect.inflate(-4, -4))

        # Mission title
        title_text = header_font.render(mission.title, True, TEXT_PRIMARY)
        screen.blit(title_text, (left, current_y))
        current_y += 40
        
        # Mission details
        details = [
            f"Type: {mission.mission_type.value}",
            f"Priority: {mission.priority.value}",
            f"Status: {mission.status.value}",
            f"Reward: {mission.reward.credits:,} credits",
            f"Time Limit: {mission.get_formatted_time_remaining()}",
            "",
            "Description:",
            mission.description,
            ""
        ]
        
        # Add location information if available
        if hasattr(mission, 'origin_station_id') and mission.origin_station_id:
            origin_coords = self.mission_manager.get_station_coordinates(
                mission.origin_station_id, 
                self.game.universe.stations
            )
            if origin_coords:
                details.append(f"Origin: {mission.origin_station_id} - {origin_coords}")
        
        if hasattr(mission, 'destination_station_id') and mission.destination_station_id:
            dest_coords = self.mission_manager.get_station_coordinates(
                mission.destination_station_id, 
                self.game.universe.stations
            )
            if dest_coords:
                details.append(f"Destination: {mission.destination_station_id} - {dest_coords}")
        
        # Add trading station for trading contracts
        if hasattr(mission, 'station_id') and mission.station_id and not hasattr(mission, 'origin_station_id'):
            station_coords = self.mission_manager.get_station_coordinates(
                mission.station_id, 
                self.game.universe.stations
            )
            if station_coords:
                details.append(f"Trading Station: {mission.station_id} - {station_coords}")
        
        details.extend(["", "Objectives:"])
        
        for detail in details:
            if detail == "":
                current_y += line_height // 2
                continue

            color = TEXT_PRIMARY
            if "Priority:" in detail:
                color = self._get_priority_color(mission.priority)
            elif "Reward:" in detail:
                color = (120, 230, 140)
            elif "Time Limit:" in detail and "EXPIRED" in detail:
                color = (255, 90, 90)

            text_surface = text_font.render(detail, True, color)
            screen.blit(text_surface, (left, current_y))
            current_y += line_height

        # Objectives
        for i, objective in enumerate(mission.objectives):
            obj_color = (120, 230, 140) if objective.completed else TEXT_PRIMARY
            status = "[X]" if objective.completed else "[ ]"
            obj_text = f"  {status} {objective.description}"
            obj_surface = small_font.render(obj_text, True, obj_color)
            screen.blit(obj_surface, (left + 20, current_y))
            current_y += line_height

        # Requirements
        if mission.requirements.min_reputation > 0 or mission.requirements.min_cargo_capacity > 0:
            current_y += line_height
            req_header = text_font.render("Requirements:", True, TEXT_PRIMARY)
            screen.blit(req_header, (left, current_y))
            current_y += line_height

            if mission.requirements.min_reputation > 0:
                req_text = f"  Minimum Reputation: {mission.requirements.min_reputation}"
                # min_faction_standing is set equal to min_reputation at
                # generation time (see mission_manager.py), so rather than a
                # second line repeating the same number, note the faction
                # inline on this one
                if mission.requirements.min_faction_standing > 0:
                    faction = self.mission_manager.resolve_mission_faction(mission, self.game)
                    if faction:
                        req_text += f" (also requires {faction} standing)"
                req_surface = small_font.render(req_text, True, TEXT_PRIMARY)
                screen.blit(req_surface, (left + 20, current_y))
                current_y += line_height

            if mission.requirements.min_cargo_capacity > 0:
                req_text = f"  Minimum Cargo Space: {mission.requirements.min_cargo_capacity}"
                req_surface = small_font.render(req_text, True, TEXT_PRIMARY)
                screen.blit(req_surface, (left + 20, current_y))
                current_y += line_height

        screen.set_clip(original_clip)
    
    def _get_priority_color(self, priority):
        """Get color for mission priority."""
        from ..missions.mission_types import MissionPriority
        
        priority_colors = {
            MissionPriority.LOW: (150, 150, 150),
            MissionPriority.MEDIUM: (255, 255, 255),
            MissionPriority.HIGH: (255, 200, 0),
            MissionPriority.URGENT: (255, 0, 0)
        }
        return priority_colors.get(priority, (255, 255, 255))
    
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.viewing_details:
                    self.viewing_details = False
                else:
                    self.game.change_state(GameStates.PLAYING)
            
            elif not self.viewing_details:
                self._handle_list_input(event)
            else:
                self._handle_details_input(event)
    
    def _handle_list_input(self, event):
        """Handle input when viewing mission list."""
        missions = self.available_missions if self.current_tab == "available" else self.active_missions
        
        if event.key == pygame.K_TAB:
            # Switch tabs
            self.current_tab = "active" if self.current_tab == "available" else "available"
            self.selected_mission_index = 0
            self.refresh_missions()
        
        elif event.key == pygame.K_UP and missions:
            self.selected_mission_index = (self.selected_mission_index - 1) % len(missions)
        
        elif event.key == pygame.K_DOWN and missions:
            self.selected_mission_index = (self.selected_mission_index + 1) % len(missions)
        
        elif event.key == pygame.K_RETURN and missions:
            self.viewing_details = True
        
        elif event.key == pygame.K_a and missions:
            # Accept mission
            self._accept_mission()
    
    def _handle_details_input(self, event):
        """Handle input when viewing mission details."""
        missions = self.available_missions if self.current_tab == "available" else self.active_missions
        
        if event.key == pygame.K_a and missions:
            # Accept mission
            self._accept_mission()
        
        elif event.key == pygame.K_x and self.current_tab == "active" and missions:
            # Abandon mission
            self._abandon_mission()
    
    def _accept_mission(self):
        """Accept the currently selected mission."""
        missions = self.available_missions if self.current_tab == "available" else self.active_missions
        
        if not missions or self.selected_mission_index >= len(missions):
            return
        
        mission = missions[self.selected_mission_index]
        
        if self.current_tab != "available":
            self.message = "Can only accept available missions"
            self.message_timer = 2.0
            return
        
        success, message = self.mission_manager.accept_mission(mission.id, self.game.ship, self.game)
        
        self.message = message
        self.message_timer = 2.0
        
        if success:
            self.refresh_missions()
            # Switch to active tab to show the accepted mission
            self.current_tab = "active"
            self.selected_mission_index = 0
    
    def _abandon_mission(self):
        """Abandon the currently selected active mission."""
        if self.current_tab != "active" or not self.active_missions:
            return
        
        if self.selected_mission_index >= len(self.active_missions):
            return
        
        mission = self.active_missions[self.selected_mission_index]
        success, message = self.mission_manager.abandon_mission(mission.id, self.game.ship, self.game)
        
        self.message = message
        self.message_timer = 2.0
        
        if success:
            self.refresh_missions()