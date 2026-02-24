import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.items.equipment_manager import EquipmentManager  # noqa: E402


class TestAccessorySlots(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock(spec=DatabaseManager)
        self.eq_manager = EquipmentManager(self.db)
        self.discord_id = 12345

        # Common Mocks
        self.db.get_player.return_value = {"class_id": 1, "level": 10}
        self.db.get_guild_rank.return_value = "F"
        self.db.get_player_stats_json.return_value = {}

        # Patch allowed slots check to always allow "accessory"
        self.eq_manager._get_player_allowed_slots = MagicMock(return_value=["accessory"])
        # Patch requirements check to always pass
        self.eq_manager.check_requirements = MagicMock(return_value=(True, None))

    def test_equip_first_accessory(self):
        """Test equipping the first accessory works normally."""
        # 0 equipped
        self.db.get_equipped_items.return_value = []

        # New item
        new_item = {
            "id": 101,
            "item_key": "ring_1",
            "slot": "accessory",
            "item_name": "Ring One",
            "rarity": "Common",
            "item_source_table": "equipment",
            "item_type": "equipment",
            "equipped": 0,
        }
        self.db.get_inventory_item.return_value = new_item

        # Mock set_item_equipped success
        self.db.set_item_equipped.return_value = None

        success, msg = self.eq_manager.equip_item(self.discord_id, 101)

        self.assertTrue(success)
        self.assertIn("Item equipped", msg)
        self.db.set_item_equipped.assert_called_with(101, 1)

    def test_equip_second_accessory(self):
        """Test equipping a second accessory is allowed."""
        # 1 equipped
        existing = {
            "id": 101,
            "item_key": "ring_1",
            "slot": "accessory",
            "item_name": "Ring One",
            "rarity": "Common",
            "item_source_table": "equipment",
            "equipped": 1,
        }
        self.db.get_equipped_items.return_value = [existing]

        # New item (different key)
        new_item = {
            "id": 102,
            "item_key": "ring_2",
            "slot": "accessory",
            "item_name": "Ring Two",
            "rarity": "Common",
            "item_source_table": "equipment",
            "item_type": "equipment",
            "equipped": 0,
        }
        self.db.get_inventory_item.return_value = new_item

        success, msg = self.eq_manager.equip_item(self.discord_id, 102)

        self.assertTrue(success)
        self.assertIn("Item equipped", msg)
        self.db.set_item_equipped.assert_called_with(102, 1)

    def test_equip_third_accessory_fails(self):
        """Test equipping a third accessory fails due to capacity."""
        # 2 equipped
        existing1 = {
            "id": 101,
            "item_key": "ring_1",
            "slot": "accessory",
            "item_name": "Ring One",
            "rarity": "Common",
            "equipped": 1,
        }
        existing2 = {
            "id": 102,
            "item_key": "ring_2",
            "slot": "accessory",
            "item_name": "Ring Two",
            "rarity": "Common",
            "equipped": 1,
        }
        self.db.get_equipped_items.return_value = [existing1, existing2]

        # New item
        new_item = {
            "id": 103,
            "item_key": "ring_3",
            "slot": "accessory",
            "item_name": "Ring Three",
            "rarity": "Common",
            "item_source_table": "equipment",
            "item_type": "equipment",
            "equipped": 0,
        }
        self.db.get_inventory_item.return_value = new_item

        success, msg = self.eq_manager.equip_item(self.discord_id, 103)

        self.assertFalse(success)
        self.assertIn("Accessory slots full", msg)
        # Should NOT have called set_item_equipped
        self.db.set_item_equipped.assert_not_called()

    def test_equip_duplicate_accessory_fails(self):
        """Test equipping a duplicate accessory key fails."""
        # 1 equipped
        existing = {
            "id": 101,
            "item_key": "ring_1",
            "slot": "accessory",
            "item_name": "Ring One",
            "rarity": "Common",
            "equipped": 1,
        }
        self.db.get_equipped_items.return_value = [existing]

        # New item (same key "ring_1")
        new_item = {
            "id": 102,
            "item_key": "ring_1",
            "slot": "accessory",
            "item_name": "Ring One (Copy)",
            "rarity": "Common",
            "item_source_table": "equipment",
            "item_type": "equipment",
            "equipped": 0,
        }
        self.db.get_inventory_item.return_value = new_item

        success, msg = self.eq_manager.equip_item(self.discord_id, 102)

        self.assertFalse(success)
        self.assertIn("cannot equip two of the same accessory", msg)

    def test_save_loadout_multi_accessory(self):
        """Test saving loadout handles multiple accessories correctly."""
        acc1 = {
            "id": 101,
            "item_key": "ring_1",
            "slot": "accessory",
            "item_name": "Ring One",
            "rarity": "Common",
            "equipped": 1,
        }
        acc2 = {
            "id": 102,
            "item_key": "ring_2",
            "slot": "accessory",
            "item_name": "Ring Two",
            "rarity": "Common",
            "equipped": 1,
        }
        self.db.get_equipped_items.return_value = [acc1, acc2]

        self.eq_manager.save_loadout(self.discord_id, "MultiRing")

        # Check arguments to save_equipment_set
        args = self.db.save_equipment_set.call_args
        self.assertIsNotNone(args)
        items_dict = args[0][2]

        # Should have accessory_1 and accessory_2 keys
        self.assertIn("accessory_1", items_dict)
        self.assertIn("accessory_2", items_dict)
        self.assertEqual(items_dict["accessory_1"]["item_key"], "ring_1")
        self.assertEqual(items_dict["accessory_2"]["item_key"], "ring_2")

    def test_equip_loadout_multi_accessory(self):
        """Test equipping loadout handles multiple accessories correctly."""
        # Loadout data
        loadout_items = {
            "accessory_1": {"item_key": "ring_1", "rarity": "Common", "item_name": "Ring One", "slot": "accessory"},
            "accessory_2": {"item_key": "ring_2", "rarity": "Common", "item_name": "Ring Two", "slot": "accessory"},
        }
        self.db.get_equipment_set.return_value = {"items": loadout_items}

        # Currently 0 equipped
        self.db.get_equipped_items.return_value = []

        # Inventory search results (find_one)
        # We need side_effect to return different items for different calls
        # Call 1: ring_1 -> returns Item 101
        # Call 2: ring_2 -> returns Item 102

        item101 = {"id": 101, "item_key": "ring_1", "slot": "accessory"}
        item102 = {"id": 102, "item_key": "ring_2", "slot": "accessory"}

        def find_side_effect(query, projection=None):
            if query.get("item_key") == "ring_1":
                return item101
            if query.get("item_key") == "ring_2":
                return item102
            return None

        self.db._col.return_value.find_one.side_effect = find_side_effect

        # Mock equip_item to succeed for both calls
        # We need to ensure equip_item doesn't use get_equipped_items from the mock that returns [] forever
        # But equip_item calls get_equipped_items internally.
        # This makes testing complex because equip_item relies on DB state.
        # We can mock equip_item directly for this test since we tested equip_item separately.

        with patch.object(self.eq_manager, "equip_item", return_value=(True, "Equipped")) as mock_equip:
            success, msg = self.eq_manager.equip_loadout(self.discord_id, "MultiRing")

            self.assertTrue(success)
            self.assertIn("Equipped 2 items", msg)

            # Verify calls
            # Call 1: ID 101
            # Call 2: ID 102
            calls = mock_equip.call_args_list
            ids = sorted([c[0][1] for c in calls])
            self.assertEqual(ids, [101, 102])


if __name__ == "__main__":
    unittest.main()
