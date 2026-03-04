import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from game_systems.data.materials import MATERIALS


def main():
    print(f"{'Material':<30} | {'Value':<10}")
    print("-" * 43)

    sorted_materials = sorted(MATERIALS.items(), key=lambda x: x[1].get("value", 0), reverse=True)

    for key, data in sorted_materials:
        print(f"{data.get('name', key):<30} | {data.get('value', 0):<10}")


if __name__ == "__main__":
    main()
