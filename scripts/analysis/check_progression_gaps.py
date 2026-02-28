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
from game_systems.data.materials import MATERIALS
from game_systems.data.monsters import MONSTERS

# Constants
STEPS_PER_HOUR = 4
REGEN_CHANCE = 0.40
COMBAT_CHANCE = 0.60

# Aurum Multipliers
TIER_MULTIPLIER = {"Normal": 1.5, "Elite": 5.0, "Boss": 20.0}


def calculate_ev(location_key, location_data, player_luck=10):
    """
    Calculates the expected Total Value per hour (Aurum + Material Value).
    """
    # --- Regen (Gathering) EV ---
    gatherables = location_data.get("gatherables", [])

    if not gatherables:
        gatherables = [("medicinal_herb", 50), ("iron_ore", 20), ("ancient_wood", 10)]

    total_weight = sum(w for _, w in gatherables)
    weighted_value_sum = 0
    for item_key, weight in gatherables:
        mat = MATERIALS.get(item_key, {})
        value = mat.get("value", 0)
        weighted_value_sum += value * weight

    avg_item_value = weighted_value_sum / total_weight if total_weight > 0 else 0

    # Base 35% + Luck Bonus (Luck / 2500) -> 10 Luck = +0.004 -> 35.4%
    gather_chance = 0.35 + (player_luck / 2500.0)
    gather_chance = min(1.0, max(0.0, gather_chance))

    # Base 1 + (Luck / 25) -> 10 Luck = +0 -> 1.2
    avg_quantity = (1 + int(player_luck / 25)) + 0.20
    avg_quantity = min(3.0, avg_quantity)

    gather_ev = gather_chance * avg_quantity * avg_item_value

    # Fallback EV (Scavenge)
    fallback_chance = 1.0 - gather_chance
    fallback_ev = fallback_chance * 0.5 * 3.0  # Avg 3 Aurum

    # --- Combat EV ---
    monsters = location_data.get("monsters", [])
    combat_ev_aurum = 0
    combat_ev_materials = 0

    if monsters:
        total_monster_weight = sum(w for _, w in monsters)

        for monster_key, weight in monsters:
            monster = MONSTERS.get(monster_key)
            if not monster:
                continue

            prob = weight / total_monster_weight

            # Aurum
            level = monster.get("level", 1)
            tier = monster.get("tier", "Normal")
            base_aurum = max(1, level * 2)
            tier_mult = TIER_MULTIPLIER.get(tier, 1.0)
            luck_bonus = 1.0 + min(0.5, player_luck / 1000.0)
            avg_aurum = base_aurum * tier_mult * luck_bonus
            combat_ev_aurum += prob * avg_aurum

            # Drops
            drops = monster.get("drops", [])
            avg_drop_value = 0
            for item_key, drop_chance in drops:
                mat = MATERIALS.get(item_key, {})
                value = mat.get("value", 0)
                final_chance = (drop_chance / 100.0) * (1.0 + (player_luck / 1000.0))
                final_chance = min(1.0, final_chance)
                avg_drop_value += final_chance * value

            combat_ev_materials += prob * avg_drop_value

    # --- Totals ---
    step_val = (REGEN_CHANCE * (gather_ev + fallback_ev)) + (COMBAT_CHANCE * (combat_ev_aurum + combat_ev_materials))

    return step_val * STEPS_PER_HOUR


def main():
    print(f"{'Location':<25} | {'Rk':<2} | {'Lvl':<3} | {'EV/Hr':<8} | {'Delta':<8} | {'Status'}")
    print("-" * 75)

    data_points = []
    for key, data in LOCATIONS.items():
        if key == "guild_arena":
            continue

        ev = calculate_ev(key, data)
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
