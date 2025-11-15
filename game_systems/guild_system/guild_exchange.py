"""
guild_exchange.py

Handles the logic for exchanging monster materials (Magic Stones, Drop Items)
for Gold (Valis) at the Guild Hall.
This is the core economic loop inspired by Danmachi.
"""

from database.database_manager import DatabaseManager
from game_systems.data.materials import MATERIALS
from typing import Tuple, Dict, List


class GuildExchange:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def _get_player_materials(self, discord_id: int) -> List[Dict]:
        """Fetches all items from inventory marked as 'material'."""
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT item_key, item_name, count FROM inventory WHERE discord_id = ? AND item_type = 'material'",
            (discord_id,),
        )
        materials = [dict(row) for row in cur.fetchall()]
        conn.close()
        return materials

    def calculate_exchange_value(self, discord_id: int) -> Tuple[int, List[Dict]]:
        """
        Calculates the total value of all materials in a player's inventory.
        Returns (total_value, list_of_materials).
        """
        player_mats = self._get_player_materials(discord_id)
        total_value = 0

        for item in player_mats:
            # Get the base value from our static data
            mat_data = MATERIALS.get(item["item_key"])
            if mat_data:
                item_value = mat_data.get("value", 0)
                total_value += item_value * item["count"]

        return total_value, player_mats

    def exchange_all_materials(self, discord_id: int) -> Tuple[int, List[Dict]]:
        """
        Sells all materials in the player's inventory.
        1. Calculates total value.
        2. Adds gold to player.
        3. Deletes materials from inventory.
        Returns (total_earned, list_of_sold_items).
        """
        total_value, sold_items = self.calculate_exchange_value(discord_id)

        if total_value == 0:
            return 0, []

        conn = self.db.connect()
        cur = conn.cursor()

        # 1. Add gold to player
        cur.execute(
            "UPDATE players SET gold = gold + ? WHERE discord_id = ?",
            (total_value, discord_id),
        )

        # 2. Delete all materials from inventory
        cur.execute(
            "DELETE FROM inventory WHERE discord_id = ? AND item_type = 'material'",
            (discord_id,),
        )

        conn.commit()
        conn.close()

        return total_value, sold_items
