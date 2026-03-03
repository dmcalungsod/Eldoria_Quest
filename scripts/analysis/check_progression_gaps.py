"""
scripts/analysis/check_progression_gaps.py

Analyzes progression gaps by calculating the change in Expected Value (EV)
between adventure locations when sorted by level requirement.
Highlights "reward cliffs" where difficulty increases but rewards decrease.

Usage: python3 scripts/analysis/check_progression_gaps.py
"""

import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from game_systems.data.adventure_locations import LOCATIONS
from scripts.analysis.economy_utils import calculate_expected_value_stats



def calculate_ev(location_data, player_luck=10):
    """
    Calculates the expected Total Value per hour (Aurum + Material Value).
    """
    stats = calculate_expected_value_stats(location_data, player_luck)
    return stats["total_hourly"]


def main():
    print(f"{'Location':<25} | {'Rk':<2} | {'Lvl':<3} | {'EV/Hr':<8} | {'Delta':<8} | {'Status'}")
    print("-" * 75)

    data_points = []
    for key, data in LOCATIONS.items():
        if key == "guild_arena":
            continue

        ev = calculate_ev(data)
        data_points.append(
            {"name": data["name"], "rank": data.get("min_rank", "F"), "level": data.get("level_req", 1), "ev": ev}
        )

    # Sort by Level Requirement
    data_points.sort(key=lambda x: x["level"])

    prev_ev = 0
    for i, dp in enumerate(data_points):
        delta = 0
        if prev_ev > 0:
            delta = ((dp["ev"] - prev_ev) / prev_ev) * 100

        status = ""
        if i > 0:
            if delta < -10:
                status = "🔴 CRITICAL DROP"
            elif delta < 0:
                status = "🟠 Decrease"
            elif delta > 50:
                status = "🟢 Spike"

        # Format Delta
        delta_str = f"{delta:+.1f}%" if i > 0 else "-"

        print(f"{dp['name']:<25} | {dp['rank']:<2} | {dp['level']:<3} | {dp['ev']:<8.1f} | {delta_str:<8} | {status}")

        prev_ev = dp["ev"]


if __name__ == "__main__":
    main()
