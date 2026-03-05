import json
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.monsters import MONSTERS
from scripts.analysis.economy_utils import calculate_expected_value_stats


def main():
    print(f"Number of monsters in DB: {len(MONSTERS)}")
    data = LOCATIONS.get("silent_city_ouros")
    if data:
        stats = calculate_expected_value_stats(data)
        print("Expected Value Stats for The Silent City of Ouros:")
        print(json.dumps(stats, indent=2))
    else:
        print("Location 'silent_city_ouros' not found.")

if __name__ == "__main__":
    main()
