import os
import sys
import unittest

# Add repo root to path so we can import game_systems
sys.path.append(os.getcwd())

from game_systems.data.consumables import CONSUMABLES
from game_systems.data.materials import MATERIALS
from game_systems.data.recipes import RECIPES


class TestCraftingData(unittest.TestCase):
    def test_new_travel_supplies_recipes(self):
        """Verify that the new Hardtack and Pitch Torch recipes exist and are valid."""
        target_recipes = ["craft_hardtack", "craft_pitch_torch"]

        for recipe_id in target_recipes:
            self.assertIn(recipe_id, RECIPES, f"Recipe {recipe_id} not found in RECIPES.")
            recipe = RECIPES[recipe_id]

            # Check Output
            output_key = recipe["output_key"]
            self.assertIn(output_key, CONSUMABLES, f"Output {output_key} for {recipe_id} not found in CONSUMABLES.")

            # Check Materials
            for mat_key, amount in recipe["materials"].items():
                self.assertIn(mat_key, MATERIALS, f"Material {mat_key} for {recipe_id} not found in MATERIALS.")
                self.assertGreater(amount, 0, f"Material amount for {mat_key} must be positive.")

    def test_all_recipes_validity(self):
        """Verify all recipes in RECIPES refer to valid materials and outputs."""
        for recipe_id, recipe in RECIPES.items():
            # Check Output
            output_key = recipe["output_key"]
            # Output can be in CONSUMABLES or MATERIALS (for refinement)
            valid_output = (output_key in CONSUMABLES) or (output_key in MATERIALS)
            self.assertTrue(valid_output, f"Output {output_key} for {recipe_id} not found in CONSUMABLES or MATERIALS.")

            # Check Materials
            if "materials" in recipe:
                for mat_key, amount in recipe["materials"].items():
                    # Special case: inputs in HIDDEN_RECIPES might be different, but RECIPES structure is dict.
                    # Some recipes might use items as materials? usually not.
                    # Let's assume only MATERIALS for now.

                    # Exception: Some recipes might use intermediate items?
                    # "heroic_potion" uses "strength_brew" (consumable) as material.
                    # So we should check if material is in MATERIALS OR CONSUMABLES.

                    valid_material = (mat_key in MATERIALS) or (mat_key in CONSUMABLES)
                    self.assertTrue(
                        valid_material, f"Material {mat_key} for {recipe_id} not found in MATERIALS or CONSUMABLES."
                    )


if __name__ == "__main__":
    unittest.main()
