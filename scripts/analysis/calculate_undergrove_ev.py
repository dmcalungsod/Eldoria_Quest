import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.monsters import MONSTERS
from game_systems.data.materials import MATERIALS
from scripts.analysis.economy_utils import calculate_expected_value_stats

def main():
    # temporarily mock the missing monsters so we can see EV
    MONSTERS['spore_stalker'] = {
        "level": 25,
        "tier": "Normal",
        "drops": [
            ["fungal_spores", 40],
            ["iron_ore", 20],
            ["magic_stone_small", 15]
        ]
    }
    MONSTERS['fungal_hulk'] = {
        "level": 26,
        "tier": "Elite",
        "drops": [
            ["bioluminescent_sap", 40],
            ["iron_ore", 40],
            ["magic_stone_medium", 25]
        ]
    }
    MONSTERS['bioluminescent_myriapod'] = {
        "level": 25,
        "tier": "Normal",
        "drops": [
            ["bioluminescent_sap", 30],
            ["iron_ore", 30],
            ["magic_stone_small", 20]
        ]
    }

    MATERIALS['fungal_spores'] = {"value": 15}
    MATERIALS['bioluminescent_sap'] = {"value": 35}

    data = LOCATIONS.get("the_undergrove")
    if data:
        stats = calculate_expected_value_stats(data)
        print("Expected Value Stats for The Undergrove with mocked monsters/materials:")
        print(json.dumps(stats, indent=2))

        # also print Frostfall Expanse for comparison
        vs_data = LOCATIONS.get("frostfall_expanse")
        if vs_data:
            vs_stats = calculate_expected_value_stats(vs_data)
            print("\nExpected Value Stats for The Frostfall Expanse:")
            print(json.dumps(vs_stats, indent=2))

        vs_data = LOCATIONS.get("whispering_archives")
        if vs_data:
            vs_stats = calculate_expected_value_stats(vs_data)
            print("\nExpected Value Stats for The Whispering Archives:")
            print(json.dumps(vs_stats, indent=2))

    else:
        print("Location 'the_undergrove' not found.")

if __name__ == "__main__":
    main()
