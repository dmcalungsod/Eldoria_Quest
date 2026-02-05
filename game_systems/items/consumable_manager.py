"""
consumable_manager.py

Handles all logic for using consumable items from the inventory.
Hardened: Uses atomic check-and-consume logic to prevent item loss on error.
"""

import json
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
        inventory_db_id is the PRIMARY KEY (id) from the inventory table.
        Transactional: Deducts item AND applies effect simultaneously.
        """
        try:
            with self.db.get_connection() as conn:
                # 1. Fetch Item & Verify Ownership
                item = conn.execute(
                    "SELECT id, item_key, item_type, count FROM inventory WHERE id = ? AND discord_id = ?",
                    (inventory_db_id, discord_id),
                ).fetchone()

                if not item:
                    return False, "Item not found in your inventory."
                if item["item_type"] != "consumable":
                    return False, "This item is not usable."

                # 2. Get Static Item Data
                item_key = item["item_key"]
                item_data = CONSUMABLES.get(item_key)
                if not item_data:
                    return False, "Item data is missing. Cannot use."

                effect = item_data.get("effect", {})

                # 3. Get Player Vitals & Stats
                p_row = conn.execute(
                    "SELECT current_hp, current_mp FROM players WHERE discord_id = ?", (discord_id,)
                ).fetchone()

                s_row = conn.execute("SELECT stats_json FROM stats WHERE discord_id = ?", (discord_id,)).fetchone()

                if not p_row or not s_row:
                    return False, "Player data error."

                stats = PlayerStats.from_dict(json.loads(s_row["stats_json"]))

                current_hp = p_row["current_hp"]
                current_mp = p_row["current_mp"]
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

                    current_hp = new_hp  # Update local var for DB write later
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

                    current_mp = new_mp  # Update local var for DB write later
                    message_lines.append(f"You restored {restored_for} MP.")
                    item_used = True

                # -- Buff Logic --
                # Treat as buff if explicit type OR has duration
                is_buff_item = item_data.get("type") == "buff"
                duration = effect.get("duration_s")

                if is_buff_item or duration:
                    duration = duration or 300  # Default fallback
                    buffs_applied = []

                    # Keys to ignore as they are immediate effects or metadata
                    ignored_keys = {
                        "heal", "mana", "duration_s",
                        "cure_poison", "cure_bleed",
                        "escape", "aoe_atk", "status", "chance"
                    }

                    for key, val in effect.items():
                        if key not in ignored_keys:
                            # Store this effect as an active buff
                            self.db.add_active_buff(
                                discord_id,
                                item_key,
                                item_data["name"],
                                key,
                                val,
                                duration
                            )
                            buffs_applied.append(f"{key.upper()} +{val}")

                    if buffs_applied:
                        message_lines.append(f"Buffs applied: {', '.join(buffs_applied)} ({duration}s).")
                        item_used = True

                if not item_used:
                    return False, "This item has no usable effect right now."

                # 5. Apply Updates to DB (Atomically)

                # Update Vitals
                conn.execute(
                    "UPDATE players SET current_hp = ?, current_mp = ? WHERE discord_id = ?",
                    (current_hp, current_mp, discord_id),
                )

                # Remove Item
                if item["count"] > 1:
                    conn.execute("UPDATE inventory SET count = count - 1 WHERE id = ?", (inventory_db_id,))
                else:
                    conn.execute("DELETE FROM inventory WHERE id = ?", (inventory_db_id,))

                return True, " ".join(message_lines)

        except Exception as e:
            logger.error(f"Item use error for {discord_id}: {e}", exc_info=True)
            return False, "An unexpected error occurred while using the item."
