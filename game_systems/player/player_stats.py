"""
Core Stats Module for Eldoria Quest

Defines:
- StatBlock: stores base + bonus values
- PlayerStats: 6 core stats + derived stats (HP, MP)
"""

import math  # <-- IMPORT MATH
from dataclasses import dataclass
from typing import Any, Dict, List


# --- NEW HELPER FUNCTION ---
def calculate_tiered_bonus(stat_value, base_effect_per_point):
    """
    Calculates a stat's total effect based on a tiered scaling
    where each 100-point milestone adds +25% to the base multiplier.

    Tier 1 (1-100 pts): 1.00x
    Tier 2 (101-200 pts): 1.25x
    Tier 3 (201-300 pts): 1.50x
    ...
    Tier 10 (901-999 pts): 3.25x

    Example: 250 END (10 HP per point)
    - 100 points @ 1.00x = 100 * 10 * 1.00 = 1000
    - 100 points @ 1.25x = 100 * 10 * 1.25 = 1250
    - 50 points  @ 1.50x =  50 * 10 * 1.50 =  750
    - Total = 3000 HP
    """
    total_effect = 0
    remaining_points = stat_value
    current_tier = 0

    while remaining_points > 0:
        # Determine points to calculate for this tier
        points_in_this_tier = min(remaining_points, 100)

        # Calculate the additive multiplier
        # Tier 0 (1-100) = 1.0 + (0 * 0.25) = 1.0x
        # Tier 1 (101-200) = 1.0 + (1 * 0.25) = 1.25x
        # Tier 2 (201-300) = 1.0 + (2 * 0.25) = 1.50x
        multiplier = 1.0 + (current_tier * 0.25)

        # Add to the total effect
        total_effect += points_in_this_tier * base_effect_per_point * multiplier

        # Decrement points and move to the next tier
        remaining_points -= points_in_this_tier
        current_tier += 1

    return math.floor(total_effect)


# --- END NEW HELPER FUNCTION ---


@dataclass
class StatBlock:
    """Stores the base and bonus values of a stat."""

    base: int = 1
    bonus: int = 0

    @property
    def total(self) -> int:
        return self.base + self.bonus


# ---------------------------------------------
# PlayerStats
# ---------------------------------------------
class PlayerStats:
    """
    Manages all stats for a player character.
    ...
    """

    def __init__(self, str_base=1, end_base=1, dex_base=1, agi_base=1, mag_base=1, lck_base=1):
        self._stats: Dict[str, StatBlock] = {
            "STR": StatBlock(base=str_base),
            "END": StatBlock(base=end_base),
            "DEX": StatBlock(base=dex_base),
            "AGI": StatBlock(base=agi_base),
            "MAG": StatBlock(base=mag_base),
            "LCK": StatBlock(base=lck_base),
        }

    # --- Total stat properties ---
    @property
    def strength(self):
        return self._stats["STR"].total

    @property
    def endurance(self):
        return self._stats["END"].total

    @property
    def dexterity(self):
        return self._stats["DEX"].total

    @property
    def agility(self):
        return self._stats["AGI"].total

    @property
    def magic(self):
        return self._stats["MAG"].total

    @property
    def luck(self):
        return self._stats["LCK"].total

    # --- Derived stats (MODIFIED) ---
    @property
    def max_hp(self) -> int:
        # Formula was: 50 + (self.endurance * 10)
        # NEW Formula: 50 + Tiered Bonus from END (10 HP per point)
        hp_bonus = calculate_tiered_bonus(self.endurance, 10)
        return 50 + hp_bonus

    @property
    def max_mp(self) -> int:
        # Formula was: 20 + (self.magic * 5)
        # NEW Formula: 20 + Tiered Bonus from MAG (5 MP per point)
        mp_bonus = calculate_tiered_bonus(self.magic, 5)
        return 20 + mp_bonus

    # --- Stat modification ---
    def set_base_stat(self, stat_name, value):
        key = stat_name.upper()
        if key in self._stats:
            self._stats[key].base = max(0, value)

    def add_base_stat(self, stat_name, amount):
        key = stat_name.upper()
        if key in self._stats:
            self._stats[key].base += amount

    def add_bonus_stat(self, stat_name, amount):
        key = stat_name.upper()
        if key in self._stats:
            self._stats[key].bonus += amount

    def recalculate_bonuses(self, equipped_items: List[Any]):
        # Reset all bonuses
        for key in self._stats:
            self._stats[key].bonus = 0

        # Apply item bonuses
        for item in equipped_items:
            if hasattr(item, "stats_bonus") and isinstance(item.stats_bonus, dict):
                for stat, val in item.stats_bonus.items():
                    self.add_bonus_stat(stat, val)

    # --- Serialization ---
    def to_dict(self):
        return {k: {"base": v.base, "bonus": v.bonus} for k, v in self._stats.items()}

    @classmethod
    def from_dict(cls, data):
        new = cls()
        for key, vals in data.items():
            u = key.upper()
            if u in new._stats:
                new._stats[u].base = vals.get("base", 1)
                new._stats[u].bonus = vals.get("bonus", 0)
        return new

    # --- Simple output dicts ---
    def get_base_stats_dict(self):
        return {k: v.base for k, v in self._stats.items()}

    def get_total_stats_dict(self):
        return {
            "STR": self.strength,
            "END": self.endurance,
            "DEX": self.dexterity,
            "AGI": self.agility,
            "MAG": self.magic,
            "LCK": self.luck,
            "HP": self.max_hp,
            "MP": self.max_mp,
        }
