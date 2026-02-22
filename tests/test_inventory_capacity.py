import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Mock pymongo BEFORE importing database_manager
sys.modules['pymongo'] = MagicMock()
sys.modules['pymongo.errors'] = MagicMock()
sys.modules['pymongo.collection'] = MagicMock()
sys.modules['pymongo.results'] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Adjust path for execution from root
if os.path.basename(os.getcwd()) != 'tests':
    sys.path.insert(0, os.getcwd())

from game_systems.player.player_stats import PlayerStats  # noqa: E402
from database.database_manager import DatabaseManager, BASE_INVENTORY_SLOTS  # noqa: E402

class TestInventoryCapacity(unittest.TestCase):
    def setUp(self):
        # Reset Singleton
        DatabaseManager._instance = None
        DatabaseManager._initialized = False

    def test_player_stats_capacity_formula(self):
        """Test formula: 10 + floor(STR * 0.5) + floor(DEX * 0.25)"""
        # Case 1: Base stats (1, 1) -> 10 + 0 + 0 = 10
        stats = PlayerStats(str_base=1, dex_base=1)
        self.assertEqual(stats.max_inventory_slots, 10)

        # Case 2: 10 STR, 10 DEX -> 10 + 5 + 2 = 17
        stats = PlayerStats(str_base=10, dex_base=10)
        self.assertEqual(stats.max_inventory_slots, 17)

        # Case 3: 20 STR, 4 DEX -> 10 + 10 + 1 = 21
        stats = PlayerStats(str_base=20, dex_base=4)
        self.assertEqual(stats.max_inventory_slots, 21)

        # Case 4: 9 STR (4.5->4), 3 DEX (0.75->0) -> 10 + 4 + 0 = 14
        stats = PlayerStats(str_base=9, dex_base=3)
        self.assertEqual(stats.max_inventory_slots, 14)

    @patch('database.database_manager.MongoClient')
    def test_calculate_inventory_limit(self, mock_mongo):
        """Test DB method delegates to PlayerStats correctly"""
        # Mock instance creation
        db = DatabaseManager()
        # Mock get_player_stats_json
        db.get_player_stats_json = MagicMock()

        # Test default fallback
        db.get_player_stats_json.return_value = {}
        self.assertEqual(db.calculate_inventory_limit(123), BASE_INVENTORY_SLOTS)

        # Test with stats
        stats_data = {"STR": {"base": 10, "bonus": 0}, "DEX": {"base": 10, "bonus": 0}}
        db.get_player_stats_json.return_value = stats_data

        # Should be 17
        self.assertEqual(db.calculate_inventory_limit(123), 17)

    @patch('database.database_manager.MongoClient')
    def test_add_inventory_item_capacity_check(self, mock_mongo):
        """Test add_inventory_item respects dynamic limit"""
        db = DatabaseManager()

        # We need to patch the methods on the instance, but add_inventory_item calls self.get_inventory_slot_count
        # Since we just created the instance, we can mock its methods directly.

        # Mock dependencies
        db.get_inventory_slot_count = MagicMock()
        db.calculate_inventory_limit = MagicMock()

        # Mock collection access (self._col)
        # self._col(name) returns a collection mock
        mock_col = MagicMock()
        db.db = MagicMock()
        db.db.__getitem__.return_value = mock_col
        # db._col is just a helper using db[name], so mocking db[...] works

        # However, add_inventory_item calls self.find_stackable_item
        db.find_stackable_item = MagicMock()

        # Setup 1: Limit 15, Used 15 -> Full
        db.calculate_inventory_limit.return_value = 15
        db.get_inventory_slot_count.return_value = 15

        # Try to add item (new stack)
        db.find_stackable_item.return_value = None

        # Result should be False
        result = db.add_inventory_item(123, "potion", "Potion", "consumable", "Common", 1)
        self.assertFalse(result)

        # Setup 2: Limit 15, Used 14 -> OK
        db.get_inventory_slot_count.return_value = 14

        # Mock counter update for ID generation
        # db._col("counters").find_one_and_update...
        # db.db["counters"].find_one_and_update
        mock_counters = MagicMock()
        mock_counters.find_one_and_update.return_value = {"seq": 100}

        # We need to make sure db._col returns different mocks for different collections or handle it
        # Actually simplest is just to patch _col method
        with patch.object(db, '_col') as mock_col_method:
             mock_col_method.return_value = MagicMock()
             mock_col_method.return_value.find_one_and_update.return_value = {"seq": 100}

             result = db.add_inventory_item(123, "potion", "Potion", "consumable", "Common", 1)
             self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
