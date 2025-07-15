# src/camera.py
from pygame import Vector2
from .settings import game_settings, CameraMode

class Camera:
    def __init__(self, width, height, universe_width=10000, universe_height=10000):
        self.position = Vector2(0, 0)
        self.target_position = Vector2(0, 0)
        self.width = width
        self.height = height
        self.universe_width = universe_width
        self.universe_height = universe_height
        
    def follow(self, target, delta_time=0.016):  
        """Follow target based on current camera mode"""
        camera_mode = game_settings.camera_mode
        
        if camera_mode == CameraMode.CENTERED:
            self._follow_centered(target)
        elif camera_mode == CameraMode.SMOOTH:
            self._follow_smooth(target, delta_time)
        elif camera_mode == CameraMode.DEADZONE:
            self._follow_deadzone(target)
    
    def _follow_centered(self, target):
        """Center the camera on target immediately (original behavior)"""
        # Calculate desired camera position
        desired_x = target.position.x - (self.width / 2)
        desired_y = target.position.y - (self.height / 2)
        
        # Handle wrapping for x coordinate
        if abs(desired_x - self.position.x) > self.universe_width / 2:
            if desired_x > self.position.x:
                desired_x -= self.universe_width
            else:
                desired_x += self.universe_width
                
        # Handle wrapping for y coordinate
        if abs(desired_y - self.position.y) > self.universe_height / 2:
            if desired_y > self.position.y:
                desired_y -= self.universe_height
            else:
                desired_y += self.universe_height
        
        # Update camera position immediately
        self.position.x = desired_x
        self.position.y = desired_y
    
    def _follow_smooth(self, target, delta_time):
        """Smoothly follow target with interpolation"""
        # Calculate desired camera position
        desired_x = target.position.x - (self.width / 2)
        desired_y = target.position.y - (self.height / 2)
        
        # Handle wrapping for x coordinate
        if abs(desired_x - self.position.x) > self.universe_width / 2:
            if desired_x > self.position.x:
                desired_x -= self.universe_width
            else:
                desired_x += self.universe_width
                
        # Handle wrapping for y coordinate
        if abs(desired_y - self.position.y) > self.universe_height / 2:
            if desired_y > self.position.y:
                desired_y -= self.universe_height
            else:
                desired_y += self.universe_height
        
        # Smooth interpolation
        smoothing = game_settings.camera_smoothing
        self.position.x += (desired_x - self.position.x) * smoothing * delta_time * 60
        self.position.y += (desired_y - self.position.y) * smoothing * delta_time * 60
    
    def _follow_deadzone(self, target):
        """Only move camera when target leaves deadzone area"""
        # Calculate where target appears on screen
        ship_screen_pos = target.position - self.position
        center = Vector2(self.width/2, self.height/2)
        offset_from_center = ship_screen_pos - center
        
        deadzone_radius = game_settings.camera_deadzone_radius
        
        if offset_from_center.length() > deadzone_radius:
            # Move camera to bring ship back into deadzone
            move_amount = offset_from_center.length() - deadzone_radius
            if offset_from_center.length() > 0:  # Avoid division by zero
                direction = offset_from_center.normalize()
                self.position += direction * move_amount
    
    def get_offset(self):
        """Get camera offset for rendering"""
        return self.position
    
    def screen_to_world(self, screen_pos):
        """Convert screen coordinates to world coordinates"""
        return Vector2(
            screen_pos[0] + self.position.x,
            screen_pos[1] + self.position.y
        )
    
    def world_to_screen(self, world_pos):
        """Convert world coordinates to screen coordinates with wrapping"""
        # Calculate relative position
        rel_x = world_pos.x - self.position.x
        rel_y = world_pos.y - self.position.y
        
        # Handle wrapping
        if abs(rel_x) > self.universe_width / 2:
            if rel_x > 0:
                rel_x -= self.universe_width
            else:
                rel_x += self.universe_width
                
        if abs(rel_y) > self.universe_height / 2:
            if rel_y > 0:
                rel_y -= self.universe_height
            else:
                rel_y += self.universe_height
                
        return Vector2(rel_x, rel_y)