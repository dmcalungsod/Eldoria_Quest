"""
test_crafting_dismantle.py

Tests for CraftingSystem.dismantle_item logic.
"""

import sys
from unittest.mock import MagicMock

# Mock pymongo before importing DatabaseManager
sys.modules["pymongo"] = MagicMock()

import unittest  # noqa: E402

from game_systems.crafting.crafting_system import CraftingSystem  # noqa: E402


class TestCraftingDismantle(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.system = CraftingSystem(self.mock_db)
        self.discord_id = 12345
        self.inv_id = 999

    def test_get_dismantle_rewards_recipe(self):
        """Test rewards calculation based on known recipe."""
        # "Rusted Shortsword" recipe: {"iron_ore": 3, "wolf_fang": 1}
        # Half: iron_ore -> 1, wolf_fang -> 0 -> max(1, 0) -> 1
        rewards = self.system.get_dismantle_rewards("Rusted Shortsword", "Common")
        self.assertEqual(rewards, {"iron_ore": 1, "wolf_fang": 1})

    def test_get_dismantle_rewards_fallback(self):
        """Test fallback rewards for unknown items based on rarity."""
        # Unknown item
        rewards = self.system.get_dismantle_rewards("Mystery Sword", "Rare")
        self.assertEqual(rewards, {"mithril_ore": 1})

        rewards = self.system.get_dismantle_rewards("Mystery Godblade", "Mythical")
        self.assertEqual(rewards, {"celestial_dust": 1})

        # Default fallback
        rewards = self.system.get_dismantle_rewards("Unknown Junk", "Unknown")
        self.assertEqual(rewards, {"iron_ore": 1})

    def test_dismantle_item_not_found(self):
        self.mock_db.get_inventory_item_by_id.return_value = None
        success, msg, _ = self.system.dismantle_item(self.discord_id, self.inv_id)
        self.assertFalse(success)
        self.assertIn("not found", msg)

    def test_dismantle_item_not_equipment(self):
        self.mock_db.get_inventory_item_by_id.return_value = {
            "item_name": "Potion",
            "item_type": "consumable",
            "equipped": 0,
        }
        success, msg, _ = self.system.dismantle_item(self.discord_id, self.inv_id)
        self.assertFalse(success)
        self.assertIn("Only equipment", msg)

    def test_dismantle_item_equipped(self):
        self.mock_db.get_inventory_item_by_id.return_value = {
            "item_name": "Sword",
            "item_type": "equipment",
            "equipped": 1,
        }
        success, msg, _ = self.system.dismantle_item(self.discord_id, self.inv_id)
        self.assertFalse(success)
        self.assertIn("equipped", msg)

    def test_dismantle_item_success(self):
        # Setup item
        self.mock_db.get_inventory_item_by_id.return_value = {
            "item_name": "Rusted Shortsword",
            "item_type": "equipment",
            "equipped": 0,
            "rarity": "Common",
        }
        # Setup consume success
        self.mock_db.consume_item_atomic.return_value = True

        success, msg, rewards = self.system.dismantle_item(self.discord_id, self.inv_id)

        self.assertTrue(success)
        self.assertEqual(rewards, {"iron_ore": 1, "wolf_fang": 1})
        self.assertIn("Dismantled", msg)

        # Verify DB calls
        self.mock_db.consume_item_atomic.assert_called_with(self.inv_id, 1)
        self.mock_db.add_inventory_items_bulk.assert_called_once()

        # Check bulk add args
        call_args = self.mock_db.add_inventory_items_bulk.call_args
        args, _ = call_args
        uid, items = args
        self.assertEqual(uid, self.discord_id)

        # Verify item structure
        # Sort items by item_key to ensure deterministic comparison or just check keys existence
        keys = [i["item_key"] for i in items]
        self.assertIn("iron_ore", keys)
        self.assertIn("wolf_fang", keys)


if __name__ == "__main__":
    unittest.main()
