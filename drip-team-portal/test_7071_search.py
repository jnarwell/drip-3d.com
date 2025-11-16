#!/usr/bin/env python3
"""Test script to verify 7071 search functionality"""

from backend.app.services.materials_project import MaterialsProjectService

# Initialize service
mp_service = MaterialsProjectService()

# Test parsing of "7071"
print("Testing search term parsing for '7071':")
search_type, elements = mp_service.parse_material_search("7071")
print(f"  Search type: {search_type}")
print(f"  Elements: {elements}")
print()

# Test actual search
print("Testing Materials Project search for '7071':")
results = mp_service.search_aluminum_alloys("-".join(elements))
print(f"  Found {len(results)} results")

if results:
    print("\nTop 3 results:")
    for i, result in enumerate(results[:3]):
        print(f"\n  {i+1}. {result.get('formula')} (ID: {result.get('mp_id')})")
        print(f"     Common name: {result.get('common_name', 'N/A')}")
        print(f"     Density: {result.get('density', 'N/A')} g/cm³")
        if result.get('has_standard'):
            print(f"     Has engineering standard data: Yes")
else:
    print("  No results found - checking direct Al-Zn-Mg-Cu search...")
    # Try direct element search
    direct_results = mp_service.search_materials_summary(elements=["Al", "Zn", "Mg", "Cu"], limit=10)
    print(f"  Direct search found {len(direct_results)} results")
    if direct_results:
        print("\n  First result from direct search:")
        print(f"    Formula: {direct_results[0].get('formula_pretty')}")
        print(f"    ID: {direct_results[0].get('material_id')}")