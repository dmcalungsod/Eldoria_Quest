
import sys
import unittest
from unittest.mock import MagicMock

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from game_systems.items.equipment_manager import EquipmentManager  # noqa: E402


class TestArmorSlots(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.manager = EquipmentManager(self.mock_db)

        # Setup mocks
        self.mock_db.get_player.return_value = {"class_id": 1, "level": 10, "name": "Player"}
        self.mock_db.get_guild_rank.return_value = "F"

        # Mock allowed slots to allow everything for this test
        self.manager._get_player_allowed_slots = MagicMock(return_value=["helm", "leather_cap", "heavy_armor", "medium_armor"])
        self.manager.check_requirements = MagicMock(return_value=(True, None))

        self.inventory = {}

        def get_inv(uid, iid):
            return self.inventory.get(iid)

        self.mock_db.get_inventory_item.side_effect = get_inv

        def mock_unequip(uid, iid):
            if iid in self.inventory:
                self.inventory[iid]["equipped"] = 0

        self.manager._unequip_logic = MagicMock(side_effect=mock_unequip)

        def mock_equip(iid, val):
            if iid in self.inventory:
                self.inventory[iid]["equipped"] = val

        self.mock_db.set_item_equipped.side_effect = mock_equip
        self.manager.recalculate_player_stats = MagicMock()

    def test_head_slot_conflict(self):
        # 1. Create items
        helm = {
            "id": 1, "item_key": "helm", "item_name": "Iron Helm",
            "item_type": "equipment", "slot": "helm", "rarity": "Common", "equipped": 0, "count": 1
        }
        cap = {
            "id": 2, "item_key": "cap", "item_name": "Leather Cap",
            "item_type": "equipment", "slot": "leather_cap", "rarity": "Common", "equipped": 0, "count": 1
        }
        self.inventory[1] = helm
        self.inventory[2] = cap

        # 2. Equip Helm
        self.mock_db.get_equipped_items.return_value = []
        self.manager.equip_item(1, 1)
        self.inventory[1]["equipped"] = 1

        # 3. Equip Cap
        self.mock_db.get_equipped_items.return_value = [self.inventory[1]]
        self.manager.equip_item(1, 2)
        self.inventory[2]["equipped"] = 1

        # 4. Verify Helm unequipped
        self.manager._unequip_logic.assert_called_with(1, 1)

    def test_body_slot_conflict(self):
        # 1. Create items
        plate = {
            "id": 3, "item_key": "plate", "item_name": "Plate Armor",
            "item_type": "equipment", "slot": "heavy_armor", "rarity": "Common", "equipped": 0, "count": 1
        }
        leather = {
            "id": 4, "item_key": "leather", "item_name": "Leather Armor",
            "item_type": "equipment", "slot": "medium_armor", "rarity": "Common", "equipped": 0, "count": 1
        }
        self.inventory[3] = plate
        self.inventory[4] = leather

        # 2. Equip Plate
        self.mock_db.get_equipped_items.return_value = []
        self.manager.equip_item(1, 3)
        self.inventory[3]["equipped"] = 1

        # 3. Equip Leather
        self.mock_db.get_equipped_items.return_value = [self.inventory[3]]
        self.manager.equip_item(1, 4)

        # 4. Verify Plate unequipped
        self.manager._unequip_logic.assert_called_with(1, 3)

    def test_get_slot_display_name(self):
        self.assertEqual(self.manager.get_slot_display_name("helm"), "Head")
        self.assertEqual(self.manager.get_slot_display_name("leather_cap"), "Head")
        self.assertEqual(self.manager.get_slot_display_name("heavy_armor"), "Body")
        self.assertEqual(self.manager.get_slot_display_name("medium_armor"), "Body")

if __name__ == "__main__":
    unittest.main()
