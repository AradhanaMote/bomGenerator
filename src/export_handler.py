import csv
import json
from typing import Dict, Any, List
from datetime import datetime

class ExportHandler:
    """Handles BOM export to various formats"""
    
    def export_to_csv(self, bom: Dict[str, Any], filename: str) -> str:
        """Export BOM to CSV format"""
        
        csv_filename = f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Product:', bom.get('product_name', 'Unknown')])
            writer.writerow(['Description:', bom.get('description', '')])
            writer.writerow([])
            
            # Write component headers
            writer.writerow(['Component', 'Category', 'Quantity', 'Unit', 
                           'Est. Cost (USD)', 'Subcomponents', 'Notes'])
            
            # Write components
            for comp in bom.get('components', []):
                writer.writerow([
                    comp.get('name', ''),
                    comp.get('category', ''),
                    comp.get('quantity', ''),
                    comp.get('unit', ''),
                    comp.get('estimated_cost', ''),
                    len(comp.get('subcomponents', [])),
                    comp.get('notes', '')
                ])
                
                # Write subcomponents indented
                for sub in comp.get('subcomponents', []):
                    writer.writerow([
                        f"  - {sub.get('name', '')}",
                        '',
                        sub.get('quantity', ''),
                        sub.get('unit', ''),
                        '',
                        '',
                        '✓' if sub.get('verify_needed') else ''
                    ])
            
            # Write total
            writer.writerow([])
            writer.writerow(['TOTAL ESTIMATED COST', '', '', '', 
                           f"${bom.get('cost_estimate', {}).get('total_usd', 0)}"])
        
        return csv_filename