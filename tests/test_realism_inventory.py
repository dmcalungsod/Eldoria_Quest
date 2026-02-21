import unittest
from unittest.mock import MagicMock, patch
import sys
import json

# Mock sys.modules for pymongo before importing DatabaseManager
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.MongoClient"] = MagicMock()
sys.modules["pymongo.UpdateOne"] = MagicMock()
sys.modules["pymongo.InsertOne"] = MagicMock()

# Now we can import
from database.database_manager import DatabaseManager
from game_systems.items.inventory_manager import InventoryManager

class TestRealismInventory(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager()
        # Mock the collection
        self.db.db = MagicMock()
        self.db._col = MagicMock()
        self.inventory_col = MagicMock()
        self.players_col = MagicMock()
        self.counters_col = MagicMock()

        def col_side_effect(name):
            if name == "inventory": return self.inventory_col
            if name == "players": return self.players_col
            if name == "counters": return self.counters_col
            return MagicMock()

        self.db._col.side_effect = col_side_effect

        self.inv_manager = InventoryManager(self.db)
        self.discord_id = 12345

    def test_inventory_limit_logic(self):
        # 1. Mock DB to report 20 slots
        with patch.object(self.db, 'get_inventory_slot_count', return_value=20):
            # 2. Try adding new unique item
            with patch.object(self.db, 'find_stackable_item', return_value=None):
                success = self.inv_manager.add_item(
                    self.discord_id, "new_item", "New Item", "material", "Common", 1
                )
                self.assertFalse(success, "Should fail when inventory is full")

        # 3. Mock DB to report 19 slots
        with patch.object(self.db, 'get_inventory_slot_count', return_value=19):
            with patch.object(self.db, 'find_stackable_item', return_value=None):
                 # Should succeed
                 with patch.object(self.db, '_next_inventory_id', return_value=999):
                    success = self.inv_manager.add_item(
                        self.discord_id, "new_item_2", "New Item 2", "material", "Common", 1
                    )
                    self.assertTrue(success, "Should succeed when space available")

    def test_add_items_bulk_limit(self):
        # Mock 18 slots used (MAX=20)
        with patch.object(self.db, 'get_inventory_slot_count', return_value=18):
            items = [
                {"item_key": "k1", "rarity": "Common", "amount": 1, "item_name": "I1", "item_type": "material"}, # New (19)
                {"item_key": "k2", "rarity": "Common", "amount": 1, "item_name": "I2", "item_type": "material"}, # New (20)
                {"item_key": "k3", "rarity": "Common", "amount": 1, "item_name": "I3", "item_type": "material"}, # New (Fail)
            ]

            # Mock find (existing stacks) to return empty
            self.inventory_col.find.return_value = []

            # Mock bulk_write
            self.inventory_col.bulk_write.return_value = MagicMock()

            # Mock counters
            self.counters_col.find_one_and_update.return_value = {"seq": 100}

            failed = self.inv_manager.add_items_bulk(self.discord_id, items)

            self.assertEqual(len(failed), 1, "Should have 1 failed item")
            self.assertEqual(failed[0]["item_key"], "k3")

    def test_purchase_item_full(self):
        # Mock full inventory
        with patch.object(self.db, 'get_inventory_slot_count', return_value=20):
            with patch.object(self.db, 'find_stackable_item', return_value=None):
                # Mock balance check
                with patch.object(self.db, 'deduct_aurum', return_value=100):
                    # Mock refund
                    self.players_col.update_one = MagicMock()

                    success, msg, bal = self.db.purchase_item(
                        self.discord_id, "shop_item", {"name": "Shop Item", "rarity": "Common"}, 10
                    )

                    self.assertFalse(success)
                    self.assertEqual(msg, "Inventory Full.")
                    self.assertEqual(bal, 110) # 100 + 10 Refunded

if __name__ == '__main__':
    unittest.main()
