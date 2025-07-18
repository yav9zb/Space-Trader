"""
Base Building System for Space Trader

This module provides a comprehensive base building system allowing players to:
- Construct and manage space stations and outposts
- Build modular facilities for production, storage, and defense
- Create automated trading networks
- Establish supply chains and resource production
"""

from .base_entity import PlayerBase, BaseModule, ModuleType
from .base_manager import BaseManager
from .construction_system import ConstructionSystem
from .resource_production import ProductionSystem

__all__ = [
    'PlayerBase',
    'BaseModule', 
    'ModuleType',
    'BaseManager',
    'ConstructionSystem',
    'ProductionSystem'
]