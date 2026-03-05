import json
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.materials import MATERIALS

def main():
    missing_materials = []
    affected_locations = []

    for loc_key, loc_data in LOCATIONS.items():
        gatherables = loc_data.get("gatherables", [])
        for mat_key, weight in gatherables:
            if mat_key not in MATERIALS:
                missing_materials.append(mat_key)
                if loc_key not in affected_locations:
                    affected_locations.append(loc_key)
                print(f"Location '{loc_key}' references missing gatherable: '{mat_key}'")

    print("\nSummary:")
    print(f"Missing materials: {set(missing_materials)}")
    print(f"Affected locations: {affected_locations}")

if __name__ == "__main__":
    main()
