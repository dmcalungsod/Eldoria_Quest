import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mocking necessary modules before import
sys.modules["discord"] = MagicMock()
sys.modules["discord.ext"] = MagicMock()
mock_pymongo = MagicMock()
mock_pymongo.errors = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_pymongo.errors

from game_systems.items.consumable_manager import ConsumableManager  # noqa: E402


class TestDualConsumableBug(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.manager = ConsumableManager(self.mock_db)

        # Mock CONSUMABLES data
        # We inject a test item into the global CONSUMABLES dictionary
        # Since it is imported, we might need to patch the dict where it is used
        # But since CONSUMABLES is a global variable in the module, let's patch it there.
        self.test_item_key = "test_dual_elixir"
        self.test_item_data = {
            "id": self.test_item_key,
            "name": "Dual Elixir",
            "type": "potion",
            "effect": {"heal": 50, "mana": 50},
            "rarity": "Common",
            "description": "Restores both HP and MP.",
        }

    def test_use_dual_item_full_hp_missing_mp(self):
        """
        Test using an item that restores both HP and MP when HP is full but MP is not.
        Expected: Should restore MP.
        Current Bug: Fails saying 'already at full health'.
        """
        discord_id = 12345
        inventory_id = 999

        # Setup Player Data
        # Max HP: 100, Current HP: 100 (Full)
        # Max MP: 100, Current MP: 0 (Empty)

        self.mock_db.get_inventory_item.return_value = {
            "item_key": self.test_item_key,
            "item_type": "consumable",
        }

        self.mock_db.get_player_vitals.return_value = {
            "current_hp": 100,
            "current_mp": 0,
        }

        # Mock PlayerStats to return max values
        stats_mock = MagicMock()
        stats_mock.max_hp = 100
        stats_mock.max_mp = 100

        # We need to mock PlayerStats.from_dict
        with (
            patch("game_systems.items.consumable_manager.PlayerStats") as MockPlayerStats,
            patch.dict(
                "game_systems.items.consumable_manager.CONSUMABLES",
                {self.test_item_key: self.test_item_data},
            ),
        ):
            MockPlayerStats.from_dict.return_value = stats_mock

            # Execute
            success, message = self.manager.use_item(discord_id, inventory_id)

            print(f"Result: success={success}, message='{message}'")

            # Assertions
            # This should BE True if fixed. Currently expected to be False.
            if not success and "already at full health" in message:
                print("BUG REPRODUCED: Item failed because HP is full, ignoring MP restoration.")
            elif success:
                print("BUG NOT REPRODUCED: Item worked correctly.")

            self.assertTrue(success, "Item usage should succeed because MP needs restoring.")
            self.assertIn("restored", message.lower())

    def test_use_dual_item_full_hp_full_mp(self):
        """
        Test using a dual item when both HP and MP are full.
        Expected: Fail with specific message "You are already at full health and mana."
        """
        discord_id = 12345
        inventory_id = 999

        self.mock_db.get_inventory_item.return_value = {
            "item_key": self.test_item_key,
            "item_type": "consumable",
        }

        self.mock_db.get_player_vitals.return_value = {
            "current_hp": 100,
            "current_mp": 100,
        }

        stats_mock = MagicMock()
        stats_mock.max_hp = 100
        stats_mock.max_mp = 100

        with (
            patch("game_systems.items.consumable_manager.PlayerStats") as MockPlayerStats,
            patch.dict(
                "game_systems.items.consumable_manager.CONSUMABLES",
                {self.test_item_key: self.test_item_data},
            ),
        ):
            MockPlayerStats.from_dict.return_value = stats_mock

            success, message = self.manager.use_item(discord_id, inventory_id)

            print(f"Full/Full Result: success={success}, message='{message}'")

            self.assertFalse(success)
            self.assertEqual(message, "You are already at full health and mana.")


if __name__ == "__main__":
    unittest.main()
