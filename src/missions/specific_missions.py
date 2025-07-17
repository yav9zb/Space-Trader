import random
import time
from typing import Optional, List, Dict, Any

from .mission_types import (
    Mission, MissionType, MissionPriority, MissionStatus,
    MissionObjective, MissionRequirement, MissionReward, MissionPenalty
)

try:
    from ..trading.commodity import commodity_registry
except ImportError:
    from trading.commodity import commodity_registry


class DeliveryMission(Mission):
    """A mission to deliver specific cargo from one station to another."""
    
    def __init__(self, origin_station_id: str, destination_station_id: str, 
                 commodity_id: str, quantity: int, mission_id: str = None):
        super().__init__(mission_id)
        
        self.mission_type = MissionType.DELIVERY
        self.origin_station_id = origin_station_id
        self.destination_station_id = destination_station_id
        self.commodity_id = commodity_id
        self.quantity = quantity
        
        # Get commodity info
        try:
            commodity = commodity_registry.get_commodity(commodity_id)
            commodity_name = commodity.name
            base_value = commodity.base_price * quantity
        except KeyError:
            commodity_name = commodity_id
            base_value = quantity * 50
        
        # Set mission details
        self.title = f"Deliver {commodity_name}"
        self.description = f"Transport {quantity} units of {commodity_name} from {origin_station_id} to {destination_station_id}. Cargo will be provided at pickup."
        
        # Set requirements
        cargo_space_needed = quantity
        self.requirements = MissionRequirement(
            min_cargo_capacity=cargo_space_needed,
            min_reputation=0
        )
        
        # Create objectives
        self.objectives = [
            MissionObjective(
                description=f"Pick up {quantity} units of {commodity_name}",
                target_station_id=origin_station_id,
                target_commodity=commodity_id,
                target_quantity=quantity
            ),
            MissionObjective(
                description=f"Deliver {quantity} units of {commodity_name}",
                target_station_id=destination_station_id,
                target_commodity=commodity_id,
                target_quantity=quantity
            )
        ]
        
        # Set rewards based on distance and cargo value
        base_reward = max(500, int(base_value * 0.3))
        # Use mission ID hash for deterministic randomness
        reputation_seed = hash(self.id + "reputation") % 11 + 5  # 5-15 range
        penalty_seed = hash(self.id + "penalty") % 11 + 10  # 10-20 range
        time_seed = hash(self.id + "time") % 14401 + 7200  # 2-6 hours range
        
        self.reward = MissionReward(
            credits=base_reward,
            reputation_bonus=reputation_seed
        )
        
        # Set penalties
        self.penalty = MissionPenalty(
            credits=int(base_reward * 0.2),
            reputation_loss=penalty_seed
        )
        
        # Set time limit (2-6 hours of real time)
        self.time_limit = time_seed
        
        self.progress_description = f"Pick up {commodity_name} at origin station"
        self.pickup_completed = False
    
    def update_progress(self, ship, current_station=None) -> bool:
        """Update delivery mission progress."""
        if self.status not in [MissionStatus.ACCEPTED, MissionStatus.IN_PROGRESS]:
            return False
        
        if self.is_expired():
            self.status = MissionStatus.EXPIRED
            return False
        
        # Check pickup objective
        if not self.pickup_completed and current_station:
            station_name = getattr(current_station, 'name', str(current_station))
            if station_name == self.origin_station_id:
                # Automatically provide cargo to player when docked at pickup station
                if ship.cargo_hold.can_add(self.commodity_id, self.quantity):
                    if ship.cargo_hold.add_mission_cargo(self.commodity_id, self.quantity):
                        self.objectives[0].completed = True
                        self.pickup_completed = True
                        self.progress_description = f"Deliver {self.quantity} units to {self.destination_station_id}"
                        self.status = MissionStatus.IN_PROGRESS
                        print(f"DEBUG: Pickup completed! Added {self.quantity} {self.commodity_id} to cargo hold")
                        return False
                else:
                    self.progress_description = f"Clear cargo space to pick up {self.quantity} units"
                    print(f"DEBUG: Cannot pickup - not enough cargo space. Need {self.quantity} units")
                    return False
            else:
                print(f"DEBUG: At station {station_name}, but need to be at {self.origin_station_id} for pickup")
        
        # Check delivery objective
        if self.pickup_completed and current_station:
            station_name = getattr(current_station, 'name', str(current_station))
            if station_name == self.destination_station_id:
                # Check if player still has the cargo to deliver
                if ship.cargo_hold.get_quantity(self.commodity_id) >= self.quantity:
                    # Remove cargo from player's hold and complete mission
                    if ship.cargo_hold.remove_mission_cargo(self.commodity_id, self.quantity):
                        self.objectives[1].completed = True
                        self.complete()
                        return True
                else:
                    self.progress_description = f"Missing cargo! Need {self.quantity} units of {self.commodity_id}"
        
        # Update completion percentage
        completed_objectives = sum(1 for obj in self.objectives if obj.completed)
        self.completion_percentage = completed_objectives / len(self.objectives)
        
        return False


class TradingContractMission(Mission):
    """A mission to trade specific quantities of commodities for profit."""
    
    def __init__(self, station_id: str, buy_commodity: str, buy_quantity: int,
                 sell_commodity: str, sell_quantity: int, mission_id: str = None):
        super().__init__(mission_id)
        
        self.mission_type = MissionType.TRADING_CONTRACT
        self.origin_station_id = station_id
        self.buy_commodity = buy_commodity
        self.buy_quantity = buy_quantity
        self.sell_commodity = sell_commodity
        self.sell_quantity = sell_quantity
        
        # Get commodity names
        try:
            buy_name = commodity_registry.get_commodity(buy_commodity).name
            sell_name = commodity_registry.get_commodity(sell_commodity).name
        except KeyError:
            buy_name = buy_commodity
            sell_name = sell_commodity
        
        self.title = f"Trade {buy_name} for {sell_name}"
        self.description = (f"Bring {buy_quantity} units of {buy_name} to {station_id} and "
                           f"exchange them for {sell_quantity} units of {sell_name}.")
        
        # Set requirements - player needs to bring the buy commodity
        self.requirements = MissionRequirement(
            min_cargo_capacity=max(buy_quantity, sell_quantity),
            min_reputation=10,
            required_items={buy_commodity: buy_quantity}
        )
        
        # Create objectives
        self.objectives = [
            MissionObjective(
                description=f"Bring {buy_quantity} units of {buy_name} to station",
                target_commodity=buy_commodity,
                target_quantity=buy_quantity,
                target_station_id=station_id
            ),
            MissionObjective(
                description=f"Receive {sell_quantity} units of {sell_name}",
                target_station_id=station_id,
                target_commodity=sell_commodity,
                target_quantity=sell_quantity
            )
        ]
        
        # Set rewards - no bonus items since trade gives the commodity
        base_reward = buy_quantity * 100 + sell_quantity * 120
        # Use mission ID hash for deterministic randomness
        reputation_seed = hash(self.id + "reputation") % 16 + 10  # 10-25 range
        penalty_seed = hash(self.id + "penalty") % 16 + 15  # 15-30 range
        time_seed = hash(self.id + "time") % 18001 + 10800  # 3-8 hours range
        
        self.reward = MissionReward(
            credits=base_reward,
            reputation_bonus=reputation_seed
        )
        
        # Set penalties
        self.penalty = MissionPenalty(
            credits=int(base_reward * 0.3),
            reputation_loss=penalty_seed
        )
        
        # Longer time limit for trading missions
        self.time_limit = time_seed
        
        self.progress_description = f"Bring {buy_quantity} units of {buy_name} to {station_id}"
        self.trade_completed = False
    
    def update_progress(self, ship, current_station=None) -> bool:
        """Update trading contract mission progress."""
        if self.status not in [MissionStatus.ACCEPTED, MissionStatus.IN_PROGRESS]:
            return False
        
        if self.is_expired():
            self.status = MissionStatus.EXPIRED
            return False
        
        if not current_station:
            return False
        
        station_name = getattr(current_station, 'name', str(current_station))
        if station_name == self.origin_station_id:
            # Check if player has the required commodity to trade
            if ship.cargo_hold.get_quantity(self.buy_commodity) >= self.buy_quantity:
                if not self.objectives[0].completed:
                    self.objectives[0].completed = True
                    self.progress_description = f"Ready to trade for {self.sell_quantity} units"
                    self.status = MissionStatus.IN_PROGRESS
                
                # If first objective complete, perform the trade
                if self.objectives[0].completed and not self.trade_completed:
                    # Check if there's space for the new commodity
                    if ship.cargo_hold.can_add(self.sell_commodity, self.sell_quantity):
                        # Remove the buy commodity and add the sell commodity
                        if ship.cargo_hold.remove_cargo(self.buy_commodity, self.buy_quantity):
                            if ship.cargo_hold.add_cargo(self.sell_commodity, self.sell_quantity):
                                self.objectives[1].completed = True
                                self.trade_completed = True
                                self.complete()
                                return True
                    else:
                        self.progress_description = f"Clear cargo space for {self.sell_quantity} units"
            else:
                needed = self.buy_quantity - ship.cargo_hold.get_quantity(self.buy_commodity)
                self.progress_description = f"Need {needed} more units of {self.buy_commodity}"
        
        # Update completion percentage
        completed_objectives = sum(1 for obj in self.objectives if obj.completed)
        self.completion_percentage = completed_objectives / len(self.objectives)
        
        return False


class SupplyRunMission(Mission):
    """A mission to deliver multiple types of supplies to a station."""
    
    def __init__(self, destination_station_id: str, required_supplies: Dict[str, int], 
                 mission_id: str = None):
        super().__init__(mission_id)
        
        self.mission_type = MissionType.SUPPLY_RUN
        self.destination_station_id = destination_station_id
        self.required_supplies = required_supplies
        
        supply_names = []
        total_quantity = 0
        for commodity_id, quantity in required_supplies.items():
            try:
                name = commodity_registry.get_commodity(commodity_id).name
                supply_names.append(f"{quantity} {name}")
                total_quantity += quantity
            except KeyError:
                supply_names.append(f"{quantity} {commodity_id}")
                total_quantity += quantity
        
        self.title = "Supply Run"
        self.description = f"Deliver supplies to {destination_station_id}: {', '.join(supply_names[:3])}{'...' if len(supply_names) > 3 else ''}"
        
        # Set requirements
        self.requirements = MissionRequirement(
            min_cargo_capacity=total_quantity,
            min_reputation=5
        )
        
        # Create objectives for each supply
        self.objectives = []
        for commodity_id, quantity in required_supplies.items():
            try:
                name = commodity_registry.get_commodity(commodity_id).name
            except KeyError:
                name = commodity_id
            
            self.objectives.append(MissionObjective(
                description=f"Deliver {quantity} units of {name}",
                target_station_id=destination_station_id,
                target_commodity=commodity_id,
                target_quantity=quantity
            ))
        
        # Set rewards based on total supplies
        base_reward = total_quantity * 80
        # Use mission ID hash for deterministic randomness
        reputation_seed = hash(self.id + "reputation") % 21 + 15  # 15-35 range
        penalty_seed = hash(self.id + "penalty") % 21 + 20  # 20-40 range
        
        self.reward = MissionReward(
            credits=base_reward,
            reputation_bonus=reputation_seed
        )
        
        # Set penalties
        self.penalty = MissionPenalty(
            credits=int(base_reward * 0.25),
            reputation_loss=penalty_seed
        )
        
        # Time limit based on number of supplies
        base_time = 14400  # 4 hours
        self.time_limit = base_time + (len(required_supplies) * 3600)  # +1 hour per supply type
        
        self.progress_description = "Gather required supplies and deliver to station"
    
    def update_progress(self, ship, current_station=None) -> bool:
        """Update supply run mission progress."""
        if self.status not in [MissionStatus.ACCEPTED, MissionStatus.IN_PROGRESS]:
            return False
        
        if self.is_expired():
            self.status = MissionStatus.EXPIRED
            return False
        
        if not current_station:
            return False
        
        station_name = getattr(current_station, 'name', str(current_station))
        if station_name == self.destination_station_id:
            # Check each required supply
            completed_supplies = 0
            missing_supplies = []
            
            for i, (commodity_id, required_quantity) in enumerate(self.required_supplies.items()):
                current_quantity = ship.cargo_hold.get_quantity(commodity_id)
                
                if current_quantity >= required_quantity:
                    if not self.objectives[i].completed:
                        # Remove the supplied commodity and mark objective complete
                        if ship.cargo_hold.remove_cargo(commodity_id, required_quantity):
                            self.objectives[i].completed = True
                            completed_supplies += 1
                    else:
                        completed_supplies += 1
                else:
                    needed = required_quantity - current_quantity
                    try:
                        commodity_name = commodity_registry.get_commodity(commodity_id).name
                    except KeyError:
                        commodity_name = commodity_id
                    missing_supplies.append(f"{needed} {commodity_name}")
            
            # Update progress description
            if missing_supplies:
                self.progress_description = f"Still need: {', '.join(missing_supplies[:2])}{'...' if len(missing_supplies) > 2 else ''}"
            else:
                self.progress_description = "All supplies delivered!"
            
            # Check if mission is complete
            if completed_supplies == len(self.required_supplies):
                self.complete()
                return True
            
            # Update status
            if completed_supplies > 0 and self.status == MissionStatus.ACCEPTED:
                self.status = MissionStatus.IN_PROGRESS
        else:
            # Update progress based on what player has
            have_count = 0
            for commodity_id, required_quantity in self.required_supplies.items():
                if ship.cargo_hold.get_quantity(commodity_id) >= required_quantity:
                    have_count += 1
            
            if have_count > 0:
                self.progress_description = f"Have {have_count}/{len(self.required_supplies)} supplies. Deliver to {self.destination_station_id}"
            else:
                self.progress_description = "Gather required supplies and deliver to station"
        
        # Update completion percentage
        completed_objectives = sum(1 for obj in self.objectives if obj.completed)
        self.completion_percentage = completed_objectives / len(self.objectives)
        
        return False


class EmergencyDeliveryMission(Mission):
    """An urgent mission with higher rewards but strict time limits."""
    
    def __init__(self, origin_station_id: str, destination_station_id: str,
                 commodity_id: str, quantity: int, mission_id: str = None):
        super().__init__(mission_id)
        
        self.mission_type = MissionType.EMERGENCY_DELIVERY
        self.priority = MissionPriority.URGENT
        self.origin_station_id = origin_station_id
        self.destination_station_id = destination_station_id
        self.commodity_id = commodity_id
        self.quantity = quantity
        
        try:
            commodity_name = commodity_registry.get_commodity(commodity_id).name
        except KeyError:
            commodity_name = commodity_id
        
        self.title = f"URGENT: Deliver {commodity_name}"
        self.description = (f"EMERGENCY DELIVERY REQUIRED! Transport {quantity} units of "
                           f"{commodity_name} from {origin_station_id} to {destination_station_id} immediately. Lives may depend on this delivery!")
        
        # Higher requirements for emergency missions
        self.requirements = MissionRequirement(
            min_cargo_capacity=quantity,
            min_reputation=20
        )
        
        # Create objectives
        self.objectives = [
            MissionObjective(
                description=f"Pick up {quantity} units of {commodity_name} (URGENT)",
                target_station_id=origin_station_id,
                target_commodity=commodity_id,
                target_quantity=quantity
            ),
            MissionObjective(
                description=f"Deliver {quantity} units of {commodity_name} (URGENT)",
                target_station_id=destination_station_id,
                target_commodity=commodity_id,
                target_quantity=quantity
            )
        ]
        
        # Much higher rewards for emergency missions
        base_reward = quantity * 200
        # Use mission ID hash for deterministic randomness
        reputation_seed = hash(self.id + "reputation") % 26 + 25  # 25-50 range
        penalty_seed = hash(self.id + "penalty") % 41 + 40  # 40-80 range
        time_seed = hash(self.id + "time") % 5401 + 1800  # 30 minutes to 2 hours range
        
        self.reward = MissionReward(
            credits=base_reward,
            reputation_bonus=reputation_seed
        )
        
        # Higher penalties for failure
        self.penalty = MissionPenalty(
            credits=int(base_reward * 0.5),
            reputation_loss=penalty_seed
        )
        
        # Much shorter time limit (30 minutes to 2 hours)
        self.time_limit = time_seed
        
        self.progress_description = "URGENT: Pick up emergency supplies immediately!"
        self.pickup_completed = False
    
    def update_progress(self, ship, current_station=None) -> bool:
        """Update emergency delivery mission progress."""
        if self.status not in [MissionStatus.ACCEPTED, MissionStatus.IN_PROGRESS]:
            return False
        
        if self.is_expired():
            self.status = MissionStatus.EXPIRED
            return False
        
        # Check pickup objective
        if not self.pickup_completed and current_station:
            station_name = getattr(current_station, 'name', str(current_station))
            if station_name == self.origin_station_id:
                # Automatically provide emergency cargo when docked at pickup station
                if ship.cargo_hold.can_add(self.commodity_id, self.quantity):
                    if ship.cargo_hold.add_mission_cargo(self.commodity_id, self.quantity):
                        self.objectives[0].completed = True
                        self.pickup_completed = True
                        self.progress_description = f"URGENT: Deliver to {self.destination_station_id} NOW!"
                        self.status = MissionStatus.IN_PROGRESS
                        return False
                else:
                    self.progress_description = f"URGENT: Clear {self.quantity} cargo space immediately!"
                    return False
        
        # Check delivery objective
        if self.pickup_completed and current_station:
            station_name = getattr(current_station, 'name', str(current_station))
            if station_name == self.destination_station_id:
                # Check if player still has the emergency cargo
                if ship.cargo_hold.get_quantity(self.commodity_id) >= self.quantity:
                    # Remove emergency cargo and complete mission
                    if ship.cargo_hold.remove_mission_cargo(self.commodity_id, self.quantity):
                        self.objectives[1].completed = True
                        self.complete()
                        return True
                else:
                    self.progress_description = f"EMERGENCY CARGO LOST! Mission failed!"
                    self.status = MissionStatus.FAILED
        
        # Update completion percentage
        completed_objectives = sum(1 for obj in self.objectives if obj.completed)
        self.completion_percentage = completed_objectives / len(self.objectives)
        
        return False


class ExplorationMission(Mission):
    """A mission to explore and report on distant sectors."""
    
    def __init__(self, target_sectors: List[tuple], mission_id: str = None):
        super().__init__(mission_id)
        
        self.mission_type = MissionType.EXPLORATION
        self.target_sectors = target_sectors  # List of (x, y) coordinates
        
        self.title = "Exploration Contract"
        self.description = f"Survey {len(target_sectors)} unexplored sectors and report your findings."
        
        # Set requirements
        self.requirements = MissionRequirement(
            min_reputation=15,
            min_cargo_capacity=10  # Space for survey equipment
        )
        
        # Create objectives for each sector
        self.objectives = []
        for i, (x, y) in enumerate(target_sectors):
            self.objectives.append(MissionObjective(
                description=f"Survey sector ({x}, {y})",
                target_station_id=f"sector_{x}_{y}"
            ))
        
        # Set rewards
        base_reward = len(target_sectors) * 800
        # Use mission ID hash for deterministic randomness
        reputation_seed = hash(self.id + "reputation") % 21 + 20  # 20-40 range
        penalty_seed = hash(self.id + "penalty") % 11 + 15  # 15-25 range
        
        self.reward = MissionReward(
            credits=base_reward,
            reputation_bonus=reputation_seed
        )
        
        # Set penalties
        self.penalty = MissionPenalty(
            credits=int(base_reward * 0.2),
            reputation_loss=penalty_seed
        )
        
        # Long time limit for exploration
        self.time_limit = len(target_sectors) * 7200 + 14400  # 2 hours per sector + 4 base hours
        
        self.progress_description = "Begin exploration of target sectors"
        self.explored_sectors = set()
    
    def update_progress(self, ship, current_station=None) -> bool:
        """Update exploration progress based on ship position."""
        if self.status not in [MissionStatus.ACCEPTED, MissionStatus.IN_PROGRESS]:
            return False
        
        if self.is_expired():
            self.status = MissionStatus.EXPIRED
            return False
        
        # Check if ship is in any target sector
        ship_sector_x = int(ship.position.x // 1000)
        ship_sector_y = int(-ship.position.y // 1000)  # Invert Y for consistency with display
        current_sector = (ship_sector_x, ship_sector_y)
        
        if current_sector in self.target_sectors and current_sector not in self.explored_sectors:
            self.explored_sectors.add(current_sector)
            
            # Mark corresponding objective as complete
            for obj in self.objectives:
                if obj.target_station_id == f"sector_{current_sector[0]}_{current_sector[1]}":
                    obj.completed = True
                    break
        
        # Update progress
        completed_objectives = len(self.explored_sectors)
        self.completion_percentage = completed_objectives / len(self.target_sectors)
        
        if completed_objectives == len(self.target_sectors):
            self.complete()
            return True
        
        # Update status
        if self.status == MissionStatus.ACCEPTED and completed_objectives > 0:
            self.status = MissionStatus.IN_PROGRESS
        
        self.progress_description = f"Explored {completed_objectives}/{len(self.target_sectors)} sectors"
        
        return False