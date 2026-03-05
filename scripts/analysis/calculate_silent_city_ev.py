import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.monsters import MONSTERS
from scripts.analysis.economy_utils import calculate_expected_value_stats


def main():
    # temporarily mock the missing monsters so we can see EV
    MONSTERS['temporal_wraith'] = {
        "level": 42,
        "tier": "Normal",
        "drops": [
            ["chronal_dust", 60],
            ["ancient_ourosan_coin", 50],
            ["magic_stone_flawless", 15]
        ]
    }
    MONSTERS['hollowed_sentinel'] = {
        "level": 42,
        "tier": "Elite",
        "drops": [
            ["perfected_glass", 75],
            ["ancient_ourosan_coin", 80],
            ["magic_stone_flawless", 25]
        ]
    }
    MONSTERS['abyssal_creeper'] = {
        "level": 43,
        "tier": "Normal",
        "drops": [
            ["perfected_glass", 50],
            ["void_touched_relic", 30],
            ["magic_stone_large", 50]
        ]
    }

    data = LOCATIONS.get("silent_city_ouros")
    if data:
        stats = calculate_expected_value_stats(data)
        print("Expected Value Stats for The Silent City of Ouros with mocked monsters:")
        print(json.dumps(stats, indent=2))

        # also print Void Sanctum for comparison
        vs_data = LOCATIONS.get("void_sanctum")
        vs_stats = calculate_expected_value_stats(vs_data)
        print("\nExpected Value Stats for The Void Sanctum:")
        print(json.dumps(vs_stats, indent=2))
    else:
        print("Location 'silent_city_ouros' not found.")

if __name__ == "__main__":
    main()
