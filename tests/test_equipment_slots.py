import sys
import unittest
from unittest.mock import MagicMock

# Mock pymongo before importing modules that use it
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from game_systems.items.equipment_manager import EquipmentManager  # noqa: E402


class TestEquipmentSlots(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.manager = EquipmentManager(self.mock_db)

        # Setup common mock returns
        self.mock_db.get_player_field.return_value = 2  # Class ID 2 (Mage)
        self.mock_db.get_player.return_value = {"class_id": 2, "level": 10, "name": "MagePlayer"}
        self.mock_db.get_guild_rank.return_value = "A"

        # Mage allowed slots (including new 'wand')
        # We need to ensure _get_player_allowed_slots returns correctly in the test environment
        # But wait, EquipmentManager imports CLASSES from game_systems.data.class_data
        # which we modified. Python should load the modified file.

        # Mocking items
        self.wand = {
            "id": 101,
            "item_key": "gen_wand_001",
            "item_name": "Apprentice Wand",
            "item_type": "equipment",
            "slot": "wand",
            "rarity": "Common",
            "equipped": 0,
            "count": 1,
        }
        self.orb = {
            "id": 102,
            "item_key": "gen_orb_001",
            "item_name": "Basic Orb",
            "item_type": "equipment",
            "slot": "orb",
            "rarity": "Common",
            "equipped": 0,
            "count": 1,
        }
        self.staff = {
            "id": 103,
            "item_key": "gen_staff_001",
            "item_name": "Gnarled Staff",
            "item_type": "equipment",
            "slot": "staff",
            "rarity": "Common",
            "equipped": 0,
            "count": 1,
        }

        self.inventory = {101: self.wand, 102: self.orb, 103: self.staff}

        self.mock_db.get_inventory_item.side_effect = lambda uid, iid: self.inventory.get(iid)

        # Mock recalculate and check_requirements
        self.manager.recalculate_player_stats = MagicMock()
        self.manager.check_requirements = MagicMock(return_value=(True, None))

        # Mock _unequip_logic to just update our local inventory state for tracking
        def mock_unequip(uid, iid):
            if iid in self.inventory:
                self.inventory[iid]["equipped"] = 0

        self.manager._unequip_logic = MagicMock(side_effect=mock_unequip)

        # Mock set_item_equipped
        def mock_equip(iid, val):
            if iid in self.inventory:
                self.inventory[iid]["equipped"] = val

        self.mock_db.set_item_equipped.side_effect = mock_equip

    def test_wand_and_orb_coexist(self):
        # 1. Equip Wand
        self.mock_db.get_equipped_items.return_value = []
        self.manager.equip_item(1, 101)
        self.inventory[101]["equipped"] = 1

        # 2. Equip Orb
        self.mock_db.get_equipped_items.return_value = [self.inventory[101]]
        success, msg = self.manager.equip_item(1, 102)

        self.assertTrue(success)
        self.assertEqual(self.inventory[101]["equipped"], 1, "Wand should remain equipped")
        # Note: In real DB, set_item_equipped would be called.
        # But our test doesn't actually update the list returned by get_equipped_items unless we manage state carefully.
        # But 'manager.equip_item' logic calls '_unequip_logic' if conflict.
        # Here, no conflict expected.
        self.manager._unequip_logic.assert_not_called()

    def test_staff_unequips_wand_and_orb(self):
        # Setup: Wand and Orb equipped
        self.inventory[101]["equipped"] = 1
        self.inventory[102]["equipped"] = 1
        self.mock_db.get_equipped_items.return_value = [self.inventory[101], self.inventory[102]]

        # Equip Staff
        success, msg = self.manager.equip_item(1, 103)

        self.assertTrue(success)
        # Should have called unequip for 101 and 102
        self.manager._unequip_logic.assert_any_call(1, 101)
        self.manager._unequip_logic.assert_any_call(1, 102)
        self.assertIn("Unequipped Apprentice Wand", msg)
        self.assertIn("Unequipped Basic Orb", msg)

    def test_wand_unequips_staff(self):
        # Setup: Staff equipped
        self.inventory[103]["equipped"] = 1
        self.mock_db.get_equipped_items.return_value = [self.inventory[103]]

        # Equip Wand
        success, msg = self.manager.equip_item(1, 101)

        self.assertTrue(success)
        self.manager._unequip_logic.assert_called_with(1, 103)
        self.assertIn("Unequipped Gnarled Staff", msg)

    def test_orb_unequips_staff(self):
        # Setup: Staff equipped
        self.inventory[103]["equipped"] = 1
        self.mock_db.get_equipped_items.return_value = [self.inventory[103]]

        # Equip Orb
        success, msg = self.manager.equip_item(1, 102)

        self.assertTrue(success)
        self.manager._unequip_logic.assert_called_with(1, 103)
        self.assertIn("Unequipped Gnarled Staff", msg)


if __name__ == "__main__":
    unittest.main()
