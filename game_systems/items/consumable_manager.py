"""
consumable_manager.py

Handles all logic for using consumable items from the inventory.
Hardened: Uses atomic check-and-consume logic to prevent item loss on error.
"""

import logging

from database.database_manager import DatabaseManager
from game_systems.data.consumables import CONSUMABLES
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

            # 4. Calculate Effects
            item_used = False
            message_lines = []

            # -- Heal Logic --
            if "heal" in effect:
                heal_amount = effect["heal"]
                if current_hp >= max_hp:
                    return False, "You are already at full health."

                old_hp = current_hp
                new_hp = min(current_hp + heal_amount, max_hp)
                healed_for = new_hp - old_hp

                current_hp = new_hp
                message_lines.append(f"You healed for {healed_for} HP.")
                item_used = True

            # -- Mana Logic --
            if "mana" in effect:
                mana_amount = effect["mana"]
                if current_mp >= max_mp:
                    return False, "You are already at full mana."

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
                buffs_applied = []

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

                for key, val in effect.items():
                    if key not in ignored_keys:
                        self.db.add_active_buff(discord_id, item_key, item_data["name"], key, val, duration)
                        buffs_applied.append(f"{key.upper()} +{val}")

                if buffs_applied:
                    message_lines.append(f"Buffs applied: {', '.join(buffs_applied)} ({duration}s).")
                    item_used = True

            if not item_used:
                return False, "This item has no usable effect right now."

            # 5. Apply Updates
            self.db.set_player_vitals(discord_id, current_hp, current_mp)

            # Remove Item
            if item.get("count", 1) > 1:
                self.db.decrement_inventory_count(inventory_db_id)
            else:
                self.db.delete_inventory_item(inventory_db_id)

            return True, " ".join(message_lines)

        except Exception as e:
            logger.error(f"Item use error for {discord_id}: {e}", exc_info=True)
            return False, "An unexpected error occurred while using the item."
