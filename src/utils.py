import json
import yaml
from datetime import datetime
from typing import Dict, Any, List, Optional
import re

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {
            "llm": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "temperature": 0.3,
                "max_tokens": 2000
            }
        }

def save_to_json(data: Dict[str, Any], filename: str) -> str:
    """Save data to JSON file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_filename = f"{filename}_{timestamp}.json"
    
    with open(full_filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    return full_filename

def load_from_json(filename: str) -> Dict[str, Any]:
    """Load data from JSON file"""
    with open(filename, 'r') as f:
        return json.load(f)

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format amount as currency string"""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}
    symbol = symbols.get(currency, "$")
    return f"{symbol}{amount:,.2f}"

def validate_email(email: str) -> bool:
    """Simple email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    # Replace invalid characters with underscore
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split a list into smaller chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def get_user_input(prompt: str, default: Optional[str] = None) -> str:
    """Get user input with default value"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()

def confirm_action(prompt: str) -> bool:
    """Ask user for confirmation"""
    response = input(f"{prompt} (y/n): ").strip().lower()
    return response in ['y', 'yes', 'true']

def display_table(data: List[List[str]], headers: Optional[List[str]] = None):
    """Display data as a formatted table"""
    try:
        from tabulate import tabulate
        if headers:
            print(tabulate(data, headers=headers, tablefmt="grid"))
        else:
            print(tabulate(data, tablefmt="grid"))
    except ImportError:
        # Fallback simple table if tabulate not available
        if headers:
            print(" | ".join(headers))
            print("-" * (sum(len(h) for h in headers) + 3 * (len(headers) - 1)))
        for row in data:
            print(" | ".join(str(cell) for cell in row))

def calculate_component_weight(component: Dict[str, Any]) -> float:
    """Calculate estimated weight of a component"""
    # This is a simplified estimation
    weight_map = {
        "battery": 2.5,  # kg
        "motor": 3.0,
        "frame": 5.0,
        "wheel": 1.5,
        "brake": 0.5,
        "display": 0.2,
        "controller": 0.3,
        "wire": 0.1,
        "screw": 0.01,
        "nut": 0.01,
        "bolt": 0.02
    }
    
    comp_name = component.get("name", "").lower()
    quantity = component.get("quantity", 1)
    
    for key, weight in weight_map.items():
        if key in comp_name:
            return weight * quantity
    
    return 0.1 * quantity  # Default weight

def generate_component_id(component_name: str, index: int) -> str:
    """Generate a unique ID for a component"""
    # Create a slug from the name
    slug = re.sub(r'[^a-z0-9]', '_', component_name.lower())
    slug = re.sub(r'_+', '_', slug).strip('_')
    
    # Truncate if too long
    if len(slug) > 20:
        slug = slug[:20]
    
    return f"comp-{index:03d}-{slug}"

def merge_boms(bom1: Dict[str, Any], bom2: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two BOMs together"""
    merged = {
        "product_name": f"{bom1.get('product_name', 'Product')} + {bom2.get('product_name', 'Product')}",
        "description": f"Combined BOM: {bom1.get('description', '')} and {bom2.get('description', '')}",
        "components": bom1.get('components', []) + bom2.get('components', []),
        "total_components": len(bom1.get('components', [])) + len(bom2.get('components', [])),
        "generated_at": datetime.now().isoformat(),
        "merged_from": [bom1.get('revision_id', 'unknown'), bom2.get('revision_id', 'unknown')]
    }
    
    # Merge cost estimates if available
    total_cost = 0
    if 'cost_estimate' in bom1:
        total_cost += bom1['cost_estimate'].get('total_usd', 0)
    if 'cost_estimate' in bom2:
        total_cost += bom2['cost_estimate'].get('total_usd', 0)
    
    merged['cost_estimate'] = {
        "total_usd": total_cost,
        "currency": "USD",
        "estimated_at": datetime.now().isoformat()
    }
    
    return merged

def highlight_verification_needed(bom: Dict[str, Any]) -> None:
    """Print BOM with verification flags highlighted"""
    print("\n" + "="*60)
    print("BOM WITH VERIFICATION FLAGS")
    print("="*60)
    
    for comp in bom.get('components', []):
        # Highlight components needing verification
        if comp.get('verify_needed'):
            print(f"⚠️  {comp['name']} - NEEDS VERIFICATION")
        else:
            print(f"✅ {comp['name']}")
        
        # Check subcomponents
        for sub in comp.get('subcomponents', []):
            if sub.get('verify_needed'):
                print(f"  ⚠️  {sub['name']} - NEEDS VERIFICATION")
            else:
                print(f"  ✅ {sub['name']}")
        
        print()  # Blank line between components

def parse_quantity_string(qty_str: str) -> Dict[str, Any]:
    """Parse quantity strings like '10 pieces' or '2.5 meters'"""
    # Pattern to match number and unit
    pattern = r'^([\d.]+)\s*([a-zA-Z]+)$'
    match = re.match(pattern, qty_str.strip().lower())
    
    if match:
        return {
            "quantity": float(match.group(1)),
            "unit": match.group(2)
        }
    
    return {
        "quantity": 1,
        "unit": "piece"
    }

def create_bom_summary(bom: Dict[str, Any]) -> Dict[str, Any]:
    """Create a summary of the BOM"""
    components = bom.get('components', [])
    
    # Count by category
    categories = {}
    for comp in components:
        cat = comp.get('category', 'other')
        categories[cat] = categories.get(cat, 0) + 1
    
    # Count items needing verification
    needs_verify = sum(1 for comp in components if comp.get('verify_needed'))
    
    return {
        "product_name": bom.get('product_name', 'Unknown'),
        "total_components": len(components),
        "categories": categories,
        "needs_verification": needs_verify,
        "total_cost": bom.get('cost_estimate', {}).get('total_usd', 0),
        "revision": bom.get('revision_id', 'None'),
        "generated": bom.get('generated_at', 'Unknown')
    }

def print_bom_summary(bom: Dict[str, Any]):
    """Pretty print BOM summary"""
    summary = create_bom_summary(bom)
    
    print("\n" + "="*60)
    print(f"📊 BOM SUMMARY: {summary['product_name']}")
    print("="*60)
    print(f"📦 Total Components: {summary['total_components']}")
    print(f"📁 Categories: {', '.join(f'{k}:{v}' for k,v in summary['categories'].items())}")
    print(f"⚠️  Needs Verification: {summary['needs_verification']}")
    print(f"💰 Total Cost: ${summary['total_cost']:,.2f}")
    print(f"📌 Revision: {summary['revision']}")
    print(f"🕐 Generated: {summary['generated']}")

# If running this file directly, show example usage
if __name__ == "__main__":
    # Test the utility functions
    print("Testing utils.py functions...")
    
    # Test component ID generation
    comp_id = generate_component_id("Lithium Battery Pack", 1)
    print(f"Generated ID: {comp_id}")
    
    # Test quantity parsing
    qty = parse_quantity_string("10 pieces")
    print(f"Parsed quantity: {qty}")
    
    # Test currency formatting
    money = format_currency(1234.56)
    print(f"Formatted currency: {money}")
    
    # Test filename sanitization
    bad_filename = "my/bad:file?name*.txt"
    good_filename = sanitize_filename(bad_filename)
    print(f"Sanitized filename: {good_filename}")