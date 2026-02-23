import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.append(os.getcwd())

# Mock dependencies before imports
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestInventoryScaling(unittest.TestCase):
    def test_scaling_formula(self):
        """
        Verify the scaling formula:
        Total = Base(10) + floor(STR * 0.5) + floor(DEX * 0.25)
        """
        # Case 1: Base stats (1, 1) -> 10 + 0 + 0 = 10
        stats = PlayerStats(str_base=1, dex_base=1)
        self.assertEqual(stats.max_inventory_slots, 10)

        # Case 2: STR=10, DEX=10 -> 10 + 5 + 2 = 17
        stats = PlayerStats(str_base=10, dex_base=10)
        self.assertEqual(stats.max_inventory_slots, 17)

        # Case 3: STR=20, DEX=20 -> 10 + 10 + 5 = 25
        stats = PlayerStats(str_base=20, dex_base=20)
        self.assertEqual(stats.max_inventory_slots, 25)

        # Case 4: High STR/DEX -> STR=100, DEX=100 -> 10 + 50 + 25 = 85
        stats = PlayerStats(str_base=100, dex_base=100)
        self.assertEqual(stats.max_inventory_slots, 85)

    def test_database_manager_uses_scaling(self):
        """Verify DatabaseManager.calculate_inventory_limit uses PlayerStats."""
        db = DatabaseManager()
        discord_id = 12345

        # Mock stats JSON returning STR=10, DEX=10
        stats_data = {"STR": {"base": 10}, "DEX": {"base": 10}}
        with patch.object(db, "get_player_stats_json", return_value=stats_data):
            limit = db.calculate_inventory_limit(discord_id)
            self.assertEqual(limit, 17)

    def test_fallback_to_base(self):
        """Verify fallback if stats missing."""
        db = DatabaseManager()
        discord_id = 12345

        with patch.object(db, "get_player_stats_json", return_value=None):
            limit = db.calculate_inventory_limit(discord_id)
            self.assertEqual(limit, 10)  # BASE_INVENTORY_SLOTS


if __name__ == "__main__":
    unittest.main()
