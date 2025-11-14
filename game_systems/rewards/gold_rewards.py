"""
gold_rewards.py

Calculates Gold drops.
Exposes 'GoldRewards' class for CombatEngine.
"""

import random
import math

class GoldRewards:
    TIER_MULT = {
        "Normal": 1.0,
        "Elite": 2.0,
        "Boss": 8.0
    }

    @staticmethod
    def generate(monster_data: dict) -> int:
        """
        Generates gold drop amount.
        """
        level = monster_data.get("level", 1)
        tier = monster_data.get("tier", "Normal")
        
        # Base calculation
        base_gold = max(1, level * 3)
        multiplier = GoldRewards.TIER_MULT.get(tier, 1.0)
        
        # Variance +/- 20%
        variance = random.uniform(0.8, 1.2)
        
        final_gold = base_gold * multiplier * variance
        return max(1, math.floor(final_gold))