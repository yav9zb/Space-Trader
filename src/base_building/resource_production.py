"""
Resource Production System - Handles automated production chains and resource management.
"""

import time
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from .base_entity import ModuleType, PlayerBase


class ResourceType(Enum):
    """Types of resources in the game."""
    # Raw Materials
    METAL = "Metal"
    ICE = "Ice"
    ORGANICS = "Organics"
    RARE_METALS = "Rare_Metals"
    
    # Processed Materials
    ELECTRONICS = "Electronics"
    MACHINERY = "Machinery"
    TEXTILES = "Textiles"
    CHEMICALS = "Chemicals"
    
    # Advanced Materials
    COMPUTERS = "Computers"
    WEAPONS = "Weapons"
    LUXURY = "Luxury"
    FUEL = "Fuel"
    
    # Energy
    POWER = "Power"


@dataclass
class ProductionRecipe:
    """Recipe for producing resources."""
    inputs: Dict[str, int] = field(default_factory=dict)  # resource -> amount
    outputs: Dict[str, int] = field(default_factory=dict)  # resource -> amount
    production_time: float = 1.0  # seconds per cycle
    power_required: int = 0
    crew_required: int = 0


class ProductionSystem:
    """Manages resource production and processing chains."""
    
    # Production recipes for different modules
    PRODUCTION_RECIPES = {
        ModuleType.MINING_FACILITY: [
            ProductionRecipe(
                inputs={},
                outputs={"Metal": 5, "Rare_Metals": 1},
                production_time=10.0,
                power_required=50
            )
        ],
        
        ModuleType.REFINERY: [
            ProductionRecipe(
                inputs={"Metal": 2},
                outputs={"Electronics": 1},
                production_time=8.0,
                power_required=40
            ),
            ProductionRecipe(
                inputs={"Metal": 3, "Rare_Metals": 1},
                outputs={"Machinery": 1},
                production_time=12.0,
                power_required=60
            ),
            ProductionRecipe(
                inputs={"Ice": 4},
                outputs={"Fuel": 2, "Chemicals": 1},
                production_time=6.0,
                power_required=30
            )
        ],
        
        ModuleType.FACTORY: [
            ProductionRecipe(
                inputs={"Electronics": 2, "Machinery": 1},
                outputs={"Computers": 1},
                production_time=15.0,
                power_required=50,
                crew_required=2
            ),
            ProductionRecipe(
                inputs={"Metal": 3, "Electronics": 1},
                outputs={"Weapons": 1},
                production_time=10.0,
                power_required=40,
                crew_required=1
            ),
            ProductionRecipe(
                inputs={"Organics": 2, "Chemicals": 1},
                outputs={"Textiles": 2},
                production_time=8.0,
                power_required=25,
                crew_required=1
            ),
            ProductionRecipe(
                inputs={"Rare_Metals": 2, "Electronics": 2, "Organics": 1},
                outputs={"Luxury": 1},
                production_time=20.0,
                power_required=30,
                crew_required=3
            )
        ],
        
        ModuleType.RESEARCH_LAB: [
            ProductionRecipe(
                inputs={"Computers": 1, "Electronics": 2},
                outputs={"Research_Data": 1},
                production_time=30.0,
                power_required=60,
                crew_required=3
            )
        ]
    }
    
    def __init__(self):
        self.production_queues: Dict[str, List[Dict[str, Any]]] = {}  # base_id -> production queue
        self.active_productions: Dict[str, Dict[str, Any]] = {}  # module_id -> production data
        
        # Global production statistics
        self.stats = {
            'total_production_cycles': 0,
            'resources_produced': {},
            'resources_consumed': {},
            'production_efficiency': 1.0
        }
        
        # Market demand simulation (affects production priorities)
        self.market_demand = {
            resource.value: 1.0 for resource in ResourceType
        }
        
        self.last_update = time.time()
    
    def start_production(self, base: PlayerBase, module_id: str, recipe_index: int = 0) -> bool:
        """Start production in a specific module."""
        # Find the module
        module = None
        for mod in set(base.modules.values()):
            if id(mod) == module_id or f"{mod.grid_position.x},{mod.grid_position.y}" == module_id:
                module = mod
                break
        
        if not module or not module.is_operational:
            return False
        
        # Check if module can produce
        if module.module_type not in self.PRODUCTION_RECIPES:
            return False
        
        recipes = self.PRODUCTION_RECIPES[module.module_type]
        if recipe_index >= len(recipes):
            return False
        
        recipe = recipes[recipe_index]
        
        # Check if we have required inputs
        if not self._can_start_production(base, recipe):
            return False
        
        # Consume inputs
        for resource, amount in recipe.inputs.items():
            base.remove_resource(resource, amount)
        
        # Start production
        production_data = {
            'recipe': recipe,
            'start_time': time.time(),
            'base_id': id(base),
            'module': module,
            'progress': 0.0
        }
        
        self.active_productions[str(id(module))] = production_data
        return True
    
    def _can_start_production(self, base: PlayerBase, recipe: ProductionRecipe) -> bool:
        """Check if base can start production with given recipe."""
        # Check input resources
        for resource, amount in recipe.inputs.items():
            if not base.has_resource(resource, amount):
                return False
        
        # Check power availability (simplified)
        if base.power_generation < base.power_consumption + recipe.power_required:
            return False
        
        # Check crew availability
        available_crew = base.crew_capacity - base.crew_count
        if available_crew < recipe.crew_required:
            return False
        
        return True
    
    def update_production(self, bases: Dict[str, PlayerBase], delta_time: float) -> None:
        """Update all active productions."""
        current_time = time.time()
        completed_productions = []
        
        for module_id, production_data in self.active_productions.items():
            recipe = production_data['recipe']
            elapsed_time = current_time - production_data['start_time']
            
            # Update progress
            production_data['progress'] = min(1.0, elapsed_time / recipe.production_time)
            
            # Check if production is complete
            if production_data['progress'] >= 1.0:
                completed_productions.append(module_id)
        
        # Complete finished productions
        for module_id in completed_productions:
            self._complete_production(bases, module_id)
        
        # Auto-start production for modules set to continuous production
        self._auto_start_productions(bases)
        
        # Update statistics
        self._update_statistics(delta_time)
        
        self.last_update = current_time
    
    def _complete_production(self, bases: Dict[str, PlayerBase], module_id: str) -> None:
        """Complete a production cycle and deliver outputs."""
        if module_id not in self.active_productions:
            return
        
        production_data = self.active_productions[module_id]
        recipe = production_data['recipe']
        
        # Find the base
        base = None
        for b in bases.values():
            if id(b) == production_data['base_id']:
                base = b
                break
        
        if not base:
            del self.active_productions[module_id]
            return
        
        # Deliver outputs
        for resource, amount in recipe.outputs.items():
            produced = base.add_resource(resource, amount)
            
            # Update statistics
            if resource not in self.stats['resources_produced']:
                self.stats['resources_produced'][resource] = 0
            self.stats['resources_produced'][resource] += produced
        
        # Update input consumption stats
        for resource, amount in recipe.inputs.items():
            if resource not in self.stats['resources_consumed']:
                self.stats['resources_consumed'][resource] = 0
            self.stats['resources_consumed'][resource] += amount
        
        self.stats['total_production_cycles'] += 1
        
        # Remove from active productions
        del self.active_productions[module_id]
    
    def _auto_start_productions(self, bases: Dict[str, PlayerBase]) -> None:
        """Automatically start production in idle modules."""
        for base in bases.values():
            unique_modules = set(base.modules.values())
            
            for module in unique_modules:
                if not module.is_operational:
                    continue
                
                module_id = str(id(module))
                if module_id in self.active_productions:
                    continue  # Already producing
                
                # Try to start production
                if module.module_type in self.PRODUCTION_RECIPES:
                    recipes = self.PRODUCTION_RECIPES[module.module_type]
                    
                    # Find the best recipe to start based on demand and availability
                    best_recipe_index = self._choose_best_recipe(base, recipes)
                    
                    if best_recipe_index is not None:
                        self.start_production(base, module_id, best_recipe_index)
    
    def _choose_best_recipe(self, base: PlayerBase, recipes: List[ProductionRecipe]) -> Optional[int]:
        """Choose the best recipe to start based on various factors."""
        best_score = -1
        best_index = None
        
        for i, recipe in enumerate(recipes):
            if not self._can_start_production(base, recipe):
                continue
            
            score = 0
            
            # Factor 1: Market demand for outputs
            for resource, amount in recipe.outputs.items():
                demand = self.market_demand.get(resource, 1.0)
                score += demand * amount
            
            # Factor 2: Availability of inputs (prefer recipes with abundant inputs)
            input_availability = 1.0
            for resource, amount in recipe.inputs.items():
                available = base.get_resource_amount(resource)
                if available < amount * 3:  # Prefer if we have 3x the required amount
                    input_availability *= 0.5
            
            score *= input_availability
            
            # Factor 3: Production efficiency (outputs per time)
            if recipe.production_time > 0:
                total_output_value = sum(recipe.outputs.values())
                efficiency = total_output_value / recipe.production_time
                score *= efficiency
            
            if score > best_score:
                best_score = score
                best_index = i
        
        return best_index
    
    def _update_statistics(self, delta_time: float) -> None:
        """Update production system statistics."""
        # Calculate overall production efficiency
        active_count = len(self.active_productions)
        total_modules = sum(
            len(set(base.modules.values())) 
            for base_id, base in {}  # Would need bases parameter
        )
        
        if total_modules > 0:
            self.stats['production_efficiency'] = active_count / total_modules
        
        # Update market demand (simulate market fluctuations)
        self._update_market_demand(delta_time)
    
    def _update_market_demand(self, delta_time: float) -> None:
        """Simulate market demand fluctuations."""
        import random
        
        for resource in ResourceType:
            # Small random fluctuations
            change = random.uniform(-0.01, 0.01) * delta_time
            self.market_demand[resource.value] = max(0.1, min(2.0, 
                self.market_demand[resource.value] + change))
    
    def get_production_status(self, base: PlayerBase) -> Dict[str, Any]:
        """Get production status for a base."""
        unique_modules = set(base.modules.values())
        production_modules = [
            mod for mod in unique_modules 
            if mod.module_type in self.PRODUCTION_RECIPES and mod.is_operational
        ]
        
        status = {
            'total_production_modules': len(production_modules),
            'active_productions': 0,
            'idle_modules': 0,
            'module_status': {}
        }
        
        for module in production_modules:
            module_id = str(id(module))
            
            if module_id in self.active_productions:
                status['active_productions'] += 1
                production_data = self.active_productions[module_id]
                status['module_status'][module_id] = {
                    'status': 'producing',
                    'progress': production_data['progress'],
                    'recipe': production_data['recipe']
                }
            else:
                status['idle_modules'] += 1
                status['module_status'][module_id] = {
                    'status': 'idle',
                    'available_recipes': self.PRODUCTION_RECIPES[module.module_type]
                }
        
        return status
    
    def get_resource_flow_analysis(self, base: PlayerBase) -> Dict[str, Any]:
        """Analyze resource production and consumption flows."""
        analysis = {
            'production_rates': {},
            'consumption_rates': {},
            'net_flows': {},
            'bottlenecks': [],
            'surpluses': []
        }
        
        # Calculate theoretical production rates
        unique_modules = set(base.modules.values())
        for module in unique_modules:
            if module.module_type not in self.PRODUCTION_RECIPES or not module.is_operational:
                continue
            
            recipes = self.PRODUCTION_RECIPES[module.module_type]
            for recipe in recipes:
                # Calculate per-hour rates
                cycles_per_hour = 3600 / recipe.production_time
                
                for resource, amount in recipe.outputs.items():
                    if resource not in analysis['production_rates']:
                        analysis['production_rates'][resource] = 0
                    analysis['production_rates'][resource] += amount * cycles_per_hour
                
                for resource, amount in recipe.inputs.items():
                    if resource not in analysis['consumption_rates']:
                        analysis['consumption_rates'][resource] = 0
                    analysis['consumption_rates'][resource] += amount * cycles_per_hour
        
        # Calculate net flows
        all_resources = set(analysis['production_rates'].keys()) | set(analysis['consumption_rates'].keys())
        for resource in all_resources:
            production = analysis['production_rates'].get(resource, 0)
            consumption = analysis['consumption_rates'].get(resource, 0)
            analysis['net_flows'][resource] = production - consumption
            
            # Identify bottlenecks and surpluses
            if production < consumption:
                analysis['bottlenecks'].append({
                    'resource': resource,
                    'deficit': consumption - production
                })
            elif production > consumption * 1.5:  # 50% surplus threshold
                analysis['surpluses'].append({
                    'resource': resource,
                    'surplus': production - consumption
                })
        
        return analysis
    
    def optimize_production_chain(self, base: PlayerBase) -> List[str]:
        """Provide optimization suggestions for production chain."""
        suggestions = []
        analysis = self.get_resource_flow_analysis(base)
        
        # Suggest modules for bottlenecks
        for bottleneck in analysis['bottlenecks']:
            resource = bottleneck['resource']
            
            # Find modules that can produce this resource
            for module_type, recipes in self.PRODUCTION_RECIPES.items():
                for recipe in recipes:
                    if resource in recipe.outputs:
                        suggestions.append(
                            f"Consider building {module_type.value.replace('_', ' ')} "
                            f"to increase {resource} production"
                        )
                        break
        
        # Suggest storage for surpluses
        for surplus in analysis['surpluses']:
            suggestions.append(
                f"Consider adding more storage for {surplus['resource']} "
                f"(surplus: {surplus['surplus']:.1f}/hour)"
            )
        
        # Power efficiency suggestions
        if base.power_consumption >= base.power_generation * 0.9:
            suggestions.append("Power consumption is near capacity. Consider building more power generators.")
        
        # Crew suggestions
        if base.crew_count >= base.crew_capacity * 0.8:
            suggestions.append("Crew capacity is near limit. Consider building more habitats.")
        
        return suggestions
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get production system statistics."""
        return dict(self.stats)