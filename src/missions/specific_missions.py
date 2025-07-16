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
        self.description = f"Transport {quantity} units of {commodity_name} to the destination station. Cargo will be provided at pickup."
        
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
        self.reward = MissionReward(
            credits=base_reward,
            reputation_bonus=random.randint(5, 15)
        )
        
        # Set penalties
        self.penalty = MissionPenalty(
            credits=int(base_reward * 0.2),
            reputation_loss=random.randint(10, 20)
        )
        
        # Set time limit (2-6 hours of real time)
        self.time_limit = random.randint(7200, 21600)  # 2-6 hours in seconds
        
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
            station_id = getattr(current_station, 'id', str(current_station))
            if station_id == self.origin_station_id:
                # Check if player has the required cargo
                if ship.cargo_hold.get_quantity(self.commodity_id) >= self.quantity:
                    self.objectives[0].completed = True
                    self.pickup_completed = True
                    self.progress_description = f"Deliver {self.quantity} units to destination"
                    self.status = MissionStatus.IN_PROGRESS
        
        # Check delivery objective
        if self.pickup_completed and current_station:
            station_id = getattr(current_station, 'id', str(current_station))
            if station_id == self.destination_station_id:
                # Check if player still has the cargo to deliver
                if ship.cargo_hold.get_quantity(self.commodity_id) >= self.quantity:
                    self.objectives[1].completed = True
                    self.complete()
                    return True
        
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
        self.description = (f"Acquire {buy_quantity} units of {buy_name} and "
                           f"exchange them for {sell_quantity} units of {sell_name} at this station.")
        
        # Set requirements
        self.requirements = MissionRequirement(
            min_cargo_capacity=max(buy_quantity, sell_quantity),
            min_reputation=10
        )
        
        # Create objectives
        self.objectives = [
            MissionObjective(
                description=f"Acquire {buy_quantity} units of {buy_name}",
                target_commodity=buy_commodity,
                target_quantity=buy_quantity
            ),
            MissionObjective(
                description=f"Exchange for {sell_quantity} units of {sell_name}",
                target_station_id=station_id,
                target_commodity=sell_commodity,
                target_quantity=sell_quantity
            )
        ]
        
        # Set rewards
        base_reward = buy_quantity * 100 + sell_quantity * 120
        self.reward = MissionReward(
            credits=base_reward,
            reputation_bonus=random.randint(10, 25),
            bonus_items={sell_commodity: sell_quantity}
        )
        
        # Set penalties
        self.penalty = MissionPenalty(
            credits=int(base_reward * 0.3),
            reputation_loss=random.randint(15, 30)
        )
        
        # Longer time limit for trading missions
        self.time_limit = random.randint(10800, 28800)  # 3-8 hours
        
        self.progress_description = f"Acquire {buy_quantity} units of {buy_name}"
        self.trade_completed = False


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
        self.description = f"Deliver required supplies: {', '.join(supply_names[:3])}{'...' if len(supply_names) > 3 else ''}"
        
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
        self.reward = MissionReward(
            credits=base_reward,
            reputation_bonus=random.randint(15, 35)
        )
        
        # Set penalties
        self.penalty = MissionPenalty(
            credits=int(base_reward * 0.25),
            reputation_loss=random.randint(20, 40)
        )
        
        # Time limit based on number of supplies
        base_time = 14400  # 4 hours
        self.time_limit = base_time + (len(required_supplies) * 3600)  # +1 hour per supply type
        
        self.progress_description = "Gather required supplies and deliver to station"


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
                           f"{commodity_name} immediately. Lives may depend on this delivery!")
        
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
        self.reward = MissionReward(
            credits=base_reward,
            reputation_bonus=random.randint(25, 50)
        )
        
        # Higher penalties for failure
        self.penalty = MissionPenalty(
            credits=int(base_reward * 0.5),
            reputation_loss=random.randint(40, 80)
        )
        
        # Much shorter time limit (30 minutes to 2 hours)
        self.time_limit = random.randint(1800, 7200)
        
        self.progress_description = "URGENT: Pick up emergency supplies immediately!"
        self.pickup_completed = False


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
        self.reward = MissionReward(
            credits=base_reward,
            reputation_bonus=random.randint(20, 40)
        )
        
        # Set penalties
        self.penalty = MissionPenalty(
            credits=int(base_reward * 0.2),
            reputation_loss=random.randint(15, 25)
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
        ship_sector_y = int(ship.position.y // 1000)
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