"""
crafting_system.py

Core logic for the Crafting / Alchemy system.
"""

import logging
import random

from database.database_manager import DatabaseManager
from game_systems.data.consumables import CONSUMABLES
from game_systems.data.crafting_recipes import EQUIPMENT_RECIPES
from game_systems.data.equipments import EQUIPMENT_DATA
from game_systems.data.materials import MATERIALS
from game_systems.data.recipes import HIDDEN_RECIPES, RECIPES
from game_systems.player.achievement_system import AchievementSystem

logger = logging.getLogger("eldoria.crafting")

# XP Rewards for crafting
CRAFTING_XP_REWARDS = {
    "Common": 10,
    "Uncommon": 25,
    "Rare": 50,
    "Epic": 100,
    "Legendary": 250,
    "Mythical": 500,
}


def calculate_crafting_xp_req(level: int) -> int:
    """Calculates XP needed for the next crafting level."""
    return int(50 * (level**1.3))


class CraftingSystem:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def _add_crafting_xp(self, discord_id: int, rarity: str, is_discovery: bool = False) -> str:
        """
        Awards Crafting XP and handles level ups.
        Returns a message string (empty if no level up/significant event).
        """
        # Calculate XP Amount
        base_xp = CRAFTING_XP_REWARDS.get(rarity, 5)
        if is_discovery:
            base_xp *= 5  # Large bonus for discovery

        # Fetch current progress
        player = self.db.get_player(discord_id)
        if not player:
            return ""

        current_level = player.get("crafting_level", 1)
        current_xp = player.get("crafting_xp", 0)

        # Add XP
        current_xp += base_xp
        msg_extras = ""
        leveled_up = False

        # Level Up Check
        req_xp = calculate_crafting_xp_req(current_level)
        while current_xp >= req_xp:
            current_xp -= req_xp
            current_level += 1
            req_xp = calculate_crafting_xp_req(current_level)
            leveled_up = True

        if leveled_up:
            msg_extras = f"\n⚒️ **Crafting Level Up!** You are now Level **{current_level}**!"

        # Update DB
        self.db.update_player_fields(
            discord_id,
            crafting_level=current_level,
            crafting_xp=current_xp,
        )

        # Check Achievements
        if leveled_up:
            achievements = AchievementSystem(self.db)
            ach_msg = achievements.check_crafting_achievements(discord_id)
            if ach_msg:
                msg_extras += f"\n{ach_msg}"

        return f" (+{base_xp} Craft XP){msg_extras}"

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

    def _roll_quality(self, base_rarity: str, discord_id: int | None = None) -> str:
        """
        Rolls for a quality upgrade (10% chance per tier + Crafting Level bonus).
        """
        tiers = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythical"]
        try:
            current_index = tiers.index(base_rarity)
        except ValueError:
            return base_rarity

        # Calculate Chance
        base_chance = 0.10
        if discord_id:
            player = self.db.get_player(discord_id)
            if player:
                level = player.get("crafting_level", 1)
                base_chance += level * 0.005  # +0.5% per level

        # Roll
        if random.random() < base_chance:
            if current_index + 1 < len(tiers):
                current_index += 1
                # Cascade: 50% reduced chance for subsequent upgrades
                while random.random() < (base_chance * 0.5) and current_index + 1 < len(tiers):
                    current_index += 1

        return tiers[current_index]

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
            success_msg_extras = ""

            if recipe_type == "equipment":
                # Equipment Crafting Logic
                item_data = EQUIPMENT_DATA.get(output_key)
                if not item_data:
                    return False, "System Error: Equipment data missing.", None

                # Resolve DB ID
                db_id = self.db.get_equipment_id_by_name(item_data["name"])
                if not db_id:
                    return (
                        False,
                        f"System Error: Equipment '{item_data['name']}' not found in database.",
                        None,
                    )

                # --- QUALITY ROLL ---
                base_rarity = item_data.get("rarity", "Common")
                new_rarity = self._roll_quality(base_rarity, discord_id)

                final_name = item_data["name"]

                if new_rarity != base_rarity:
                    prefix_map = {
                        "Uncommon": "Fine",
                        "Rare": "Superior",
                        "Epic": "Exquisite",
                        "Legendary": "Masterwork",
                        "Mythical": "Divine",
                    }
                    prefix = prefix_map.get(new_rarity, "Improved")
                    final_name = f"{prefix} {final_name}"
                    success_msg_extras = f"\n✨ **Critical Success!** Upgraded to **{new_rarity}**!"

                self.db.add_inventory_item(
                    discord_id,
                    str(db_id),  # Key must be the ID string for equipment stats logic
                    final_name,
                    "equipment",
                    new_rarity,
                    output_amount,
                    item_data.get("slot"),
                    "equipment",  # Item source table
                )

            elif recipe_type == "material":
                # Material Refinement Logic
                item_data = MATERIALS.get(output_key)
                if not item_data:
                    return False, "System Error: Output material data missing.", None

                final_name = item_data["name"]

                self.db.add_inventory_item(
                    discord_id,
                    output_key,
                    final_name,
                    "material",
                    item_data["rarity"],
                    output_amount,
                    None,
                    None,
                )

            else:
                # Consumable Logic
                item_data = CONSUMABLES.get(output_key)
                if not item_data:
                    return False, "System Error: Output item data missing.", None

                final_name = item_data["name"]

                self.db.add_inventory_item(
                    discord_id,
                    output_key,
                    final_name,
                    "consumable",
                    item_data["rarity"],
                    output_amount,
                    None,
                    None,
                )

            # Add XP
            xp_msg = self._add_crafting_xp(discord_id, item_data.get("rarity", "Common"))

            logger.info(f"User {discord_id} crafted {output_amount}x {output_key}")
            return (
                True,
                f"Successfully crafted **{final_name}** x{output_amount}!{success_msg_extras}{xp_msg}",
                item_data,
            )

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

        # 3. Resolve Original Name (Handle prefixed quality items)
        original_name = item["item_name"]
        if item.get("item_source_table") == "equipment":
            try:
                # item_key for equipment is the ID
                db_id = int(item["item_key"])
                original_data = self.db.get_item_from_source_table("equipment", db_id)
                if original_data:
                    original_name = original_data["name"]
            except Exception:
                pass  # Fallback to stored name

        # 4. Calculate Rewards
        rewards = self.get_dismantle_rewards(original_name, item["rarity"])
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

    def experiment(self, discord_id: int, material_inv_ids: list[int]) -> tuple[bool, str, dict | None]:
        """
        Attempts to discover a recipe by combining materials.
        material_inv_ids: List of inventory IDs (primary keys) to consume.
        """
        # 1. Fetch Items and Validate Ownership
        input_keys = []

        # Check for duplicates in input IDs
        if len(material_inv_ids) != len(set(material_inv_ids)):
            return False, "Cannot use the same item stack multiple times.", None

        for inv_id in material_inv_ids:
            item = self.db.get_inventory_item(discord_id, inv_id)
            if not item:
                return False, "One or more materials not found.", None
            if item["item_type"] != "material":
                return False, "Only materials can be used for experiments.", None

            input_keys.append(item["item_key"])

        # 2. Check for Match
        input_set = set(input_keys)
        match = None

        for recipe in HIDDEN_RECIPES:
            if recipe["inputs"] == input_set:
                match = recipe
                break

        try:
            # 3. Consume Materials (Atomic-ish)
            for inv_id in material_inv_ids:
                if not self.db.consume_item_atomic(inv_id, 1):
                    logger.error(f"Failed to consume {inv_id} during experiment for {discord_id}")

            if match:
                # 4. Success Logic
                output_key = match["output_key"]
                output_amount = match["output_amount"]

                # Check what type of item it is
                item_data = CONSUMABLES.get(output_key)
                item_type = "consumable"
                if not item_data:
                    # Check Materials
                    item_data = MATERIALS.get(output_key)
                    item_type = "material"

                if not item_data:
                    return (
                        False,
                        f"System Error: Output {output_key} not defined.",
                        None,
                    )

                final_name = item_data["name"]

                self.db.add_inventory_item(
                    discord_id,
                    output_key,
                    final_name,
                    item_type,
                    item_data["rarity"],
                    output_amount,
                )

                # Add XP (Discovery Bonus)
                xp_msg = self._add_crafting_xp(discord_id, item_data.get("rarity", "Common"), is_discovery=True)

                logger.info(f"User {discord_id} discovered {output_key} via experiment.")
                return (
                    True,
                    f"✨ **Discovery!** You mixed the ingredients and created **{final_name}**!{xp_msg}",
                    item_data,
                )

            else:
                # 5. Failure Logic (Add Slag)
                slag_data = MATERIALS.get("slag")
                if slag_data:
                    self.db.add_inventory_item(
                        discord_id,
                        "slag",
                        slag_data["name"],
                        "material",
                        slag_data["rarity"],
                        1,
                    )
                return (
                    False,
                    "The mixture turns volatile and collapses into useless slag.",
                    None,
                )

        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Experiment data error for {discord_id}: {e}", exc_info=True)
            return False, "An error occurred during experimentation.", None
        except Exception as e:
            logger.error(f"Unexpected experiment error for {discord_id}: {e}", exc_info=True)
            return False, "An unexpected error occurred.", None
