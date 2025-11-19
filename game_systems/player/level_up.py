"""
Level Up System for Eldoria Quest

Handles:
- Experience calculation
- Level-up thresholds (Quadratic curve)
- State management for leveling
"""

from .player_stats import PlayerStats


class LevelUpSystem:
    """
    Standalone Level-Up Manager.
    Logic only; persistence is handled by external systems.
    """

    STAT_LIST = ["STR", "END", "DEX", "AGI", "MAG", "LCK"]

    def __init__(
        self,
        stats: PlayerStats,
        level: int = 1,
        exp: int = 0,
        exp_to_next: int = 1000,
    ):
        self.stats = stats
        self.level = max(1, level)
        self.exp = max(0, exp)
        self.exp_to_next = max(100, exp_to_next)

    def add_exp(self, amount: int) -> bool:
        """
        Adds EXP and checks for level-up.
        Returns True if the player leveled up at least once.
        """
        if amount <= 0:
            return False

        self.exp += amount
        leveled_up = False

        # Handle multiple level-ups
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level_up()
            leveled_up = True

        return leveled_up

    def level_up(self):
        """Apply level-up logic."""
        self.level += 1

        # Increase EXP requirement using quadratic formula
        # Formula: R_L = 1000 * L^2 - 500 * L + 500
        new_level = self.level
        self.exp_to_next = int(1000 * (new_level**2) - 500 * new_level + 500)

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "exp": self.exp,
            "exp_to_next": self.exp_to_next,
            "stats": self.stats.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return cls(PlayerStats())

        stats_data = data.get("stats", {})
        stats = PlayerStats.from_dict(stats_data)

        return cls(
            stats=stats,
            level=data.get("level", 1),
            exp=data.get("exp", 0),
            exp_to_next=data.get("exp_to_next", 1000),
        )
