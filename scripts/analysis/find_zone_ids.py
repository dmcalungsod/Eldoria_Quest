import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from game_systems.data.adventure_locations import LOCATIONS

def main():
    names = ["The Shrouded Fen", "The Clockwork Halls", "The Celestial Archipelago", "The Shimmering Wastes", "The Silent City of Ouros"]

    for key, data in LOCATIONS.items():
        if data.get("name") in names:
            print(f"'{data.get('name')}' ID is: {key}")

if __name__ == "__main__":
    main()
