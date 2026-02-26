"""
Tests for Travel Supplies & Alchemist Items Crafting
--------------------------------------------------
Verifies recipes for Hardtack, Pitch Torch, Phial of Vitriol, and Bitter Panacea.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.data.recipes import RECIPES

class TestCraftingSupplies(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules to mock pymongo globally
        self.patcher = patch.dict(
            "sys.modules",
            {
                "pymongo": MagicMock(),
                "pymongo.collection": MagicMock(),
                "pymongo.results": MagicMock(),
            },
        )
        self.patcher.start()

        # Import CraftingSystem inside the test method
        from game_systems.crafting.crafting_system import CraftingSystem

        self.mock_db = MagicMock()
        self.crafting = CraftingSystem(self.mock_db)
        self.discord_id = 12345

    def tearDown(self):
        self.patcher.stop()

    def test_new_supplies_recipes_exist(self):
        """Verify new supply recipes are loaded."""
        self.assertIn("craft_hardtack", RECIPES)
        self.assertIn("craft_pitch_torch", RECIPES)
        self.assertIn("craft_phial_of_vitriol", RECIPES)
        self.assertIn("craft_bitter_panacea", RECIPES)

    def test_crafting_hardtack(self):
        """Test crafting 'hardtack' (Consumes consumable + material)."""
        recipe_id = "craft_hardtack"
        recipe = RECIPES[recipe_id]

        # Mock sufficient funds
        self.mock_db.get_player.return_value = {"aurum": 100}

        # Mock inventory counts
        # Needs: {"food_ration": 1, "medicinal_herb": 1}
        def get_count_side_effect(discord_id, item_key):
            counts = {"food_ration": 5, "medicinal_herb": 5}
            return counts.get(item_key, 0)

        self.mock_db.get_inventory_item_count.side_effect = get_count_side_effect
        self.mock_db.remove_inventory_item.return_value = True

        # Attempt craft
        success, msg, item_data = self.crafting.craft_item(self.discord_id, recipe_id)

        self.assertTrue(success)
        self.assertIn("Hardtack", msg)
        self.assertIn("x2", msg) # Verifies output amount
        self.assertIsNotNone(item_data)

        # Verify deductions
        self.mock_db.increment_player_fields.assert_called_with(self.discord_id, aurum=-recipe["cost"])
        self.mock_db.remove_inventory_item.assert_any_call(self.discord_id, "food_ration", 1)
        self.mock_db.remove_inventory_item.assert_any_call(self.discord_id, "medicinal_herb", 1)

        # Verify item addition
        self.mock_db.add_inventory_item.assert_called()
        args, _ = self.mock_db.add_inventory_item.call_args
        self.assertEqual(args[1], "hardtack")
        self.assertEqual(args[5], 2)  # Amount 2

    def test_crafting_pitch_torch(self):
        """Test crafting 'pitch_torch' (Output 3)."""
        recipe_id = "craft_pitch_torch"
        recipe = RECIPES[recipe_id]

        # Mock sufficient funds
        self.mock_db.get_player.return_value = {"aurum": 100}

        # Mock inventory counts
        # Needs: {"treant_branch": 1, "slime_gel": 2}
        def get_count_side_effect(discord_id, item_key):
            counts = {"treant_branch": 5, "slime_gel": 5}
            return counts.get(item_key, 0)

        self.mock_db.get_inventory_item_count.side_effect = get_count_side_effect
        self.mock_db.remove_inventory_item.return_value = True

        # Attempt craft
        success, msg, item_data = self.crafting.craft_item(self.discord_id, recipe_id)

        self.assertTrue(success)
        self.assertIn("Pitch Torch", msg)
        self.assertIn("x3", msg)

        # Verify deductions
        self.mock_db.remove_inventory_item.assert_any_call(self.discord_id, "treant_branch", 1)
        self.mock_db.remove_inventory_item.assert_any_call(self.discord_id, "slime_gel", 2)

        # Verify item addition
        args, _ = self.mock_db.add_inventory_item.call_args
        self.assertEqual(args[1], "pitch_torch")
        self.assertEqual(args[5], 3)  # Amount 3

if __name__ == "__main__":
    unittest.main()
