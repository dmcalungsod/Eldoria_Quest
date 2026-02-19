"""
crafting_system.py

Core logic for the Crafting / Alchemy system.
"""

import logging

from database.database_manager import DatabaseManager
from game_systems.data.consumables import CONSUMABLES
from game_systems.data.equipments import EQUIPMENT_DATA
from game_systems.data.recipes import RECIPES
from game_systems.data.crafting_recipes import EQUIPMENT_RECIPES

logger = logging.getLogger("eldoria.crafting")


class CraftingSystem:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_recipes(self, discord_id: int) -> dict:
        """Returns all available recipes for the player."""
        # Merge dictionaries.
        all_recipes = {**RECIPES, **EQUIPMENT_RECIPES}
        return all_recipes

    def can_craft(self, discord_id: int, recipe_id: str) -> tuple[bool, str]:
        """Checks if a player can craft a specific recipe."""
        all_recipes = self.get_recipes(discord_id)
        recipe = all_recipes.get(recipe_id)
        if not recipe:
            return False, "Recipe not found."

        # Check Gold
        cost = recipe.get("cost", 0)
        player = self.db.get_player(discord_id)
        if not player or player.get("aurum", 0) < cost:
            return False, f"Insufficient Aurum ({cost} required)."

        # Check Materials
        materials = recipe.get("materials", {})
        for mat_key, amount in materials.items():
            owned = self.db.get_inventory_item_count(discord_id, mat_key)
            if owned < amount:
                return False, f"Missing material: {mat_key} ({owned}/{amount})"

        return True, "Ready to craft."

    def craft_item(self, discord_id: int, recipe_id: str) -> tuple[bool, str, dict | None]:
        """
        Executes the crafting process safely.
        Returns: (Success, Message, ResultItemData)
        """
        # Double-check conditions
        can, msg = self.can_craft(discord_id, recipe_id)
        if not can:
            return False, msg, None

        all_recipes = self.get_recipes(discord_id)
        recipe = all_recipes[recipe_id]

        cost = recipe.get("cost", 0)
        materials = recipe.get("materials", {})
        output_key = recipe["output_key"]
        output_amount = recipe.get("output_amount", 1)
        recipe_type = recipe.get("type", "consumable")  # Default to consumable for legacy recipes

        try:
            # 1. Deduct Gold
            self.db.increment_player_fields(discord_id, aurum=-cost)

            # 2. Remove Materials
            for mat_key, amount in materials.items():
                if not self.db.remove_inventory_item(discord_id, mat_key, amount):
                    logger.error(f"CRITICAL: Failed to remove {mat_key} during crafting for {discord_id}")
                    # Continue best effort

            # 3. Add Output Item
            item_data = None

            if recipe_type == "equipment":
                # Equipment Crafting Logic
                item_data = EQUIPMENT_DATA.get(output_key)
                if not item_data:
                    return False, "System Error: Equipment data missing.", None

                # Resolve DB ID
                db_id = self.db.get_equipment_id_by_name(item_data["name"])
                if not db_id:
                    return False, f"System Error: Equipment '{item_data['name']}' not found in database.", None

                self.db.add_inventory_item(
                    discord_id,
                    str(db_id),  # Key must be the ID string for equipment stats logic
                    item_data["name"],
                    "equipment",
                    item_data["rarity"],
                    output_amount,
                    item_data.get("slot"),
                    "equipment",  # Item source table
                )

            else:
                # Consumable Logic
                item_data = CONSUMABLES.get(output_key)
                if not item_data:
                    return False, "System Error: Output item data missing.", None

                self.db.add_inventory_item(
                    discord_id,
                    output_key,
                    item_data["name"],
                    "consumable",
                    item_data["rarity"],
                    output_amount,
                    None,
                    None,
                )

            logger.info(f"User {discord_id} crafted {output_amount}x {output_key}")
            return True, f"Successfully crafted **{item_data['name']}** x{output_amount}!", item_data

        except Exception as e:
            logger.error(f"Crafting system error for {discord_id}: {e}", exc_info=True)
            return False, "An error occurred during crafting.", None
