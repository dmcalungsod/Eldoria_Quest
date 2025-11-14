"""
Core Stats Module for Eldoria Quest

Defines:
- StatBlock: stores base + bonus values
- PlayerStats: 7 core stats + derived stats (HP, MP)
"""

from dataclasses import dataclass
from typing import Dict, List, Any


# ---------------------------------------------
# StatBlock
# ---------------------------------------------
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

    Core Stats:
        STR, DEX, CON, INT, WIS, CHA, LCK

    Derived Stats:
        HP = 50 + CON * 10
        MP = 20 + INT * 5 + WIS * 3
    """

    def __init__(self, str_base=1, dex_base=1, con_base=1,
                 int_base=1, wis_base=1, cha_base=1, lck_base=1):

        self._stats: Dict[str, StatBlock] = {
            "STR": StatBlock(base=str_base),
            "DEX": StatBlock(base=dex_base),
            "CON": StatBlock(base=con_base),
            "INT": StatBlock(base=int_base),
            "WIS": StatBlock(base=wis_base),
            "CHA": StatBlock(base=cha_base),
            "LCK": StatBlock(base=lck_base),
        }

    # --- Total stat properties ---
    @property
    def strength(self): return self._stats["STR"].total
    @property
    def dexterity(self): return self._stats["DEX"].total
    @property
    def constitution(self): return self._stats["CON"].total
    @property
    def intelligence(self): return self._stats["INT"].total
    @property
    def wisdom(self): return self._stats["WIS"].total
    @property
    def charisma(self): return self._stats["CHA"].total
    @property
    def luck(self): return self._stats["LCK"].total

    # --- Derived stats ---
    @property
    def max_hp(self) -> int:
        return 50 + (self.constitution * 10)

    @property
    def max_mp(self) -> int:
        return 20 + (self.intelligence * 5) + (self.wisdom * 3)

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
            "DEX": self.dexterity,
            "CON": self.constitution,
            "INT": self.intelligence,
            "WIS": self.wisdom,
            "CHA": self.charisma,
            "LCK": self.luck,
            "HP": self.max_hp,
            "MP": self.max_mp,
        }
