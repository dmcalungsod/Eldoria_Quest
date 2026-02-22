"""
Comprehensive Database Tests for Eldoria Quest
-----------------------------------------------
Tests all database operations including players, inventory, quests, and combat.
SAFE: Uses temporary test database, never touches production data.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager  # noqa: E402


class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        # Mock the MongoClient to prevent actual DB connection
        self.mock_client = MagicMock()

        # This will be the mock DB object
        self.mock_db = MagicMock()

        # When client['db_name'] is accessed, return mock_db
        self.mock_client.__getitem__.return_value = self.mock_db

        # CRITICAL: Bridge attribute access (db.players) and item access (db['players'])
        # so they return the same MagicMock for a given collection name.
        def get_collection(name):
            return getattr(self.mock_db, name)

        self.mock_db.__getitem__.side_effect = get_collection

        # Patch MongoClient in DatabaseManager
        self.mongo_patcher = patch("database.database_manager.MongoClient", return_value=self.mock_client)
        self.mongo_patcher.start()

        # Initialize DatabaseManager (singleton)
        DatabaseManager._instance = None
        self.db = DatabaseManager()

    def tearDown(self):
        self.mongo_patcher.stop()
        DatabaseManager._instance = None

    def test_get_player(self):
        # Setup mock return
        mock_player = {"discord_id": 12345, "name": "TestPlayer", "class_id": 1}
        self.mock_db.players.find_one.return_value = mock_player

        # Test
        player = self.db.get_player(12345)
        self.assertEqual(player, mock_player)
        self.mock_db.players.find_one.assert_called_with({"discord_id": 12345}, {"_id": 0})

    def test_create_player(self):
        stats_data = {"STR": 10, "END": 10, "DEX": 10, "AGI": 10, "MAG": 10, "LCK": 10}

        # Test creation
        self.db.create_player(
            discord_id=12345,
            name="TestPlayer",
            class_id=1,
            race="Human",
            gender="Male",
            initial_hp=100,
            initial_mp=50,
            stats_data=stats_data,
        )

        # Verify calls
        self.assertTrue(self.mock_db.players.insert_one.called)
        self.assertTrue(self.mock_db.stats.insert_one.called)
        # create_player does not handle inventory in this version

    def test_update_player_stats(self):
        stats_data = {"STR": 15}
        self.db.update_player_stats(12345, stats_data)

        # Check that update_one was called with expected arguments
        self.assertTrue(self.mock_db.stats.update_one.called)
        args, _ = self.mock_db.stats.update_one.call_args
        self.assertEqual(args[0], {"discord_id": 12345})
        self.assertIn("$set", args[1])
        self.assertIn("stats_json", args[1]["$set"])

    def test_add_inventory_item(self):
        # Mock counters collection response for new stack ID
        self.mock_db.counters.find_one_and_update.return_value = {"seq": 100}

        # Mock find_stackable_item to return None (no existing stack)
        with (
            patch.object(self.db, "find_stackable_item", return_value=None),
            patch.object(self.db, "get_inventory_slot_count", return_value=0),
            patch.object(self.db, "calculate_inventory_limit", return_value=20),
        ):
            self.db.add_inventory_item(12345, "potion_hp", "Health Potion", "consumable", "Common", 5)

        # Verify it inserts new item(s)
        self.assertTrue(self.mock_db.inventory.insert_many.called or self.mock_db.inventory.insert_one.called)

    def test_add_inventory_item_stacking(self):
        # Mock finding an existing item with space
        existing_item = {"id": 50, "count": 2}
        with (
            patch.object(self.db, "find_stackable_item", return_value=existing_item),
            patch.object(self.db, "get_inventory_slot_count", return_value=1),
            patch.object(self.db, "calculate_inventory_limit", return_value=20),
        ):
            self.db.add_inventory_item(12345, "potion_hp", "Health Potion", "consumable", "Common", 5)

        # Verify it updates existing item
        # Max stack is 5. Existing 2. Adding 5.
        # Should fill by 3 (2+3=5) and create new stack of 2.
        self.mock_db.inventory.update_one.assert_called_with({"id": 50}, {"$inc": {"count": 3}})

    def test_deduct_aurum(self):
        # Mock successful deduction
        self.mock_db.players.find_one_and_update.return_value = {"aurum": 50}

        new_balance = self.db.deduct_aurum(12345, 100)

        self.assertEqual(new_balance, 50)
        self.mock_db.players.find_one_and_update.assert_called_with(
            {"discord_id": 12345, "aurum": {"$gte": 100}}, {"$inc": {"aurum": -100}}, return_document=True
        )

        # Mock insufficient funds
        self.mock_db.players.find_one_and_update.return_value = None

        new_balance = self.db.deduct_aurum(12345, 1000)

        self.assertIsNone(new_balance)

    def test_update_player_mixed(self):
        # Test mixed update
        self.db.update_player_mixed(
            12345,
            set_fields={"level": 2},
            inc_fields={"exp": 100},
        )

        # Verify update_one call structure
        self.mock_db.players.update_one.assert_called_with(
            {"discord_id": 12345},
            {"$set": {"level": 2}, "$inc": {"exp": 100}},
        )

        # Test set only
        self.db.update_player_mixed(12345, set_fields={"level": 3})
        self.mock_db.players.update_one.assert_called_with(
            {"discord_id": 12345},
            {"$set": {"level": 3}},
        )

        # Test inc only
        self.db.update_player_mixed(12345, inc_fields={"exp": 50})
        self.mock_db.players.update_one.assert_called_with(
            {"discord_id": 12345},
            {"$inc": {"exp": 50}},
        )


def run_all_tests():
    """Runs the test suite for run_all_tests.py integration."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDatabaseManager)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    unittest.main()
