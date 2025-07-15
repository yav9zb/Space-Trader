from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import random

from .commodity import Commodity, CommodityCategory, commodity_registry


class StationType(Enum):
    """Types of space stations with different trading characteristics."""
    TRADING = "Trading Post"
    MILITARY = "Military Base"
    MINING = "Mining Station"
    RESEARCH = "Research Station"
    SHIPYARD = "Shipyard"


@dataclass
class MarketPrice:
    """Price information for a commodity at a station."""
    commodity_id: str
    buy_price: int    # Price player pays to buy from station
    sell_price: int   # Price station pays to buy from player
    available: bool = True
    stock: int = 100  # How much station has to sell
    demand: int = 50  # How much station wants to buy


class StationMarket:
    """Market system for a single station."""
    
    def __init__(self, station_type: StationType, station_name: str = "Unknown Station"):
        self.station_type = station_type
        self.station_name = station_name
        self.prices: Dict[str, MarketPrice] = {}
        self._initialize_market()
    
    def _initialize_market(self):
        """Initialize market prices based on station type."""
        all_commodities = commodity_registry.get_all_commodities()
        
        for commodity in all_commodities:
            buy_price, sell_price, stock, demand = self._calculate_prices(commodity)
            
            self.prices[commodity.id] = MarketPrice(
                commodity_id=commodity.id,
                buy_price=buy_price,
                sell_price=sell_price,
                available=True,
                stock=stock,
                demand=demand
            )
    
    def _calculate_prices(self, commodity: Commodity) -> tuple:
        """Calculate buy/sell prices based on station type and commodity."""
        base_price = commodity.base_price
        
        # Station type modifiers
        buy_modifier = 1.0
        sell_modifier = 0.8  # Stations generally pay less than they charge
        stock = 100
        demand = 50
        
        if self.station_type == StationType.TRADING:
            # Balanced prices, good general trading
            buy_modifier = 1.1
            sell_modifier = 0.9
            
        elif self.station_type == StationType.MINING:
            if commodity.category == CommodityCategory.METALS:
                # Cheap metals (they produce them)
                buy_modifier = 0.7
                sell_modifier = 0.6
                stock = 200
                demand = 20
            elif commodity.category == CommodityCategory.FOOD:
                # Expensive food (they need it)
                buy_modifier = 1.4
                sell_modifier = 1.2
                stock = 30
                demand = 100
            else:
                buy_modifier = 1.2
                sell_modifier = 0.8
                
        elif self.station_type == StationType.RESEARCH:
            if commodity.category == CommodityCategory.TECHNOLOGY:
                # Cheap technology (they produce it)
                buy_modifier = 0.8
                sell_modifier = 0.7
                stock = 150
                demand = 30
            elif commodity.category == CommodityCategory.CONSUMER:
                # Expensive consumer goods (scientists don't care about luxury)
                buy_modifier = 0.6
                sell_modifier = 0.5
                stock = 20
                demand = 10
            else:
                buy_modifier = 1.1
                sell_modifier = 0.9
                
        elif self.station_type == StationType.MILITARY:
            if commodity.category == CommodityCategory.TECHNOLOGY:
                # Expensive technology (military equipment)
                buy_modifier = 1.3
                sell_modifier = 1.1
                stock = 80
                demand = 80
            elif commodity.category == CommodityCategory.CONSUMER:
                # Less interested in luxury goods
                buy_modifier = 0.9
                sell_modifier = 0.7
                stock = 40
                demand = 20
            else:
                buy_modifier = 1.1
                sell_modifier = 0.9
                
        elif self.station_type == StationType.SHIPYARD:
            if commodity.category == CommodityCategory.METALS:
                # Need metals for ship construction
                buy_modifier = 1.2
                sell_modifier = 1.0
                stock = 60
                demand = 120
            elif commodity.category == CommodityCategory.TECHNOLOGY:
                # Need technology for ship systems
                buy_modifier = 1.3
                sell_modifier = 1.1
                stock = 70
                demand = 100
            else:
                buy_modifier = 1.0
                sell_modifier = 0.8
        
        # Add some randomness (±10%)
        variation = random.uniform(0.9, 1.1)
        buy_modifier *= variation
        sell_modifier *= variation
        
        # Calculate final prices
        buy_price = max(1, int(base_price * buy_modifier))
        sell_price = max(1, int(base_price * sell_modifier))
        
        # Ensure sell price is never higher than buy price
        if sell_price >= buy_price:
            sell_price = max(1, buy_price - 1)
        
        return buy_price, sell_price, stock, demand
    
    def get_buy_price(self, commodity_id: str) -> Optional[int]:
        """Get the price for buying a commodity from the station."""
        if commodity_id not in self.prices:
            return None
        return self.prices[commodity_id].buy_price
    
    def get_sell_price(self, commodity_id: str) -> Optional[int]:
        """Get the price for selling a commodity to the station."""
        if commodity_id not in self.prices:
            return None
        return self.prices[commodity_id].sell_price
    
    def can_buy_from_station(self, commodity_id: str, quantity: int = 1) -> bool:
        """Check if player can buy commodity from station."""
        if commodity_id not in self.prices:
            return False
        market_price = self.prices[commodity_id]
        return market_price.available and market_price.stock >= quantity
    
    def can_sell_to_station(self, commodity_id: str, quantity: int = 1) -> bool:
        """Check if player can sell commodity to station."""
        if commodity_id not in self.prices:
            return False
        market_price = self.prices[commodity_id]
        return market_price.available and market_price.demand >= quantity
    
    def buy_from_station(self, commodity_id: str, quantity: int) -> bool:
        """Process buying commodity from station (reduces station stock)."""
        if not self.can_buy_from_station(commodity_id, quantity):
            return False
        
        self.prices[commodity_id].stock -= quantity
        # Increase demand slightly when stock is sold
        self.prices[commodity_id].demand = min(200, self.prices[commodity_id].demand + quantity // 2)
        return True
    
    def sell_to_station(self, commodity_id: str, quantity: int) -> bool:
        """Process selling commodity to station (reduces station demand)."""
        if not self.can_sell_to_station(commodity_id, quantity):
            return False
        
        self.prices[commodity_id].demand -= quantity
        # Increase stock slightly when commodity is bought
        self.prices[commodity_id].stock = min(300, self.prices[commodity_id].stock + quantity // 2)
        return True
    
    def get_available_commodities(self) -> List[Commodity]:
        """Get list of commodities available for purchase."""
        available = []
        for commodity_id, market_price in self.prices.items():
            if market_price.available and market_price.stock > 0:
                try:
                    commodity = commodity_registry.get_commodity(commodity_id)
                    available.append(commodity)
                except KeyError:
                    continue
        
        # Sort by name for consistent display
        available.sort(key=lambda c: c.name)
        return available
    
    def get_market_summary(self) -> str:
        """Get a summary of the market for display."""
        available_count = len(self.get_available_commodities())
        return f"{self.station_type.value} - {available_count} commodities available"
    
    def refresh_market(self):
        """Refresh market prices and stock (called periodically)."""
        for market_price in self.prices.values():
            # Slowly restore stock and demand toward baseline
            if market_price.stock < 100:
                market_price.stock = min(100, market_price.stock + random.randint(1, 5))
            if market_price.demand < 50:
                market_price.demand = min(50, market_price.demand + random.randint(1, 3))
            
            # Small price fluctuations (±5%)
            try:
                commodity = commodity_registry.get_commodity(market_price.commodity_id)
                base_buy = commodity.base_price * self._get_station_modifier(commodity)[0]
                base_sell = commodity.base_price * self._get_station_modifier(commodity)[1]
                
                variation = random.uniform(0.95, 1.05)
                market_price.buy_price = max(1, int(base_buy * variation))
                market_price.sell_price = max(1, int(base_sell * variation))
                
                # Ensure sell price is never higher than buy price
                if market_price.sell_price >= market_price.buy_price:
                    market_price.sell_price = max(1, market_price.buy_price - 1)
                    
            except KeyError:
                continue
    
    def _get_station_modifier(self, commodity: Commodity) -> tuple:
        """Get buy/sell modifiers for station type and commodity category."""
        # This mirrors the logic from _calculate_prices but without randomness
        buy_modifier = 1.0
        sell_modifier = 0.8
        
        if self.station_type == StationType.TRADING:
            buy_modifier = 1.1
            sell_modifier = 0.9
        elif self.station_type == StationType.MINING:
            if commodity.category == CommodityCategory.METALS:
                buy_modifier = 0.7
                sell_modifier = 0.6
            elif commodity.category == CommodityCategory.FOOD:
                buy_modifier = 1.4
                sell_modifier = 1.2
            else:
                buy_modifier = 1.2
                sell_modifier = 0.8
        elif self.station_type == StationType.RESEARCH:
            if commodity.category == CommodityCategory.TECHNOLOGY:
                buy_modifier = 0.8
                sell_modifier = 0.7
            elif commodity.category == CommodityCategory.CONSUMER:
                buy_modifier = 0.6
                sell_modifier = 0.5
            else:
                buy_modifier = 1.1
                sell_modifier = 0.9
        elif self.station_type == StationType.MILITARY:
            if commodity.category == CommodityCategory.TECHNOLOGY:
                buy_modifier = 1.3
                sell_modifier = 1.1
            elif commodity.category == CommodityCategory.CONSUMER:
                buy_modifier = 0.9
                sell_modifier = 0.7
            else:
                buy_modifier = 1.1
                sell_modifier = 0.9
        elif self.station_type == StationType.SHIPYARD:
            if commodity.category == CommodityCategory.METALS:
                buy_modifier = 1.2
                sell_modifier = 1.0
            elif commodity.category == CommodityCategory.TECHNOLOGY:
                buy_modifier = 1.3
                sell_modifier = 1.1
            else:
                buy_modifier = 1.0
                sell_modifier = 0.8
        
        return buy_modifier, sell_modifier