"""
scripts/analysis/analyze_economy.py

Analyzes the economy of Eldoria Quest by calculating the Expected Value (EV) per hour
for each adventure location based on drop rates, monster stats, and material values.

Usage: python3 scripts/analysis/analyze_economy.py
"""

import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from game_systems.data.adventure_locations import LOCATIONS
from scripts.analysis.economy_utils import calculate_expected_value_stats


def calculate_expected_value(location_data, player_luck=10):
    """
    Calculates the expected Aurum and Material value per hour for a given location.
    """
    return calculate_expected_value_stats(location_data, player_luck)


def main():
    print(f"| {'Location':<25} | {'Rank':<4} | {'Lvl':<3} | {'Aurum/Hr':<10} | {'Mat Val/Hr':<10} | {'Total/Hr':<10} |")
    print(f"|{'-' * 27}|{'-' * 6}|{'-' * 5}|{'-' * 12}|{'-' * 12}|{'-' * 12}|")

    # Sort locations by level requirement
    sorted_locations = sorted(LOCATIONS.items(), key=lambda x: x[1].get("level_req", 1))

    for key, data in sorted_locations:
        if key == "guild_arena":
            continue  # Skip arena

        stats = calculate_expected_value(data)

        print(
            f"| {data['name']:<25} | {stats['min_rank']:<4} | {stats['min_level']:<3} | {stats['hourly_aurum']:<10.1f} | {stats['hourly_materials']:<10.1f} | {stats['total_hourly']:<10.1f} |"
        )


if __name__ == "__main__":
    main()
