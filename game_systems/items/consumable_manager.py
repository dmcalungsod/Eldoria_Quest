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

    def use_item(self, discord_id: int, inventory_db_id: int) -> tuple[bool, str]:
        """
        Uses a consumable item from the inventory.
        inventory_db_id is the PRIMARY KEY (id) from the inventory collection.
        """
        try:
            # 1. Fetch Item & Verify Ownership
            item = self.db.get_inventory_item(discord_id, inventory_db_id)

            if not item:
                return False, "Item not found in your inventory."
            if item.get("item_type") != "consumable":
                return False, "This item is not usable."

            # 2. Get Static Item Data
            item_key = item["item_key"]
            item_data = CONSUMABLES.get(item_key)
            if not item_data:
                return False, "Item data is missing. Cannot use."

            effect = item_data.get("effect", {})

            # 3. Get Player Vitals & Stats
            vitals = self.db.get_player_vitals(discord_id)
            stats_json = self.db.get_player_stats_json(discord_id)

            if not vitals or not stats_json:
                return False, "Player data error."

            stats = PlayerStats.from_dict(stats_json)

            current_hp = vitals["current_hp"]
            current_mp = vitals["current_mp"]
            max_hp = stats.max_hp
            max_mp = stats.max_mp

            # --- PASSIVE SKILL CHECK (Triage) ---
            healing_multiplier = 1.0
            try:
                skill_levels = self.db.get_player_skill_levels(discord_id)
                for s_key, s_level in skill_levels.items():
                    skill_def = SKILLS.get(s_key)
                    if (
                        skill_def
                        and skill_def.get("type") == "Passive"
                        and "passive_bonus" in skill_def
                    ):
                        bonuses = skill_def["passive_bonus"]
                        if "healing_item_potency" in bonuses:
                            # 0.2 * level
                            healing_multiplier += bonuses["healing_item_potency"] * s_level
            except Exception as e:
                logger.error(f"Error checking passive skills for {discord_id}: {e}")

            # 4. Calculate Effects (In Memory Only)
            item_used = False
            message_lines = []
            buffs_to_apply = []

            # -- Heal Logic --
            if "heal" in effect:
                base_heal = effect["heal"]
                heal_amount = int(base_heal * healing_multiplier)

                if current_hp < max_hp:
                    old_hp = current_hp
                    new_hp = min(current_hp + heal_amount, max_hp)
                    healed_for = new_hp - old_hp

                    current_hp = new_hp
                    msg = f"You healed for {healed_for} HP."
                    if healing_multiplier > 1.0:
                        msg += f" (Boosted x{healing_multiplier:.1f})"
                    message_lines.append(msg)
                    item_used = True

            # -- Mana Logic --
            if "mana" in effect:
                mana_amount = effect["mana"]
                if current_mp < max_mp:
                    old_mp = current_mp
                    new_mp = min(current_mp + mana_amount, max_mp)
                    restored_for = new_mp - old_mp

                    current_mp = new_mp
                    message_lines.append(f"You restored {restored_for} MP.")
                    item_used = True

            # -- Buff Logic --
            is_buff_item = item_data.get("type") == "buff"
            duration = effect.get("duration_s")

            if is_buff_item or duration:
                duration = duration or 300

                ignored_keys = {
                    "heal",
                    "mana",
                    "duration_s",
                    "cure_poison",
                    "cure_bleed",
                    "escape",
                    "aoe_atk",
                    "status",
                    "chance",
                }

                buff_names_for_msg = []
                for key, val in effect.items():
                    if key not in ignored_keys:
                        # Defer DB write until after consumption
                        buffs_to_apply.append({"key": key, "val": val, "duration": duration})
                        buff_names_for_msg.append(f"{key.upper()} +{val}")

                if buff_names_for_msg:
                    message_lines.append(f"Buffs applied: {', '.join(buff_names_for_msg)} ({duration}s).")
                    item_used = True

            if not item_used:
                if "heal" in effect and "mana" in effect:
                    return False, "You are already at full health and mana."
                elif "heal" in effect:
                    return False, "You are already at full health."
                elif "mana" in effect:
                    return False, "You are already at full mana."
                else:
                    return False, "This item has no usable effect right now."

            # 5. Consume Item Atomically (Fixes Race Condition)
            # We do this BEFORE applying effects to prevent duplication
            if not self.db.consume_item_atomic(inventory_db_id, 1):
                return False, "Item no longer available."

            try:
                # 6. Apply Updates (Vitals)
                self.db.set_player_vitals(discord_id, current_hp, current_mp)

                # 7. Apply Buffs (Deferred)
                if buffs_to_apply:
                    bulk_list = []
                    for b in buffs_to_apply:
                        # Map to add_active_buffs_bulk format
                        bulk_list.append(
                            {
                                "buff_id": item_key,
                                "name": item_data["name"],
                                "stat": b["key"],
                                "amount": b["val"],
                                "duration_s": b["duration"],
                            }
                        )
                    self.db.add_active_buffs_bulk(discord_id, bulk_list)

                return True, " ".join(message_lines)

            except Exception as e:
                # Rollback: Refund item if effect application fails
                logger.error(f"Item use error for {discord_id} (Refunding): {e}", exc_info=True)
                self.db.increment_inventory_count(inventory_db_id, 1)
                # Re-raise to be caught by outer block for generic error message
                raise e

        except Exception as e:
            logger.error(f"Item use error for {discord_id}: {e}", exc_info=True)
            return False, "An unexpected error occurred while using the item."
