"""
game_systems/items/inventory_manager.py

Manages player inventory with atomic database transactions.
Hardened against duplication bugs and concurrency issues.
"""

import logging
from typing import List, Dict, Any
from database.database_manager import DatabaseManager

logger = logging.getLogger("eldoria.items")

class InventoryManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def add_item(
        self,
        discord_id: int,
        item_key: str,
        item_name: str,
        item_type: str,
        rarity: str = "Common",
        amount: int = 1,
        slot: str = None,
        item_source_table: str = None,
    ) -> bool:
        """
        Adds an item to the player's inventory.
        Uses an atomic transaction to handle stacking or new insertions.
        """
        if amount <= 0:
            logger.warning(f"Attempted to add invalid amount {amount} of {item_key} for {discord_id}")
            return False

        try:
            with self.db.get_connection() as conn:
                # Check for existing stackable (unequipped) item
                cursor = conn.execute(
                    """
                    SELECT id, count FROM inventory
                    WHERE discord_id = ?
                      AND item_key = ?
                      AND rarity = ?
                      AND slot IS ?
                      AND item_source_table IS ?
                      AND equipped = 0
                    LIMIT 1
                    """,
                    (discord_id, item_key, rarity, slot, item_source_table),
                )
                row = cursor.fetchone()

                if row:
                    # Stack existing item
                    new_count = row["count"] + amount
                    conn.execute(
                        "UPDATE inventory SET count = ? WHERE id = ?",
                        (new_count, row["id"]),
                    )
                    logger.info(f"Stacked {amount}x {item_key} for user {discord_id}. New total: {new_count}")
                else:
                    # Create new entry
                    conn.execute(
                        """
                        INSERT INTO inventory (
                            discord_id, item_key, item_name, item_type,
                            rarity, slot, item_source_table, count, equipped
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                        """,
                        (discord_id, item_key, item_name, item_type, rarity, slot, item_source_table, amount),
                    )
                    logger.info(f"Inserted new item {item_key} (x{amount}) for user {discord_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to add item {item_key} for {discord_id}: {e}", exc_info=True)
            return False

    def remove_item(self, discord_id: int, item_key: str, amount: int = 1) -> bool:
        """
        Removes items safely. Returns True if successful, False if insufficient quantity.
        Prioritizes unequipped stacks.
        """
        if amount <= 0:
            return False

        try:
            with self.db.get_connection() as conn:
                # Lock row for update
                cursor = conn.execute(
                    "SELECT id, count FROM inventory WHERE discord_id = ? AND item_key = ? AND equipped = 0 LIMIT 1",
                    (discord_id, item_key),
                )
                row = cursor.fetchone()

                if not row or row["count"] < amount:
                    logger.warning(f"User {discord_id} tried to remove {amount} {item_key} but had insufficient stock.")
                    return False

                new_count = row["count"] - amount
                if new_count <= 0:
                    conn.execute("DELETE FROM inventory WHERE id = ?", (row["id"],))
                else:
                    conn.execute("UPDATE inventory SET count = ? WHERE id = ?", (new_count, row["id"]))
                
                logger.info(f"Removed {amount}x {item_key} from user {discord_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to remove item {item_key} for {discord_id}: {e}", exc_info=True)
            return False

    def get_inventory(self, discord_id: int) -> List[Dict[str, Any]]:
        """Fetches the player's full inventory."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT id, item_key, item_name, item_type, slot,
                           rarity, item_source_table, count, equipped
                    FROM inventory
                    WHERE discord_id = ?
                    ORDER BY item_type, item_name
                    """,
                    (discord_id,),
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to fetch inventory for {discord_id}: {e}", exc_info=True)
            return []