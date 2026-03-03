"""
scripts/analysis/rank_duration.py

Lists all adventure locations with their rank and level requirement.
Uses static game data (no DB needed).

Usage: python scripts/analysis/rank_duration.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from game_systems.data.adventure_locations import LOCATIONS


def analyze():
    print(f"\n{'Location':<28} {'Rank':>4}  {'Level Req':>9}")
    print("-" * 46)

    sorted_locations = sorted(LOCATIONS.items(), key=lambda x: x[1].get("level_req", 0))

    for key, data in sorted_locations:
        if key == "guild_arena":
            continue
        name = data.get("name", key)
        rank = data.get("min_rank", "?")
        level = data.get("level_req", "?")
        print(f"{name:<28} {rank:>4}  {level:>9}")


if __name__ == "__main__":
    analyze()
