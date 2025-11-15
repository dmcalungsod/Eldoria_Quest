"""
Level Up System for Eldoria Quest

This module handles:
- Experience gain
- Automatic level-up
- Auto scaling experience requirements per level
- Integration with PlayerStats for recalculating derived stats (HP, MP)
"""

from typing import Dict
from .player_stats import PlayerStats


class LevelUpSystem:
    """
    Standalone Level-Up Manager.

    Leveling up no longer grants stats automatically.
    It only increases the level and the EXP requirement for the next level.
    """

    # Updated to the new 6-stat system
    STAT_LIST = ["STR", "END", "DEX", "AGI", "MAG", "LCK"]

    def __init__(
        self,
        stats: PlayerStats,
        level: int = 1,
        exp: int = 0,
        # --- CHANGE 1: Set new default ---
        exp_to_next: int = 1000,
    ):
        self.stats = stats
        self.level = level
        self.exp = exp
        self.exp_to_next = exp_to_next

    # -----------------------------------------------------------
    # EXP Handling
    # -----------------------------------------------------------
    def add_exp(self, amount: int) -> bool:
        """
        Adds EXP and checks for level-up.
        Returns:
            True if the player leveled up
            False otherwise
        """
        self.exp += amount
        leveled_up = False

        # Handle multiple level-ups if EXP exceeds requirement
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level_up()
            leveled_up = True

        return leveled_up

    # -----------------------------------------------------------
    # Level Up Logic
    # -----------------------------------------------------------
    def level_up(self):
        """Apply the level-up bonuses."""
        self.level += 1

        # --- CHANGE 2: REMOVED AUTOMATIC STAT GAINS ---
        # for stat in self.STAT_LIST:
        #    self.stats.add_base_stat(stat, 1)
        # --- END OF CHANGE ---

        # Increase the EXP required for the next level
        self.exp_to_next = int(self.exp_to_next * 1.22)  # 22% growth rate

    # -----------------------------------------------------------
    # Serialization
    # -----------------------------------------------------------
    def to_dict(self) -> Dict:
        """Convert all level + stat data to a dictionary for saving."""
        return {
            "level": self.level,
            "exp": self.exp,
            "exp_to_next": self.exp_to_next,
            "stats": self.stats.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict):
        """Reconstruct a LevelUpSystem object from saved data."""
        stats = PlayerStats.from_dict(data["stats"])
        return cls(
            stats=stats,
            level=data.get("level", 1),
            exp=data.get("exp", 0),
            # --- CHANGE 3: Set new default ---
            exp_to_next=data.get("exp_to_next", 1000),
        )
