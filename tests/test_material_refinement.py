import os
import sys
import unittest
from unittest.mock import MagicMock

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo
mock_pymongo = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = MagicMock()

from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.crafting.crafting_system import CraftingSystem  # noqa: E402


class TestMaterialRefinement(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock(spec=DatabaseManager)
        self.crafting = CraftingSystem(self.db)
        self.discord_id = 12345

    def test_refine_iron_ingot(self):
        # Setup: Player has 3 iron_ore and enough aurum
        self.db.get_player.return_value = {"aurum": 100}

        # Mock inventory counts
        def get_count_side_effect(discord_id, item_key):
            if item_key == "iron_ore":
                return 3
            return 0
        self.db.get_inventory_item_count.side_effect = get_count_side_effect

        self.db.remove_inventory_item.return_value = True

        # Execute
        recipe_id = "refine_iron_ingot"
        success, msg, item = self.crafting.craft_item(self.discord_id, recipe_id)

        # Verify
        self.assertTrue(success, f"Refinement failed: {msg}")
        self.db.remove_inventory_item.assert_called_with(self.discord_id, "iron_ore", 3)
        self.db.add_inventory_item.assert_called_with(
            self.discord_id,
            "iron_ingot",
            "Iron Ingot",
            "material",
            "Common",
            1,
            None,
            None
        )

    def test_craft_iron_dirk_with_ingots(self):
        # Setup: Player has 3 iron_ingot, 2 wolf_fang and enough aurum
        self.db.get_player.return_value = {"aurum": 200}

        # Mock inventory counts
        def get_count_side_effect(discord_id, item_key):
            if item_key == "iron_ingot":
                return 3
            elif item_key == "wolf_fang":
                return 2
            return 0
        self.db.get_inventory_item_count.side_effect = get_count_side_effect

        self.db.remove_inventory_item.return_value = True
        self.db.get_equipment_id_by_name.return_value = 101

        # Execute
        recipe_id = "craft_iron_dirk"
        success, msg, item = self.crafting.craft_item(self.discord_id, recipe_id)

        # Verify
        self.assertTrue(success, f"Crafting failed: {msg}")
        # Should remove materials
        self.db.remove_inventory_item.assert_any_call(self.discord_id, "iron_ingot", 3)
        self.db.remove_inventory_item.assert_any_call(self.discord_id, "wolf_fang", 2)

        # Should add equipment
        # Note: add_inventory_item args for equipment are a bit complex, just checking call
        self.db.add_inventory_item.assert_called()
        args, _ = self.db.add_inventory_item.call_args
        self.assertEqual(args[3], "equipment")

    def test_insufficient_materials_for_refinement(self):
        # Setup: Player has 2 iron_ore (needs 3)
        self.db.get_player.return_value = {"aurum": 100}
        self.db.get_inventory_item_count.return_value = 2

        # Execute
        recipe_id = "refine_iron_ingot"
        success, msg, item = self.crafting.craft_item(self.discord_id, recipe_id)

        # Verify
        self.assertFalse(success)
        self.assertIn("Missing material", msg)

if __name__ == "__main__":
    unittest.main()
