import sys
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.llm_processor_gemini import GeminiLLMProcessor
from src.bom_parser import BOMParser
from src.cost_estimator import CostEstimator
from src.export_handler import ExportHandler
from src.revision_control import RevisionControl
from src.utils import display_table, get_user_input

class BOMGenerator:
    """Main application class"""
    
    def __init__(self):
        self.llm = GeminiLLMProcessor()
        self.parser = BOMParser()
        self.cost_estimator = CostEstimator()
        self.exporter = ExportHandler()
        self.revision_control = RevisionControl()
        self.current_bom = None
        
    def run(self):
        """Main application loop"""
        print("\n" + "="*60)
        print("🤖 AI-Based Bill of Materials (BOM) Generator")
        print("="*60)
        
        while True:
            self._show_menu()
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == '1':
                self._generate_new_bom()
            elif choice == '2':
                self._view_current_bom()
            elif choice == '3':
                self._edit_bom()
            elif choice == '4':
                self._export_bom()
            elif choice == '5':
                self._show_revisions()
            elif choice == '6':
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please try again.")
    
    def _show_menu(self):
        """Display main menu"""
        print("\n" + "-"*60)
        print("MAIN MENU")
        print("-"*60)
        print("1. 🔄 Generate New BOM from Description")
        print("2. 📋 View Current BOM")
        print("3. ✏️ Edit Current BOM")
        print("4. 💾 Export BOM (CSV/JSON)")
        print("5. 📚 Show Revision History")
        print("6. 🚪 Exit")
    
    def _generate_new_bom(self):
        """Generate a new BOM from user description"""
        print("\n" + "-"*60)
        print("🔧 GENERATE NEW BOM")
        print("-"*60)
        
        description = input("\nEnter product description: ").strip()
        if not description:
            print("❌ Description cannot be empty")
            return
        
        print("\n⏳ Generating BOM using AI...")
        
        # Step 1: Generate using LLM
        raw_bom = self.llm.generate_bom(description)
        
        # Step 2: Validate and clean
        print("✓ Validating BOM structure...")
        validated_bom = self.parser.validate_and_clean(raw_bom)
        
        # Step 3: Estimate costs
        print("💰 Estimating costs...")
        self.current_bom = self.cost_estimator.estimate_cost(validated_bom)
        
        # Step 4: Save revision
        rev_id = self.revision_control.save_revision(self.current_bom)
        self.current_bom['revision_id'] = rev_id
        
        print("\n✅ BOM generated successfully!")
        print(f"📌 Revision: {rev_id}")
        
        # Display preview
        self._display_bom_preview()
    
    def _display_bom_preview(self):
        """Show a preview of the current BOM"""
        if not self.current_bom:
            print("❌ No BOM loaded")
            return
            
        print("\n" + "-"*60)
        print(f"📊 BOM PREVIEW: {self.current_bom.get('product_name', 'Unknown')}")
        print("-"*60)
        
        # Convert to table format
        table = self.parser.to_table_format(self.current_bom)
        
        # Display using tabulate
        from tabulate import tabulate
        print(tabulate(table[1:], headers=table[0], tablefmt="grid"))
        
        # Show total cost
        total_cost = self.current_bom.get('cost_estimate', {}).get('total_usd', 0)
        print(f"\n💰 TOTAL ESTIMATED COST: ${total_cost:,.2f}")
    
    def _view_current_bom(self):
        """View the current BOM in detail"""
        if not self.current_bom:
            print("\n❌ No BOM loaded. Generate one first!")
            return
            
        self._display_bom_preview()
    
    def _edit_bom(self):
        """Allow manual editing of the BOM"""
        if not self.current_bom:
            print("\n❌ No BOM to edit. Generate one first!")
            return
            
        print("\n" + "-"*60)
        print("✏️ MANUAL BOM EDITOR")
        print("-"*60)
        print("Current components:")
        
        # Show current components with indices
        for i, comp in enumerate(self.current_bom['components'], 1):
            print(f"{i}. {comp['name']} (x{comp['quantity']}) - ${comp.get('estimated_cost', 0)}")
        
        print("\nOptions:")
        print("1. Add component")
        print("2. Edit component")
        print("3. Delete component")
        print("4. Done editing")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '1':
            self._add_component()
        elif choice == '2':
            self._edit_component()
        elif choice == '3':
            self._delete_component()
        elif choice == '4':
            # Save revision
            rev_id = self.revision_control.save_revision(
                self.current_bom, 
                user="manual_edit"
            )
            self.current_bom['revision_id'] = rev_id
            print(f"\n✅ Changes saved as revision: {rev_id}")
    
    def _add_component(self):
        """Add a new component manually"""
        print("\n➕ Add New Component")
        name = input("Component name: ").strip()
        category = input("Category (mechanical/electrical/other): ").strip()
        qty = input("Quantity: ").strip()
        
        new_component = {
            "id": f"comp-{len(self.current_bom['components'])+1}",
            "name": name,
            "category": category,
            "quantity": int(qty) if qty.isdigit() else 1,
            "unit": "piece",
            "subcomponents": [],
            "verify_needed": False,
            "notes": "Manually added"
        }
        
        self.current_bom['components'].append(new_component)
        print("✅ Component added!")
    
    def _export_bom(self):
        """Export BOM to various formats"""
        if not self.current_bom:
            print("\n❌ No BOM to export. Generate one first!")
            return
            
        print("\n" + "-"*60)
        print("💾 EXPORT BOM")
        print("-"*60)
        print("1. Export as CSV")
        print("2. Export as JSON")
        print("3. Back")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '1':
            filename = input("Enter base filename (without extension): ").strip()
            if not filename:
                filename = self.current_bom.get('product_name', 'bom').lower().replace(' ', '_')
            
            csv_file = self.exporter.export_to_csv(self.current_bom, filename)
            print(f"\n✅ BOM exported to: {csv_file}")
            
        elif choice == '2':
            filename = input("Enter filename (without extension): ").strip()
            if not filename:
                filename = self.current_bom.get('product_name', 'bom').lower().replace(' ', '_')
            
            json_file = f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_file, 'w') as f:
                json.dump(self.current_bom, f, indent=2)
            print(f"\n✅ BOM exported to: {json_file}")
    
    def _show_revisions(self):
        """Show revision history"""
        print("\n" + "-"*60)
        print("📚 REVISION HISTORY")
        print("-"*60)
        
        revisions = sorted(Path(self.revision_control.storage_dir).glob("*.json"))
        
        if not revisions:
            print("No revisions found.")
            return
        
        for rev_file in revisions[-5:]:  # Show last 5 revisions
            with open(rev_file, 'r') as f:
                rev = json.load(f)
                print(f"\n📌 {rev['revision_id']}")
                print(f"   Time: {rev['timestamp']}")
                print(f"   User: {rev['user']}")
                if rev.get('changes'):
                    print(f"   Changes: {', '.join(rev['changes'][:2])}")

def main():
    generator = BOMGenerator()
    generator.run()

if __name__ == "__main__":
    main()