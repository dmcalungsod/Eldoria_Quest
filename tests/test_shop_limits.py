import datetime
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Fix path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock modules before import
mock_pymongo = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["discord"] = MagicMock()

from database.database_manager import DatabaseManager
from game_systems.core.world_time import WorldTime


class TestShopLimits(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_db = MagicMock()
        self.mock_client.__getitem__.return_value = self.mock_db

        # Configure mock_db to return attributes when indexed
        # This handles self.db['collection_name'] calls
        def get_collection(name):
            return getattr(self.mock_db, name)

        self.mock_db.__getitem__.side_effect = get_collection

        # Patch MongoClient
        patcher = patch("database.database_manager.MongoClient", return_value=self.mock_client)
        self.patcher = patcher.start()

        # Reset Singleton
        DatabaseManager._instance = None
        self.db = DatabaseManager()

        # Mock collections
        self.players = self.mock_db.players
        self.inventory = self.mock_db.inventory

    def tearDown(self):
        self.patcher.stop()
        DatabaseManager._instance = None

    def test_get_shop_daily_count_reset(self):
        """Verify that get_shop_daily_count returns empty dict if date mismatches."""
        user_id = 123
        today = WorldTime.now().date().isoformat()
        yesterday = (WorldTime.now() - datetime.timedelta(days=1)).date().isoformat()

        # Case 1: Old date
        self.players.find_one.return_value = {"shop_daily": {"date": yesterday, "counts": {"potion": 5}}}

        counts = self.db.get_shop_daily_count(user_id)
        self.assertEqual(counts, {}, "Should return empty dict for old date")

        # Case 2: Today's date
        self.players.find_one.return_value = {"shop_daily": {"date": today, "counts": {"potion": 2}}}

        counts = self.db.get_shop_daily_count(user_id)
        self.assertEqual(counts, {"potion": 2}, "Should return counts for today")

    def test_purchase_enforces_limit(self):
        """Verify purchase_item blocks transaction if limit reached."""
        user_id = 123
        item = "potion"
        limit = 3
        item_data = {"name": "Potion", "type": "consumable", "rarity": "Common"}

        # Mock daily count to limit
        with patch.object(self.db, "get_shop_daily_count", return_value={"potion": 3}):
            success, msg, _ = self.db.purchase_item(user_id, item, item_data, 10, daily_limit=limit)

            self.assertFalse(success)
            self.assertEqual(msg, "Daily limit reached.")
            # Verify no deduction or add
            self.players.find_one_and_update.assert_not_called()

    def test_purchase_increments_count(self):
        """Verify purchase_item increments count on success."""
        user_id = 123
        item = "potion"
        limit = 3
        item_data = {"name": "Potion", "type": "consumable", "rarity": "Common"}

        # Mock daily count below limit
        with patch.object(self.db, "get_shop_daily_count", return_value={"potion": 2}):
            # Mock success path
            with patch.object(self.db, "deduct_aurum", return_value=100):
                with patch.object(self.db, "add_inventory_item", return_value=True):
                    with patch.object(self.db, "increment_shop_daily_count") as mock_inc:
                        success, _, _ = self.db.purchase_item(user_id, item, item_data, 10, daily_limit=limit)

                        self.assertTrue(success)
                        mock_inc.assert_called_once_with(user_id, item, 1)

    def test_purchase_refund_no_increment(self):
        """Verify failure (inventory full) does NOT increment count."""
        user_id = 123
        item = "potion"
        limit = 3
        item_data = {"name": "Potion", "type": "consumable", "rarity": "Common"}

        with patch.object(self.db, "get_shop_daily_count", return_value={"potion": 0}):
            # Mock deduction success
            with patch.object(self.db, "deduct_aurum", return_value=100):
                # Mock inventory FULL failure
                with patch.object(self.db, "add_inventory_item", return_value=False):
                    with patch.object(self.db, "increment_shop_daily_count") as mock_inc:
                        success, msg, _ = self.db.purchase_item(user_id, item, item_data, 10, daily_limit=limit)

                        self.assertFalse(success)
                        self.assertIn("Inventory Full", msg)
                        mock_inc.assert_not_called()


if __name__ == "__main__":
    unittest.main()
