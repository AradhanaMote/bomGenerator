import json
from typing import Dict, Any, Optional
import os

class CostEstimator:
    """Handles cost estimation for BOM components"""
    
    def __init__(self, price_db_path: str = "data/component_prices.json"):
        self.price_db = self._load_price_database(price_db_path)
        
    def _load_price_database(self, path: str) -> Dict:
        """Load component price database"""
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return self._create_default_price_db(path)
    
    def _create_default_price_db(self, path: str) -> Dict:
        """Create default price database"""
        default_db = {
            "battery": {"lithium": 50.0, "lead_acid": 30.0, "unit": "per_kwh"},
            "motor": {"dc_brushless": 75.0, "brushed": 40.0, "unit": "each"},
            "controller": {"standard": 35.0, "advanced": 65.0, "unit": "each"},
            "brakes": {"disc": 25.0, "drum": 15.0, "unit": "per_pair"},
            "display": {"lcd": 20.0, "led": 15.0, "unit": "each"},
            "frame": {"aluminum": 80.0, "steel": 50.0, "unit": "each"},
            "wheels": {"pneumatic": 30.0, "solid": 20.0, "unit": "per_pair"},
            "throttle": {"standard": 12.0, "unit": "each"},
            "charger": {"standard": 25.0, "fast": 45.0, "unit": "each"},
            "wiring": {"harness": 15.0, "unit": "each"}
        }
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(default_db, f, indent=2)
            
        return default_db
    
    def estimate_cost(self, bom: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate costs for each component
        """
        total_cost = 0.0
        cost_breakdown = []
        
        for component in bom.get("components", []):
            comp_name = component["name"].lower()
            estimated_cost = self._get_component_cost(comp_name, component)
            
            component["estimated_cost"] = estimated_cost
            component["cost_unit"] = "USD"
            total_cost += estimated_cost * component.get("quantity", 1)
            
            cost_breakdown.append({
                "name": component["name"],
                "quantity": component.get("quantity", 1),
                "unit_cost": estimated_cost,
                "total": estimated_cost * component.get("quantity", 1)
            })
        
        bom["cost_estimate"] = {
            "total_usd": round(total_cost, 2),
            "breakdown": cost_breakdown,
            "currency": "USD",
            "estimated_at": "2024-01-01"
        }
        
        return bom
    
    def _get_component_cost(self, comp_name: str, component: Dict) -> float:
        """Get cost for a specific component"""
        for key in self.price_db:
            if key in comp_name:
                prices = self.price_db[key]
                if isinstance(prices, dict):
                    # Try to match subtype
                    for subtype, price in prices.items():
                        if subtype in comp_name:
                            return price
                    # Return first price if no subtype match
                    return list(prices.values())[0]
                return prices
        return 25.0  # Default cost if unknown