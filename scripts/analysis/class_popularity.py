"""
scripts/analysis/class_popularity.py

Analyzes class distribution across all registered players.
Uses db_helper for live MongoDB or stored JSON fallback.

Usage: python scripts/analysis/class_popularity.py
"""

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from db_helper import get_players  # noqa: E402


# Map class_id -> name (mirrors classes defined in the DB/game data)
CLASS_NAMES = {
    1: "Warrior",
    2: "Mage",
    3: "Rogue",
    4: "Cleric",
    5: "Ranger",
    6: "Alchemist",
}


def analyze():
    players = get_players()

    if not players:
        print("No player data available. Skipping analysis.")
        return

    class_counts = Counter()
    for player in players:
        class_id = player.get("class_id")
        class_counts[class_id] += 1

    total = len(players)

    print(f"\n{'=' * 40}")
    print(f"  Class Popularity ({total} players total)")
    print(f"{'=' * 40}")
    print(f"{'Class':<15} {'Count':>6} {'Share':>8}")
    print(f"{'-' * 15} {'-' * 6} {'-' * 8}")

    for class_id, count in class_counts.most_common():
        name = CLASS_NAMES.get(class_id, f"Unknown ({class_id})")
        pct = (count / total * 100) if total > 0 else 0
        bar = "█" * int(pct / 5)
        print(f"{name:<15} {count:>6} {pct:>7.1f}% {bar}")

    print(f"{'=' * 40}")


if __name__ == "__main__":
    analyze()
