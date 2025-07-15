import pygame
import logging
from pygame import Vector2
from .docking_state import DockingState, DockingResult

logger = logging.getLogger(__name__)


class DockingManager:
    """Manages ship docking operations and state transitions."""
    
    def __init__(self):
        self.docking_state = DockingState.FREE_FLIGHT
        self.target_station = None
        self.docking_timer = 0.0
        self.docking_duration = 2.0  # Seconds for docking animation
        self.last_status_message = ""
        
        # Docking parameters
        self.max_docking_speed = 50.0  # Maximum velocity for docking
        self.docking_range_buffer = 20.0  # Extra range beyond station size
        self.approach_detection_range = 100.0  # Range to detect approaching ships
        
        # Auto-docking settings (can be moved to settings later)
        self.auto_dock_enabled = True
        self.require_confirmation = False
        
    def update(self, ship, stations, delta_time):
        """Update docking system state and handle transitions."""
        previous_state = self.docking_state
        
        if self.docking_state == DockingState.FREE_FLIGHT:
            self._update_free_flight(ship, stations)
        elif self.docking_state == DockingState.APPROACHING:
            self._update_approaching(ship, stations)
        elif self.docking_state == DockingState.DOCKING:
            self._update_docking(ship, delta_time)
        elif self.docking_state == DockingState.DOCKED:
            self._update_docked(ship)
        elif self.docking_state == DockingState.UNDOCKING:
            self._update_undocking(ship, delta_time)
            
        # Log state changes
        if previous_state != self.docking_state:
            logger.info(f"Docking state changed: {previous_state.value} -> {self.docking_state.value}")
            
    def _update_free_flight(self, ship, stations):
        """Handle free flight state - detect approaching stations."""
        nearest_station = self._find_nearest_station(ship, stations)
        
        if nearest_station:
            distance = (ship.position - nearest_station.position).length()
            detection_range = nearest_station.size + self.approach_detection_range
            
            if distance <= detection_range:
                self.target_station = nearest_station
                self.docking_state = DockingState.APPROACHING
                self.last_status_message = f"Approaching {nearest_station.name}"
                
    def _update_approaching(self, ship, stations):
        """Handle approaching state - check for docking conditions."""
        if not self.target_station:
            self.docking_state = DockingState.FREE_FLIGHT
            return
            
        # Check if still in approach range
        distance = (ship.position - self.target_station.position).length()
        detection_range = self.target_station.size + self.approach_detection_range
        
        if distance > detection_range:
            # Moved away from station
            self.target_station = None
            self.docking_state = DockingState.FREE_FLIGHT
            self.last_status_message = ""
            return
            
        # Check if docking conditions are met
        can_dock, reason = self._can_dock(ship, self.target_station)
        
        if can_dock:
            if self.auto_dock_enabled and not self.require_confirmation:
                self._initiate_docking(ship)
            else:
                self.last_status_message = f"Ready to dock - Press D to dock with {self.target_station.name}"
        else:
            self._update_status_message_for_reason(reason)
            
    def _update_docking(self, ship, delta_time):
        """Handle active docking sequence."""
        self.docking_timer += delta_time
        
        if self.docking_timer >= self.docking_duration:
            # Docking complete
            self._complete_docking(ship)
        else:
            # Animate ship toward docking position
            self._animate_docking(ship, delta_time)
            
    def _update_docked(self, ship):
        """Handle docked state - ship is stationary at station."""
        if self.target_station:
            # Keep ship positioned at station
            dock_position = self._get_dock_position(self.target_station)
            ship.position = dock_position
            ship.velocity = Vector2(0, 0)  # No movement while docked
            
    def _update_undocking(self, ship, delta_time):
        """Handle undocking sequence."""
        self.docking_timer += delta_time
        
        if self.docking_timer >= self.docking_duration:
            # Undocking complete
            self.docking_state = DockingState.FREE_FLIGHT
            self.target_station = None
            self.docking_timer = 0.0
            self.last_status_message = "Undocked successfully"
        else:
            # Animate ship away from station
            self._animate_undocking(ship, delta_time)
            
    def attempt_manual_docking(self, ship, stations):
        """Attempt manual docking initiated by player input."""
        if self.docking_state == DockingState.DOCKED:
            return DockingResult.ALREADY_DOCKED
            
        if self.docking_state != DockingState.APPROACHING:
            # Try to find a nearby station
            nearest_station = self._find_nearest_dockable_station(ship, stations)
            if nearest_station:
                self.target_station = nearest_station
            else:
                return DockingResult.NO_TARGET
                
        # Check docking conditions
        can_dock, reason = self._can_dock(ship, self.target_station)
        if not can_dock:
            return reason
            
        # Initiate docking
        self._initiate_docking(ship)
        return DockingResult.SUCCESS
        
    def attempt_undocking(self, ship):
        """Attempt to undock from current station."""
        if self.docking_state != DockingState.DOCKED:
            return DockingResult.INVALID_STATE
            
        self._initiate_undocking(ship)
        return DockingResult.SUCCESS
        
    def _can_dock(self, ship, station):
        """Check if ship can dock with station."""
        if not station:
            return False, DockingResult.NO_TARGET
            
        # Check distance
        distance = (ship.position - station.position).length()
        max_distance = station.size + ship.size + self.docking_range_buffer
        
        if distance > max_distance:
            return False, DockingResult.TOO_FAR
            
        # Check velocity
        if ship.velocity.length() > self.max_docking_speed:
            return False, DockingResult.TOO_FAST
            
        return True, DockingResult.SUCCESS
        
    def _find_nearest_station(self, ship, stations):
        """Find the nearest station to the ship."""
        if not stations:
            return None
            
        nearest_station = None
        nearest_distance = float('inf')
        
        for station in stations:
            distance = (ship.position - station.position).length()
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_station = station
                
        return nearest_station
        
    def _find_nearest_dockable_station(self, ship, stations):
        """Find the nearest station within docking range."""
        nearest_station = None
        nearest_distance = float('inf')
        
        for station in stations:
            distance = (ship.position - station.position).length()
            max_distance = station.size + ship.size + self.docking_range_buffer
            
            if distance <= max_distance and distance < nearest_distance:
                nearest_distance = distance
                nearest_station = station
                
        return nearest_station
        
    def _initiate_docking(self, ship):
        """Begin the docking sequence."""
        self.docking_state = DockingState.DOCKING
        self.docking_timer = 0.0
        self.last_status_message = f"Docking with {self.target_station.name}..."
        logger.info(f"Initiating docking with {self.target_station.name}")
        
    def _complete_docking(self, ship):
        """Complete the docking sequence."""
        self.docking_state = DockingState.DOCKED
        self.docking_timer = 0.0
        
        # Position ship at docking point
        dock_position = self._get_dock_position(self.target_station)
        ship.position = dock_position
        ship.velocity = Vector2(0, 0)
        
        self.last_status_message = f"Docked at {self.target_station.name}"
        logger.info(f"Successfully docked at {self.target_station.name}")
        
    def _initiate_undocking(self, ship):
        """Begin the undocking sequence."""
        self.docking_state = DockingState.UNDOCKING
        self.docking_timer = 0.0
        self.last_status_message = f"Undocking from {self.target_station.name}..."
        logger.info(f"Initiating undocking from {self.target_station.name}")
        
    def _get_dock_position(self, station):
        """Calculate the docking position for a station."""
        # For now, dock at the station's position
        # In the future, this could be a specific docking port
        return Vector2(station.position.x, station.position.y)
        
    def _animate_docking(self, ship, delta_time):
        """Animate ship movement during docking."""
        if not self.target_station:
            return
            
        # Move ship toward docking position
        dock_position = self._get_dock_position(self.target_station)
        direction = dock_position - ship.position
        
        if direction.length() > 0:
            # Smooth movement toward dock
            move_speed = 30.0  # Units per second
            move_vector = direction.normalize() * move_speed * delta_time
            ship.position += move_vector
            
        # Gradually reduce velocity
        ship.velocity *= 0.95
        
    def _animate_undocking(self, ship, delta_time):
        """Animate ship movement during undocking."""
        if not self.target_station:
            return
            
        # Move ship away from station
        direction = ship.position - self.target_station.position
        
        if direction.length() > 0:
            # Move away from station
            move_speed = 20.0  # Units per second
            move_vector = direction.normalize() * move_speed * delta_time
            ship.position += move_vector
        else:
            # Ship is at exact station position - move in a default direction
            move_speed = 20.0
            default_direction = Vector2(1, 0)  # Move right
            ship.position += default_direction * move_speed * delta_time
            
    def _update_status_message_for_reason(self, reason):
        """Update status message based on docking failure reason."""
        if reason == DockingResult.TOO_FAST:
            self.last_status_message = f"Reduce speed to dock (Current: {int(self.max_docking_speed)}+ units/s)"
        elif reason == DockingResult.TOO_FAR:
            self.last_status_message = f"Move closer to {self.target_station.name} to dock"
            
    def get_status_message(self):
        """Get the current docking status message."""
        return self.last_status_message
        
    def get_docking_state(self):
        """Get the current docking state."""
        return self.docking_state
        
    def get_target_station(self):
        """Get the current target station."""
        return self.target_station
        
    def is_docked(self):
        """Check if ship is currently docked."""
        return self.docking_state == DockingState.DOCKED
        
    def is_docking_in_progress(self):
        """Check if docking sequence is in progress."""
        return self.docking_state in [DockingState.DOCKING, DockingState.UNDOCKING]