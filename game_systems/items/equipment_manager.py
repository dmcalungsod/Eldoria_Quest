"""
equipment_manager.py

Handles all logic for equipping, unequipping, and recalculating stats
based on a player's gear.
"""

import sqlite3
from typing import Dict, Tuple

from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats


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
        cur.execute(f"SELECT * FROM {source_table} WHERE id = ?", (item_key,))
        item_row = cur.fetchone()
        conn.close()

        if not item_row:
            return {}

        bonuses = {}
        for key, stat in self.stat_map.items():
            if key in item_row.keys() and item_row[key] != 0:
                bonuses[stat] = item_row[key]
        return bonuses

    def recalculate_player_stats(self, discord_id: int):
        """
        Recalculates a player's total stats based on equipped items.
        1. Fetches base stats.
        2. Creates a PlayerStats object.
        3. Fetches all equipped items.
        4. Gets bonuses for each item and applies them.
        5. Saves the new stats_json back to the database.
        """
        base_stats_json = self.db.get_player_stats_json(discord_id)
        if not base_stats_json:
            print(f"Error: Could not find base stats for {discord_id}")
            return

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

    def equip_item(self, discord_id: int, inventory_db_id: int) -> Tuple[bool, str]:
        """
        Equips an item from the inventory.
        inventory_db_id is the PRIMARY KEY (id) from the inventory table.
        """
        conn = self.db.connect()
        cur = conn.cursor()

        cur.execute(
            "SELECT item_type, slot, equipped FROM inventory WHERE id = ? AND discord_id = ?",
            (inventory_db_id, discord_id),
        )
        item = cur.fetchone()

        if not item:
            conn.close()
            return False, "Item not found in your inventory."
        if item["item_type"] != "equipment":
            conn.close()
            return False, "This item cannot be equipped."
        if item["equipped"] == 1:
            conn.close()
            return False, "This item is already equipped."

        slot_to_equip = item["slot"]

        # Unequip any item currently in that slot
        cur.execute(
            """
            UPDATE inventory SET equipped = 0 
            WHERE discord_id = ? AND slot = ? AND equipped = 1
        """,
            (discord_id, slot_to_equip),
        )

        # Equip the new item
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
        Unequips an item from the inventory.
        """
        conn = self.db.connect()
        cur = conn.cursor()

        cur.execute(
            "SELECT equipped FROM inventory WHERE id = ? AND discord_id = ?",
            (inventory_db_id, discord_id),
        )
        item = cur.fetchone()

        if not item:
            conn.close()
            return False, "Item not found in your inventory."
        if item["equipped"] == 0:
            conn.close()
            return False, "This item is not equipped."

        # Unequip the item
        cur.execute(
            "UPDATE inventory SET equipped = 0 WHERE id = ?", (inventory_db_id,)
        )
        conn.commit()
        conn.close()

        # Recalculate stats after changes
        self.recalculate_player_stats(discord_id)
        return True, "Item unequipped."
