"""
guild_exchange.py

Handles exchanging materials for currency.
Hardened: Uses DatabaseManager methods to prevent duping/currency exploits.
"""

import logging

from database.database_manager import DatabaseManager
from game_systems.data.materials import MATERIALS

logger = logging.getLogger("eldoria.economy")


class GuildExchange:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def calculate_exchange_value(self, discord_id: int) -> tuple[int, list[dict]]:
        """Read-only calculation of inventory value."""
        total_value = 0
        material_list = []

        try:
            items = list(
                self.db._col("inventory").find(
                    {"discord_id": discord_id, "item_type": "material"},
                    {"_id": 0, "item_key": 1, "item_name": 1, "count": 1},
                )
            )

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

    def exchange_all_materials(self, discord_id: int) -> tuple[int, list[dict]]:
        """
        Sells all materials.
        Deletes items individually to prevent race conditions, then adds gold.
        """
        total_value = 0
        sold_items = []

        try:
            # 1. Fetch all material items (just IDs and counts first)
            cursor = self.db._col("inventory").find({"discord_id": discord_id, "item_type": "material"})

            # 2. Iterate and attempt to delete each item atomically
            for item in cursor:
                # Atomically delete: returns the document if found and deleted, None otherwise
                deleted_item = self.db._col("inventory").find_one_and_delete(
                    {"id": item["id"], "discord_id": discord_id}
                )

                if deleted_item:
                    mat_data = MATERIALS.get(deleted_item["item_key"])
                    if mat_data:
                        val = mat_data.get("value", 0) * deleted_item["count"]
                        total_value += val
                        sold_items.append(deleted_item)

            # 3. Add Aurum (only for items we successfully deleted)
            if total_value > 0:
                self.db.increment_player_fields(discord_id, aurum=total_value)
                logger.info(f"User {discord_id} exchanged materials for {total_value} Aurum.")

            return total_value, sold_items

        except Exception as e:
            logger.error(f"Exchange transaction failed for {discord_id}: {e}", exc_info=True)
            return 0, []
