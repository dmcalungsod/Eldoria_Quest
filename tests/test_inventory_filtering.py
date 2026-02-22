import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Adjust path to include the root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo globally
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.collection"] = MagicMock()
sys.modules["pymongo.results"] = MagicMock()

# Mock discord globally
mock_discord = MagicMock()
sys.modules["discord"] = mock_discord
# Ensure discord.ui refers to the same mock object as mock_discord.ui
sys.modules["discord.ui"] = mock_discord.ui

class MockView:
    def __init__(self, timeout=None):
        self.timeout = timeout
        self.children = []

    def add_item(self, item):
        self.children.append(item)

# Mock Button/Select/View classes for inheritance
mock_discord.ui.View = MockView
mock_discord.ui.Button = MagicMock
mock_discord.ui.Select = MagicMock
mock_discord.ButtonStyle = MagicMock()

# Mock SelectOption
class MockSelectOption:
    def __init__(self, label, value, emoji=None, description=None):
        self.label = label
        self.value = value
        self.emoji = emoji
        self.description = description

mock_discord.SelectOption = MockSelectOption

# Import the module to test
from game_systems.character.ui.inventory_view import InventoryView  # noqa: E402


class TestInventoryFiltering(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 123

        # Mock InventoryManager and EquipmentManager inside InventoryView
        # Since InventoryView instantiates them in __init__, we need to patch the classes where they are imported
        # But InventoryView imports them from their modules.
        # We can patch them via the module path used in inventory_view.py

        self.inv_manager_patcher = patch('game_systems.character.ui.inventory_view.InventoryManager')
        self.eq_manager_patcher = patch('game_systems.character.ui.inventory_view.EquipmentManager')
        self.con_manager_patcher = patch('game_systems.character.ui.inventory_view.ConsumableManager')

        self.mock_inv_cls = self.inv_manager_patcher.start()
        self.mock_eq_cls = self.eq_manager_patcher.start()
        self.mock_con_cls = self.con_manager_patcher.start()

        self.mock_inv_manager = self.mock_inv_cls.return_value
        self.mock_eq_manager = self.mock_eq_cls.return_value

        # Configure constants on the CLASS mock (so EquipmentManager.SLOT_LIST works)
        self.mock_eq_cls.TWO_HANDED_SLOTS = {"greatsword", "bow", "staff"}
        self.mock_eq_cls.MAIN_HAND_SLOTS = {"sword", "mace", "dagger", "wand"}
        self.mock_eq_cls.OFF_HAND_SLOTS = {"shield", "orb", "tome", "quiver", "offhand_dagger"}

        # Mock Player Data
        self.mock_db.get_player.return_value = {"level": 10, "class_id": 1}
        self.mock_db.get_guild_rank.return_value = "F"
        self.mock_eq_manager._get_player_allowed_slots.return_value = ["sword", "heavy_armor"]

        # Mock Equipment Data (used in check_requirements)
        self.mock_eq_manager.check_requirements.return_value = (True, None)
        self.mock_eq_manager.get_slot_display_name.side_effect = lambda x: x.replace("_", " ").title()

    def tearDown(self):
        self.inv_manager_patcher.stop()
        self.eq_manager_patcher.stop()
        self.con_manager_patcher.stop()

    def test_filter_weapons(self):
        """Test that filtering by Weapon only shows weapons."""
        items = [
            {"id": 1, "item_name": "Sword", "item_type": "equipment", "slot": "sword", "item_key": "sword", "equipped": 0},
            {"id": 2, "item_name": "Armor", "item_type": "equipment", "slot": "heavy_armor", "item_key": "armor", "equipped": 0},
            {"id": 3, "item_name": "Potion", "item_type": "consumable", "count": 1},
        ]
        self.mock_inv_manager.get_inventory.return_value = items

        # Need to patch EQUIPMENT_DATA to avoid lookup errors
        with patch('game_systems.character.ui.inventory_view.EQUIPMENT_DATA', {}):
            view = InventoryView(self.mock_db, self.mock_user, None, current_filter="Weapon")

        # Check Equip Select Options
        options = view.equip_select.options
        self.assertEqual(len(options), 1)
        self.assertEqual(options[0].label, "Sword (Sword)")

        # Check Use Select (should be disabled/hidden)
        self.assertTrue(view.use_select.disabled)

    def test_filter_consumables(self):
        """Test that filtering by Consumable hides Equip and shows Use."""
        items = [
            {"id": 1, "item_name": "Sword", "item_type": "equipment", "slot": "sword", "item_key": "sword", "equipped": 0},
            {"id": 3, "item_name": "Potion", "item_type": "consumable", "count": 1},
        ]
        self.mock_inv_manager.get_inventory.return_value = items

        with patch('game_systems.character.ui.inventory_view.EQUIPMENT_DATA', {}):
            view = InventoryView(self.mock_db, self.mock_user, None, current_filter="Consumable")

        # Equip Select should be disabled
        self.assertTrue(view.equip_select.disabled)

        # Use Select should have option
        self.assertEqual(len(view.use_select.options), 1)
        self.assertIn("Potion", view.use_select.options[0].label)

    def test_greyed_out_logic_persists(self):
        """Test that invalid items are still shown but locked in filtered view."""
        items = [
            {"id": 1, "item_name": "God Sword", "item_type": "equipment", "slot": "sword", "item_key": "god_sword", "equipped": 0},
        ]
        self.mock_inv_manager.get_inventory.return_value = items

        # Mock requirements fail
        self.mock_eq_manager.check_requirements.return_value = (False, "Req: Lvl 99")

        with patch('game_systems.character.ui.inventory_view.EQUIPMENT_DATA', {}):
            view = InventoryView(self.mock_db, self.mock_user, None, current_filter="Weapon")

        options = view.equip_select.options
        self.assertEqual(len(options), 1)
        self.assertIn("🔒", options[0].label)
        self.assertIn("Req: Lvl 99", options[0].description)

    def test_filter_all(self):
        """Test 'All' filter shows everything appropriate."""
        items = [
            {"id": 1, "item_name": "Sword", "item_type": "equipment", "slot": "sword", "item_key": "sword", "equipped": 0},
            {"id": 3, "item_name": "Potion", "item_type": "consumable", "count": 1},
        ]
        self.mock_inv_manager.get_inventory.return_value = items

        with patch('game_systems.character.ui.inventory_view.EQUIPMENT_DATA', {}):
            view = InventoryView(self.mock_db, self.mock_user, None, current_filter="All")

        # Equip Select has Sword
        self.assertFalse(view.equip_select.disabled)
        self.assertEqual(len(view.equip_select.options), 1)
        self.assertIn("Sword", view.equip_select.options[0].label)

        # Use Select has Potion
        self.assertFalse(view.use_select.disabled)
        self.assertEqual(len(view.use_select.options), 1)
        self.assertIn("Potion", view.use_select.options[0].label)

if __name__ == "__main__":
    unittest.main()
