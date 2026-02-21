import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(os.getcwd())


class TestShopTransactionFailure(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock Pymongo
        mock_pymongo = MagicMock()
        mock_pymongo.errors = MagicMock()
        sys.modules["pymongo"] = mock_pymongo
        sys.modules["pymongo.errors"] = mock_pymongo.errors

        # Mock Discord
        mock_discord = MagicMock()
        sys.modules["discord"] = mock_discord
        sys.modules["discord.ext"] = MagicMock()
        sys.modules["discord.ui"] = MagicMock()

        # Import module under test
        import database.database_manager

        importlib.reload(database.database_manager)

        self.DatabaseManager = database.database_manager.DatabaseManager

        # Mock MongoClient
        self.mock_client = MagicMock()
        self.mock_db = MagicMock()

        # When client['db_name'] is accessed, return mock_db
        self.mock_client.__getitem__.return_value = self.mock_db

        # Setup mock db to return mocks for collection access via attribute
        # e.g. db.players -> MagicMock
        def get_collection(name):
            return getattr(self.mock_db, name)

        self.mock_db.__getitem__.side_effect = get_collection

        # Patch MongoClient
        self.patcher = patch("database.database_manager.MongoClient", return_value=self.mock_client)
        self.patcher.start()

        # Reset Singleton
        self.DatabaseManager._instance = None
        self.db = self.DatabaseManager()

    def tearDown(self):
        self.patcher.stop()
        self.modules_patcher.stop()
        if hasattr(self, "DatabaseManager"):
            self.DatabaseManager._instance = None

    def test_purchase_item_refunds_on_inventory_failure(self):
        """
        Verify that if item addition fails after gold deduction,
        the gold is refunded.
        """
        user_id = 12345
        item_key = "potion_hp"
        price = 50
        item_data = {"name": "Health Potion", "rarity": "Common"}

        # 1. Mock deduct_aurum to SUCCEED
        # Note: We assign it to the instance directly
        # The real method calls find_one_and_update
        self.db.deduct_aurum = MagicMock(return_value=50)  # Assuming new balance 50

        # 2. Mock inventory failure
        # In the FIXED version, we expect add_inventory_item to be called.
        # But in the BROKEN version, purchase_item uses manual logic.
        # So we mock the underlying collection method to simulate failure.

        # purchase_item calls find_one then update_one/insert_one on inventory
        # Let's mock find_one -> None (new item path)
        self.mock_db.inventory.find_one.return_value = None

        # Mock insert_one -> RAISE EXCEPTION
        self.mock_db.inventory.insert_one.side_effect = Exception("DB Insert Failed")

        # Also mock add_inventory_item to fail IF it's called (future proofing)
        self.db.add_inventory_item = MagicMock(side_effect=Exception("DB Insert Failed"))

        # Mock counters (needed for insert path in original impl)
        self.mock_db.counters.find_one_and_update.return_value = {"seq": 99}

        # Mock players collection for refund verification
        self.mock_db.players.update_one = MagicMock()

        # 3. Call purchase_item
        # This should fail if inventory insert fails
        try:
            success, result, new_aurum = self.db.purchase_item(user_id, item_key, item_data, price)
        except Exception:
            # If it raises exception instead of returning failure, catch it
            success = False
            result = "Exception"

        # 4. Verify Failure
        self.assertFalse(success, "Purchase should fail if inventory add fails")
        # In current code, it might catch exception and return "System error" or similar?
        # But it WON'T refund.

        # 5. Verify REFUND
        # Check if players.update_one was called to refund the gold
        # We look for ANY call with $inc: {aurum: price}

        calls = self.mock_db.players.update_one.call_args_list
        refund_called = False
        for call in calls:
            args, _ = call
            if not args:
                continue
            query, update = args
            if query.get("discord_id") == user_id and update.get("$inc", {}).get("aurum") == price:
                refund_called = True
                break

        self.assertTrue(refund_called, "Gold should be refunded on inventory failure")


if __name__ == "__main__":
    unittest.main()
