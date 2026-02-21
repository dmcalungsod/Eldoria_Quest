import unittest
from unittest.mock import MagicMock

from game_systems.crafting.crafting_system import CraftingSystem
from game_systems.data.crafting_recipes import EQUIPMENT_RECIPES
from game_systems.data.equipments import EQUIPMENT_DATA
from game_systems.data.materials import MATERIALS


class TestCraftingEquipment(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.system = CraftingSystem(self.mock_db)
        self.discord_id = 12345

    def test_craft_equipment_success(self):
        # Setup recipe
        # We assume "craft_rusted_sword" exists in EQUIPMENT_RECIPES
        recipe_id = "craft_rusted_sword"
        recipe = EQUIPMENT_RECIPES.get(recipe_id)
        if not recipe:
            self.skipTest("Recipe craft_rusted_sword not found in EQUIPMENT_RECIPES")

        # Mock Player (Aurum)
        self.mock_db.get_player.return_value = {"aurum": 1000}

        # Mock Inventory (Materials)
        self.mock_db.get_inventory_item_count.return_value = 100

        # Mock Remove Item
        self.mock_db.remove_inventory_item.return_value = True

        # Mock Equipment ID Lookup
        # _col("equipment").find_one(...) -> {"id": 101}
        mock_col = MagicMock()
        self.mock_db._col.return_value = mock_col
        mock_col.find_one.return_value = {"id": 101}
        self.mock_db.get_equipment_id_by_name.return_value = 101

        # Execute
        success, msg, item_data = self.system.craft_item(self.discord_id, recipe_id)

        # Assert
        self.assertTrue(success, f"Crafting failed with message: {msg}")
        self.assertIn("Successfully crafted", msg)
        self.assertEqual(item_data["name"], "Rusted Shortsword")

        # Verify DB Calls
        # 1. Aurum deducted
        self.mock_db.increment_player_fields.assert_called_with(self.discord_id, aurum=-recipe["cost"])

        # 2. Materials removed
        for mat, amount in recipe["materials"].items():
            self.mock_db.remove_inventory_item.assert_any_call(self.discord_id, mat, amount)

        # 3. Item Added
        # Note: add_inventory_item args: discord_id, item_key, item_name, item_type, rarity, amount, slot, item_source_table
        self.mock_db.add_inventory_item.assert_called_with(
            self.discord_id,
            "101",  # str(db_id)
            "Rusted Shortsword",
            "equipment",
            "Common",
            1,
            "sword",
            "equipment",
        )

    def test_craft_equipment_missing_material(self):
        recipe_id = "craft_rusted_sword"
        if recipe_id not in EQUIPMENT_RECIPES:
            self.skipTest("Recipe not found")

        self.mock_db.get_player.return_value = {"aurum": 1000}
        self.mock_db.get_inventory_item_count.return_value = 0  # Missing mats

        success, msg, item_data = self.system.craft_item(self.discord_id, recipe_id)

        self.assertFalse(success)
        self.assertIn("Missing material", msg)
        self.mock_db.add_inventory_item.assert_not_called()

    def test_recipe_data_integrity(self):
        """Verifies that all equipment recipes point to valid items and materials."""
        for recipe_id, recipe in EQUIPMENT_RECIPES.items():
            # Check Output Key exists in EQUIPMENT_DATA
            output_key = recipe["output_key"]
            self.assertIn(
                output_key, EQUIPMENT_DATA, f"Output key {output_key} for {recipe_id} not found in EQUIPMENT_DATA."
            )

            # Check Name matches EQUIPMENT_DATA name
            equip_name = EQUIPMENT_DATA[output_key]["name"]
            recipe_name = recipe["name"]
            self.assertEqual(
                equip_name,
                recipe_name,
                f"Name mismatch for {recipe_id}. Recipe: '{recipe_name}', Equip: '{equip_name}'.",
            )

            # Check Materials exist in MATERIALS
            for mat_key, amt in recipe["materials"].items():
                self.assertIn(mat_key, MATERIALS, f"Material {mat_key} for {recipe_id} not found in MATERIALS.")


if __name__ == "__main__":
    unittest.main()
