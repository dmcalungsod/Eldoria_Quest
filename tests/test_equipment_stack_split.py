import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dependencies
mock_pymongo = MagicMock()
mock_pymongo_errors = MagicMock()
mock_pymongo_errors.DuplicateKeyError = Exception

sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_pymongo_errors
sys.modules["discord"] = MagicMock()

# Now import the modules under test
from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.items.equipment_manager import EquipmentManager  # noqa: E402


class TestStackEquipBug(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock(spec=DatabaseManager)
        self.manager = EquipmentManager(self.mock_db)

        # Setup common mocks
        # _get_player_allowed_slots uses get_player_field
        self.mock_db.get_player_field.return_value = 1

        # equip_item uses get_player
        self.mock_db.get_player.return_value = {"class_id": 1, "level": 10}

        self.mock_db.get_guild_rank.return_value = "F"
        self.mock_db.get_equipped_items.return_value = []

    def test_equip_stack_bug(self):
        """
        Reproduce bug where equipping from a stack equips the entire stack
        instead of splitting off one item.
        """
        discord_id = 123
        inv_id = 100

        # 1. Setup simulated inventory item (Stack of 2 Swords)
        item_stack = {
            "id": inv_id,
            "discord_id": discord_id,
            "item_key": "iron_sword",
            "item_name": "Iron Sword",
            "item_type": "equipment",
            "rarity": "Common",
            "slot": "sword",
            "count": 2,
            "equipped": 0,
            "item_source_table": "equipment",
        }

        self.mock_db.get_inventory_item.return_value = item_stack

        # Mock find_stackable_item to return the SAME stack (simulating the bug behavior)
        # Because add_inventory_item will look for unequipped stack, and our stack IS unequipped
        self.mock_db.find_stackable_item.return_value = item_stack

        # Mock CLASSES to allow 'sword'
        with patch(
            "game_systems.items.equipment_manager.CLASSES",
            {"Warrior": {"id": 1, "allowed_slots": ["sword"]}},
        ):
            # Execute Equip
            # Mock recalculate_player_stats to avoid needing PlayerStats dependencies
            self.manager.recalculate_player_stats = MagicMock()

            success, msg = self.manager.equip_item(discord_id, inv_id)

            print(f"Success: {success}, Msg: {msg}")

            # THE FIX:
            # We expect that we call the safe split method split_stack_to_equipped.

            # Assert that split_stack_to_equipped WAS called
            self.mock_db.split_stack_to_equipped.assert_called_with(discord_id, inv_id, item_stack)

            # Assert that insert_equipped_split was NOT called directly (it is called inside split_stack_to_equipped)
            # But EquipmentManager shouldn't call it directly anymore.
            self.mock_db.insert_equipped_split.assert_not_called()

            # Assert that add_inventory_item was NOT called
            self.mock_db.add_inventory_item.assert_not_called()

            # Assert that set_item_equipped was NOT called (for the split logic)
            self.mock_db.set_item_equipped.assert_not_called()

            print("Fix verified: split_stack_to_equipped was called.")


if __name__ == "__main__":
    unittest.main()
