"""
consumable_manager.py

Handles all logic for using consumable items from the inventory.
"""

import json
from typing import Tuple

from database.database_manager import DatabaseManager
from game_systems.items.inventory_manager import InventoryManager
from game_systems.player.player_stats import PlayerStats
from game_systems.data.consumables import CONSUMABLES


class ConsumableManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.inv_manager = InventoryManager(self.db)

    def use_item(self, discord_id: int, inventory_db_id: int) -> Tuple[bool, str]:
        """
        Uses a consumable item from the inventory.
        inventory_db_id is the PRIMARY KEY (id) from the inventory table.
        """
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT item_key, item_type FROM inventory WHERE id = ? AND discord_id = ?",
            (inventory_db_id, discord_id),
        )
        item = cur.fetchone()
        conn.close()

        if not item:
            return False, "Item not found in your inventory."
        if item["item_type"] != "consumable":
            return False, "This item is not usable."

        # 1. Get Item Effect from static data
        item_key = item["item_key"]
        item_data = CONSUMABLES.get(item_key)
        if not item_data:
            return False, "Item data is missing. Cannot use."

        effect = item_data.get("effect", {})

        # 2. Get Player Vitals & Stats
        vitals = self.db.get_player_vitals(discord_id)
        stats_json = self.db.get_player_stats_json(discord_id)
        stats = PlayerStats.from_dict(stats_json)

        current_hp = vitals["current_hp"]
        current_mp = vitals["current_mp"]
        max_hp = stats.max_hp
        max_mp = stats.max_mp

        message_lines = []
        item_used = False

        # 3. Apply Effects
        if "heal" in effect:
            heal_amount = effect["heal"]
            if current_hp >= max_hp:
                return False, "You are already at full health."

            old_hp = current_hp
            current_hp = min(current_hp + heal_amount, max_hp)
            healed_for = current_hp - old_hp
            message_lines.append(f"You healed for {healed_for} HP.")
            item_used = True

        if "mana" in effect:
            mana_amount = effect["mana"]
            if current_mp >= max_mp:
                return False, "You are already at full mana."

            old_mp = current_mp
            current_mp = min(current_mp + mana_amount, max_mp)
            restored_for = current_mp - old_mp
            message_lines.append(f"You restored {restored_for} MP.")
            item_used = True

        # (Future: Add 'buff' logic here)

        if not item_used:
            return False, "This item has no usable effect right now."

        # 4. Save new vitals and remove item
        self.db.set_player_vitals(discord_id, current_hp, current_mp)
        self.inv_manager.remove_item(discord_id, item_key, 1)

        return True, " ".join(message_lines)
