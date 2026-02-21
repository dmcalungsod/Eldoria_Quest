import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock sys.modules for pymongo before importing DatabaseManager
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.MongoClient"] = MagicMock()
sys.modules["pymongo.UpdateOne"] = MagicMock()
sys.modules["pymongo.InsertOne"] = MagicMock()

from database.database_manager import MAX_STACK_CONSUMABLE, DatabaseManager  # noqa: E402


class TestStackLimits(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager()
        self.db.db = MagicMock()
        self.db._col = MagicMock()
        self.inventory_col = MagicMock()
        self.counters_col = MagicMock()

        def col_side_effect(name):
            if name == "inventory":
                return self.inventory_col
            if name == "counters":
                return self.counters_col
            return MagicMock()

        self.db._col.side_effect = col_side_effect
        self.discord_id = 12345

        # Reset mocks
        self.inventory_col.reset_mock()
        self.counters_col.reset_mock()

    def test_consumable_overflow_creates_new_stack(self):
        # Scenario: Add 25 potions (MAX=20).
        # Existing stack: None.
        # Expectation: 1 stack of 20, 1 stack of 5.

        # Mocks
        self.inventory_col.find_one.return_value = None
        self.inventory_col.count_documents.return_value = 0
        self.counters_col.find_one_and_update.return_value = {"seq": 100}

        success = self.db.add_inventory_item(self.discord_id, "hp_potion", "Potion", "consumable", "Common", 25)

        self.assertTrue(success)

        # Check find_stackable_item call
        self.inventory_col.find_one.assert_called()
        args, kwargs = self.inventory_col.find_one.call_args
        query = args[0]
        self.assertIn("count", query)
        self.assertEqual(query["count"], {"$lt": MAX_STACK_CONSUMABLE})

        # Check insert_many call
        self.inventory_col.insert_many.assert_called_once()
        args, _ = self.inventory_col.insert_many.call_args
        inserted_docs = args[0]
        self.assertEqual(len(inserted_docs), 2)
        self.assertEqual(inserted_docs[0]["count"], 20)
        self.assertEqual(inserted_docs[1]["count"], 5)

    def test_fill_existing_stack_then_overflow(self):
        # Scenario: Add 10 potions. Existing stack has 15 (MAX=20).
        # Expectation: Fill existing to 20 (+5), Create new stack of 5.

        existing_stack = {"id": 10, "count": 15}
        self.inventory_col.find_one.return_value = existing_stack
        self.inventory_col.count_documents.return_value = 1
        self.counters_col.find_one_and_update.return_value = {"seq": 100}

        success = self.db.add_inventory_item(self.discord_id, "hp_potion", "Potion", "consumable", "Common", 10)

        self.assertTrue(success)

        self.inventory_col.update_one.assert_called_with({"id": 10}, {"$inc": {"count": 5}})

        self.inventory_col.insert_many.assert_called_once()
        inserted_docs = self.inventory_col.insert_many.call_args[0][0]
        self.assertEqual(len(inserted_docs), 1)
        self.assertEqual(inserted_docs[0]["count"], 5)

    def test_inventory_full_on_overflow(self):
        # Scenario: Add 25 potions. No existing stack.
        # Inventory is ALMOST full (19/20 slots).
        # Need 2 slots (20, 5). Only 1 available.
        # Expectation: Fail. No changes.

        self.inventory_col.find_one.return_value = None
        self.inventory_col.count_documents.return_value = 19

        success = self.db.add_inventory_item(self.discord_id, "hp_potion", "Potion", "consumable", "Common", 25)

        self.assertFalse(success)
        self.inventory_col.insert_many.assert_not_called()
        self.inventory_col.update_one.assert_not_called()

    def test_equipment_no_stack(self):
        # Scenario: Add 2 Swords. MAX_EQUIPMENT=1.
        # Expectation: 2 separate stacks of 1.

        self.inventory_col.find_one.return_value = None
        self.inventory_col.count_documents.return_value = 0
        self.counters_col.find_one_and_update.return_value = {"seq": 100}

        success = self.db.add_inventory_item(self.discord_id, "sword", "Sword", "equipment", "Common", 2)

        self.assertTrue(success)

        self.inventory_col.insert_many.assert_called_once()
        inserted_docs = self.inventory_col.insert_many.call_args[0][0]
        self.assertEqual(len(inserted_docs), 2)
        self.assertEqual(inserted_docs[0]["count"], 1)
        self.assertEqual(inserted_docs[1]["count"], 1)

    @patch("database.database_manager.UpdateOne")
    @patch("database.database_manager.InsertOne")
    def test_bulk_add_distribution(self, MockInsertOne, MockUpdateOne):
        # Scenario: Bulk add 30 potions. Existing stack of 10. MAX=20.
        # Total 40. Existing(10) -> Full(20). New(20).

        items = [
            {
                "item_key": "hp_potion",
                "item_name": "Potion",
                "item_type": "consumable",
                "rarity": "Common",
                "amount": 30,
            }
        ]

        # Mock find returning existing stack
        existing_doc = {"id": 50, "count": 10, "item_key": "hp_potion", "rarity": "Common", "equipped": 0}

        # Mock find().sort() chain
        cursor = MagicMock()
        cursor.sort.return_value = [existing_doc]  # Sort ASC by count
        self.inventory_col.find.return_value = cursor

        self.inventory_col.count_documents.return_value = 1  # 1 slot used
        self.counters_col.find_one_and_update.return_value = {"seq": 200}

        failed = self.db.add_inventory_items_bulk(self.discord_id, items)

        self.assertEqual(len(failed), 0)

        self.inventory_col.bulk_write.assert_called_once()
        ops = self.inventory_col.bulk_write.call_args[0][0]
        self.assertEqual(len(ops), 2)

        # Check UpdateOne call
        MockUpdateOne.assert_called_with({"id": 50}, {"$inc": {"count": 10}})

        # Check InsertOne call
        insert_call = MockInsertOne.call_args
        doc = insert_call[0][0]
        self.assertEqual(doc["count"], 20)
        self.assertEqual(doc["item_key"], "hp_potion")


if __name__ == "__main__":
    unittest.main()
