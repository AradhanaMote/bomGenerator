import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List
import os

class RevisionControl:
    """Handles BOM versioning and revision tracking"""
    
    def __init__(self, storage_dir: str = "data/revisions"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
    def save_revision(self, bom: Dict[str, Any], user: str = "system") -> str:
        """Save a new revision of the BOM"""
        
        # Generate revision ID
        bom_hash = hashlib.md5(
            json.dumps(bom, sort_keys=True).encode()
        ).hexdigest()[:8]
        
        revision = {
            "revision_id": f"REV-{datetime.now().strftime('%Y%m%d')}-{bom_hash}",
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "bom": bom,
            "previous_revision": bom.get("revision_id"),
            "changes": self._detect_changes(bom.get("previous_bom"), bom)
        }
        
        # Save to file
        filename = f"{self.storage_dir}/{revision['revision_id']}.json"
        with open(filename, 'w') as f:
            json.dump(revision, f, indent=2)
        
        return revision['revision_id']
    
    def _detect_changes(self, old_bom: Dict, new_bom: Dict) -> List[str]:
        """Detect changes between revisions"""
        changes = []
        if not old_bom:
            return ["Initial version"]
            
        old_components = {c['id']: c for c in old_bom.get('components', [])}
        new_components = {c['id']: c for c in new_bom.get('components', [])}
        
        # Check for added components
        for comp_id in new_components:
            if comp_id not in old_components:
                changes.append(f"Added: {new_components[comp_id]['name']}")
        
        # Check for removed components
        for comp_id in old_components:
            if comp_id not in new_components:
                changes.append(f"Removed: {old_components[comp_id]['name']}")
        
        return changes