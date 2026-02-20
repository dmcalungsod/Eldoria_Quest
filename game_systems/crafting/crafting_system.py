"""
crafting_system.py

Core logic for the Crafting / Alchemy system.
"""

import logging

from database.database_manager import DatabaseManager
from game_systems.data.consumables import CONSUMABLES
from game_systems.data.crafting_recipes import EQUIPMENT_RECIPES
from game_systems.data.equipments import EQUIPMENT_DATA
from game_systems.data.materials import MATERIALS
from game_systems.data.recipes import RECIPES

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

    def get_dismantle_rewards(self, item_name: str, rarity: str) -> dict[str, int]:
        """
        Calculates materials returned from dismantling an item.
        Prioritizes recipe data, falls back to rarity-based scrap.
        """
        # 1. Check Recipes
        for recipe in EQUIPMENT_RECIPES.values():
            if recipe["name"] == item_name:
                rewards = {}
                for mat_key, amount in recipe.get("materials", {}).items():
                    # Refund 50% (rounded down, min 1)
                    refund = max(1, int(amount * 0.5))
                    rewards[mat_key] = refund
                return rewards

        # 2. Fallback by Rarity
        fallback_map = {
            "Common": "iron_ore",
            "Uncommon": "magic_stone_medium",
            "Rare": "mithril_ore",
            "Epic": "titan_shard",
            "Legendary": "celestial_dust",
            "Mythical": "celestial_dust",
        }
        # Default to iron_ore if rarity unknown
        mat_key = fallback_map.get(rarity, "iron_ore")
        return {mat_key: 1}

    def dismantle_item(self, discord_id: int, inv_id: int) -> tuple[bool, str, dict | None]:
        """
        Dismantles a specific inventory item into materials.
        Returns: (Success, Message, RewardsDict)
        """
        # 1. Fetch Item
        item = self.db.get_inventory_item_by_id(inv_id, discord_id)
        if not item:
            return False, "Item not found in inventory.", None

        # 2. Validate
        if item.get("item_type") != "equipment":
            return False, "Only equipment can be dismantled.", None

        if item.get("equipped", 0) == 1:
            return False, "Cannot dismantle equipped items.", None

        # 3. Calculate Rewards
        rewards = self.get_dismantle_rewards(item["item_name"], item["rarity"])
        if not rewards:
            return False, "No materials could be salvaged.", None

        try:
            # 4. Remove Item (Atomic consume of 1)
            if not self.db.consume_item_atomic(inv_id, 1):
                return False, "Failed to consume item (ghost item?).", None

            # 5. Add Materials
            items_to_add = []
            for mat_key, amount in rewards.items():
                mat_data = MATERIALS.get(mat_key)
                if not mat_data:
                    # Fallback if material key invalid (shouldn't happen with correct data)
                    continue

                items_to_add.append(
                    {
                        "item_key": mat_key,
                        "item_name": mat_data["name"],
                        "item_type": "material",
                        "rarity": mat_data["rarity"],
                        "amount": amount,
                    }
                )

            if items_to_add:
                self.db.add_inventory_items_bulk(discord_id, items_to_add)

            # Format Message
            reward_strs = []
            for mat_key, amount in rewards.items():
                m_name = MATERIALS.get(mat_key, {}).get("name", mat_key)
                reward_strs.append(f"{m_name} x{amount}")

            msg = f"Dismantled **{item['item_name']}** and salvaged: {', '.join(reward_strs)}"
            logger.info(f"User {discord_id} dismantled {inv_id} for {rewards}")
            return True, msg, rewards

        except Exception as e:
            logger.error(f"Dismantle error for {discord_id}: {e}", exc_info=True)
            return False, "An error occurred during dismantling.", None
