import pytest
from pygame import Vector2
from src.docking.docking_manager import DockingManager
from src.docking.docking_state import DockingState, DockingResult
from src.entities.ship import Ship
from src.entities.station import Station


class TestDockingManager:
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.docking_manager = DockingManager()
        self.ship = Ship(100, 100)
        self.station = Station(200, 200)
        self.stations = [self.station]
        
    def test_initialization(self):
        """Test DockingManager initialization."""
        assert self.docking_manager.docking_state == DockingState.FREE_FLIGHT
        assert self.docking_manager.target_station is None
        assert self.docking_manager.docking_timer == 0.0
        assert self.docking_manager.max_docking_speed == 50.0
        assert self.docking_manager.docking_range_buffer == 20.0
        
    def test_free_flight_to_approaching(self):
        """Test transition from free flight to approaching state."""
        # Position ship near station
        distance = self.station.size + self.docking_manager.approach_detection_range - 10
        self.ship.position = Vector2(
            self.station.position.x - distance, 
            self.station.position.y
        )
        
        self.docking_manager.update(self.ship, self.stations, 0.016)
        
        assert self.docking_manager.docking_state == DockingState.APPROACHING
        assert self.docking_manager.target_station == self.station
        assert "Approaching" in self.docking_manager.get_status_message()
        
    def test_approaching_to_free_flight(self):
        """Test transition from approaching back to free flight when moving away."""
        # First get into approaching state
        self.docking_manager.docking_state = DockingState.APPROACHING
        self.docking_manager.target_station = self.station
        
        # Move ship far away
        self.ship.position = Vector2(1000, 1000)
        
        self.docking_manager.update(self.ship, self.stations, 0.016)
        
        assert self.docking_manager.docking_state == DockingState.FREE_FLIGHT
        assert self.docking_manager.target_station is None
        
    def test_can_dock_success(self):
        """Test successful docking conditions."""
        # Position ship close to station
        distance = self.station.size + self.ship.size + self.docking_manager.docking_range_buffer - 5
        self.ship.position = Vector2(
            self.station.position.x - distance,
            self.station.position.y
        )
        # Set low velocity
        self.ship.velocity = Vector2(10, 0)
        
        can_dock, reason = self.docking_manager._can_dock(self.ship, self.station)
        
        assert can_dock is True
        assert reason == DockingResult.SUCCESS
        
    def test_can_dock_too_far(self):
        """Test docking failure due to distance."""
        # Position ship far from station
        self.ship.position = Vector2(1000, 1000)
        self.ship.velocity = Vector2(10, 0)
        
        can_dock, reason = self.docking_manager._can_dock(self.ship, self.station)
        
        assert can_dock is False
        assert reason == DockingResult.TOO_FAR
        
    def test_can_dock_too_fast(self):
        """Test docking failure due to high velocity."""
        # Position ship close to station
        distance = self.station.size + self.ship.size + self.docking_manager.docking_range_buffer - 5
        self.ship.position = Vector2(
            self.station.position.x - distance,
            self.station.position.y
        )
        # Set high velocity
        self.ship.velocity = Vector2(100, 0)
        
        can_dock, reason = self.docking_manager._can_dock(self.ship, self.station)
        
        assert can_dock is False
        assert reason == DockingResult.TOO_FAST
        
    def test_manual_docking_success(self):
        """Test successful manual docking."""
        # Position ship for successful docking
        distance = self.station.size + self.ship.size + self.docking_manager.docking_range_buffer - 5
        self.ship.position = Vector2(
            self.station.position.x - distance,
            self.station.position.y
        )
        self.ship.velocity = Vector2(10, 0)
        
        result = self.docking_manager.attempt_manual_docking(self.ship, self.stations)
        
        assert result == DockingResult.SUCCESS
        assert self.docking_manager.docking_state == DockingState.DOCKING
        assert self.docking_manager.target_station == self.station
        
    def test_manual_docking_no_target(self):
        """Test manual docking with no nearby stations."""
        # Position ship far from all stations
        self.ship.position = Vector2(1000, 1000)
        
        result = self.docking_manager.attempt_manual_docking(self.ship, self.stations)
        
        assert result == DockingResult.NO_TARGET
        
    def test_manual_docking_already_docked(self):
        """Test manual docking when already docked."""
        self.docking_manager.docking_state = DockingState.DOCKED
        
        result = self.docking_manager.attempt_manual_docking(self.ship, self.stations)
        
        assert result == DockingResult.ALREADY_DOCKED
        
    def test_docking_sequence(self):
        """Test complete docking sequence."""
        # Setup for docking
        self.docking_manager.docking_state = DockingState.DOCKING
        self.docking_manager.target_station = self.station
        self.docking_manager.docking_timer = 0.0
        
        # Simulate docking duration
        delta_time = 0.5
        for _ in range(5):  # 2.5 seconds total
            self.docking_manager.update(self.ship, self.stations, delta_time)
            
        assert self.docking_manager.docking_state == DockingState.DOCKED
        assert self.ship.velocity.length() == 0  # Ship should be stationary
        
    def test_undocking_success(self):
        """Test successful undocking."""
        # Setup docked state
        self.docking_manager.docking_state = DockingState.DOCKED
        self.docking_manager.target_station = self.station
        
        result = self.docking_manager.attempt_undocking(self.ship)
        
        assert result == DockingResult.SUCCESS
        assert self.docking_manager.docking_state == DockingState.UNDOCKING
        
    def test_undocking_invalid_state(self):
        """Test undocking when not docked."""
        self.docking_manager.docking_state = DockingState.FREE_FLIGHT
        
        result = self.docking_manager.attempt_undocking(self.ship)
        
        assert result == DockingResult.INVALID_STATE
        
    def test_undocking_sequence(self):
        """Test complete undocking sequence."""
        # Setup for undocking
        self.docking_manager.docking_state = DockingState.UNDOCKING
        self.docking_manager.target_station = self.station
        self.docking_manager.docking_timer = 0.0
        
        # Simulate undocking duration
        delta_time = 0.5
        for _ in range(5):  # 2.5 seconds total
            self.docking_manager.update(self.ship, self.stations, delta_time)
            
        assert self.docking_manager.docking_state == DockingState.FREE_FLIGHT
        assert self.docking_manager.target_station is None
        
    def test_find_nearest_station(self):
        """Test finding nearest station."""
        # Add multiple stations
        station2 = Station(300, 300)
        station3 = Station(150, 150)  # This should be nearest
        stations = [self.station, station2, station3]
        
        nearest = self.docking_manager._find_nearest_station(self.ship, stations)
        
        assert nearest == station3
        
    def test_find_nearest_dockable_station(self):
        """Test finding nearest dockable station."""
        # Position ship close to station
        distance = self.station.size + self.ship.size + self.docking_manager.docking_range_buffer - 5
        self.ship.position = Vector2(
            self.station.position.x - distance,
            self.station.position.y
        )
        
        # Add another station that's closer but not in docking range
        close_station = Station(110, 110)
        stations = [self.station, close_station]
        
        nearest_dockable = self.docking_manager._find_nearest_dockable_station(self.ship, stations)
        
        # Should return the station that's in docking range, not the closest one
        assert nearest_dockable == self.station
        
    def test_auto_docking_disabled(self):
        """Test behavior when auto-docking is disabled."""
        self.docking_manager.auto_dock_enabled = False
        
        # Position ship for successful docking
        distance = self.station.size + self.ship.size + self.docking_manager.docking_range_buffer - 5
        self.ship.position = Vector2(
            self.station.position.x - distance,
            self.station.position.y
        )
        self.ship.velocity = Vector2(10, 0)
        
        # Set to approaching state
        self.docking_manager.docking_state = DockingState.APPROACHING
        self.docking_manager.target_station = self.station
        
        self.docking_manager.update(self.ship, self.stations, 0.016)
        
        # Should stay in approaching state, not auto-dock
        assert self.docking_manager.docking_state == DockingState.APPROACHING
        assert "Press D to dock" in self.docking_manager.get_status_message()
        
    def test_status_messages(self):
        """Test various status messages."""
        # Too fast message
        self.docking_manager.docking_state = DockingState.APPROACHING
        self.docking_manager.target_station = self.station
        distance = self.station.size + self.ship.size + self.docking_manager.docking_range_buffer - 5
        self.ship.position = Vector2(
            self.station.position.x - distance,
            self.station.position.y
        )
        self.ship.velocity = Vector2(100, 0)  # Too fast
        
        self.docking_manager.update(self.ship, self.stations, 0.016)
        
        assert "Reduce speed" in self.docking_manager.get_status_message()
        
        # Too far message - set ship within approach range but outside docking range
        approach_distance = self.station.size + self.docking_manager.approach_detection_range - 10
        docking_distance = self.station.size + self.ship.size + self.docking_manager.docking_range_buffer + 10
        self.ship.position = Vector2(
            self.station.position.x - docking_distance,  # Too far for docking but within approach
            self.station.position.y
        )
        self.ship.velocity = Vector2(10, 0)
        
        self.docking_manager.update(self.ship, self.stations, 0.016)
        
        assert "Move closer" in self.docking_manager.get_status_message()
        
    def test_state_queries(self):
        """Test state query methods."""
        assert not self.docking_manager.is_docked()
        assert not self.docking_manager.is_docking_in_progress()
        
        self.docking_manager.docking_state = DockingState.DOCKED
        assert self.docking_manager.is_docked()
        assert not self.docking_manager.is_docking_in_progress()
        
        self.docking_manager.docking_state = DockingState.DOCKING
        assert not self.docking_manager.is_docked()
        assert self.docking_manager.is_docking_in_progress()
        
        self.docking_manager.docking_state = DockingState.UNDOCKING
        assert not self.docking_manager.is_docked()
        assert self.docking_manager.is_docking_in_progress()


class TestDockingState:
    
    def test_docking_state_enum(self):
        """Test DockingState enum values."""
        assert DockingState.FREE_FLIGHT.value == "free_flight"
        assert DockingState.APPROACHING.value == "approaching"
        assert DockingState.DOCKING.value == "docking"
        assert DockingState.DOCKED.value == "docked"
        assert DockingState.UNDOCKING.value == "undocking"
        
    def test_docking_result_enum(self):
        """Test DockingResult enum values."""
        assert DockingResult.SUCCESS.value == "success"
        assert DockingResult.TOO_FAST.value == "too_fast"
        assert DockingResult.TOO_FAR.value == "too_far"
        assert DockingResult.NO_TARGET.value == "no_target"
        assert DockingResult.ALREADY_DOCKED.value == "already_docked"
        assert DockingResult.INVALID_STATE.value == "invalid_state"


class TestDockingIntegration:
    """Integration tests for docking system with ship and station interactions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.docking_manager = DockingManager()
        self.ship = Ship(100, 100)
        self.station = Station(200, 200)
        self.stations = [self.station]
        
    def test_ship_position_during_docking(self):
        """Test that ship position is correctly managed during docking."""
        original_position = Vector2(self.ship.position)
        
        # Setup docking
        self.docking_manager.docking_state = DockingState.DOCKING
        self.docking_manager.target_station = self.station
        self.docking_manager.docking_timer = 0.0
        
        # Complete docking sequence
        delta_time = 0.5
        for _ in range(5):
            self.docking_manager.update(self.ship, self.stations, delta_time)
            
        # Ship should be at station position when docked
        dock_position = self.docking_manager._get_dock_position(self.station)
        assert self.ship.position == dock_position
        assert self.ship.velocity.length() == 0
        
    def test_ship_movement_restrictions_when_docked(self):
        """Test that ship movement is restricted when docked."""
        # Setup docked state
        self.docking_manager.docking_state = DockingState.DOCKED
        self.docking_manager.target_station = self.station
        
        # Try to move ship
        original_position = Vector2(self.ship.position)
        self.ship.velocity = Vector2(50, 50)
        
        # Update docking system (should keep ship at station)
        self.docking_manager.update(self.ship, self.stations, 0.016)
        
        # Ship should remain at docking position with zero velocity
        assert self.ship.velocity.length() == 0
        
    def test_collision_detection_integration(self):
        """Test that docking works with existing collision detection."""
        # Position ship very close to station (within collision range)
        collision_distance = self.station.size + self.ship.size - 5
        self.ship.position = Vector2(
            self.station.position.x - collision_distance,
            self.station.position.y
        )
        self.ship.velocity = Vector2(10, 0)
        
        # Should be able to dock despite being in collision range
        result = self.docking_manager.attempt_manual_docking(self.ship, self.stations)
        assert result == DockingResult.SUCCESS
        
    def test_zero_distance_collision_handling(self):
        """Test that collision detection handles zero-distance scenarios."""
        # Position ship exactly at station position
        self.ship.position = Vector2(self.station.position.x, self.station.position.y)
        self.ship.velocity = Vector2(10, 0)
        
        # This should not crash due to zero-length vector normalization
        collision_occurred = self.ship.check_collision_detailed(self.station)
        
        # Should detect collision and handle it gracefully
        assert collision_occurred is True
        # Ship should be moved away from station position
        assert self.ship.position != self.station.position
        
    def test_zero_velocity_collision_handling(self):
        """Test collision detection when ship has zero velocity."""
        # Position ship exactly at station position with zero velocity
        self.ship.position = Vector2(self.station.position.x, self.station.position.y)
        self.ship.velocity = Vector2(0, 0)  # Zero velocity
        
        # This should not crash due to zero-length vector scaling
        collision_occurred = self.ship.check_collision_detailed(self.station)
        
        # Should detect collision and handle it gracefully
        assert collision_occurred is True
        # Ship should be moved away from station position
        assert self.ship.position != self.station.position
        # Ship should have some velocity after collision
        assert self.ship.velocity.length() > 0
        
    def test_undocking_from_same_position(self):
        """Test undocking when ship is at exact station position."""
        # Setup docked state with ship at exact station position
        self.docking_manager.docking_state = DockingState.UNDOCKING
        self.docking_manager.target_station = self.station
        self.docking_manager.docking_timer = 0.0
        self.ship.position = Vector2(self.station.position.x, self.station.position.y)
        
        # This should not crash and should move ship away
        self.docking_manager.update(self.ship, self.stations, 0.1)
        
        # Ship should be moved away from station
        assert self.ship.position != self.station.position