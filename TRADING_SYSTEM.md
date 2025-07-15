# Trading System Technical Documentation

## Overview

The trading system provides the core economic gameplay loop, allowing players to buy and sell commodities at different stations to generate profit and progress through the game.

## Architecture

### Core Components

1. **Commodity System** (`src/trading/commodity.py`)
   - Define tradeable goods with properties
   - Handle supply/demand mechanics
   - Price calculation logic

2. **Cargo System** (`src/trading/cargo.py`)
   - Ship inventory management
   - Capacity and weight limits
   - Cargo hold visualization

3. **Market System** (`src/trading/market.py`)
   - Station-specific commodity availability
   - Dynamic pricing based on station type
   - Buy/sell transaction handling

4. **Trading Interface** (`src/states/trading_state.py`)
   - UI for commodity trading
   - Transaction confirmation
   - Market information display

## Data Model

### Commodity Definition
```python
@dataclass
class Commodity:
    id: str
    name: str
    description: str
    base_price: int
    category: CommodityCategory
    volume: int  # Cargo space per unit
    
class CommodityCategory(Enum):
    FOOD = "Food & Agriculture"
    METALS = "Metals & Minerals" 
    TECHNOLOGY = "Technology"
    ENERGY = "Energy & Fuel"
    CONSUMER = "Consumer Goods"
```

### Market Pricing
- **Base Price**: Standard market value
- **Station Modifiers**: Different station types have different prices
  - Trading Posts: Standard prices
  - Mining Stations: Cheap metals, expensive food
  - Research Labs: Expensive technology, cheap consumer goods
- **Supply/Demand**: Simple multipliers based on availability

### Ship Cargo
```python
@dataclass
class CargoHold:
    capacity: int = 50  # Total cargo units
    items: Dict[str, int] = field(default_factory=dict)  # commodity_id -> quantity
    
    def can_add(self, commodity_id: str, quantity: int) -> bool
    def add_cargo(self, commodity_id: str, quantity: int) -> bool
    def remove_cargo(self, commodity_id: str, quantity: int) -> bool
    def get_used_capacity(self) -> int
```

## Implementation Plan

### Phase 1: Basic Trading (Current)
- [x] Design system architecture
- [ ] Create commodity definitions
- [ ] Implement cargo system
- [ ] Create basic market system
- [ ] Build trading UI state
- [ ] Add credits system

### Phase 2: Enhanced Economics
- [ ] Dynamic pricing based on supply/demand
- [ ] Station-specific specializations
- [ ] Cargo missions and contracts
- [ ] Market news and events

### Phase 3: Advanced Features
- [ ] Commodity production chains
- [ ] Player-owned cargo ships
- [ ] Trade route optimization
- [ ] Economic simulation

## User Interface Design

### Trading Screen Layout
```
┌─────────────────────────────────────────────────────────────┐
│  TRADING - [Station Name] ([Station Type])                 │
├─────────────────────────────────────────────────────────────┤
│  Credits: 1,250                    Cargo: 23/50 units      │
├─────────────────────────────────────────────────────────────┤
│  STATION MARKET                    │   YOUR CARGO           │
│  ┌─────────────────────────────────┐│  ┌──────────────────── │
│  │ Food Rations        Buy: 45    ││  │ Food Rations    3   │
│  │ [BUY] [SELL]                   ││  │ Metal Ore      12   │
│  │                                ││  │ Electronics     8   │
│  │ Metal Ore          Buy: 120    ││  │                     │
│  │ [BUY] [SELL]       Sell: 80    ││  │                     │
│  │                                ││  │                     │
│  │ Electronics        Buy: 340    ││  │                     │
│  │ [BUY] [SELL]                   ││  │                     │
│  └─────────────────────────────────┘│  └──────────────────── │
├─────────────────────────────────────────────────────────────┤
│  [ESC] Exit Trading                                         │
└─────────────────────────────────────────────────────────────┘
```

### Trading Controls
- **Arrow Keys**: Navigate commodity list
- **ENTER**: Select commodity for transaction
- **B**: Quick buy selected commodity
- **S**: Quick sell selected commodity
- **ESC**: Exit trading interface
- **TAB**: Switch between station market and cargo view

## Station Specializations

### Trading Posts
- **Specialty**: General goods, balanced prices
- **Good Deals**: Consumer goods
- **Expensive**: Raw materials

### Mining Stations
- **Specialty**: Metals and raw materials
- **Good Deals**: Metal ore, rare minerals
- **Expensive**: Food, consumer goods

### Research Labs
- **Specialty**: Technology and advanced equipment
- **Good Deals**: Electronics, computers
- **Expensive**: Food, basic materials

### Military Bases
- **Specialty**: Weapons and defense systems
- **Good Deals**: Military equipment
- **Expensive**: Luxury goods

### Shipyards
- **Specialty**: Ship parts and equipment
- **Good Deals**: Ship components
- **Expensive**: Organic materials

## Economic Balance

### Initial Commodity Set
1. **Food Rations** - Base: 50, Volume: 1
2. **Metal Ore** - Base: 100, Volume: 2  
3. **Electronics** - Base: 300, Volume: 1
4. **Fuel Cells** - Base: 80, Volume: 1
5. **Consumer Goods** - Base: 150, Volume: 1

### Profit Margins
- **Low Risk**: 10-20% profit (common goods)
- **Medium Risk**: 20-40% profit (specialized goods)
- **High Risk**: 40-100% profit (rare/illegal goods)

### Cargo Progression
- **Starting Ship**: 20 units cargo capacity
- **Upgraded Hold**: 50 units (purchasable upgrade)
- **Cargo Ship**: 200+ units (different ship class)

## Technical Integration

### Docking System Integration
```python
# In PlayingState when docked
if event.key == pygame.K_t:  # Trade
    if self.game.docking_manager.is_docked():
        station = self.game.docking_manager.get_target_station()
        self.game.change_state(GameStates.TRADING, station)
```

### Save System Integration
- Player credits
- Cargo contents
- Market prices (if dynamic)
- Trade history

### Settings Integration
- Transaction confirmation prompts
- Price display preferences
- Market refresh rates
- Auto-sort cargo

This trading system design provides a solid foundation for economic gameplay while remaining extensible for future enhancements.