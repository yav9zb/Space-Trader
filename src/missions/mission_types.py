from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import time
import uuid


class MissionType(Enum):
    """Types of missions available in the game."""
    DELIVERY = "Delivery"
    TRADING_CONTRACT = "Trading Contract"
    SUPPLY_RUN = "Supply Run"
    EXPLORATION = "Exploration"
    EMERGENCY_DELIVERY = "Emergency Delivery"


class MissionStatus(Enum):
    """Current status of a mission."""
    AVAILABLE = "Available"
    ACCEPTED = "Accepted"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"
    EXPIRED = "Expired"


class MissionPriority(Enum):
    """Priority levels for missions."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


@dataclass
class MissionReward:
    """Rewards for completing a mission."""
    credits: int = 0
    reputation_bonus: int = 0
    bonus_items: Dict[str, int] = field(default_factory=dict)  # commodity_id -> quantity
    
    def get_total_value(self) -> int:
        """Calculate total reward value in credits."""
        total = self.credits
        # Add estimated value of bonus items (could be enhanced with market prices)
        for commodity_id, quantity in self.bonus_items.items():
            total += quantity * 50  # Rough estimate
        return total


@dataclass
class MissionPenalty:
    """Penalties for failing or abandoning a mission."""
    credits: int = 0
    reputation_loss: int = 0
    
    def get_total_cost(self) -> int:
        """Calculate total penalty cost."""
        return self.credits


@dataclass
class MissionRequirement:
    """Requirements that must be met to accept/complete a mission."""
    min_reputation: int = 0
    min_cargo_capacity: int = 0
    required_upgrades: List[str] = field(default_factory=list)
    required_items: Dict[str, int] = field(default_factory=dict)  # commodity_id -> quantity
    
    def is_met_by_ship(self, ship) -> bool:
        """Check if ship meets the requirements."""
        # Check cargo capacity
        if ship.cargo_hold.capacity < self.min_cargo_capacity:
            return False
        
        # Check required items in cargo
        for commodity_id, required_quantity in self.required_items.items():
            if ship.cargo_hold.get_quantity(commodity_id) < required_quantity:
                return False
        
        # Check upgrades (could be enhanced with actual upgrade checking)
        # For now, assume all upgrade requirements are met
        
        return True


@dataclass
class MissionObjective:
    """A single objective within a mission."""
    description: str
    completed: bool = False
    target_station_id: Optional[str] = None
    target_commodity: Optional[str] = None
    target_quantity: int = 0
    
    def check_completion(self, ship, current_station=None) -> bool:
        """Check if this objective is completed."""
        # Implementation depends on objective type
        # This is a basic framework that can be extended
        return self.completed


class Mission:
    """Base class for all missions."""
    
    def __init__(self, mission_id: str = None):
        self.id = mission_id or str(uuid.uuid4())
        self.title = "Unknown Mission"
        self.description = "No description available"
        self.mission_type = MissionType.DELIVERY
        self.status = MissionStatus.AVAILABLE
        self.priority = MissionPriority.MEDIUM
        
        # Timing
        self.created_at = time.time()
        self.accepted_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.expires_at: Optional[float] = None
        self.time_limit: Optional[float] = None  # Duration in seconds after acceptance
        
        # Stations involved
        self.origin_station_id: Optional[str] = None
        self.destination_station_id: Optional[str] = None
        
        # Mission details
        self.requirements = MissionRequirement()
        self.objectives: List[MissionObjective] = []
        self.reward = MissionReward()
        self.penalty = MissionPenalty()
        
        # Progress tracking
        self.progress_description = "Not started"
        self.completion_percentage = 0.0
    
    def can_accept(self, ship, reputation: int = 0) -> tuple[bool, str]:
        """Check if this mission can be accepted by the given ship."""
        if self.status != MissionStatus.AVAILABLE:
            return False, "Mission is not available"
        
        if self.is_expired():
            return False, "Mission has expired"
        
        if reputation < self.requirements.min_reputation:
            return False, f"Requires reputation of {self.requirements.min_reputation}"
        
        if not self.requirements.is_met_by_ship(ship):
            return False, "Ship does not meet mission requirements"
        
        return True, "Mission can be accepted"
    
    def accept(self, ship) -> bool:
        """Accept this mission."""
        can_accept, reason = self.can_accept(ship)
        if not can_accept:
            return False
        
        self.status = MissionStatus.ACCEPTED
        self.accepted_at = time.time()
        
        # Set time limit if specified
        if self.time_limit:
            self.expires_at = self.accepted_at + self.time_limit
        
        self.progress_description = "Mission accepted"
        return True
    
    def abandon(self) -> MissionPenalty:
        """Abandon this mission and return penalties."""
        if self.status == MissionStatus.ACCEPTED or self.status == MissionStatus.IN_PROGRESS:
            self.status = MissionStatus.FAILED
            return self.penalty
        return MissionPenalty()
    
    def update_progress(self, ship, current_station=None) -> bool:
        """Update mission progress. Returns True if mission is completed."""
        if self.status not in [MissionStatus.ACCEPTED, MissionStatus.IN_PROGRESS]:
            return False
        
        if self.is_expired():
            self.status = MissionStatus.EXPIRED
            return False
        
        # Check objectives
        completed_objectives = 0
        for objective in self.objectives:
            if objective.check_completion(ship, current_station):
                objective.completed = True
                completed_objectives += 1
        
        # Update progress percentage
        if self.objectives:
            self.completion_percentage = completed_objectives / len(self.objectives)
        
        # Check if all objectives are complete
        if completed_objectives == len(self.objectives):
            self.complete()
            return True
        
        # Update status to in progress if not already
        if self.status == MissionStatus.ACCEPTED:
            self.status = MissionStatus.IN_PROGRESS
        
        return False
    
    def complete(self):
        """Mark mission as completed."""
        self.status = MissionStatus.COMPLETED
        self.completed_at = time.time()
        self.completion_percentage = 1.0
        self.progress_description = "Mission completed!"
    
    def is_expired(self) -> bool:
        """Check if mission has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def get_time_remaining(self) -> Optional[float]:
        """Get time remaining in seconds, or None if no time limit."""
        if self.expires_at is None:
            return None
        return max(0, self.expires_at - time.time())
    
    def get_formatted_time_remaining(self) -> str:
        """Get formatted time remaining string."""
        remaining = self.get_time_remaining()
        if remaining is None:
            return "No time limit"
        
        if remaining <= 0:
            return "EXPIRED"
        
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        seconds = int(remaining % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize mission to dictionary for saving."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "mission_type": self.mission_type.value,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at,
            "accepted_at": self.accepted_at,
            "completed_at": self.completed_at,
            "expires_at": self.expires_at,
            "time_limit": self.time_limit,
            "origin_station_id": self.origin_station_id,
            "destination_station_id": self.destination_station_id,
            "requirements": {
                "min_reputation": self.requirements.min_reputation,
                "min_cargo_capacity": self.requirements.min_cargo_capacity,
                "required_upgrades": self.requirements.required_upgrades,
                "required_items": self.requirements.required_items
            },
            "objectives": [
                {
                    "description": obj.description,
                    "completed": obj.completed,
                    "target_station_id": obj.target_station_id,
                    "target_commodity": obj.target_commodity,
                    "target_quantity": obj.target_quantity
                }
                for obj in self.objectives
            ],
            "reward": {
                "credits": self.reward.credits,
                "reputation_bonus": self.reward.reputation_bonus,
                "bonus_items": self.reward.bonus_items
            },
            "penalty": {
                "credits": self.penalty.credits,
                "reputation_loss": self.penalty.reputation_loss
            },
            "progress_description": self.progress_description,
            "completion_percentage": self.completion_percentage
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Mission':
        """Deserialize mission from dictionary."""
        mission = cls(data["id"])
        mission.title = data["title"]
        mission.description = data["description"]
        mission.mission_type = MissionType(data["mission_type"])
        mission.status = MissionStatus(data["status"])
        mission.priority = MissionPriority(data["priority"])
        mission.created_at = data["created_at"]
        mission.accepted_at = data.get("accepted_at")
        mission.completed_at = data.get("completed_at")
        mission.expires_at = data.get("expires_at")
        mission.time_limit = data.get("time_limit")
        mission.origin_station_id = data.get("origin_station_id")
        mission.destination_station_id = data.get("destination_station_id")
        
        # Reconstruct requirements
        req_data = data["requirements"]
        mission.requirements = MissionRequirement(
            min_reputation=req_data["min_reputation"],
            min_cargo_capacity=req_data["min_cargo_capacity"],
            required_upgrades=req_data["required_upgrades"],
            required_items=req_data["required_items"]
        )
        
        # Reconstruct objectives
        mission.objectives = [
            MissionObjective(
                description=obj_data["description"],
                completed=obj_data["completed"],
                target_station_id=obj_data.get("target_station_id"),
                target_commodity=obj_data.get("target_commodity"),
                target_quantity=obj_data.get("target_quantity", 0)
            )
            for obj_data in data["objectives"]
        ]
        
        # Reconstruct reward and penalty
        reward_data = data["reward"]
        mission.reward = MissionReward(
            credits=reward_data["credits"],
            reputation_bonus=reward_data["reputation_bonus"],
            bonus_items=reward_data["bonus_items"]
        )
        
        penalty_data = data["penalty"]
        mission.penalty = MissionPenalty(
            credits=penalty_data["credits"],
            reputation_loss=penalty_data["reputation_loss"]
        )
        
        mission.progress_description = data["progress_description"]
        mission.completion_percentage = data["completion_percentage"]
        
        return mission