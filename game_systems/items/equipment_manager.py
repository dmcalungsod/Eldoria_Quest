"""
equipment_manager.py

Handles all logic for equipping, unequipping, and recalculating stats
based on a player's gear.
"""

import sqlite3
from typing import Dict, Tuple

from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats

# --- NEW IMPORT ---
from game_systems.data.class_data import CLASSES

# --- END IMPORT ---


class EquipmentManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.stat_bonus_keys = [
            "str_bonus",
            "end_bonus",
            "dex_bonus",
            "agi_bonus",
            "mag_bonus",
            "lck_bonus",
        ]
        self.stat_map = {
            "str_bonus": "STR",
            "end_bonus": "END",
            "dex_bonus": "DEX",
            "agi_bonus": "AGI",
            "mag_bonus": "MAG",
            "lck_bonus": "LCK",
        }
        self.valid_tables = ["equipment", "class_equipment"]

    # --- NEW HELPER FUNCTION ---
    def _get_player_allowed_slots(self, discord_id: int) -> list:
        """Fetches the player's class and returns their allowed slots."""
        player_row = self.db.get_player(discord_id)
        if not player_row:
            return []

        player_class_id = player_row["class_id"]

        # Find the class name from the ID
        class_name = None
        for name, data in CLASSES.items():
            if data["id"] == player_class_id:
                class_name = name
                break

        if class_name:
            return CLASSES[class_name].get("allowed_slots", [])

        return []

    # --- END HELPER ---

    def _get_item_bonuses(self, item_key: str, source_table: str) -> Dict:
        """
        Safely fetches the stat bonuses for a single item from its source table.
        """
        if source_table not in self.valid_tables:
            print(f"Error: Invalid source table '{source_table}'")
            return {}

        conn = self.db.connect()
        cur = conn.cursor()

        # f-string is safe here due to the valid_tables check
        query_table = "equipment" if source_table == "equipment" else "class_equipment"
        cur.execute(f"SELECT * FROM {query_table} WHERE id = ?", (item_key,))
        item_row = cur.fetchone()
        conn.close()

        if not item_row:
            return {}

        bonuses = {}
        for key, stat in self.stat_map.items():
            if key in item_row.keys() and item_row[key] != 0:
                bonuses[stat] = item_row[key]
        return bonuses

    def recalculate_player_stats(self, discord_id: int) -> PlayerStats:
        """
        Recalculates a player's total stats based on equipped items.
        1. Fetches base stats.
        2. Creates a PlayerStats object.
        3. Fetches all equipped items.
        4. Gets bonuses for each item and applies them.
        5. Saves the new stats_json back to the database.

        Returns the updated PlayerStats object.
        """
        base_stats_json = self.db.get_player_stats_json(discord_id)
        if not base_stats_json:
            print(f"Error: Could not find base stats for {discord_id}")
            # Return an empty stats object to prevent crashes
            return PlayerStats()

        # 1. Create PlayerStats object from BASE stats
        stats = PlayerStats.from_dict(base_stats_json)

        # 2. Fetch all equipped items
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT item_key, item_source_table FROM inventory
            WHERE discord_id = ? AND equipped = 1
        """,
            (discord_id,),
        )
        equipped_items = cur.fetchall()
        conn.close()

        # 3. Apply bonuses from items
        for item in equipped_items:
            bonuses = self._get_item_bonuses(
                item["item_key"], item["item_source_table"]
            )
            for stat, value in bonuses.items():
                stats.add_bonus_stat(stat, value)

        # 4. Save the new stats (base + bonus) back to the DB
        self.db.update_player_stats(discord_id, stats.to_dict())

        # --- NEW: Return the recalculated stats object ---
        return stats
        # --- END NEW ---

    def equip_item(self, discord_id: int, inventory_db_id: int) -> Tuple[bool, str]:
        """
        Equips an item from an inventory stack.
        If stack count > 1, it splits one off.
        If count == 1, it equips the stack.
        """
        conn = self.db.connect()
        cur = conn.cursor()

        # Get the full details of the stack we're equipping from
        cur.execute(
            "SELECT * FROM inventory WHERE id = ? AND discord_id = ?",
            (inventory_db_id, discord_id),
        )
        item_stack = cur.fetchone()

        if not item_stack:
            conn.close()
            return False, "Item not found in your inventory."
        if item_stack["item_type"] != "equipment":
            conn.close()
            return False, "This item cannot be equipped."
        if item_stack["equipped"] == 1:
            conn.close()
            return False, "This item is already equipped."

        slot_to_equip = item_stack["slot"]

        # --- NEW CLASS RESTRICTION ---
        allowed_slots = self._get_player_allowed_slots(discord_id)
        if slot_to_equip not in allowed_slots:
            conn.close()
            return False, f"Your class cannot equip this item type ({slot_to_equip})."
        # --- END NEW RESTRICTION ---

        # Unequip any item currently in that slot
        cur.execute(
            """
            SELECT id FROM inventory 
            WHERE discord_id = ? AND slot = ? AND equipped = 1
        """,
            (discord_id, slot_to_equip),
        )
        item_to_unequip = cur.fetchone()

        # --- We must close and re-open connection if we call another self. method ---
        conn.close()

        if item_to_unequip:
            # Use the new unequip logic to handle stacking
            self.unequip_item(discord_id, item_to_unequip["id"])

        # Re-open connection to finish the equip
        conn = self.db.connect()
        cur = conn.cursor()

        # Re-fetch the item_stack in case it was modified by the unequip
        cur.execute(
            "SELECT * FROM inventory WHERE id = ? AND discord_id = ?",
            (inventory_db_id, discord_id),
        )
        item_stack = cur.fetchone()

        # Final check
        if not item_stack or item_stack["equipped"] == 1:
            conn.close()
            # This can happen if the item was merged by the unequip call
            return True, "Item equipped."

        # Now, equip the new item
        if item_stack["count"] > 1:
            # 1. Decrement the stack
            cur.execute(
                "UPDATE inventory SET count = count - 1 WHERE id = ?",
                (inventory_db_id,),
            )

            # 2. Create a new, separate row for the equipped item
            cur.execute(
                """
                INSERT INTO inventory (discord_id, item_key, item_name, item_type, rarity, 
                                       slot, item_source_table, count, equipped)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1)
                """,
                (
                    discord_id,
                    item_stack["item_key"],
                    item_stack["item_name"],
                    item_stack["item_type"],
                    item_stack["rarity"],
                    item_stack["slot"],
                    item_stack["item_source_table"],
                ),
            )
        else:
            # Just equip the stack of 1
            cur.execute(
                "UPDATE inventory SET equipped = 1 WHERE id = ?", (inventory_db_id,)
            )

        conn.commit()
        conn.close()

        # Recalculate stats after changes
        self.recalculate_player_stats(discord_id)
        return True, "Item equipped."

    def unequip_item(self, discord_id: int, inventory_db_id: int) -> Tuple[bool, str]:
        """
        Unequips an item, merging it with an existing unequipped stack if possible.
        """
        conn = self.db.connect()
        cur = conn.cursor()

        # Get the details of the item we are unequipping
        cur.execute(
            "SELECT * FROM inventory WHERE id = ? AND discord_id = ?",
            (inventory_db_id, discord_id),
        )
        item_to_unequip = cur.fetchone()

        if not item_to_unequip:
            conn.close()
            return False, "Item not found in your inventory."
        if item_to_unequip["equipped"] == 0:
            conn.close()
            return False, "This item is not equipped."

        # --- THIS IS THE FIX ---
        # Now, find an unequipped stack of the *exact same* item
        cur.execute(
            """
            SELECT id FROM inventory
            WHERE discord_id = ? 
              AND item_key = ? 
              AND rarity = ?
              AND slot = ?
              AND item_source_table = ?
              AND equipped = 0
            LIMIT 1
        """,
            (
                discord_id,
                item_to_unequip["item_key"],
                item_to_unequip["rarity"],
                item_to_unequip["slot"],
                item_to_unequip["item_source_table"],
            ),
        )
        stack_row = cur.fetchone()
        # --- END OF FIX ---

        if stack_row:
            # A stack exists! Add this item to it and delete the equipped row.

            # 1. Increment the stack
            cur.execute(
                "UPDATE inventory SET count = count + 1 WHERE id = ?",
                (stack_row["id"],),
            )

            # 2. Delete the (now unequipped) item
            cur.execute("DELETE FROM inventory WHERE id = ?", (inventory_db_id,))

        else:
            # No stack exists. This item becomes the new unequipped stack.
            # We just set its equipped status to 0 and its count to 1.
            cur.execute(
                "UPDATE inventory SET equipped = 0, count = 1 WHERE id = ?",
                (inventory_db_id,),
            )

        conn.commit()
        conn.close()

        # Recalculate stats after changes
        self.recalculate_player_stats(discord_id)
        return True, "Item unequipped."
