from dataclasses import dataclass, field
from typing import Dict, List
from .commodity import Commodity, commodity_registry


@dataclass
class CargoHold:
    """Ship's cargo hold for storing commodities."""
    capacity: int = 50  # Total cargo units
    items: Dict[str, int] = field(default_factory=dict)  # commodity_id -> quantity
    
    def can_add(self, commodity_id: str, quantity: int) -> bool:
        """Check if we can add the specified quantity of a commodity."""
        if quantity <= 0:
            return False
            
        try:
            commodity = commodity_registry.get_commodity(commodity_id)
        except KeyError:
            return False
            
        required_space = commodity.volume * quantity
        return self.get_available_capacity() >= required_space
    
    def add_cargo(self, commodity_id: str, quantity: int) -> bool:
        """Add cargo to the hold. Returns True if successful."""
        if not self.can_add(commodity_id, quantity):
            return False
            
        if commodity_id in self.items:
            self.items[commodity_id] += quantity
        else:
            self.items[commodity_id] = quantity
            
        return True
    
    def remove_cargo(self, commodity_id: str, quantity: int) -> bool:
        """Remove cargo from the hold. Returns True if successful."""
        if quantity <= 0:
            return False
            
        if commodity_id not in self.items:
            return False
            
        if self.items[commodity_id] < quantity:
            return False
            
        self.items[commodity_id] -= quantity
        
        # Remove empty entries
        if self.items[commodity_id] == 0:
            del self.items[commodity_id]
            
        return True
    
    def get_quantity(self, commodity_id: str) -> int:
        """Get the quantity of a specific commodity."""
        return self.items.get(commodity_id, 0)
    
    def get_used_capacity(self) -> int:
        """Calculate total used cargo space."""
        total_used = 0
        for commodity_id, quantity in self.items.items():
            try:
                commodity = commodity_registry.get_commodity(commodity_id)
                total_used += commodity.volume * quantity
            except KeyError:
                # Handle unknown commodities gracefully
                continue
        return total_used
    
    def get_available_capacity(self) -> int:
        """Get remaining cargo space."""
        return self.capacity - self.get_used_capacity()
    
    def is_empty(self) -> bool:
        """Check if cargo hold is empty."""
        return len(self.items) == 0
    
    def is_full(self) -> bool:
        """Check if cargo hold is at capacity."""
        return self.get_available_capacity() == 0
    
    def get_cargo_items(self) -> List[tuple]:
        """Get list of (commodity, quantity) tuples for UI display."""
        cargo_list = []
        for commodity_id, quantity in self.items.items():
            try:
                commodity = commodity_registry.get_commodity(commodity_id)
                cargo_list.append((commodity, quantity))
            except KeyError:
                # Skip unknown commodities
                continue
        
        # Sort by commodity name for consistent display
        cargo_list.sort(key=lambda x: x[0].name)
        return cargo_list
    
    def get_total_value(self) -> int:
        """Calculate total value of cargo at base prices."""
        total_value = 0
        for commodity_id, quantity in self.items.items():
            try:
                commodity = commodity_registry.get_commodity(commodity_id)
                total_value += commodity.base_price * quantity
            except KeyError:
                continue
        return total_value
    
    def clear(self):
        """Remove all cargo from the hold."""
        self.items.clear()
    
    def get_cargo_summary(self) -> str:
        """Get a summary string of cargo contents."""
        if self.is_empty():
            return "Empty"
        
        cargo_count = len(self.items)
        used_space = self.get_used_capacity()
        
        if cargo_count == 1:
            return f"1 type, {used_space}/{self.capacity} units"
        else:
            return f"{cargo_count} types, {used_space}/{self.capacity} units"