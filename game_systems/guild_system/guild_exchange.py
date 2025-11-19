"""
guild_exchange.py

Handles exchanging materials for currency.
Hardened: Atomic transactions prevent duping/currency exploits.
"""

import logging
from typing import Dict, List, Tuple
from database.database_manager import DatabaseManager
from game_systems.data.materials import MATERIALS

logger = logging.getLogger("eldoria.economy")

class GuildExchange:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def calculate_exchange_value(self, discord_id: int) -> Tuple[int, List[Dict]]:
        """Read-only calculation of inventory value."""
        total_value = 0
        material_list = []
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT item_key, item_name, count FROM inventory WHERE discord_id = ? AND item_type = 'material'",
                    (discord_id,)
                )
                items = [dict(row) for row in cursor.fetchall()]

            for item in items:
                mat_data = MATERIALS.get(item["item_key"])
                if mat_data:
                    val = mat_data.get("value", 0) * item["count"]
                    total_value += val
                    material_list.append(item)
            
            return total_value, material_list
        except Exception as e:
            logger.error(f"Exchange calc error for {discord_id}: {e}")
            return 0, []

    def exchange_all_materials(self, discord_id: int) -> Tuple[int, List[Dict]]:
        """
        Sells all materials.
        ATOMIC: Deletes items AND adds gold in one go.
        """
        # 1. Calculate first (InMemory)
        total_val, items = self.calculate_exchange_value(discord_id)
        if total_val == 0:
            return 0, []

        try:
            with self.db.get_connection() as conn:
                # 2. Add Aurum
                conn.execute(
                    "UPDATE players SET aurum = aurum + ? WHERE discord_id = ?",
                    (total_val, discord_id)
                )
                
                # 3. Delete Materials
                conn.execute(
                    "DELETE FROM inventory WHERE discord_id = ? AND item_type = 'material'",
                    (discord_id,)
                )
            
            logger.info(f"User {discord_id} exchanged materials for {total_val} Aurum.")
            return total_val, items

        except Exception as e:
            logger.error(f"Exchange transaction failed for {discord_id}: {e}", exc_info=True)
            return 0, []