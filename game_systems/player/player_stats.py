"""
game_systems/player/player_stats.py

Core Stats Module for Eldoria Quest
Hardened: Tiered scaling logic and robust serialization.
"""

import math
from dataclasses import dataclass
from typing import Any


# --- NEW HELPER FUNCTION (Used by Combat) ---
def calculate_tiered_bonus(stat_value: int, base_effect_per_point: float) -> int:
    """
    Calculates a stat's total effect based on a tiered scaling
    where each 100-point milestone adds +25% to the base multiplier.

    Tier 1 (1-100 pts): 1.00x
    Tier 2 (101-200 pts): 1.25x
    ...

    Optimized: Uses O(1) arithmetic formula instead of O(N) loop.
    Formula:
      T = floor(stat / 100)
      R = stat % 100
      Total = 100 * base * (T + 0.125 * T * (T - 1)) + R * base * (1 + 0.25 * T)
    """
    if stat_value <= 0:
        return 0

    # Number of full 100-point tiers
    full_tiers = stat_value // 100
    # Remaining points in the partial tier
    remaining_points = stat_value % 100

    # 1. Contribution from full tiers
    # Sum of arithmetic series: 100 * base * sum(1 + 0.25*i for i in 0..T-1)
    # Sum = 100 * base * (T + 0.125 * T * (T-1))
    full_tiers_effect = 100.0 * base_effect_per_point * (full_tiers + 0.125 * full_tiers * (full_tiers - 1))

    # 2. Contribution from remaining points
    # Multiplier for the current tier is (1 + 0.25 * T)
    current_tier_multiplier = 1.0 + (full_tiers * 0.25)
    remaining_effect = remaining_points * base_effect_per_point * current_tier_multiplier

    return math.floor(full_tiers_effect + remaining_effect)


def calculate_practice_threshold(current_base: int) -> int:
    """
    Calculates the XP required to gain the NEXT point in a stat via practice.
    Base: 100
    Scaling: +5 per current point.

    This scaling ensures that grinding 'practice' (combat actions) becomes
    progressively harder as the stat increases, preventing high-level exploits.
    """
    base = 100
    scaling = 5
    return base + (current_base * scaling)


@dataclass
class StatBlock:
    """Stores the base and bonus values of a stat."""

    base: int = 1
    bonus: int = 0

    @property
    def total(self) -> int:
        return self.base + self.bonus


class PlayerStats:
    """
    Manages all stats for a player character.
    """

    def __init__(self, str_base=1, end_base=1, dex_base=1, agi_base=1, mag_base=1, lck_base=1):
        self._stats: dict[str, StatBlock] = {
            "STR": StatBlock(base=str_base),
            "END": StatBlock(base=end_base),
            "DEX": StatBlock(base=dex_base),
            "AGI": StatBlock(base=agi_base),
            "MAG": StatBlock(base=mag_base),
            "LCK": StatBlock(base=lck_base),
            "DEF": StatBlock(base=0),  # Bonus/Item stat only
        }

    # --- Total stat properties ---
    @property
    def strength(self) -> int:
        return self._stats["STR"].total

    @property
    def endurance(self) -> int:
        return self._stats["END"].total

    @property
    def dexterity(self) -> int:
        return self._stats["DEX"].total

    @property
    def agility(self) -> int:
        return self._stats["AGI"].total

    @property
    def magic(self) -> int:
        return self._stats["MAG"].total

    @property
    def luck(self) -> int:
        return self._stats["LCK"].total

    @property
    def defense(self) -> int:
        return self._stats["DEF"].total

    # --- Derived stats ---
    @property
    def max_hp(self) -> int:
        # Formula: 50 + Tiered Bonus from END (10 HP per point base)
        hp_bonus = calculate_tiered_bonus(self.endurance, 10.0)
        return 50 + hp_bonus

    @property
    def max_mp(self) -> int:
        # Formula: 20 + Tiered Bonus from MAG (5 MP per point base)
        mp_bonus = calculate_tiered_bonus(self.magic, 5.0)
        return 20 + mp_bonus

    @property
    def max_inventory_slots(self) -> int:
        """
        Calculates total inventory slots based on STR and DEX.
        Formula: Base(10) + floor(STR * 0.5) + floor(DEX * 0.25).
        """
        base_slots = 10
        str_bonus = math.floor(self.strength * 0.5)
        dex_bonus = math.floor(self.dexterity * 0.25)
        return max(base_slots, base_slots + str_bonus + dex_bonus)

    # --- Stat modification ---
    def set_base_stat(self, stat_name: str, value: int):
        key = stat_name.upper()
        if key in self._stats:
            self._stats[key].base = max(0, value)

    def add_base_stat(self, stat_name: str, amount: int):
        key = stat_name.upper()
        if key in self._stats:
            self._stats[key].base += amount

    def add_bonus_stat(self, stat_name: str, amount: int):
        key = stat_name.upper()
        if key in self._stats:
            self._stats[key].bonus += amount

    def recalculate_bonuses(self, equipped_items: list[Any]):
        """Resets bonuses and re-applies them from item list."""
        # Reset all bonuses
        for key in self._stats:
            self._stats[key].bonus = 0

        # Apply item bonuses
        for item in equipped_items:
            # Handle dict or object items safely
            if isinstance(item, dict):
                bonuses = item.get("stats_bonus", {})
            else:
                bonuses = getattr(item, "stats_bonus", {})

            if bonuses:
                for stat, val in bonuses.items():
                    self.add_bonus_stat(stat, val)

    # --- Serialization ---
    def to_dict(self) -> dict[str, dict[str, int]]:
        return {k: {"base": v.base, "bonus": v.bonus} for k, v in self._stats.items()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        new = cls()
        if not data:
            return new

        for key, vals in data.items():
            u = key.upper()
            if u in new._stats and isinstance(vals, dict):
                new._stats[u].base = vals.get("base", 1)
                new._stats[u].bonus = vals.get("bonus", 0)
        return new

    # --- Simple output dicts ---
    def get_base_stats_dict(self) -> dict[str, int]:
        return {k: v.base for k, v in self._stats.items()}

    def get_total_stats_dict(self) -> dict[str, int]:
        return {
            "STR": self.strength,
            "END": self.endurance,
            "DEX": self.dexterity,
            "AGI": self.agility,
            "MAG": self.magic,
            "LCK": self.luck,
            "DEF": self.defense,
            "HP": self.max_hp,
            "MP": self.max_mp,
        }
