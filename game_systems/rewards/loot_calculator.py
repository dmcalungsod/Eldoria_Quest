"""
loot_calculator.py

Centralized drop chance calculation.
Replaces additive luck scaling with multiplicative scaling for better balance.
"""

import math
import random
from typing import List, Tuple

from game_systems.data.materials import MATERIALS


class LootCalculator:
    """
    Handles drop rate calculations and RNG rolls.
    """

    HIGH_RARITY_TIERS = {"Epic", "Legendary", "Mythical"}

    @staticmethod
    def calculate_drop_chance(base_chance: float, rarity: str, luck: int, loot_boost: float = 1.0) -> float:
        """
        Calculates the final drop chance as a percentage (0-100).

        Args:
            base_chance: The base probability (0-100).
            rarity: The rarity tier of the item.
            luck: The player's Luck stat.
            loot_boost: Multiplier from buffs/events (default 1.0).

        Returns:
            The final percentage chance (0.0 to 100.0).
        """
        # Base multiplier from buffs/events
        multiplier = max(0.0, float(loot_boost))

        # Luck scaling (Multiplicative)
        # Formula: 1 + (Luck / 1000)
        # Example: 0 Luck -> 1.0x, 500 Luck -> 1.5x, 1000 Luck -> 2.0x
        # Only applies to High Rarity items to preserve their value while rewarding high Luck stats.
        if rarity in LootCalculator.HIGH_RARITY_TIERS:
            luck_factor = 1.0 + (max(0, luck) / 1000.0)
            multiplier *= luck_factor

        final_chance = base_chance * multiplier

        # Cap at 100%
        return min(100.0, max(0.0, final_chance))

    @staticmethod
    def roll_drops(drops_list: List[Tuple[str, float]], luck: int, loot_boost: float = 1.0) -> List[str]:
        """
        Processes a list of potential drops and returns the keys of items that dropped.

        Args:
            drops_list: List of (item_key, base_chance) tuples.
            luck: Player's Luck stat.
            loot_boost: Active loot multiplier.

        Returns:
            List of item keys that successfully dropped.
        """
        actual_drops = []

        for drop_key, base_chance in drops_list:
            mat = MATERIALS.get(drop_key, {})
            rarity = mat.get("rarity", "Common")

            final_chance = LootCalculator.calculate_drop_chance(base_chance, rarity, luck, loot_boost)

            # Use uniform distribution to support fractional percentages (e.g., 0.5% chance)
            # random.uniform(0, 100) returns a float between 0.0 and 100.0
            roll = random.uniform(0, 100)

            if roll <= final_chance:
                actual_drops.append(drop_key)

        return actual_drops
