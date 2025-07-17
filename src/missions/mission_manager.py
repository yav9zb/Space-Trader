import random
import time
import logging
from typing import List, Dict, Optional, Any

from .mission_types import Mission, MissionStatus, MissionType
from .specific_missions import (
    DeliveryMission, TradingContractMission, SupplyRunMission,
    EmergencyDeliveryMission, ExplorationMission
)

try:
    from ..trading.commodity import commodity_registry
    from ..entities.station import StationType
except ImportError:
    from trading.commodity import commodity_registry
    from entities.station import StationType

logger = logging.getLogger(__name__)


class MissionManager:
    """Manages all missions in the game including generation, tracking, and completion."""
    
    def __init__(self):
        self.available_missions: List[Mission] = []
        self.active_missions: List[Mission] = []
        self.completed_missions: List[Mission] = []
        self.failed_missions: List[Mission] = []
        
        # Mission generation settings
        self.max_active_missions = 5
        self.mission_generation_interval = 900  # Generate new missions every 15 minutes
        self.last_generation_time = 0
        
        # On-demand mission generation
        self.missions_per_station_range = (1, 10)  # Random range for missions per station
        self.visited_stations = set()  # Track which stations have been visited
        self.station_mission_seeds = {}  # Store seeds for deterministic mission generation per station
        
        # Station mission preferences based on type
        self.station_mission_preferences = {
            StationType.TRADING: {
                MissionType.DELIVERY: 0.4,
                MissionType.TRADING_CONTRACT: 0.4,
                MissionType.SUPPLY_RUN: 0.2
            },
            StationType.MILITARY: {
                MissionType.EMERGENCY_DELIVERY: 0.3,
                MissionType.SUPPLY_RUN: 0.3,
                MissionType.EXPLORATION: 0.2,
                MissionType.DELIVERY: 0.2
            },
            StationType.MINING: {
                MissionType.DELIVERY: 0.4,
                MissionType.SUPPLY_RUN: 0.4,
                MissionType.TRADING_CONTRACT: 0.2
            },
            StationType.RESEARCH: {
                MissionType.EXPLORATION: 0.4,
                MissionType.DELIVERY: 0.3,
                MissionType.SUPPLY_RUN: 0.3
            },
            StationType.SHIPYARD: {
                MissionType.SUPPLY_RUN: 0.4,
                MissionType.DELIVERY: 0.3,
                MissionType.TRADING_CONTRACT: 0.3
            }
        }
    
    def update(self, game_engine):
        """Update mission system - generate new missions, check completions, etc."""
        current_time = time.time()
        
        # Refresh missions for visited stations periodically
        if (current_time - self.last_generation_time > self.mission_generation_interval):
            self.refresh_missions_for_visited_stations(game_engine)
            self.last_generation_time = current_time
        
        # Update active missions
        for mission in self.active_missions[:]:  # Copy list to avoid modification during iteration
            if mission.update_progress(game_engine.ship, self.get_current_station(game_engine)):
                # Mission completed
                self.complete_mission(mission, game_engine.ship)
            elif mission.status in [MissionStatus.FAILED, MissionStatus.EXPIRED]:
                # Mission failed or expired
                self.fail_mission(mission, game_engine.ship)
        
        # Clean up expired available missions
        self.cleanup_expired_missions()
    
    def initialize_missions(self, game_engine):
        """Initialize missions for a new game."""
        # No longer generate missions at startup - they will be generated on first visit
        logger.info("Mission system initialized - missions will be generated on first station visit")
    
    def generate_missions_for_station(self, station, game_engine):
        """Generate missions for a specific station on first visit."""
        if station.name in self.visited_stations:
            return  # Already visited and has missions
        
        # Mark station as visited
        self.visited_stations.add(station.name)
        
        # Use station name as seed for deterministic mission generation
        station_seed = hash(f"{game_engine.universe.world_seed}_{station.name}") & 0x7FFFFFFF
        self.station_mission_seeds[station.name] = station_seed
        
        # Generate missions using the station's seed
        random.seed(station_seed)
        
        # Randomly choose missions for this station
        min_missions, max_missions = self.missions_per_station_range
        station_missions = random.randint(min_missions, max_missions)
        
        logger.info(f"Generating {station_missions} missions for first visit to {station.name}")
        
        # Generate missions for this station
        missions_generated = 0
        for _ in range(station_missions):
            mission = self.generate_station_specific_mission(station, game_engine.universe.stations)
            if mission:
                self.available_missions.append(mission)
                missions_generated += 1
                logger.debug(f"Generated mission for {station.name}: {mission.title}")
        
        # Reset random seed to current time to avoid affecting other random operations
        random.seed()
        
        logger.info(f"Generated {missions_generated} missions for {station.name}")
    
    def refresh_missions_for_visited_stations(self, game_engine):
        """Refresh missions for stations that have been visited."""
        if not self.visited_stations:
            return
        
        logger.info(f"Refreshing missions for {len(self.visited_stations)} visited stations")
        
        # Remove old missions from visited stations
        self.available_missions = [
            mission for mission in self.available_missions
            if not (hasattr(mission, 'origin_station_id') and 
                   mission.origin_station_id in self.visited_stations)
        ]
        
        # Generate new missions for visited stations
        for station_name in self.visited_stations:
            station = self.get_station_by_name(station_name, game_engine.universe.stations)
            if station:
                # Use stored seed for consistent regeneration
                station_seed = self.station_mission_seeds.get(station_name, 
                    hash(f"{game_engine.universe.world_seed}_{station_name}") & 0x7FFFFFFF)
                
                # Add some time variance to the seed for different missions over time
                time_seed = int(time.time() / self.mission_generation_interval)
                combined_seed = (station_seed + time_seed) & 0x7FFFFFFF
                
                random.seed(combined_seed)
                
                # Generate new missions
                min_missions, max_missions = self.missions_per_station_range
                station_missions = random.randint(min_missions, max_missions)
                
                for _ in range(station_missions):
                    mission = self.generate_station_specific_mission(station, game_engine.universe.stations)
                    if mission:
                        self.available_missions.append(mission)
                        logger.debug(f"Refreshed mission for {station.name}: {mission.title}")
        
        # Reset random seed
        random.seed()
    
    def generate_station_specific_mission(self, origin_station, stations) -> Optional[Mission]:
        """Generate a mission specific to a particular station."""
        # For single station universes, we can only generate certain mission types
        if len(stations) < 2:
            # Only allow exploration missions and trading contracts for single station
            mission_types = [MissionType.EXPLORATION, MissionType.TRADING_CONTRACT]
            mission_type = random.choice(mission_types)
            
            try:
                if mission_type == MissionType.EXPLORATION:
                    return self._generate_exploration_mission(origin_station)
                elif mission_type == MissionType.TRADING_CONTRACT:
                    return self._generate_trading_contract_mission(origin_station)
            except Exception as e:
                logger.warning(f"Failed to generate {mission_type} mission: {e}")
                return None
        
        # Choose mission type based on this station's preferences
        station_prefs = self.station_mission_preferences.get(
            origin_station.station_type, 
            {MissionType.DELIVERY: 1.0}
        )
        
        mission_type = random.choices(
            list(station_prefs.keys()),
            weights=list(station_prefs.values())
        )[0]
        
        try:
            if mission_type == MissionType.DELIVERY:
                return self._generate_delivery_mission(origin_station, stations)
            elif mission_type == MissionType.TRADING_CONTRACT:
                return self._generate_trading_contract_mission(origin_station)
            elif mission_type == MissionType.SUPPLY_RUN:
                return self._generate_supply_run_mission(origin_station)
            elif mission_type == MissionType.EMERGENCY_DELIVERY:
                return self._generate_emergency_delivery_mission(origin_station, stations)
            elif mission_type == MissionType.EXPLORATION:
                return self._generate_exploration_mission(origin_station)
        except Exception as e:
            logger.warning(f"Failed to generate {mission_type} mission: {e}")
            return None
        
        return None
    
    def generate_random_mission(self, stations) -> Optional[Mission]:
        """Generate a random mission based on available stations."""
        if len(stations) < 2:
            return None
        
        # Choose mission type based on random station preferences
        origin_station = random.choice(stations)
        return self.generate_station_specific_mission(origin_station, stations)
    
    def _generate_delivery_mission(self, origin_station, stations) -> Optional[DeliveryMission]:
        """Generate a delivery mission."""
        # Choose destination station (not the same as origin)
        possible_destinations = [s for s in stations if s != origin_station]
        if not possible_destinations:
            return None
        
        destination_station = random.choice(possible_destinations)
        
        # Choose commodity and quantity
        commodities = commodity_registry.get_all_commodities()
        commodity = random.choice(commodities)
        quantity = random.randint(5, 25)
        
        return DeliveryMission(
            origin_station_id=origin_station.name,
            destination_station_id=destination_station.name,
            commodity_id=commodity.id,
            quantity=quantity
        )
    
    def _generate_trading_contract_mission(self, station) -> Optional[TradingContractMission]:
        """Generate a trading contract mission."""
        commodities = commodity_registry.get_all_commodities()
        if len(commodities) < 2:
            return None
        
        buy_commodity = random.choice(commodities)
        sell_commodity = random.choice([c for c in commodities if c != buy_commodity])
        
        buy_quantity = random.randint(3, 15)
        sell_quantity = random.randint(5, 20)
        
        return TradingContractMission(
            station_id=station.name,
            buy_commodity=buy_commodity.id,
            buy_quantity=buy_quantity,
            sell_commodity=sell_commodity.id,
            sell_quantity=sell_quantity
        )
    
    def _generate_supply_run_mission(self, destination_station) -> Optional[SupplyRunMission]:
        """Generate a supply run mission."""
        commodities = commodity_registry.get_all_commodities()
        if len(commodities) < 2:
            return None
        
        # Choose 2-4 different supplies
        num_supplies = random.randint(2, 4)
        selected_commodities = random.sample(commodities, min(num_supplies, len(commodities)))
        
        required_supplies = {}
        for commodity in selected_commodities:
            quantity = random.randint(3, 12)
            required_supplies[commodity.id] = quantity
        
        return SupplyRunMission(
            destination_station_id=destination_station.name,
            required_supplies=required_supplies
        )
    
    def _generate_emergency_delivery_mission(self, origin_station, stations) -> Optional[EmergencyDeliveryMission]:
        """Generate an emergency delivery mission."""
        # Emergency missions are rare
        if random.random() > 0.1:  # 10% chance
            return None
        
        possible_destinations = [s for s in stations if s != origin_station]
        if not possible_destinations:
            return None
        
        destination_station = random.choice(possible_destinations)
        
        # Medical/emergency supplies are preferred
        emergency_commodities = ["food_rations", "medical_supplies", "fuel_cells"]
        commodities = commodity_registry.get_all_commodities()
        
        # Try to find emergency commodities, otherwise use any
        commodity = None
        for emergency_id in emergency_commodities:
            try:
                commodity = commodity_registry.get_commodity(emergency_id)
                break
            except KeyError:
                continue
        
        if not commodity:
            commodity = random.choice(commodities)
        
        quantity = random.randint(8, 20)
        
        return EmergencyDeliveryMission(
            origin_station_id=origin_station.name,
            destination_station_id=destination_station.name,
            commodity_id=commodity.id,
            quantity=quantity
        )
    
    def _generate_exploration_mission(self, origin_station=None) -> Optional[ExplorationMission]:
        """Generate an exploration mission."""
        # Generate 2-4 random sectors to explore
        num_sectors = random.randint(2, 4)
        target_sectors = []
        
        for _ in range(num_sectors):
            # Generate sectors that are somewhat distant from origin
            x = random.randint(-5, 15)
            y = random.randint(-5, 15)
            target_sectors.append((x, y))
        
        # Create exploration mission with origin station if provided
        exploration_mission = ExplorationMission(target_sectors=target_sectors)
        if origin_station:
            exploration_mission.origin_station_id = origin_station.name
        
        return exploration_mission
    
    def get_available_missions_for_station(self, station_name: str) -> List[Mission]:
        """Get missions available at a specific station."""
        station_missions = []
        for mission in self.available_missions:
            # Missions are available at their origin station
            if (mission.origin_station_id == station_name or 
                (mission.origin_station_id is None and mission.mission_type == MissionType.EXPLORATION)):
                station_missions.append(mission)
        
        return station_missions
    
    def accept_mission(self, mission_id: str, ship, game_engine=None) -> tuple[bool, str]:
        """Accept a mission."""
        mission = self.get_mission_by_id(mission_id, self.available_missions)
        if not mission:
            return False, "Mission not found"
        
        if len(self.active_missions) >= self.max_active_missions:
            return False, f"Cannot accept more than {self.max_active_missions} missions"
        
        can_accept, reason = mission.can_accept(ship)
        if not can_accept:
            return False, reason
        
        if mission.accept(ship):
            self.available_missions.remove(mission)
            self.active_missions.append(mission)
            
            # Immediately update mission progress to handle cargo pickup if at origin station
            if game_engine:
                current_station = self.get_current_station(game_engine)
                if current_station:
                    mission.update_progress(ship, current_station)
            
            logger.info(f"Mission accepted: {mission.title}")
            return True, "Mission accepted successfully"
        
        return False, "Failed to accept mission"
    
    def abandon_mission(self, mission_id: str, ship) -> tuple[bool, str]:
        """Abandon an active mission."""
        mission = self.get_mission_by_id(mission_id, self.active_missions)
        if not mission:
            return False, "Mission not found in active missions"
        
        penalty = mission.abandon()
        
        # Apply penalties
        ship.credits = max(0, ship.credits - penalty.credits)
        # TODO: Apply reputation penalty when reputation system is implemented
        
        self.active_missions.remove(mission)
        self.failed_missions.append(mission)
        
        logger.info(f"Mission abandoned: {mission.title} (Penalty: {penalty.credits} credits)")
        return True, f"Mission abandoned. Penalty: {penalty.credits} credits"
    
    def complete_mission(self, mission: Mission, ship):
        """Complete a mission and apply rewards."""
        if mission in self.active_missions:
            self.active_missions.remove(mission)
        
        self.completed_missions.append(mission)
        
        # Apply rewards
        ship.credits += mission.reward.credits
        
        # Add bonus items to cargo
        for commodity_id, quantity in mission.reward.bonus_items.items():
            ship.cargo_hold.add_cargo(commodity_id, quantity)
        
        # TODO: Apply reputation bonus when reputation system is implemented
        
        logger.info(f"Mission completed: {mission.title} (Reward: {mission.reward.credits} credits)")
    
    def fail_mission(self, mission: Mission, ship):
        """Fail a mission and apply penalties."""
        if mission in self.active_missions:
            self.active_missions.remove(mission)
        
        self.failed_missions.append(mission)
        
        # Apply penalties if the mission was abandoned or failed (not just expired)
        if mission.status == MissionStatus.FAILED:
            ship.credits = max(0, ship.credits - mission.penalty.credits)
            # TODO: Apply reputation penalty when reputation system is implemented
        
        logger.info(f"Mission failed: {mission.title}")
    
    def cleanup_expired_missions(self):
        """Remove expired missions from available missions."""
        self.available_missions = [
            mission for mission in self.available_missions 
            if not mission.is_expired()
        ]
    
    def get_mission_by_id(self, mission_id: str, mission_list: List[Mission]) -> Optional[Mission]:
        """Find a mission by ID in the given list."""
        for mission in mission_list:
            if mission.id == mission_id:
                return mission
        return None
    
    def get_current_station(self, game_engine) -> Optional[Any]:
        """Get the station the player is currently docked at."""
        from ..docking.docking_state import DockingState
        
        if (hasattr(game_engine, 'docking_manager') and 
            game_engine.docking_manager.docking_state == DockingState.DOCKED):
            return game_engine.docking_manager.target_station
        
        return None
    
    def get_mission_summary(self) -> Dict[str, int]:
        """Get summary statistics of missions."""
        return {
            "available": len(self.available_missions),
            "active": len(self.active_missions),
            "completed": len(self.completed_missions),
            "failed": len(self.failed_missions)
        }
    
    def get_station_by_name(self, station_name: str, stations_list):
        """Get station object by name from the stations list."""
        for station in stations_list:
            if station.name == station_name:
                return station
        return None
    
    def get_station_coordinates(self, station_name: str, stations_list) -> Optional[str]:
        """Get formatted coordinates for a station."""
        station = self.get_station_by_name(station_name, stations_list)
        if station:
            sector_x = int(station.position.x // 1000)
            sector_y = int(-station.position.y // 1000)  # Invert Y for display consistency
            return f"Sector ({sector_x}, {sector_y})"
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize mission manager state for saving."""
        return {
            "available_missions": [mission.to_dict() for mission in self.available_missions],
            "active_missions": [mission.to_dict() for mission in self.active_missions],
            "completed_missions": [mission.to_dict() for mission in self.completed_missions],
            "failed_missions": [mission.to_dict() for mission in self.failed_missions],
            "last_generation_time": self.last_generation_time,
            "visited_stations": list(self.visited_stations),
            "station_mission_seeds": self.station_mission_seeds
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Deserialize mission manager state from save data."""
        # Clear existing missions
        self.available_missions.clear()
        self.active_missions.clear()
        self.completed_missions.clear()
        self.failed_missions.clear()
        self.visited_stations.clear()
        self.station_mission_seeds.clear()
        
        # Restore missions
        for mission_data in data.get("available_missions", []):
            mission = Mission.from_dict(mission_data)
            self.available_missions.append(mission)
        
        for mission_data in data.get("active_missions", []):
            mission = Mission.from_dict(mission_data)
            self.active_missions.append(mission)
        
        for mission_data in data.get("completed_missions", []):
            mission = Mission.from_dict(mission_data)
            self.completed_missions.append(mission)
        
        for mission_data in data.get("failed_missions", []):
            mission = Mission.from_dict(mission_data)
            self.failed_missions.append(mission)
        
        self.last_generation_time = data.get("last_generation_time", 0)
        
        # Restore visited stations
        visited_stations_data = data.get("visited_stations", [])
        self.visited_stations = set(visited_stations_data)
        
        # Restore station mission seeds
        self.station_mission_seeds = data.get("station_mission_seeds", {})


# Global mission manager instance
mission_manager = MissionManager()