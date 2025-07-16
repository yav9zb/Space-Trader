# Mission/Contract System Documentation

## Overview

The Space Trader game now includes a comprehensive mission system that provides structured objectives and gameplay goals. Players can accept various types of contracts from stations, complete them for rewards, and build reputation throughout the galaxy.

## Features Implemented

### Mission Types

**1. Delivery Missions**
- Transport specific cargo from one station to another
- Cargo is provided at pickup location
- Time-limited with rewards based on distance and cargo value
- Example: "Deliver 15 units of Food from Trading Post-342 to Mining Station-789"

**2. Trading Contract Missions**  
- Exchange one commodity for another at a specific station
- Player must acquire the required goods
- Higher reputation requirements
- Example: "Trade 10 units of Metals for 8 units of Technology"

**3. Supply Run Missions**
- Deliver multiple types of supplies to a station
- Requires larger cargo capacity
- Higher rewards for multiple commodity types
- Example: "Deliver 5 Food, 3 Metals, and 2 Energy Cells to Research Station"

**4. Emergency Delivery Missions**
- Urgent missions with short time limits
- Much higher rewards and penalties
- Rare occurrence (10% spawn chance)
- Priority: URGENT status with red highlighting

**5. Exploration Missions**
- Survey unexplored sectors of space
- Rewards based on number of sectors visited
- Longer time limits for travel
- Automatic completion when entering target sectors

### Mission System Features

**Mission Board Interface**
- Access via 'M' key when docked at stations
- Two tabs: Available missions and Active missions
- Detailed mission view with objectives, requirements, rewards
- Accept missions with 'A' key, abandon with 'X' key

**Dynamic Mission Generation**
- Missions generated based on station types
- Different stations offer different mission preferences
- Automatic generation every 30 minutes or when mission count is low
- Up to 15 available missions at any time

**Mission Tracking**
- Up to 5 active missions simultaneously
- Real-time progress tracking with completion percentages
- Automatic objective checking and completion
- Mission status updates (Available → Accepted → In Progress → Completed/Failed)

**Rewards & Penalties**
- Credit rewards based on mission difficulty and type
- Reputation bonuses for successful completion
- Penalties for abandoning or failing missions
- Bonus items for certain mission types

### Station Integration

**Station-Specific Missions**
- **Trading Posts**: Delivery (40%), Trading Contracts (40%), Supply Runs (20%)
- **Military Bases**: Emergency Delivery (30%), Supply Runs (30%), Exploration (20%), Delivery (20%)
- **Mining Stations**: Delivery (40%), Supply Runs (40%), Trading Contracts (20%)
- **Research Stations**: Exploration (40%), Delivery (30%), Supply Runs (30%)
- **Shipyards**: Supply Runs (40%), Delivery (30%), Trading Contracts (30%)

### Time Management

**Mission Time Limits**
- Delivery: 2-6 hours
- Trading Contracts: 3-8 hours  
- Supply Runs: 4+ hours (based on complexity)
- Emergency Delivery: 30 minutes - 2 hours
- Exploration: 2+ hours per sector

**Real-Time Countdown**
- Time remaining displayed in mission board
- Color-coded warnings (yellow → red for expiring)
- Automatic mission expiration handling

## Usage Guide

### Accessing Missions

1. **Dock at any station** using the docking system
2. **Press 'M'** to open the Mission Board
3. **Navigate** with UP/DOWN arrows between missions
4. **Press ENTER** to view detailed mission information
5. **Press 'A'** to accept available missions
6. **Press TAB** to switch between Available and Active missions

### Mission Workflow

**For Delivery Missions:**
1. Accept mission at origin station
2. Cargo is automatically added to your hold
3. Travel to destination station
4. Dock and mission completes automatically
5. Receive credits and reputation bonus

**For Trading Contracts:**
1. Accept mission at contract station
2. Acquire required commodities (buy or already own)
3. Return to contract station with goods
4. Mission completes when docked with required items

**For Supply Runs:**
1. Accept mission at destination station
2. Gather all required supplies from various sources
3. Return to station with all supplies
4. Mission completes when all objectives are met

### Mission Requirements

**General Requirements:**
- Sufficient cargo space for mission commodities
- Minimum reputation level (varies by mission)
- Required items in cargo (for some missions)

**Acceptance Limits:**
- Maximum 5 active missions at any time
- Must meet all mission requirements
- Cannot accept expired missions

## Technical Implementation

### Mission Architecture

**Core Classes:**
- `Mission`: Base class with common functionality
- `DeliveryMission`, `TradingContractMission`, etc.: Specific implementations
- `MissionManager`: Handles generation, tracking, and completion
- `MissionBoardState`: UI for mission interaction

**Data Structures:**
- `MissionType`: Enum of available mission types
- `MissionStatus`: Tracks mission progress states
- `MissionObjective`: Individual tasks within missions
- `MissionReward`/`MissionPenalty`: Outcome consequences

### Save System Integration

**Mission Persistence:**
- All mission states saved with game progress
- Mission timers persist across save/load
- Mission progress and objectives preserved
- Mission manager state fully serializable

**Save Data Structure:**
```json
{
  "missions": {
    "available_missions": [...],
    "active_missions": [...], 
    "completed_missions": [...],
    "failed_missions": [...],
    "last_generation_time": 1234567890
  }
}
```

### Performance Optimizations

**Generation System:**
- Missions generated in batches to reduce CPU usage
- Smart caching of mission data
- Automatic cleanup of expired missions
- Efficient serialization for save/load operations

**UI Optimizations:**
- Paginated mission display (5 missions per page)
- Efficient rendering with minimal redraw
- Responsive input handling
- Clean state management

## Configuration

### Mission Generation Settings

Located in `MissionManager.__init__()`:
```python
self.max_available_missions = 15      # Total available missions
self.max_active_missions = 5          # Player mission limit  
self.mission_generation_interval = 1800  # 30 minutes between generation
```

### Station Mission Preferences

Defined in `station_mission_preferences` dictionary:
- Controls which mission types each station type offers
- Weighted probability system for mission generation
- Easily configurable for game balance

## Future Enhancements

### Planned Features

**1. Reputation System**
- Track standing with individual stations and factions
- Unlock higher-tier missions with better reputation
- Reputation affects mission availability and rewards

**2. Mission Chains**
- Multi-part missions with connected objectives
- Story-driven mission sequences
- Escalating rewards and difficulty

**3. Faction Missions**
- Station-group specific contracts
- Competing faction objectives
- Diplomatic consequences for mission choices

**4. Timed Events**
- Special limited-time missions
- Seasonal or event-based contracts
- Community-wide objectives

**5. Mission Customization**
- Player-generated delivery requests
- Custom contract parameters
- Community mission sharing

### Technical Improvements

**1. Mission AI**
- Smarter mission generation based on player behavior
- Dynamic difficulty adjustment
- Economic simulation integration

**2. Enhanced UI**
- Mission map integration
- Route planning assistance
- Mission history and statistics

**3. Multiplayer Support**
- Shared mission board
- Cooperative mission completion
- Competitive contract bidding

## Troubleshooting

### Common Issues

**Mission not completing:**
- Verify all objectives are met
- Check cargo hold for required items
- Ensure you're docked at correct station

**Cannot accept mission:**
- Check cargo space requirements
- Verify reputation requirements
- Ensure mission hasn't expired

**Mission disappeared:**
- Check if mission expired (time limit reached)
- Verify mission wasn't completed by another player (future feature)
- Check Failed missions tab for abandoned missions

### Debug Information

All mission operations are logged to `game.log`:
- Mission generation events
- Mission acceptance/completion
- Error conditions and failures
- Performance metrics

## Controls Summary

**Mission Board Navigation:**
- **M**: Open mission board (when docked)
- **UP/DOWN**: Navigate mission list
- **TAB**: Switch between Available/Active tabs
- **ENTER**: View mission details
- **A**: Accept mission
- **X**: Abandon active mission
- **ESC**: Close mission board

The mission system adds structured gameplay objectives while maintaining the freedom of space trading, providing both casual and goal-oriented gameplay options.