import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SaveMetadata:
    """Metadata for a save file."""
    save_name: str
    save_date: str
    play_time: float
    credits: int
    ship_upgrades_value: int
    location: str


class SaveSystem:
    """Handles saving and loading game state."""
    
    def __init__(self, save_directory: str = "saves"):
        self.save_directory = Path(save_directory)
        self.save_directory.mkdir(exist_ok=True)
        
        # Ensure saves directory exists
        os.makedirs(self.save_directory, exist_ok=True)
        
        logger.info(f"Save system initialized with directory: {self.save_directory}")
    
    def save_game(self, game_engine, save_name: str = None) -> bool:
        """Save the current game state."""
        try:
            if save_name is None:
                save_name = f"autosave_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            save_data = self._collect_save_data(game_engine)
            
            # Add metadata
            save_data["metadata"] = {
                "save_name": save_name,
                "save_date": datetime.now().isoformat(),
                "play_time": getattr(game_engine, 'play_time', 0.0),
                "credits": game_engine.ship.credits,
                "ship_upgrades_value": game_engine.ship.upgrades.get_total_upgrade_value(),
                "location": self._get_current_location(game_engine)
            }
            
            save_file = self.save_directory / f"{save_name}.json"
            
            with open(save_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            logger.info(f"Game saved successfully to {save_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save game: {str(e)}")
            return False
    
    def load_game(self, save_name: str, game_engine) -> bool:
        """Load a saved game state."""
        try:
            save_file = self.save_directory / f"{save_name}.json"
            
            if not save_file.exists():
                logger.error(f"Save file not found: {save_file}")
                return False
            
            with open(save_file, 'r') as f:
                save_data = json.load(f)
            
            self._apply_save_data(save_data, game_engine)
            
            logger.info(f"Game loaded successfully from {save_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load game: {str(e)}")
            return False
    
    def get_save_list(self) -> List[SaveMetadata]:
        """Get list of available save files with metadata."""
        saves = []
        
        try:
            for save_file in self.save_directory.glob("*.json"):
                try:
                    with open(save_file, 'r') as f:
                        save_data = json.load(f)
                    
                    if "metadata" in save_data:
                        metadata = save_data["metadata"]
                        saves.append(SaveMetadata(
                            save_name=save_file.stem,
                            save_date=metadata.get("save_date", "Unknown"),
                            play_time=metadata.get("play_time", 0.0),
                            credits=metadata.get("credits", 0),
                            ship_upgrades_value=metadata.get("ship_upgrades_value", 0),
                            location=metadata.get("location", "Unknown")
                        ))
                    else:
                        # Legacy save file without metadata
                        stat = save_file.stat()
                        saves.append(SaveMetadata(
                            save_name=save_file.stem,
                            save_date=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            play_time=0.0,
                            credits=0,
                            ship_upgrades_value=0,
                            location="Unknown"
                        ))
                        
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Invalid save file {save_file}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error reading save directory: {e}")
        
        # Sort by save date (newest first)
        saves.sort(key=lambda x: x.save_date, reverse=True)
        return saves
    
    def delete_save(self, save_name: str) -> bool:
        """Delete a save file."""
        try:
            save_file = self.save_directory / f"{save_name}.json"
            
            if save_file.exists():
                save_file.unlink()
                logger.info(f"Save file deleted: {save_file}")
                return True
            else:
                logger.warning(f"Save file not found for deletion: {save_file}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete save file: {e}")
            return False
    
    def _collect_save_data(self, game_engine) -> Dict[str, Any]:
        """Collect all game data for saving."""
        save_data = {
            "version": "1.0",
            "player": self._save_player_data(game_engine),
            "universe": self._save_universe_data(game_engine),
            "game_state": self._save_game_state_data(game_engine)
        }
        
        return save_data
    
    def _save_player_data(self, game_engine) -> Dict[str, Any]:
        """Save player-related data."""
        ship = game_engine.ship
        
        player_data = {
            "ship": {
                "position": {"x": ship.position.x, "y": ship.position.y},
                "velocity": {"x": ship.velocity.x, "y": ship.velocity.y},
                "rotation": ship.rotation,
                "current_hull": ship.current_hull,
                "credits": ship.credits
            },
            "cargo": dict(ship.cargo_hold.items),  # Convert to regular dict
            "cargo_capacity": ship.cargo_hold.capacity,
            "upgrades": ship.upgrades.to_dict()
        }
        
        return player_data
    
    def _save_universe_data(self, game_engine) -> Dict[str, Any]:
        """Save universe state."""
        universe = game_engine.universe
        
        universe_data = {
            "stations": [],
            "generated_chunks": [list(chunk) for chunk in getattr(universe, 'generated_chunks', set())],
            "current_chunk": getattr(universe, 'current_chunk', {"x": 0, "y": 0})
        }
        
        # Save station data including market state
        for station in universe.stations:
            station_data = {
                "position": {"x": station.position.x, "y": station.position.y},
                "station_type": station.station_type.value,
                "name": station.name,
                "size": station.size,
                "market": self._save_market_data(station.market)
            }
            universe_data["stations"].append(station_data)
        
        return universe_data
    
    def _save_market_data(self, market) -> Dict[str, Any]:
        """Save market state for a station."""
        market_data = {
            "station_type": market.station_type.value,
            "station_name": market.station_name,
            "prices": {}
        }
        
        for commodity_id, market_price in market.prices.items():
            market_data["prices"][commodity_id] = {
                "buy_price": market_price.buy_price,
                "sell_price": market_price.sell_price,
                "stock": market_price.stock,
                "demand": market_price.demand,
                "available": market_price.available
            }
        
        return market_data
    
    def _save_game_state_data(self, game_engine) -> Dict[str, Any]:
        """Save general game state."""
        return {
            "current_state": game_engine.current_state.value,
            "credits": getattr(game_engine, 'credits', 0),  # Legacy field
            "play_time": getattr(game_engine, 'play_time', 0.0)
        }
    
    def _apply_save_data(self, save_data: Dict[str, Any], game_engine):
        """Apply loaded save data to the game engine."""
        # Load player data
        self._load_player_data(save_data.get("player", {}), game_engine)
        
        # Load universe data  
        self._load_universe_data(save_data.get("universe", {}), game_engine)
        
        # Load game state
        self._load_game_state_data(save_data.get("game_state", {}), game_engine)
    
    def _load_player_data(self, player_data: Dict[str, Any], game_engine):
        """Load player-related data."""
        ship_data = player_data.get("ship", {})
        
        # Restore ship state
        if "position" in ship_data:
            pos = ship_data["position"]
            game_engine.ship.position.x = pos["x"]
            game_engine.ship.position.y = pos["y"]
        
        if "velocity" in ship_data:
            vel = ship_data["velocity"]
            game_engine.ship.velocity.x = vel["x"]
            game_engine.ship.velocity.y = vel["y"]
        
        if "rotation" in ship_data:
            game_engine.ship.rotation = ship_data["rotation"]
        
        if "current_hull" in ship_data:
            game_engine.ship.current_hull = ship_data["current_hull"]
        
        if "credits" in ship_data:
            game_engine.ship.credits = ship_data["credits"]
        
        # Restore cargo
        if "cargo" in player_data:
            game_engine.ship.cargo_hold.items = player_data["cargo"]
        
        if "cargo_capacity" in player_data:
            game_engine.ship.cargo_hold.capacity = player_data["cargo_capacity"]
        
        # Restore upgrades
        if "upgrades" in player_data:
            game_engine.ship.upgrades.from_dict(player_data["upgrades"])  # Will need to implement this
    
    def _load_universe_data(self, universe_data: Dict[str, Any], game_engine):
        """Load universe state."""
        from src.entities.station import Station
        from src.trading.market import StationType, StationMarket
        from pygame import Vector2
        
        # Clear existing stations
        game_engine.universe.stations.clear()
        
        # Restore stations
        for station_data in universe_data.get("stations", []):
            pos = station_data["position"]
            station_type = StationType(station_data["station_type"])
            
            # Create station
            station = Station(pos["x"], pos["y"])
            station.station_type = station_type
            station.name = station_data.get("name", f"Station {len(game_engine.universe.stations)}")
            station.size = station_data.get("size", 30)
            
            # Restore market state
            market_data = station_data.get("market", {})
            station.market = StationMarket(station_type, station.name)
            self._load_market_data(market_data, station.market)
            
            game_engine.universe.stations.append(station)
        
        # Restore generated chunks
        if "generated_chunks" in universe_data:
            # Convert list of lists back to set of tuples
            chunks_list = universe_data["generated_chunks"]
            game_engine.universe.generated_chunks = set(tuple(chunk) for chunk in chunks_list)
        
        if "current_chunk" in universe_data:
            chunk = universe_data["current_chunk"]
            game_engine.universe.current_chunk = {"x": chunk["x"], "y": chunk["y"]}
    
    def _load_market_data(self, market_data: Dict[str, Any], market):
        """Load market state for a station."""
        prices_data = market_data.get("prices", {})
        
        for commodity_id, price_data in prices_data.items():
            if commodity_id in market.prices:
                market_price = market.prices[commodity_id]
                market_price.buy_price = price_data.get("buy_price", market_price.buy_price)
                market_price.sell_price = price_data.get("sell_price", market_price.sell_price)
                market_price.stock = price_data.get("stock", market_price.stock)
                market_price.demand = price_data.get("demand", market_price.demand)
                market_price.available = price_data.get("available", market_price.available)
    
    def _load_game_state_data(self, game_state_data: Dict[str, Any], game_engine):
        """Load general game state."""
        if "play_time" in game_state_data:
            game_engine.play_time = game_state_data["play_time"]
        
        # Note: We don't restore current_state as we want to start in PLAYING mode
    
    def _get_current_location(self, game_engine) -> str:
        """Get a description of the player's current location."""
        try:
            # Find nearest station
            nearest_station = None
            min_distance = float('inf')
            
            for station in game_engine.universe.stations:
                distance = (station.position - game_engine.ship.position).length()
                if distance < min_distance:
                    min_distance = distance
                    nearest_station = station
            
            if nearest_station and min_distance < 200:  # Within reasonable distance
                return f"Near {nearest_station.name}"
            else:
                # Use chunk coordinates
                chunk_x = int(game_engine.ship.position.x // 1000)
                chunk_y = int(game_engine.ship.position.y // 1000)
                return f"Sector ({chunk_x}, {chunk_y})"
                
        except Exception:
            return "Unknown Location"


# Global save system instance
save_system = SaveSystem()