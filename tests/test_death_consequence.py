
import sys
from unittest.mock import MagicMock

# Mock pymongo BEFORE importing any project modules
sys.modules["pymongo"] = MagicMock()

import unittest
from game_systems.adventure.adventure_manager import AdventureManager
import game_systems.data.emojis as E

class TestDeathConsequence(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_db = MagicMock()
        self.mock_bot = MagicMock()

        # Instantiate Manager with mocks
        self.manager = AdventureManager(self.mock_db, self.mock_bot)

        # Override internal inventory manager with mock
        self.manager.inventory_manager = MagicMock()

        # Mock DB responses for _handle_death_rewards
        self.mock_db.get_player_stats_json.return_value = {"HP": {"base": 100}, "MP": {"base": 50}}
        self.mock_db.get_player.return_value = {
            "level": 1,
            "experience": 0,
            "exp_to_next": 1000,
            "current_hp": 0,
            "current_mp": 10,
            "aurum": 100
        }
        self.mock_db.get_player_field.return_value = 100 # Current Aurum

    def test_handle_death_rewards_realism_enhancement(self):
        """
        Verify Realism Enhancement:
        - EXP item is NOT added (popped)
        - Aurum IS deducted (10% of 100 = 10)
        - Loot quantity is reduced (50% loss)
        """
        discord_id = 12345

        # Mock Session
        mock_session = MagicMock()
        mock_session.discord_id = discord_id
        # Session loot includes EXP and Items
        mock_session.loot = {
            "exp": 100,
            "wolf_fang": 2,          # Should become 1
            "magic_stone_small": 1,  # Should become 0 (removed)
            "aurum": 50              # Should be removed/ignored
        }

        # Call the method
        loss_msg = self.manager._handle_death_rewards(discord_id, mock_session)

        # Verify Inventory Additions
        call_args = self.manager.inventory_manager.add_items_bulk.call_args
        self.assertIsNotNone(call_args)
        bulk_items = call_args[0][1] # Second arg

        # 1. Verify EXP item removed (Fix)
        exp_item = next((i for i in bulk_items if i["item_key"] == "exp"), None)
        self.assertIsNone(exp_item, "EXP should NOT be added as an item")

        # 2. Verify Aurum Deduction
        # 10% of 100 = 10
        self.mock_db.deduct_aurum.assert_called_with(discord_id, 10)

        # 3. Verify Loot Reduction
        # Wolf Fang: 2 * 0.5 = 1.0 -> int(1) -> 1
        fang_item = next((i for i in bulk_items if i["item_key"] == "wolf_fang"), None)
        self.assertIsNotNone(fang_item)
        self.assertEqual(fang_item["amount"], 1)

        # Magic Stone Small: 1 * 0.5 = 0.5 -> int(0) -> 0. Should be removed.
        stone_item = next((i for i in bulk_items if i["item_key"] == "magic_stone_small"), None)
        if stone_item:
             # If it exists, amount must be > 0. If 0, logic failed to filter/remove.
             self.assertGreater(stone_item["amount"], 0, "Items with 0 amount should not be added")
        else:
             # Ideally it's not even in the list
             pass

        # 4. Verify Loss Message
        self.assertIsNotNone(loss_msg)
        self.assertIn("Losses Incurred", loss_msg)
        # We check for substring parts because order might vary or name resolution might work
        self.assertTrue("-10" in loss_msg or "10" in loss_msg)
        # Check that Wolf Fang was lost (1x)
        self.assertTrue("Wolf Fang" in loss_msg or "wolf_fang" in loss_msg)

        # Verify Aurum key popped from loot
        self.assertNotIn("aurum", mock_session.loot)
        self.assertNotIn("exp", mock_session.loot)

if __name__ == "__main__":
    unittest.main()
