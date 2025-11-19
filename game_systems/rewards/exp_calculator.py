"""
exp_calculator.py

Calculates EXP rewards based on monster tier and level difference.
Hardened: Safe math operations and bounds checking.
"""

import math


class ExpCalculator:
    TIER_MULTIPLIER = {"Normal": 1.0, "Elite": 2.5, "Boss": 10.0}

    @staticmethod
    def calculate_exp(player_level: int, monster_data: dict, exp_boost_mult: float = 1.0) -> int:
        """
        Calculates XP reward for a single player.
        """
        # Extract monster details with safe defaults
        monster_level = monster_data.get("level", 1)
        tier = monster_data.get("tier", "Normal")
        
        # Default XP formula if not specified in data
        base_xp = monster_data.get("xp", monster_level * 8)

        # Apply Tier Multiplier
        tier_mult = ExpCalculator.TIER_MULTIPLIER.get(tier, 1.0)

        # Calculate raw
        raw_xp = base_xp * tier_mult * float(exp_boost_mult)

        # Level Difference Penalty
        # If player is 5+ levels higher, reduce XP to prevent farming low mobs
        level_diff = player_level - monster_level
        
        if level_diff >= 5:
            excess = level_diff - 4
            # Max penalty 80% at level diff 12+
            reduction_fraction = min(0.8, 0.1 * excess)
            raw_xp = raw_xp * (1.0 - reduction_fraction)

        # Ensure integer and non-negative
        return max(0, math.floor(raw_xp))