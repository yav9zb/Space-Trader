from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class CommodityCategory(Enum):
    """Categories of tradeable commodities."""
    FOOD = "Food & Agriculture"
    METALS = "Metals & Minerals"
    TECHNOLOGY = "Technology"
    ENERGY = "Energy & Fuel"
    CONSUMER = "Consumer Goods"


@dataclass
class Commodity:
    """Definition of a tradeable commodity."""
    id: str
    name: str
    description: str
    base_price: int  # Standard market price in credits
    category: CommodityCategory
    volume: int  # Cargo space required per unit
    
    def __post_init__(self):
        """Validate commodity data."""
        if self.base_price <= 0:
            raise ValueError("Base price must be positive")
        if self.volume <= 0:
            raise ValueError("Volume must be positive")


class CommodityRegistry:
    """Registry of all available commodities in the game."""
    
    def __init__(self):
        self._commodities: Dict[str, Commodity] = {}
        self._initialize_default_commodities()
    
    def _initialize_default_commodities(self):
        """Initialize the standard set of commodities."""
        default_commodities = [
            Commodity(
                id="food_rations",
                name="Food Rations",
                description="Preserved food supplies for long space journeys",
                base_price=50,
                category=CommodityCategory.FOOD,
                volume=1
            ),
            Commodity(
                id="metal_ore",
                name="Metal Ore",
                description="Raw metallic materials for industrial use",
                base_price=100,
                category=CommodityCategory.METALS,
                volume=2
            ),
            Commodity(
                id="electronics",
                name="Electronics",
                description="Computer components and electronic devices",
                base_price=300,
                category=CommodityCategory.TECHNOLOGY,
                volume=1
            ),
            Commodity(
                id="fuel_cells",
                name="Fuel Cells",
                description="Compact energy storage for ship propulsion",
                base_price=80,
                category=CommodityCategory.ENERGY,
                volume=1
            ),
            Commodity(
                id="consumer_goods",
                name="Consumer Goods",
                description="Luxury items and personal accessories",
                base_price=150,
                category=CommodityCategory.CONSUMER,
                volume=1
            ),
            Commodity(
                id="rare_minerals",
                name="Rare Minerals",
                description="Exotic materials used in advanced technology",
                base_price=500,
                category=CommodityCategory.METALS,
                volume=1
            ),
            Commodity(
                id="medical_supplies",
                name="Medical Supplies",
                description="Essential healthcare equipment and medicines",
                base_price=200,
                category=CommodityCategory.CONSUMER,
                volume=1
            ),
            Commodity(
                id="machinery",
                name="Machinery",
                description="Industrial equipment and automated systems",
                base_price=400,
                category=CommodityCategory.TECHNOLOGY,
                volume=3
            )
        ]
        
        for commodity in default_commodities:
            self.register_commodity(commodity)
    
    def register_commodity(self, commodity: Commodity):
        """Register a new commodity in the system."""
        if commodity.id in self._commodities:
            raise ValueError(f"Commodity with id '{commodity.id}' already exists")
        self._commodities[commodity.id] = commodity
    
    def get_commodity(self, commodity_id: str) -> Commodity:
        """Get a commodity by ID."""
        if commodity_id not in self._commodities:
            raise KeyError(f"Unknown commodity id: {commodity_id}")
        return self._commodities[commodity_id]
    
    def get_all_commodities(self) -> List[Commodity]:
        """Get all registered commodities."""
        return list(self._commodities.values())
    
    def get_commodities_by_category(self, category: CommodityCategory) -> List[Commodity]:
        """Get all commodities in a specific category."""
        return [c for c in self._commodities.values() if c.category == category]
    
    def get_commodity_ids(self) -> List[str]:
        """Get all commodity IDs."""
        return list(self._commodities.keys())


# Global commodity registry instance
commodity_registry = CommodityRegistry()