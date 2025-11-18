"""
exp_calculator.py

Calculates EXP rewards based on monster tier and level difference.
Exposes 'ExpCalculator' class for CombatEngine.
"""

import math


class ExpCalculator:
    TIER_MULTIPLIER = {
        "Normal": 1.0,
        "Elite": 2.5,
        "Boss": 10.0
    }

    @staticmethod
    # --- MODIFIED FUNCTION SIGNATURE ---
    def calculate_exp(
        player_level: int, monster_data: dict, exp_boost_mult: float = 1.0
    ) -> int:
    # --- END MODIFIED SIGNATURE ---
        """
        Calculates XP reward for a single player.
        """
        # Extract monster details
        monster_level = monster_data.get("level", 1)
        tier = monster_data.get("tier", "Normal")
        base_xp = monster_data.get("xp", monster_level * 8)

        # Apply Tier Multiplier
        tier_mult = ExpCalculator.TIER_MULTIPLIER.get(tier, 1.0)

        # --- MODIFIED LINE ---
        raw_xp = base_xp * tier_mult * exp_boost_mult
        # --- END MODIFIED LINE ---

        # Level Difference Penalty
        # If player is 5+ levels higher, reduce XP
        level_diff = player_level - monster_level
        if level_diff >= 5:
            excess = level_diff - 4
            reduction_fraction = min(0.8, 0.1 * excess) # Cap at 80% reduction
            raw_xp = raw_xp * (1.0 - reduction_fraction)

        return max(0, math.floor(raw_xp))
