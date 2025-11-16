#!/usr/bin/env python3
"""
Consolidate duplicate 304 stainless steel entries in unified database
"""
import json
import shutil
from datetime import datetime

def consolidate_304_entries():
    """Remove duplicate 304 stainless steel entry and consolidate properties"""
    
    # Backup the current file
    backup_name = f"app/data/alloy_standards_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy("app/data/alloy_standards.json", backup_name)
    print(f"✅ Created backup: {backup_name}")
    
    # Load the current data
    with open("app/data/alloy_standards.json", "r") as f:
        data = json.load(f)
    
    # Extract both 304 entries
    basic_304 = data["stainless_steel"]["304"]
    extended_304 = data["steel_stainless"]["304"]
    
    print("📋 Consolidating 304 stainless steel entries...")
    print(f"  Basic: {basic_304['common_name']} ({basic_304['source']})")
    print(f"  Extended: {extended_304['common_name']} ({extended_304['source']})")
    
    # Create consolidated entry based on the basic version but with better name
    consolidated_304 = basic_304.copy()
    consolidated_304["common_name"] = "304 Stainless Steel (18-8)"  # Use the more descriptive name
    consolidated_304["source"] = "Consolidated_Database"  # Mark as consolidated
    
    # Ensure we have all properties from both versions
    basic_mechanical = basic_304["properties"]["mechanical"]
    extended_mechanical = extended_304["properties"]["mechanical"]
    
    # Start with basic properties (which includes brinell_hardness)
    consolidated_mechanical = basic_mechanical.copy()
    
    # Add any missing properties from extended (though there are none in this case)
    for prop_name, prop_data in extended_mechanical.items():
        if prop_name not in consolidated_mechanical:
            consolidated_mechanical[prop_name] = prop_data
            print(f"  ➕ Added {prop_name} from extended version")
    
    # Update the consolidated entry
    consolidated_304["properties"]["mechanical"] = consolidated_mechanical
    
    # Keep only the consolidated version in stainless_steel category
    data["stainless_steel"]["304"] = consolidated_304
    
    # Remove the duplicate from steel_stainless category
    del data["steel_stainless"]["304"]
    
    print(f"✅ Consolidated entry has {len(consolidated_mechanical)} mechanical properties:")
    for prop in sorted(consolidated_mechanical.keys()):
        print(f"    - {prop}")
    
    # Remove the steel_stainless category if it's now empty
    if not data["steel_stainless"]:
        del data["steel_stainless"]
        print("🗑️  Removed empty steel_stainless category")
    
    # Write back the consolidated data
    with open("app/data/alloy_standards.json", "w") as f:
        json.dump(data, f, indent=2)
    
    print("✅ Consolidation complete!")
    print(f"📊 Final result: Single 304 entry in stainless_steel category")
    return True

if __name__ == "__main__":
    consolidate_304_entries()