"""
test_equipment_sets.py

Tests for Equipment Sets / Loadouts.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.items.equipment_manager import EquipmentManager  # noqa: E402


class TestEquipmentSets(unittest.TestCase):
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
        self.eq_manager = EquipmentManager(self.db)
        self.discord_id = 12345

    def test_save_loadout_success(self):
        # Mock equipped items
        self.mock_db.inventory.find.return_value = [
            {
                "id": 1,
                "slot": "sword",
                "item_key": "iron_sword",
                "rarity": "Common",
                "item_name": "Iron Sword",
                "item_source_table": "equipment",
                "equipped": 1,
            }
        ]

        success, msg = self.eq_manager.save_loadout(self.discord_id, "Battle Set")

        self.assertTrue(success)
        self.assertIn("saved", msg)

        # Check DB update
        self.mock_db.equipment_sets.update_one.assert_called()
        call_args = self.mock_db.equipment_sets.update_one.call_args
        self.assertEqual(call_args[0][0], {"discord_id": self.discord_id, "name": "Battle Set"})
        self.assertIn("items", call_args[0][1]["$set"])
        self.assertIn("sword", call_args[0][1]["$set"]["items"])

    def test_save_loadout_empty_fail(self):
        # Mock no items
        self.mock_db.inventory.find.return_value = []

        success, msg = self.eq_manager.save_loadout(self.discord_id, "Empty Set")

        self.assertFalse(success)
        self.assertIn("No items", msg)

    def test_equip_loadout_success(self):
        # Mock loadout
        self.mock_db.equipment_sets.find_one.return_value = {
            "name": "Battle Set",
            "items": {"sword": {"item_key": "iron_sword", "rarity": "Common", "item_name": "Iron Sword"}},
        }

        # Mock currently equipped (empty)
        # We need to mock find_one explicitly since we used it in equip_loadout logic
        self.mock_db.inventory.find.return_value = []  # for get_equipped_items

        self.mock_db.inventory.find_one.return_value = {
            "id": 10,
            "item_key": "iron_sword",
            "rarity": "Common",
            "item_name": "Iron Sword",
        }

        # Mock equip_item success
        with patch.object(self.eq_manager, "equip_item", return_value=(True, "Equipped")) as mock_equip:
            success, msg = self.eq_manager.equip_loadout(self.discord_id, "Battle Set")

            self.assertTrue(success)
            self.assertIn("Equipped 1 items", msg)
            mock_equip.assert_called_with(self.discord_id, 10)

    def test_equip_loadout_missing_item(self):
        # Mock loadout
        self.mock_db.equipment_sets.find_one.return_value = {
            "name": "Battle Set",
            "items": {"sword": {"item_key": "god_slayer", "rarity": "Mythical", "item_name": "God Slayer"}},
        }

        self.mock_db.inventory.find.return_value = []  # No equipped
        self.mock_db.inventory.find_one.return_value = None  # Not found in inventory

        success, msg = self.eq_manager.equip_loadout(self.discord_id, "Battle Set")

        self.assertTrue(success)  # Operation is success, but reports missing
        self.assertIn("Missing/Failed", msg)
        self.assertIn("God Slayer", msg)

    def test_delete_loadout(self):
        self.eq_manager.delete_loadout(self.discord_id, "Old Set")
        self.mock_db.equipment_sets.delete_one.assert_called_with({"discord_id": self.discord_id, "name": "Old Set"})


if __name__ == "__main__":
    unittest.main()
