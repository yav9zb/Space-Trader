import math
import random
from enum import Enum

import pygame
from pygame import Vector2


class TraderState(Enum):
    TRAVELING = "traveling"
    FLEEING = "fleeing"


# Recolored per faction so allegiance is visible at a glance, no text needed
FACTION_COLORS = {
    "Trade Guild": (210, 180, 90),
    "Independent": (150, 170, 190),
    "Pirate Territory": (150, 170, 190),
}


class TraderShip:
    """Neutral AI ship that flies between stations. Unarmed - flees if attacked
    rather than fighting back, unlike BanditShip which it otherwise mirrors."""

    def __init__(self, position: Vector2, destination_station, faction: str = "Independent"):
        self.position = Vector2(position)
        self.velocity = Vector2(0, 0)
        self.heading = Vector2(0, -1)
        self.rotation = 0
        self.faction = faction
        self.destination_station = destination_station
        self.alive = True

        self.size = 14
        self.max_hull = 40
        self.current_hull = self.max_hull
        self.max_speed = 220
        self.thrust_force = 250
        self.rotation_speed = 120
        self.drag_coefficient = 0.98

        self.credits_reward = random.randint(50, 200)

        self.state = TraderState.TRAVELING
        self.flee_timer = 0.0
        self.max_flee_time = 6.0  # despawn after fleeing this long, like docking elsewhere

        self.color = FACTION_COLORS.get(faction, (150, 170, 190))
        self.outline_color = (60, 65, 75)

        # Same 4-point dart silhouette as the player ship, smaller
        self.points = [
            Vector2(0, -self.size),
            Vector2(-self.size * 0.55, self.size * 0.65),
            Vector2(0, self.size * 0.38),
            Vector2(self.size * 0.55, self.size * 0.65),
        ]

    def update(self, delta_time: float, game_engine):
        if self.state == TraderState.TRAVELING:
            if self.destination_station is None:
                self.alive = False
                return
            distance = (self.destination_station.position - self.position).length()
            if distance <= self.destination_station.size + 40:
                self.alive = False  # arrived - simulated docking, despawn
                return
            self._move_toward(self.destination_station.position, delta_time)

        elif self.state == TraderState.FLEEING:
            self.flee_timer += delta_time
            if self.flee_timer >= self.max_flee_time:
                self.alive = False
                return
            ship = game_engine.ship
            direction_away = self.position - ship.position
            if direction_away.length_squared() > 0:
                direction_away = direction_away.normalize()
            else:
                direction_away = Vector2(0, -1)
            target = self.position + direction_away * 1000
            self._move_toward(target, delta_time)

        self._update_physics(delta_time)

    def take_damage(self, damage: float) -> bool:
        """Apply damage. Returns True if destroyed."""
        self.current_hull -= damage
        if self.state != TraderState.FLEEING:
            self.state = TraderState.FLEEING
            self.flee_timer = 0.0
        if self.current_hull <= 0:
            self.alive = False
            return True
        return False

    def _move_toward(self, target_position: Vector2, delta_time: float):
        direction_to_target = target_position - self.position
        if direction_to_target.length_squared() == 0:
            return
        direction_to_target = direction_to_target.normalize()

        target_angle = math.degrees(math.atan2(direction_to_target.y, direction_to_target.x)) + 90
        angle_diff = target_angle - self.rotation
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360

        if abs(angle_diff) > 5:
            turn_direction = 1 if angle_diff > 0 else -1
            self.rotation += turn_direction * self.rotation_speed * delta_time

        angle_rad = math.radians(self.rotation - 90)
        self.heading = Vector2(math.cos(angle_rad), math.sin(angle_rad))

        if abs(angle_diff) <= 30:
            self.velocity += self.heading * self.thrust_force * delta_time

    def _update_physics(self, delta_time: float):
        self.velocity *= self.drag_coefficient
        speed = self.velocity.length()
        if speed > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed
        self.position += self.velocity * delta_time

    def draw(self, screen: pygame.Surface, camera_offset: Vector2):
        screen_pos = self.position - camera_offset

        transformed_points = []
        for point in self.points:
            rotated_point = point.rotate(self.rotation)
            transformed_points.append((rotated_point + screen_pos))

        pygame.draw.polygon(screen, self.color, transformed_points)
        pygame.draw.polygon(screen, self.outline_color, transformed_points, 1)
