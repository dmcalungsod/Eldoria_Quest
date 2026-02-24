"""
scripts/analysis/analyze_economy.py

Analyzes the economy of Eldoria Quest by calculating the Expected Value (EV) per hour
for each adventure location based on drop rates, monster stats, and material values.

Usage: python3 scripts/analysis/analyze_economy.py
"""

import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.monsters import MONSTERS
from game_systems.data.materials import MATERIALS

# Constants
STEPS_PER_HOUR = 4
REGEN_CHANCE = 0.40
COMBAT_CHANCE = 0.60

# Aurum Multipliers
TIER_MULTIPLIER = {"Normal": 1.5, "Elite": 5.0, "Boss": 20.0}

def calculate_expected_value(location_key, location_data, player_luck=10):
    """
    Calculates the expected Aurum and Material value per hour for a given location.
    """
    # --- Regen (Gathering) EV ---
    gatherables = location_data.get("gatherables", [])

    if not gatherables:
        # Fallback if no gatherables defined
        gatherables = [("medicinal_herb", 50), ("iron_ore", 20), ("ancient_wood", 10)]

    # 1. Avg Item Value
    total_weight = sum(w for _, w in gatherables)
    weighted_value_sum = 0
    for item_key, weight in gatherables:
        mat = MATERIALS.get(item_key, {})
        value = mat.get("value", 0)
        weighted_value_sum += value * weight

    avg_item_value = weighted_value_sum / total_weight if total_weight > 0 else 0

    # 2. Gather Probability
    # Base 35% + Luck Bonus (Luck / 2500) -> 10 Luck = +0.004 -> 35.4%
    gather_chance = 0.35 + (player_luck / 2500.0)
    gather_chance = min(1.0, max(0.0, gather_chance))

    # 3. Avg Quantity
    # Base 1 + (Luck / 25) -> 10 Luck = +0 -> 1
    # Plus 20% chance for +1
    avg_quantity = (1 + int(player_luck / 25)) + 0.20
    avg_quantity = min(3.0, avg_quantity)

    # 4. Total Gather EV
    gather_ev = gather_chance * avg_quantity * avg_item_value

    # 5. Fallback EV (Scavenge)
    # 65% chance to fail gather -> 50% Aurum (avg 3), 50% XP (0 value)
    fallback_chance = 1.0 - gather_chance
    fallback_ev = fallback_chance * 0.5 * 3.0  # Avg 3 Aurum

    total_regen_ev = gather_ev + fallback_ev

    # --- Combat EV ---
    monsters = location_data.get("monsters", [])
    # Add night monsters (weighted 50/50 for simplicity or assume uniform distribution over 24h)
    # For simplicity, let's just average the day and night pools if they exist
    # Or better, assume a standard mix.
    # Let's stick to the main monster pool for baseline analysis.

    combat_ev_aurum = 0
    combat_ev_materials = 0

    if monsters:
        total_monster_weight = sum(w for _, w in monsters)

        for monster_key, weight in monsters:
            monster = MONSTERS.get(monster_key)
            if not monster:
                continue

            prob = weight / total_monster_weight

            # Aurum Drop
            level = monster.get("level", 1)
            tier = monster.get("tier", "Normal")

            base_aurum = max(1, level * 2)
            tier_mult = TIER_MULTIPLIER.get(tier, 1.0)
            luck_bonus = 1.0 + min(0.5, player_luck / 1000.0)

            avg_aurum = base_aurum * tier_mult * luck_bonus
            combat_ev_aurum += prob * avg_aurum

            # Item Drops
            drops = monster.get("drops", [])
            avg_drop_value = 0
            for item_key, drop_chance in drops:
                mat = MATERIALS.get(item_key, {})
                value = mat.get("value", 0)

                # Drop Chance is percent (0-100)
                # Luck Multiplier: 1 + (Luck / 1000)
                final_chance = (drop_chance / 100.0) * (1.0 + (player_luck / 1000.0))
                final_chance = min(1.0, final_chance)

                avg_drop_value += final_chance * value

            combat_ev_materials += prob * avg_drop_value

    total_combat_ev = combat_ev_aurum + combat_ev_materials

    # --- Total Hourly EV ---
    # 4 Steps per Hour
    # Step EV = (Regen Chance * Regen EV) + (Combat Chance * Combat EV)
    # BUT wait, Regen EV includes Material Value (Gathering) and Aurum (Scavenge).
    # Combat EV splits Aurum and Materials.

    step_aurum = (REGEN_CHANCE * fallback_ev) + (COMBAT_CHANCE * combat_ev_aurum)
    step_materials = (REGEN_CHANCE * gather_ev) + (COMBAT_CHANCE * combat_ev_materials)

    hourly_aurum = step_aurum * STEPS_PER_HOUR
    hourly_materials = step_materials * STEPS_PER_HOUR
    total_hourly = hourly_aurum + hourly_materials

    return {
        "hourly_aurum": hourly_aurum,
        "hourly_materials": hourly_materials,
        "total_hourly": total_hourly,
        "min_rank": location_data.get("min_rank", "F"),
        "min_level": location_data.get("level_req", 1)
    }

def main():
    print(f"| {'Location':<25} | {'Rank':<4} | {'Lvl':<3} | {'Aurum/Hr':<10} | {'Mat Val/Hr':<10} | {'Total/Hr':<10} |")
    print(f"|{'-'*27}|{'-'*6}|{'-'*5}|{'-'*12}|{'-'*12}|{'-'*12}|")

    # Sort locations by level requirement
    sorted_locations = sorted(LOCATIONS.items(), key=lambda x: x[1].get("level_req", 1))

    for key, data in sorted_locations:
        if key == "guild_arena": continue # Skip arena

        stats = calculate_expected_value(key, data)

        print(f"| {data['name']:<25} | {stats['min_rank']:<4} | {stats['min_level']:<3} | {stats['hourly_aurum']:<10.1f} | {stats['hourly_materials']:<10.1f} | {stats['total_hourly']:<10.1f} |")

if __name__ == "__main__":
    main()
