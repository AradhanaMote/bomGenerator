from typing import Dict, Any, List
import json
from datetime import datetime

class BOMParser:
    """Parses and validates BOM structures"""
    
    def __init__(self):
        self.common_components = {
            "electric_scooter": [
                "battery", "motor", "controller", "brakes", "display",
                "frame", "wheels", "throttle", "charger", "wiring"
            ]
        }
    
    def validate_and_clean(self, bom: Dict[str, Any], product_type: str = "generic") -> Dict[str, Any]:
        """
        Validate BOM and clean up any obvious hallucinations
        
        This is crucial for handling LLM hallucinations [citation:5]
        """
        
        # Check for unrealistic quantities
        for component in bom.get("components", []):
            # Validate quantity
            if component.get("quantity", 0) > 100 and "screw" not in component["name"].lower():
                component["notes"] = "Unusually high quantity - please verify"
                component["verify_needed"] = True
            
            # Check against known components for this product type
            if product_type in self.common_components:
                known = self.common_components[product_type]
                if not any(k in component["name"].lower() for k in known):
                    if not component.get("verify_needed"):
                        component["notes"] = "Unusual component for this product - verify"
                        component["verify_needed"] = True
        
        # Update total count
        bom["total_components"] = len(bom.get("components", []))
        bom["validated_at"] = datetime.now().isoformat()
        
        return bom
    
    def to_table_format(self, bom: Dict[str, Any]) -> List[List[str]]:
        """Convert BOM to table format for display"""
        
        table = []
        headers = ["ID", "Component", "Category", "Qty", "Unit", "Subcomponents", "Verify", "Notes"]
        table.append(headers)
        
        for comp in bom.get("components", []):
            subcomp_count = len(comp.get("subcomponents", []))
            row = [
                comp.get("id", ""),
                comp.get("name", ""),
                comp.get("category", ""),
                str(comp.get("quantity", "")),
                comp.get("unit", ""),
                str(subcomp_count),
                "⚠️" if comp.get("verify_needed") else "✅",
                comp.get("notes", "")[:30]
            ]
            table.append(row)
            
        return table