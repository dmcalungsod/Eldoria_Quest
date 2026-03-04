import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from game_systems.data.monsters import MONSTERS


def main():
    print(f"{'Level':<5} | {'Count':<5} | {'Avg HP':<10} | {'Avg ATK':<10} | {'Avg DEF':<10}")
    print("-" * 50)

    stats_by_level = {}

    for key, data in MONSTERS.items():
        level = data.get("level", 1)
        if level not in stats_by_level:
            stats_by_level[level] = {"count": 0, "hp": 0, "atk": 0, "def": 0}

        stats_by_level[level]["count"] += 1
        stats_by_level[level]["hp"] += data.get("hp", 0)
        stats_by_level[level]["atk"] += data.get("atk", 0)
        stats_by_level[level]["def"] += data.get("def", 0)

    for level in sorted(stats_by_level.keys()):
        stats = stats_by_level[level]
        count = stats["count"]
        print(
            f"{level:<5} | {count:<5} | {stats['hp'] / count:<10.1f} | {stats['atk'] / count:<10.1f} | {stats['def'] / count:<10.1f}"
        )


if __name__ == "__main__":
    main()
