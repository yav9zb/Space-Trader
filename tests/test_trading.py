import pytest
import sys
import os

# Add src to Python path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from trading.commodity import Commodity, CommodityCategory, commodity_registry
from trading.cargo import CargoHold
from trading.market import StationMarket, StationType
from entities.station import Station


class TestCommoditySystem:
    """Test the commodity and registry system."""
    
    def test_commodity_creation(self):
        """Test creating a commodity with valid data."""
        commodity = Commodity(
            id="test_food",
            name="Test Food",
            description="A test food item",
            base_price=50,
            category=CommodityCategory.FOOD,
            volume=1
        )
        
        assert commodity.id == "test_food"
        assert commodity.name == "Test Food"
        assert commodity.base_price == 50
        assert commodity.volume == 1
        assert commodity.category == CommodityCategory.FOOD
    
    def test_commodity_validation(self):
        """Test commodity validation for invalid data."""
        # Test negative price
        with pytest.raises(ValueError):
            Commodity(
                id="invalid",
                name="Invalid",
                description="Invalid commodity",
                base_price=-10,
                category=CommodityCategory.FOOD,
                volume=1
            )
        
        # Test zero volume
        with pytest.raises(ValueError):
            Commodity(
                id="invalid",
                name="Invalid",
                description="Invalid commodity",
                base_price=50,
                category=CommodityCategory.FOOD,
                volume=0
            )
    
    def test_commodity_registry(self):
        """Test commodity registry functionality."""
        # Test getting existing commodity
        food_rations = commodity_registry.get_commodity("food_rations")
        assert food_rations.name == "Food Rations"
        assert food_rations.category == CommodityCategory.FOOD
        
        # Test getting non-existent commodity
        with pytest.raises(KeyError):
            commodity_registry.get_commodity("non_existent")
        
        # Test getting all commodities
        all_commodities = commodity_registry.get_all_commodities()
        assert len(all_commodities) >= 8  # We defined 8 initial commodities
        
        # Test getting by category
        food_commodities = commodity_registry.get_commodities_by_category(CommodityCategory.FOOD)
        assert len(food_commodities) >= 1
        assert all(c.category == CommodityCategory.FOOD for c in food_commodities)


class TestCargoSystem:
    """Test the ship cargo system."""
    
    def test_cargo_creation(self):
        """Test creating a cargo hold."""
        cargo = CargoHold(capacity=100)
        assert cargo.capacity == 100
        assert cargo.get_used_capacity() == 0
        assert cargo.get_available_capacity() == 100
        assert cargo.is_empty()
        assert not cargo.is_full()
    
    def test_cargo_add_remove(self):
        """Test adding and removing cargo."""
        cargo = CargoHold(capacity=50)
        
        # Test adding valid cargo
        assert cargo.can_add("food_rations", 5)
        assert cargo.add_cargo("food_rations", 5)
        assert cargo.get_quantity("food_rations") == 5
        assert cargo.get_used_capacity() == 5  # food_rations has volume 1
        assert not cargo.is_empty()
        
        # Test removing cargo
        assert cargo.remove_cargo("food_rations", 2)
        assert cargo.get_quantity("food_rations") == 3
        assert cargo.get_used_capacity() == 3
        
        # Test removing all cargo
        assert cargo.remove_cargo("food_rations", 3)
        assert cargo.get_quantity("food_rations") == 0
        assert cargo.is_empty()
    
    def test_cargo_capacity_limits(self):
        """Test cargo capacity constraints."""
        cargo = CargoHold(capacity=10)
        
        # Add cargo that uses all capacity (metal_ore has volume 2)
        assert cargo.add_cargo("metal_ore", 5)  # 5 * 2 = 10 volume
        assert cargo.get_used_capacity() == 10
        assert cargo.is_full()
        
        # Try to add more (should fail)
        assert not cargo.can_add("food_rations", 1)
        assert not cargo.add_cargo("food_rations", 1)
    
    def test_cargo_invalid_operations(self):
        """Test invalid cargo operations."""
        cargo = CargoHold(capacity=50)
        
        # Test adding non-existent commodity
        assert not cargo.can_add("non_existent", 1)
        assert not cargo.add_cargo("non_existent", 1)
        
        # Test removing more than available
        cargo.add_cargo("food_rations", 5)
        assert not cargo.remove_cargo("food_rations", 10)
        
        # Test removing from empty cargo
        assert not cargo.remove_cargo("electronics", 1)
    
    def test_cargo_value_calculation(self):
        """Test cargo value calculation."""
        cargo = CargoHold(capacity=100)
        
        # Add some commodities
        cargo.add_cargo("food_rations", 10)  # 10 * 50 = 500
        cargo.add_cargo("electronics", 5)    # 5 * 300 = 1500
        
        total_value = cargo.get_total_value()
        assert total_value == 2000


class TestMarketSystem:
    """Test the station market system."""
    
    def test_market_creation(self):
        """Test creating a station market."""
        market = StationMarket(StationType.TRADING, "Test Station")
        
        assert market.station_type == StationType.TRADING
        assert market.station_name == "Test Station"
        assert len(market.prices) >= 8  # Should have prices for all commodities
    
    def test_market_pricing(self):
        """Test market pricing logic."""
        trading_market = StationMarket(StationType.TRADING, "Trading Post")
        mining_market = StationMarket(StationType.MINING, "Mining Station")
        
        # Get metal ore prices
        trading_metal_price = trading_market.get_buy_price("metal_ore")
        mining_metal_price = mining_market.get_buy_price("metal_ore")
        
        # Mining stations should have cheaper metals than trading posts
        assert mining_metal_price < trading_metal_price
        
        # Get food prices  
        trading_food_price = trading_market.get_buy_price("food_rations")
        mining_food_price = mining_market.get_buy_price("food_rations")
        
        # Mining stations should have expensive food
        assert mining_food_price > trading_food_price
    
    def test_market_transactions(self):
        """Test market buy/sell transactions."""
        market = StationMarket(StationType.TRADING, "Test Station")
        
        # Test buying from station
        initial_stock = market.prices["food_rations"].stock
        assert market.can_buy_from_station("food_rations", 5)
        assert market.buy_from_station("food_rations", 5)
        
        # Stock should be reduced
        assert market.prices["food_rations"].stock == initial_stock - 5
        
        # Test selling to station
        initial_demand = market.prices["food_rations"].demand
        assert market.can_sell_to_station("food_rations", 3)
        assert market.sell_to_station("food_rations", 3)
        
        # Demand should be reduced
        assert market.prices["food_rations"].demand == initial_demand - 3
    
    def test_market_availability(self):
        """Test market commodity availability."""
        market = StationMarket(StationType.TRADING, "Test Station")
        
        available_commodities = market.get_available_commodities()
        
        # Should have commodities available
        assert len(available_commodities) > 0
        
        # All should be valid commodities
        for commodity in available_commodities:
            assert hasattr(commodity, 'id')
            assert hasattr(commodity, 'name')
            assert hasattr(commodity, 'base_price')


class TestIntegratedTrading:
    """Test integrated trading scenarios."""
    
    def test_complete_trading_scenario(self):
        """Test a complete buy/sell trading scenario."""
        # Create ship with cargo and credits
        cargo = CargoHold(capacity=50)
        credits = 1000
        
        # Create market
        market = StationMarket(StationType.TRADING, "Test Station")
        
        # Buy some food rations
        food_price = market.get_buy_price("food_rations")
        quantity_to_buy = 10
        total_cost = food_price * quantity_to_buy
        
        # Check if we can afford it
        assert credits >= total_cost
        assert cargo.can_add("food_rations", quantity_to_buy)
        assert market.can_buy_from_station("food_rations", quantity_to_buy)
        
        # Execute purchase
        assert market.buy_from_station("food_rations", quantity_to_buy)
        assert cargo.add_cargo("food_rations", quantity_to_buy)
        credits -= total_cost
        
        # Verify transaction
        assert cargo.get_quantity("food_rations") == quantity_to_buy
        assert credits == 1000 - total_cost
        
        # Now sell some back
        sell_price = market.get_sell_price("food_rations")
        quantity_to_sell = 5
        
        assert market.can_sell_to_station("food_rations", quantity_to_sell)
        assert cargo.remove_cargo("food_rations", quantity_to_sell)
        assert market.sell_to_station("food_rations", quantity_to_sell)
        credits += sell_price * quantity_to_sell
        
        # Verify final state
        assert cargo.get_quantity("food_rations") == quantity_to_buy - quantity_to_sell
        expected_credits = 1000 - total_cost + (sell_price * quantity_to_sell)
        assert credits == expected_credits


if __name__ == "__main__":
    pytest.main([__file__, "-v"])