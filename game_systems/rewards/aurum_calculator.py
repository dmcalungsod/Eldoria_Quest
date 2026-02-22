"""
aurum_calculator.py

Calculates Aurum drops based on monster tier and level.
"""

import random


class AurumCalculator:
    TIER_MULTIPLIER = {
        "Normal": 1.5,
        "Elite": 5.0,
        "Boss": 20.0
    }

    @staticmethod
    def calculate_drop(monster_level: int, tier: str, luck: int = 0) -> int:
        """
        Calculates Aurum reward for a monster kill.

        Args:
            monster_level: The monster's level.
            tier: The monster's tier (Normal, Elite, Boss).
            luck: Player's Luck stat (optional small bonus).

        Returns:
            Amount of Aurum to drop.
        """
        # Base value: Level * 2
        base_val = max(1, monster_level * 2)

        # Tier Multiplier
        mult = AurumCalculator.TIER_MULTIPLIER.get(tier, 1.0)

        # Variance: 0.8 to 1.2
        variance = random.uniform(0.8, 1.2)

        # Luck Bonus: 1% per 10 Luck (capped at +50%)
        luck_bonus = 1.0 + min(0.5, luck / 1000.0)

        final_val = int(base_val * mult * variance * luck_bonus)

        return max(1, final_val)
