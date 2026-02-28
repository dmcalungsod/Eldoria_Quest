"""
scripts/analysis/analyze_exploration.py

Analyzes boss monsters from static game data.
Lists all Bosses above level 30 and their drop tables.

Usage: python scripts/analysis/analyze_exploration.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from game_systems.data.monsters import MONSTERS


def analyze():
    print("Running boss exploration analysis...")
    print(f"\n{'Name':<25} {'Level':>5}  Drops")
    print("-" * 60)

    bosses = [(key, data) for key, data in MONSTERS.items() if data.get("tier") == "Boss" and data.get("level", 0) > 30]

    if not bosses:
        print("No bosses found above level 30.")
        return

    bosses.sort(key=lambda x: x[1].get("level", 0))
    for key, data in bosses:
        drops = data.get("drops", [])
        drop_str = ", ".join(f"{item}({chance}%)" for item, chance in drops) if drops else "None"
        print(f"{data['name']:<25} {data.get('level', '?'):>5}  {drop_str}")


if __name__ == "__main__":
    analyze()
