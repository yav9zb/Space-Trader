# src/camera.py
from pygame import Vector2

class Camera:
    def __init__(self, width, height):
        self.position = Vector2(0, 0)
        self.width = width
        self.height = height
        self.zoom = 1.0
        
    def follow(self, target):
        """Center the camera on a target"""
        self.position.x = target.position.x - (self.width / 2)
        self.position.y = target.position.y - (self.height / 2)
    
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
        """Convert world coordinates to screen coordinates"""
        return Vector2(
            world_pos[0] - self.position.x,
            world_pos[1] - self.position.y
        )