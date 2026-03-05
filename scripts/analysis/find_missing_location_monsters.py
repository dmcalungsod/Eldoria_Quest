import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.monsters import MONSTERS


def main():
    missing_monsters = []
    affected_locations = []

    for loc_key, loc_data in LOCATIONS.items():
        monsters = loc_data.get("monsters", [])
        for monster_key, weight in monsters:
            if monster_key not in MONSTERS:
                missing_monsters.append(monster_key)
                if loc_key not in affected_locations:
                    affected_locations.append(loc_key)

    print("\nSummary:")
    print(f"Missing monsters: {set(missing_monsters)}")
    print(f"Affected locations: {affected_locations}")

if __name__ == "__main__":
    main()
