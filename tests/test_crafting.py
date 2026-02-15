"""
test_crafting.py

Tests for:
1. DatabaseManager.get_inventory_item_count
2. DatabaseManager.remove_inventory_item
3. CraftingSystem
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager
from game_systems.crafting.crafting_system import CraftingSystem


class TestDatabaseEnhancements(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_db = MagicMock()
        self.mock_client.__getitem__.return_value = self.mock_db

        # Bridge collection access
        def get_collection(name):
            return getattr(self.mock_db, name)
        self.mock_db.__getitem__.side_effect = get_collection

        patcher = patch("database.database_manager.MongoClient", return_value=self.mock_client)
        patcher.start()
        self.addCleanup(patcher.stop)

        DatabaseManager._instance = None
        self.db = DatabaseManager()

    def test_get_inventory_item_count(self):
        # Mock aggregation result
        self.mock_db.inventory.aggregate.return_value = [{"total": 10}]

        count = self.db.get_inventory_item_count(12345, "herb")
        self.assertEqual(count, 10)
        self.mock_db.inventory.aggregate.assert_called()

    def test_remove_inventory_item_success(self):
        # Mock total count check
        self.mock_db.inventory.aggregate.return_value = [{"total": 10}]

        # Mock stacks: 2 stacks of 5
        self.mock_db.inventory.find.return_value.sort.return_value = [
            {"id": 1, "count": 5},
            {"id": 2, "count": 5}
        ]

        # Remove 7
        success = self.db.remove_inventory_item(12345, "herb", 7)
        self.assertTrue(success)

        # Should delete first stack (5 consumed)
        self.mock_db.inventory.delete_one.assert_called_with({"id": 1})
        # Should update second stack (2 consumed, 3 remaining)
        self.mock_db.inventory.update_one.assert_called_with({"id": 2}, {"$inc": {"count": -2}})

    def test_remove_inventory_item_fail_insufficient(self):
        self.mock_db.inventory.aggregate.return_value = [{"total": 5}]

        success = self.db.remove_inventory_item(12345, "herb", 10)
        self.assertFalse(success)


class TestCraftingSystem(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock(spec=DatabaseManager)
        self.crafting = CraftingSystem(self.db)
        self.discord_id = 12345

    def test_get_recipes(self):
        recipes = self.crafting.get_recipes(self.discord_id)
        self.assertIn("hp_potion_1", recipes)

    def test_can_craft_success(self):
        self.db.get_player.return_value = {"aurum": 100}
        self.db.get_inventory_item_count.return_value = 10

        can, msg = self.crafting.can_craft(self.discord_id, "hp_potion_1")
        self.assertTrue(can)

    def test_craft_item_success(self):
        self.db.get_player.return_value = {"aurum": 100}
        self.db.get_inventory_item_count.return_value = 10
        self.db.remove_inventory_item.return_value = True

        success, msg, item = self.crafting.craft_item(self.discord_id, "hp_potion_1")

        self.assertTrue(success)
        self.db.increment_player_fields.assert_called()
        self.db.remove_inventory_item.assert_called()
        self.db.add_inventory_item.assert_called()

if __name__ == "__main__":
    unittest.main()
