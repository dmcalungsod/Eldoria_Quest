import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add root to sys.path
sys.path.append(os.getcwd())

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from game_systems.adventure.adventure_manager import AdventureManager  # noqa: E402


class TestAdventureSupplyDeduction(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_bot = MagicMock()
        self.manager = AdventureManager(self.mock_db, self.mock_bot)

        # Mock inventory items for metadata
        self.mock_db.get_inventory_items.return_value = [
            {"item_key": "ration", "item_name": "Ration", "item_type": "consumable", "rarity": "Common", "count": 10},
            {"item_key": "torch", "item_name": "Torch", "item_type": "consumable", "rarity": "Common", "count": 10},
        ]

        self.mock_db.remove_inventory_item.side_effect = [True, False]  # First succeeds, second fails

        # Mock active session check
        self.mock_db.get_active_adventure.return_value = None

        # Mock add_inventory_item for rollback verification
        self.mock_db.add_inventory_item = MagicMock(return_value=True)

    def test_partial_deduction_failure(self):
        discord_id = 12345
        location_id = "forest_outskirts"  # valid location
        duration = 30
        supplies = {"ration": 1, "torch": 1}

        # Patch LOCATIONS to ensure validation passes
        with patch("game_systems.adventure.adventure_manager.LOCATIONS", {"forest_outskirts": {}}):
            # Execute
            result = self.manager.start_adventure(discord_id, location_id, duration, supplies)

            # Verify result is False (adventure failed to start)
            self.assertFalse(result)

            # Verify remove_inventory_item was called twice (once for ration, once for torch)
            self.assertEqual(self.mock_db.remove_inventory_item.call_count, 2)

            # Verify refund WAS attempted for the first item (ration)
            self.mock_db.add_inventory_item.assert_called_once_with(
                discord_id, "ration", "Ration", "consumable", "Common", 1, None, None
            )

            print("Test passed: Rollback triggered successfully.")


if __name__ == "__main__":
    unittest.main()
