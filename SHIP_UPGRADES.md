# Ship Upgrade System Technical Documentation

## Overview

The ship upgrade system allows players to spend credits earned from trading to improve their ship's capabilities across multiple categories. This creates a progression loop that motivates continued trading and exploration.

## Architecture

### Core Components

1. **Upgrade System** (`src/upgrades/upgrade_system.py`)
   - Define upgrade categories and tiers
   - Handle upgrade purchases and applications
   - Upgrade validation and requirements

2. **Ship Stats** (`src/entities/ship.py` - enhanced)
   - Base stats and upgrade modifiers
   - Calculate effective stats from upgrades
   - Track installed upgrades

3. **Upgrade Shop** (`src/states/upgrade_state.py`)
   - UI for browsing and purchasing upgrades
   - Display current ship stats vs upgraded stats
   - Purchase confirmation and validation

4. **Station Integration** (`src/entities/station.py` - enhanced)
   - Shipyard stations offer upgrades
   - Different stations have different upgrade availability

## Upgrade Categories

### 1. Cargo Hold Upgrades
**Purpose**: Increase cargo capacity for more profitable trading runs

| Tier | Name | Capacity | Cost | Description |
|------|------|----------|------|-------------|
| 0 | Basic Hold | 20 | - | Starting capacity |
| 1 | Expanded Hold | 35 | 2,000 | +15 cargo units |
| 2 | Large Hold | 50 | 5,000 | +30 cargo units |
| 3 | Commercial Hold | 75 | 12,000 | +55 cargo units |
| 4 | Freighter Hold | 100 | 25,000 | +80 cargo units |

### 2. Engine Upgrades
**Purpose**: Improve ship speed and maneuverability

| Tier | Name | Speed Boost | Thrust Boost | Cost | Description |
|------|------|-------------|--------------|------|-------------|
| 0 | Standard Engine | - | - | - | Basic propulsion |
| 1 | Enhanced Engine | +20% | +15% | 3,000 | Improved efficiency |
| 2 | Racing Engine | +40% | +30% | 8,000 | High-performance |
| 3 | Military Engine | +60% | +50% | 18,000 | Military-grade |
| 4 | Prototype Engine | +100% | +75% | 40,000 | Experimental tech |

### 3. Hull Upgrades
**Purpose**: Increase durability and collision resistance

| Tier | Name | Hull Points | Collision Resistance | Cost | Description |
|------|------|-------------|---------------------|------|-------------|
| 0 | Basic Hull | 100 | 1.0x | - | Standard protection |
| 1 | Reinforced Hull | 150 | 0.8x | 2,500 | Stronger materials |
| 2 | Armored Hull | 200 | 0.6x | 6,000 | Military plating |
| 3 | Advanced Hull | 300 | 0.4x | 15,000 | Composite materials |
| 4 | Titan Hull | 500 | 0.2x | 35,000 | Experimental alloys |

### 4. Scanner Upgrades
**Purpose**: Improve detection range and information display

| Tier | Name | Range Boost | Info Level | Cost | Description |
|------|------|-------------|------------|------|-------------|
| 0 | Basic Scanner | - | Basic | - | Standard sensors |
| 1 | Enhanced Scanner | +50% | Detailed | 1,500 | Better resolution |
| 2 | Long Range Scanner | +100% | Advanced | 4,000 | Extended range |
| 3 | Military Scanner | +150% | Military | 10,000 | Tactical sensors |
| 4 | Deep Space Scanner | +300% | Complete | 22,000 | Research-grade |

## Data Model

### Upgrade Definition
```python
@dataclass
class UpgradeDefinition:
    id: str
    name: str
    category: UpgradeCategory
    tier: int
    cost: int
    description: str
    requirements: List[str]  # Required previous upgrades
    stats: Dict[str, float]  # Stat modifications
    
class UpgradeCategory(Enum):
    CARGO = "Cargo Hold"
    ENGINE = "Engine"
    HULL = "Hull"
    SCANNER = "Scanner"
```

### Ship Upgrade Tracking
```python
@dataclass 
class ShipUpgrades:
    cargo_tier: int = 0
    engine_tier: int = 0
    hull_tier: int = 0
    scanner_tier: int = 0
    
    def get_total_upgrade_value(self) -> int:
        # Calculate total credits invested in upgrades
    
    def get_effective_stats(self, base_stats: ShipStats) -> ShipStats:
        # Apply all upgrade modifiers to base stats
```

## Implementation Plan

### Phase 1: Core System (Current)
- [x] Design upgrade system architecture
- [ ] Create upgrade definitions and data structures
- [ ] Implement upgrade application to ship stats
- [ ] Create basic upgrade shop interface

### Phase 2: Integration
- [ ] Add upgrade shops to Shipyard stations
- [ ] Integrate with docking system (press U for upgrades)
- [ ] Add upgrade requirements and validation
- [ ] Save/load upgrade progress

### Phase 3: Polish
- [ ] Visual upgrade indicators on ship
- [ ] Upgrade preview system (before/after stats)
- [ ] Achievement system for upgrade milestones
- [ ] Balance testing and cost tuning

## Station Integration

### Shipyard Stations
- **Upgrade Availability**: All upgrade categories
- **Special Features**: 
  - 10% discount on hull upgrades
  - Access to highest tier upgrades
  - Trade-in credit for downgrades

### Research Labs
- **Upgrade Availability**: Scanner and Engine upgrades only
- **Special Features**:
  - 15% discount on scanner upgrades
  - Early access to prototype engines
  - Research missions for upgrade discounts

### Military Bases  
- **Upgrade Availability**: Hull and Engine upgrades only
- **Special Features**:
  - 20% discount on hull upgrades
  - Military-grade exclusive upgrades
  - Reputation requirements for top-tier items

## User Interface Design

### Upgrade Shop Layout
```
┌─────────────────────────────────────────────────────────────┐
│  SHIP UPGRADES - [Station Name] ([Station Type])           │
├─────────────────────────────────────────────────────────────┤
│  Credits: 15,750                Ship: Modified Trader      │
├─────────────────────────────────────────────────────────────┤
│  CURRENT SHIP STATS            │   AVAILABLE UPGRADES       │
│  ┌─────────────────────────────┐│  ┌──────────────────────── │
│  │ Cargo: 35/35 units         ││  │ ► Cargo Hold           │
│  │ Max Speed: 480 u/s         ││  │   Large Hold - 5,000cr │
│  │ Hull: 150/150 HP           ││  │   +15 cargo capacity   │
│  │ Scanner: 1.5x range       ││  │                        │
│  │                            ││  │ ► Engine               │
│  │ Total Upgrades: 10,500cr   ││  │   Racing Engine - 8,000cr│
│  │                            ││  │   +40% speed, +30% thrust│
│  └─────────────────────────────┘│  │                        │
│                                 │  │ ► Hull                 │
│                                 │  │   Armored Hull - 6,000cr│
│                                 │  │   +50 HP, +40% resistance│
│                                 │  └──────────────────────── │
├─────────────────────────────────────────────────────────────┤
│  [UP/DOWN] Navigate  [ENTER] Purchase  [ESC] Exit          │
└─────────────────────────────────────────────────────────────┘
```

### Upgrade Controls
- **Arrow Keys**: Navigate upgrade categories and items
- **ENTER**: Purchase selected upgrade
- **TAB**: Switch between categories
- **ESC**: Exit upgrade shop
- **I**: View detailed upgrade information

## Economic Balance

### Cost Progression
- **Tier 1**: 1,500 - 3,000 credits (early game goals)
- **Tier 2**: 4,000 - 8,000 credits (mid game progression)  
- **Tier 3**: 10,000 - 18,000 credits (late game investments)
- **Tier 4**: 22,000 - 40,000 credits (end game achievements)

### Return on Investment
- **Cargo upgrades**: Pay for themselves in 3-5 trading runs
- **Engine upgrades**: Reduce travel time, increase efficiency
- **Hull upgrades**: Reduce repair costs, enable riskier routes
- **Scanner upgrades**: Find better trading opportunities

### Progression Gating
- **Prerequisites**: Higher tiers require previous tier installation
- **Station Access**: Some upgrades only available at specific stations
- **Credit Gates**: Exponential cost increase creates natural pacing

This upgrade system provides clear progression goals while maintaining the core trading gameplay loop. Players will naturally progress from basic cargo expansion to sophisticated ship modifications as their trading empire grows.