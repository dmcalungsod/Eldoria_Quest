
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Adjust path to include the root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.collection"] = MagicMock()
sys.modules["pymongo.results"] = MagicMock()

# Import after mocking
from game_systems.player.player_stats import PlayerStats
from database.database_manager import DatabaseManager

class TestInventoryCapacity(unittest.TestCase):
    def test_capacity_scaling(self):
        """Test that inventory capacity scales with STR and DEX."""
        # Base stats (1, 1, 1...)
        stats = PlayerStats()
        # Base 10 + floor(1*0.5) + floor(1*0.25) = 10 + 0 + 0 = 10
        self.assertEqual(stats.max_inventory_slots, 10)

        # Increase STR
        stats = PlayerStats(str_base=10, dex_base=1)
        # Base 10 + floor(10*0.5) + floor(1*0.25) = 10 + 5 + 0 = 15
        self.assertEqual(stats.max_inventory_slots, 15)

        # Increase DEX
        stats = PlayerStats(str_base=1, dex_base=20)
        # Base 10 + floor(1*0.5) + floor(20*0.25) = 10 + 0 + 5 = 15
        self.assertEqual(stats.max_inventory_slots, 15)

        # Increase both
        stats = PlayerStats(str_base=10, dex_base=20)
        # Base 10 + floor(10*0.5) + floor(20*0.25) = 10 + 5 + 5 = 20
        self.assertEqual(stats.max_inventory_slots, 20)

        # Test rounding behavior
        stats = PlayerStats(str_base=3, dex_base=3)
        # Base 10 + floor(3*0.5) + floor(3*0.25) = 10 + floor(1.5) + floor(0.75) = 10 + 1 + 0 = 11
        self.assertEqual(stats.max_inventory_slots, 11)

    def test_db_integration(self):
        """Test that DatabaseManager uses the calculated limit."""
        # Mocking get_player_stats_json within DatabaseManager
        with patch.object(DatabaseManager, 'get_player_stats_json') as mock_get_stats:
            mock_get_stats.return_value = {
                "STR": {"base": 20, "bonus": 0},
                "DEX": {"base": 40, "bonus": 0},
                "END": {"base": 1, "bonus": 0},
                "AGI": {"base": 1, "bonus": 0},
                "MAG": {"base": 1, "bonus": 0},
                "LCK": {"base": 1, "bonus": 0},
                "DEF": {"base": 0, "bonus": 0}
            }

            # We need to initialize DatabaseManager but avoid __init__ logic that connects to mongo
            # Or simpler: just instantiate it since pymongo is mocked
            db = DatabaseManager()

            # 10 + floor(20*0.5) + floor(40*0.25) = 10 + 10 + 10 = 30
            limit = db.calculate_inventory_limit(12345)
            self.assertEqual(limit, 30)

if __name__ == "__main__":
    unittest.main()
