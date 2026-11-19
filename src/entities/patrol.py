import math
import random

import pygame
from pygame import Vector2

try:
    from ..combat.weapons import WeaponSystem, create_weapon
except ImportError:
    from combat.weapons import WeaponSystem, create_weapon

from ..factions import is_hostile
from ..ui import gfx

PATROL_COLOR = (120, 190, 255)
PATROL_OUTLINE = (235, 245, 255)
PROVOKED_SECONDS = 120.0


class PatrolShip:
    """Armed faction patrol. It hunts bandits it can see (except bounty
    targets, which the player has to collect), and turns on the player when
    that faction's standing is hostile or the player has fired on it.
    Backup called in by the player has a lifetime and leaves when it runs out.
    """

    def __init__(self, position: Vector2, faction: str = "Trade Guild", lifetime=None):
        self.position = Vector2(position)
        self.velocity = Vector2(0, 0)
        self.heading = Vector2(0, -1)
        self.rotation = 0
        self.faction = faction
        self.alive = True
        self.lifetime = lifetime          # seconds, or None to stay until destroyed
        self.provoked_time = 0.0

        self.size = 16
        self.max_hull = 140
        self.current_hull = self.max_hull
        self.max_speed = 380
        self.thrust_force = 330
        self.rotation_speed = 160
        self.drag_coefficient = 0.98
        self.detection_range = 900.0
        self.preferred_distance = 350.0

        self.weapon_system = WeaponSystem()
        self.weapon_system.add_weapon(create_weapon("basic_laser"))

        self.patrol_center = Vector2(position)
        self.patrol_radius = 600.0
        self.patrol_target = self._random_patrol_point()

        s = self.size
        self.points = [
            Vector2(0, -s),
            Vector2(-s * 0.7, s * 0.75),
            Vector2(-s * 0.25, s * 0.45),
            Vector2(s * 0.25, s * 0.45),
            Vector2(s * 0.7, s * 0.75),
        ]

    # Hostility ---------------------------------------------------------------

    def is_hostile_to_player(self, mission_manager) -> bool:
        return self.provoked_time > 0 or is_hostile(
            mission_manager.faction_standing.get(self.faction, 0))

    # Update ------------------------------------------------------------------

    def update(self, delta_time: float, game_engine):
        self.weapon_system.update(delta_time)
        self.provoked_time = max(0.0, self.provoked_time - delta_time)

        if self.lifetime is not None:
            self.lifetime -= delta_time
            if self.lifetime <= 0:
                self.alive = False
                return

        target = self._pick_target(game_engine)
        if target is not None:
            self._engage(target, delta_time)
        else:
            if (self.patrol_target - self.position).length() < 60:
                self.patrol_target = self._random_patrol_point()
            self._move_toward(self.patrol_target, delta_time)

        self._update_physics(delta_time)

    def _pick_target(self, game_engine):
        from ..combat.combat_manager import combat_manager
        from .bandit import BanditState

        best, best_distance = None, self.detection_range
        for bandit in combat_manager.active_bandits:
            if bandit.state == BanditState.DISABLED or bandit.bounty_id or bandit.stronghold_id:
                continue
            distance = (bandit.position - self.position).length()
            if distance < best_distance:
                best, best_distance = bandit, distance

        if self.is_hostile_to_player(game_engine.mission_manager):
            distance = (game_engine.ship.position - self.position).length()
            if distance < best_distance:
                best = game_engine.ship
        return best

    def _engage(self, target, delta_time: float):
        distance = (target.position - self.position).length()
        if distance > self.preferred_distance + 60:
            self._move_toward(target.position, delta_time)
        elif distance < self.preferred_distance - 60:
            away = self.position - target.position
            if away.length_squared() > 0:
                self._move_toward(self.position + away.normalize() * 100, delta_time)
        else:
            to_target = target.position - self.position
            if to_target.length_squared() > 0:
                sideways = Vector2(-to_target.y, to_target.x).normalize()
                self._move_toward(self.position + sideways * 50, delta_time)

        if self._is_facing(target.position) and distance < 700:
            self.weapon_system.fire_weapons(
                self.position, self.heading, self, pygame.time.get_ticks() / 1000.0)

    def take_damage(self, damage: float, by_player: bool = False) -> bool:
        """Returns True if destroyed. Being shot by the player provokes the
        patrol for a couple of minutes."""
        self.current_hull -= damage
        if by_player:
            self.provoked_time = PROVOKED_SECONDS
        if self.current_hull <= 0:
            self.alive = False
            return True
        return False

    # Movement ----------------------------------------------------------------

    def _random_patrol_point(self) -> Vector2:
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0, self.patrol_radius)
        return self.patrol_center + Vector2(distance * math.cos(angle), distance * math.sin(angle))

    def _angle_to(self, direction: Vector2) -> float:
        return math.degrees(math.atan2(direction.y, direction.x)) + 90

    def _angle_diff(self, direction: Vector2) -> float:
        diff = self._angle_to(direction) - self.rotation
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        return diff

    def _is_facing(self, point: Vector2, tolerance: float = 15) -> bool:
        direction = point - self.position
        if direction.length_squared() == 0:
            return True
        return abs(self._angle_diff(direction)) <= tolerance

    def _move_toward(self, target: Vector2, delta_time: float):
        direction = target - self.position
        if direction.length_squared() == 0:
            return
        diff = self._angle_diff(direction)
        if abs(diff) > 5:
            self.rotation += (1 if diff > 0 else -1) * self.rotation_speed * delta_time
        angle = math.radians(self.rotation - 90)
        self.heading = Vector2(math.cos(angle), math.sin(angle))
        if abs(diff) <= 30:
            self.velocity += self.heading * self.thrust_force * delta_time

    def _update_physics(self, delta_time: float):
        self.velocity *= self.drag_coefficient
        speed = self.velocity.length()
        if speed > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed
        self.position += self.velocity * delta_time

    # Drawing -----------------------------------------------------------------

    def draw(self, screen: pygame.Surface, camera_offset: Vector2):
        screen_pos = self.position - camera_offset
        points = [(point.rotate(self.rotation) + screen_pos) for point in self.points]
        gfx.draw_glow(screen, screen_pos, self.size * 2.0, PATROL_COLOR, 0.3)
        if self.velocity.length() > 40:
            gfx.draw_engine_flame(screen, screen_pos, self.rotation, self.size * 0.9,
                                  (40, 110, 230), (190, 230, 255),
                                  power=min(1.3, self.velocity.length() / 300.0 + 0.4),
                                  seed=self.position.y * 0.002)
        pygame.draw.polygon(screen, PATROL_COLOR, points)
        plate = [screen_pos + (p - screen_pos) * 0.55 for p in points]
        pygame.draw.polygon(screen, gfx.darken(PATROL_COLOR, 0.4), plate)
        pygame.draw.polygon(screen, PATROL_OUTLINE, points, 2)

        if self.current_hull < self.max_hull:
            width, height = 30, 4
            x = screen_pos.x - width // 2
            y = screen_pos.y - self.size - 10
            pygame.draw.rect(screen, (100, 100, 100), (x, y, width, height))
            fraction = max(0.0, self.current_hull / self.max_hull)
            pygame.draw.rect(screen, (80, 200, 255), (x, y, int(width * fraction), height))

        self.weapon_system.draw(screen, camera_offset)
