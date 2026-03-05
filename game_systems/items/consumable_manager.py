"""
consumable_manager.py

Handles all logic for using consumable items from the inventory.
Hardened: Uses atomic check-and-consume logic to prevent item loss on error.
"""

import logging

from database.database_manager import DatabaseManager
from game_systems.data.consumables import CONSUMABLES
from game_systems.data.skills_data import SKILLS
from game_systems.items.inventory_manager import InventoryManager
from game_systems.player.player_stats import PlayerStats

logger = logging.getLogger("eldoria.consumables")


class ConsumableManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.inv_manager = InventoryManager(self.db)

    def _verify_consumable_data(self, discord_id: int, inventory_db_id: int) -> tuple[bool, str, dict, dict]:
        item = self.db.get_inventory_item(discord_id, inventory_db_id)
        if not item:
            return False, "Item not found in your inventory.", {}, {}
        if item.get("item_type") != "consumable":
            return False, "This item is not usable.", {}, {}

        item_key = item["item_key"]
        item_data = CONSUMABLES.get(item_key)
        if not item_data:
            return False, "Item data is missing. Cannot use.", {}, {}

        return True, "", item, item_data

    def _get_healing_multiplier(self, discord_id: int) -> float:
        healing_multiplier = 1.0
        try:
            skill_levels = self.db.get_player_skill_levels(discord_id)
            for s_key, s_level in skill_levels.items():
                skill_def = SKILLS.get(s_key)
                if skill_def and skill_def.get("type") == "Passive" and "passive_bonus" in skill_def:
                    bonuses = skill_def["passive_bonus"]
                    if "healing_item_potency" in bonuses:
                        base_potency = bonuses["healing_item_potency"]
                        scaling_potency = base_potency + (0.02 * (s_level - 1))
                        healing_multiplier += scaling_potency
        except Exception as e:
            logger.error(f"Error checking passive skills for {discord_id}: {e}")
        return healing_multiplier

    def _apply_healing(self, effect: dict, healing_multiplier: float, current_hp: int, max_hp: int, message_lines: list) -> tuple[bool, int]:
        item_used = False
        if "heal" in effect:
            base_heal = effect["heal"]
            heal_amount = int(base_heal * healing_multiplier)

            if current_hp < max_hp:
                old_hp = current_hp
                current_hp = min(current_hp + heal_amount, max_hp)
                healed_for = current_hp - old_hp

                msg = f"You healed for {healed_for} HP."
                if healing_multiplier > 1.0:
                    msg += f" (Boosted x{healing_multiplier:.1f})"
                message_lines.append(msg)
                item_used = True
        return item_used, current_hp

    def _apply_mana(self, effect: dict, current_mp: int, max_mp: int, message_lines: list) -> tuple[bool, int]:
        item_used = False
        if "mana" in effect:
            mana_amount = effect["mana"]
            if current_mp < max_mp:
                old_mp = current_mp
                current_mp = min(current_mp + mana_amount, max_mp)
                restored_for = current_mp - old_mp

                message_lines.append(f"You restored {restored_for} MP.")
                item_used = True
        return item_used, current_mp

    def _process_buffs(self, discord_id: int, item_data: dict, effect: dict, message_lines: list) -> tuple[bool, list]:
        item_used = False
        buffs_to_apply = []
        is_buff_item = item_data.get("type") == "buff"
        duration = effect.get("duration_s")

        if is_buff_item or duration:
            duration = duration or 300
            try:
                active_session = self.db.get_active_adventure(discord_id)
                field_kit_bonus = 0.0

                if active_session:
                    supplies = active_session.get("supplies", {})
                    if supplies.get("field_kit"):
                        field_kit_bonus = 0.05
                else:
                    inv_items = self.inv_manager.get_inventory(discord_id)
                    for inv_item in inv_items:
                        if inv_item["item_key"] == "field_kit":
                            field_kit_bonus = 0.05
                            break

                if field_kit_bonus > 0:
                    duration = int(duration * (1.0 + field_kit_bonus))
                    message_lines.append(f"(Field Kit: Duration +{int(field_kit_bonus * 100)}%)")
            except Exception as e:
                logger.error(f"Field Kit logic error: {e}")

            ignored_keys = {
                "heal", "mana", "duration_s", "cure_poison", "cure_bleed",
                "escape", "aoe_atk", "status", "chance",
            }

            buff_names_for_msg = []
            for key, val in effect.items():
                if key not in ignored_keys:
                    buffs_to_apply.append({"key": key, "val": val, "duration": duration})
                    buff_names_for_msg.append(f"{key.upper()} +{val}")

            if buff_names_for_msg:
                msg = f"Buffs applied: {', '.join(buff_names_for_msg)} ({duration}s)."
                message_lines.append(msg)
                item_used = True

        return item_used, buffs_to_apply


    def _can_use_consumable_effects(self, item_used: bool, effect: dict) -> tuple[bool, str]:
        if not item_used:
            if "heal" in effect and "mana" in effect:
                return False, "You are already at full health and mana."
            elif "heal" in effect:
                return False, "You are already at full health."
            elif "mana" in effect:
                return False, "You are already at full mana."
            else:
                return False, "This item has no usable effect right now."
        return True, ""

    def _execute_consumable_db_updates(self, discord_id: int, inventory_db_id: int, current_hp: int, current_mp: int, buffs_to_apply: list, item: dict, item_data: dict, message_lines: list) -> tuple[bool, str]:
        if not self.db.consume_item_atomic(inventory_db_id, 1):
            return False, "Item no longer available."

        try:
            self.db.set_player_vitals(discord_id, current_hp, current_mp)

            if buffs_to_apply:
                bulk_list = [
                    {
                        "buff_id": item["item_key"],
                        "name": item_data["name"],
                        "stat": b["key"],
                        "amount": b["val"],
                        "duration_s": b["duration"],
                    }
                    for b in buffs_to_apply
                ]
                self.db.add_active_buffs_bulk(discord_id, bulk_list)

            return True, " ".join(message_lines)

        except Exception as e:
            logger.error(f"Item use error for {discord_id} (Refunding): {e}", exc_info=True)
            self.db.increment_inventory_count(inventory_db_id, 1)
            raise e

    def use_item(self, discord_id: int, inventory_db_id: int) -> tuple[bool, str]:
        """
        Uses a consumable item from the inventory.
        inventory_db_id is the PRIMARY KEY (id) from the inventory collection.
        """
        try:
            valid, msg, item, item_data = self._verify_consumable_data(discord_id, inventory_db_id)
            if not valid:
                return False, msg

            effect = item_data.get("effect", {})
            vitals = self.db.get_player_vitals(discord_id)
            stats_json = self.db.get_player_stats_json(discord_id)

            if not vitals or not stats_json:
                return False, "Player data error."

            stats = PlayerStats.from_dict(stats_json)
            current_hp = vitals["current_hp"]
            current_mp = vitals["current_mp"]

            healing_multiplier = self._get_healing_multiplier(discord_id)

            message_lines = []
            item_used = False

            heal_used, current_hp = self._apply_healing(effect, healing_multiplier, current_hp, stats.max_hp, message_lines)
            item_used = item_used or heal_used

            mana_used, current_mp = self._apply_mana(effect, current_mp, stats.max_mp, message_lines)
            item_used = item_used or mana_used

            buffs_used, buffs_to_apply = self._process_buffs(discord_id, item_data, effect, message_lines)
            item_used = item_used or buffs_used

            valid, msg = self._can_use_consumable_effects(item_used, effect)
            if not valid:
                return False, msg

            return self._execute_consumable_db_updates(discord_id, inventory_db_id, current_hp, current_mp, buffs_to_apply, item, item_data, message_lines)

        except Exception as e:
            logger.error(f"Item use error for {discord_id}: {e}", exc_info=True)
            return False, "An unexpected error occurred while using the item."
