import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from game_systems.data.monsters import MONSTERS


def main():
    print("Boss Drops Analysis")
    print("-" * 50)

    for key, data in MONSTERS.items():
        if data.get("tier") == "Boss" and data.get("level", 0) > 30:
            print(f"{data['name']} (Level {data['level']})")
            for item, rate in data.get("drops", []):
                print(f"  - {item}: {rate}%")
            print()


if __name__ == "__main__":
    main()
