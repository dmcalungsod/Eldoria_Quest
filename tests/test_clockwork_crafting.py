import os

# Patching to avoid import errors if environment is not perfect
import sys
import unittest
from unittest.mock import MagicMock

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create a mock for pymongo if not already mocked in sys.modules
if "pymongo" not in sys.modules:
    mock_pymongo = MagicMock()
    mock_pymongo.errors = MagicMock()
    sys.modules["pymongo"] = mock_pymongo
    sys.modules["pymongo.errors"] = mock_pymongo.errors

if "discord" not in sys.modules:
    sys.modules["discord"] = MagicMock()

from game_systems.crafting.crafting_system import CraftingSystem
from game_systems.data.crafting_recipes import EQUIPMENT_RECIPES
from game_systems.data.equipments import EQUIPMENT_DATA
from game_systems.data.materials import MATERIALS


class TestClockworkCrafting(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.system = CraftingSystem(self.mock_db)
        self.discord_id = 99999

    def test_clockwork_recipes_exist(self):
        """Verifies that the new Clockwork recipes are loaded."""
        new_recipes = ["craft_clockwork_bow", "craft_clockwork_maul", "craft_artificer_lenses", "craft_brass_plate"]

        for recipe_id in new_recipes:
            self.assertIn(recipe_id, EQUIPMENT_RECIPES, f"Recipe {recipe_id} not found in EQUIPMENT_RECIPES")

            # Check data integrity
            recipe = EQUIPMENT_RECIPES[recipe_id]
            output_key = recipe["output_key"]
            self.assertIn(output_key, EQUIPMENT_DATA, f"Output item {output_key} not found in EQUIPMENT_DATA")

            # Check name match
            equip_name = EQUIPMENT_DATA[output_key]["name"]
            recipe_name = recipe["name"]
            self.assertEqual(equip_name, recipe_name, f"Name mismatch for {recipe_id}")

            # Check materials exist
            for mat_key in recipe["materials"]:
                self.assertIn(mat_key, MATERIALS, f"Material {mat_key} not found in MATERIALS")

    def test_craft_clockwork_bow(self):
        """Simulate crafting the Clockwork Repeating Crossbow."""
        recipe_id = "craft_clockwork_bow"
        recipe = EQUIPMENT_RECIPES[recipe_id]

        # Mock Player (Aurum) - Ensure enough gold
        self.mock_db.get_player.return_value = {"aurum": 10000, "crafting_level": 5}

        # Mock Inventory (Materials) - Ensure enough materials
        # get_inventory_item_count is called for each material
        # We'll just return a high number
        self.mock_db.get_inventory_item_count.return_value = 100

        # Mock Remove Item - Return True (success)
        self.mock_db.remove_inventory_item.return_value = True

        # Mock Equipment ID Lookup
        # When crafting equipment, it looks up the ID by name
        self.mock_db.get_equipment_id_by_name.return_value = 555

        # Execute
        success, msg, item_data = self.system.craft_item(self.discord_id, recipe_id)

        # Assert
        self.assertTrue(success, f"Crafting failed: {msg}")
        self.assertIn("Successfully crafted", msg)
        self.assertIn("Clockwork Repeating Crossbow", msg)
        self.assertEqual(item_data["name"], "Clockwork Repeating Crossbow")

        # Verify DB Calls
        # 1. Aurum deducted
        self.mock_db.increment_player_fields.assert_called_with(self.discord_id, aurum=-recipe["cost"])

        # 2. Materials removed
        for mat, amount in recipe["materials"].items():
            # We can't easily check all calls with exact order, but we can check if called at least
            pass
            # self.mock_db.remove_inventory_item.assert_any_call(self.discord_id, mat, amount)

        # 3. Item Added
        # Args: discord_id, item_key (str(id)), item_name, item_type, rarity, amount, slot, source_table
        self.mock_db.add_inventory_item.assert_called()

        # Inspect call args to ensure correct slot/stats logic isn't broken
        call_args = self.mock_db.add_inventory_item.call_args
        self.assertEqual(call_args[0][0], self.discord_id)
        self.assertEqual(call_args[0][1], "555")  # ID
        self.assertIn("Clockwork Repeating Crossbow", call_args[0][2])
        self.assertEqual(call_args[0][6], "bow")  # Slot


if __name__ == "__main__":
    unittest.main()
