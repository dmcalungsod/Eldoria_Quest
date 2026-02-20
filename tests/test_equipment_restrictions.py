import sys
from unittest.mock import MagicMock, patch

# --- MOCKING DISCORD ---
mock_discord = MagicMock()

class MockView:
    def __init__(self, timeout=None):
        self.timeout = timeout
        self.children = []
    def add_item(self, item):
        self.children.append(item)

mock_discord.ui.View = MockView

class MockSelect(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options = []
        self.disabled = False
    def add_option(self, label, value, **kwargs):
        # We need to simulate add_option behavior if used, though _set_options assigns list directly
        pass

mock_discord.ui.Select = MockSelect
mock_discord.ui.Button = MagicMock

class MockSelectOption:
    def __init__(self, label, value, emoji=None, description=None, default=False):
        self.label = label
        self.value = value
        self.emoji = emoji
        self.description = description
        self.default = default

mock_discord.SelectOption = MockSelectOption
mock_discord.ButtonStyle = MagicMock()

sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = mock_discord.ui
# -----------------------

# --- MOCKING PYMONGO ---
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.collection"] = MagicMock()
# -----------------------

import unittest  # noqa: E402
from game_systems.items.equipment_manager import EquipmentManager  # noqa: E402
from game_systems.character.ui.inventory_view import InventoryView  # noqa: E402

class TestEquipmentRestrictions(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.eq_manager = EquipmentManager(self.mock_db)

    def test_check_requirements_level(self):
        item_data = {"level_req": 10, "name": "Strong Sword"}

        # Case 1: Player Level 5 (Too low)
        player_data = {"level": 5, "rank": "F"}
        can_equip, reason = self.eq_manager.check_requirements(item_data, player_data)
        self.assertFalse(can_equip)
        self.assertEqual(reason, "Req: Lvl 10")

        # Case 2: Player Level 10 (Exact match)
        player_data = {"level": 10, "rank": "F"}
        can_equip, reason = self.eq_manager.check_requirements(item_data, player_data)
        self.assertTrue(can_equip)

        # Case 3: Player Level 15 (High enough)
        player_data = {"level": 15, "rank": "F"}
        can_equip, reason = self.eq_manager.check_requirements(item_data, player_data)
        self.assertTrue(can_equip)

    def test_check_requirements_rank(self):
        item_data = {"rank_restriction": "C", "name": "Guild Sword"}

        # Case 1: Rank F (Too low)
        player_data = {"level": 100, "rank": "F"}
        can_equip, reason = self.eq_manager.check_requirements(item_data, player_data)
        self.assertFalse(can_equip)
        self.assertEqual(reason, "Req: Rank C")

        # Case 2: Rank C (Exact match)
        player_data = {"level": 100, "rank": "C"}
        can_equip, reason = self.eq_manager.check_requirements(item_data, player_data)
        self.assertTrue(can_equip)

        # Case 3: Rank S (High enough)
        player_data = {"level": 100, "rank": "S"}
        can_equip, reason = self.eq_manager.check_requirements(item_data, player_data)
        self.assertTrue(can_equip)

    def test_equip_item_restriction(self):
        discord_id = 12345
        inv_id = 1

        # Mock Inventory Item
        self.mock_db.get_inventory_item.return_value = {
            "id": inv_id,
            "item_key": "test_sword",
            "item_type": "equipment",
            "slot": "sword",
            "equipped": 0,
            "name": "Test Sword"
        }

        # Mock Player (Level too low)
        self.mock_db.get_player.return_value = {"level": 10}
        self.mock_db.get_guild_rank.return_value = "F"

        # Mock Allowed Slots
        self.mock_db.get_player_field.return_value = 1

        # Patch EQUIPMENT_DATA in the module where it's used
        with patch("game_systems.items.equipment_manager.EQUIPMENT_DATA", {
            "test_sword": {"level_req": 50, "slot": "sword", "name": "Test Sword"}
        }):
            success, msg = self.eq_manager.equip_item(discord_id, inv_id)

        self.assertFalse(success)
        self.assertIn("Req: Lvl 50", msg)

    @patch("game_systems.character.ui.inventory_view.InventoryManager")
    @patch("game_systems.character.ui.inventory_view.EquipmentManager") # This patches the CLASS
    def test_inventory_view_ui_logic(self, MockEqManagerClass, MockInvManagerClass):
        # Setup mocks
        mock_user = MagicMock()
        mock_user.id = 123

        # Mock Inventory Items
        mock_inv = MockInvManagerClass.return_value
        mock_inv.get_inventory.return_value = [
            {"id": 1, "item_type": "equipment", "item_name": "God Sword", "slot": "sword", "equipped": 0, "item_key": "god_sword"}
        ]

        # Mock DB
        self.mock_db.get_player.return_value = {"level": 5}
        self.mock_db.get_guild_rank.return_value = "F"

        # Mock EquipmentManager INSTANCE
        mock_eq_instance = MockEqManagerClass.return_value
        mock_eq_instance._get_player_allowed_slots.return_value = ["sword"]
        mock_eq_instance.check_requirements.return_value = (False, "Req: Lvl 99")

        # We need to ensure that when InventoryView calls eq_manager.check_requirements, it hits our mock.
        # InventoryView creates self.eq_manager = EquipmentManager(self.db)
        # Since we patched the Class, self.eq_manager IS mock_eq_instance.

        # Also need to patch EQUIPMENT_DATA in inventory_view to avoid KeyErrors or empty dicts
        with patch("game_systems.character.ui.inventory_view.EQUIPMENT_DATA", {"god_sword": {"level_req": 99}}):
             view = InventoryView(self.mock_db, mock_user, None)

        # Check Dropdown Options
        # view.equip_select is a MockSelect instance (from our discord mock)
        # options should be set
        options = view.equip_select.options
        self.assertEqual(len(options), 1)

        # Verify formatting
        # options[0] is a MockSelectOption
        self.assertIn("🔒", options[0].label)
        self.assertIn("Req: Lvl 99", options[0].description)
        self.assertEqual(str(options[0].emoji), "🚫")
