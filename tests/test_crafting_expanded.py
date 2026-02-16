"""
Tests for Expanded Crafting System
----------------------------------
Verifies new recipes and material handling.
"""

import sys
import os
import unittest
from unittest.mock import MagicMock

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.crafting.crafting_system import CraftingSystem
from game_systems.data.recipes import RECIPES

class TestCraftingExpanded(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.crafting = CraftingSystem(self.mock_db)
        self.discord_id = 12345

    def test_new_recipes_exist(self):
        """Verify new recipes are loaded."""
        self.assertIn("strength_brew", RECIPES)
        self.assertIn("dex_elixir", RECIPES)
        self.assertIn("food_ration", RECIPES)
        self.assertIn("campfire_stew", RECIPES)
        self.assertIn("smoke_pellet", RECIPES)
        self.assertIn("regen_potion", RECIPES)

    def test_crafting_campfire_stew_success(self):
        """Test crafting 'campfire_stew' with sufficient materials."""
        recipe_id = "campfire_stew"
        recipe = RECIPES[recipe_id]

        # Mock sufficient funds
        self.mock_db.get_player.return_value = {"aurum": 1000}

        # Mock inventory counts
        # "campfire_stew": {"boar_meat": 2, "medicinal_herb": 2, "magic_stone_fragment": 1}
        def get_count_side_effect(discord_id, item_key):
            counts = {
                "boar_meat": 5,
                "medicinal_herb": 5,
                "magic_stone_fragment": 5
            }
            return counts.get(item_key, 0)

        self.mock_db.get_inventory_item_count.side_effect = get_count_side_effect
        self.mock_db.remove_inventory_item.return_value = True # Mock success removal

        # Attempt craft
        success, msg, item_data = self.crafting.craft_item(self.discord_id, recipe_id)

        self.assertTrue(success)
        self.assertIn("Warden's Stew", msg)
        self.assertIsNotNone(item_data)

        # Verify deductions
        self.mock_db.increment_player_fields.assert_called_with(self.discord_id, aurum=-recipe["cost"])

        # Verify material removal calls
        self.mock_db.remove_inventory_item.assert_any_call(self.discord_id, "boar_meat", 2)
        self.mock_db.remove_inventory_item.assert_any_call(self.discord_id, "medicinal_herb", 2)
        self.mock_db.remove_inventory_item.assert_any_call(self.discord_id, "magic_stone_fragment", 1)

        # Verify item addition
        self.mock_db.add_inventory_item.assert_called()
        args, _ = self.mock_db.add_inventory_item.call_args
        self.assertEqual(args[1], "campfire_stew")
        self.assertEqual(args[5], 1) # Amount

    def test_crafting_insufficient_materials(self):
        """Test failure when missing materials."""
        recipe_id = "campfire_stew"

        # Mock sufficient funds
        self.mock_db.get_player.return_value = {"aurum": 1000}

        # Mock insufficient inventory
        def get_count_side_effect(discord_id, item_key):
            counts = {
                "boar_meat": 1, # Need 2
                "medicinal_herb": 5,
                "magic_stone_fragment": 5
            }
            return counts.get(item_key, 0)

        self.mock_db.get_inventory_item_count.side_effect = get_count_side_effect

        success, msg, _ = self.crafting.craft_item(self.discord_id, recipe_id)

        self.assertFalse(success)
        self.assertIn("Missing material: boar_meat", msg)

        # Verify NO deductions
        self.mock_db.increment_player_fields.assert_not_called()
        self.mock_db.remove_inventory_item.assert_not_called()
        self.mock_db.add_inventory_item.assert_not_called()

if __name__ == "__main__":
    unittest.main()
