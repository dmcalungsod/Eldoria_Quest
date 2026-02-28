"""
scripts/analysis/economy_utils.py

Shared utilities for economy analysis scripts.
"""

from game_systems.data.materials import MATERIALS
from game_systems.data.monsters import MONSTERS

# Constants
STEPS_PER_HOUR = 4
REGEN_CHANCE = 0.40
COMBAT_CHANCE = 0.60
TIER_MULTIPLIER = {"Normal": 1.5, "Elite": 5.0, "Boss": 20.0}


def calculate_expected_value_stats(location_data: dict, player_luck: int = 10) -> dict:
    """
    Calculates the expected Aurum and Material value per hour for a given location.
    Shared math for check_progression_gaps.py and analyze_economy.py.
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

    gather_chance = min(1.0, max(0.0, 0.35 + (player_luck / 2500.0)))
    avg_quantity = min(3.0, (1 + int(player_luck / 25)) + 0.20)
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
                final_chance = min(1.0, (drop_chance / 100.0) * (1.0 + (player_luck / 1000.0)))
                avg_drop_value += final_chance * value

            combat_ev_materials += prob * avg_drop_value

    # --- Totals ---
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
        "min_level": location_data.get("level_req", 1),
    }
