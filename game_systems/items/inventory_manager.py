"""
inventory_manager.py

Manages player inventory: adding loot, removing items, and fetching the backpack.
Now uses 'item_key' as the primary identifier.
"""

import sqlite3
from database.database_manager import DatabaseManager


class InventoryManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def add_item(self, discord_id: int, item_key: str, item_name: str, item_type: str, amount: int = 1):
        """
        Adds an item to the player's inventory using its item_key.
        Stacks if it already exists.
        """
        conn = self.db.connect()
        cur = conn.cursor()

        # Check if item exists in inventory by key
        cur.execute(
            """
            SELECT count FROM inventory 
            WHERE discord_id = ? AND item_key = ? AND item_type = ?
        """,
            (discord_id, item_key, item_type),
        )

        row = cur.fetchone()

        if row:
            # Stack it
            cur.execute(
                """
                UPDATE inventory SET count = count + ? 
                WHERE discord_id = ? AND item_key = ? AND item_type = ?
            """,
                (amount, discord_id, item_key, item_type),
            )
        else:
            # Create new entry
            cur.execute(
                """
                INSERT INTO inventory (discord_id, item_key, item_name, item_type, count)
                VALUES (?, ?, ?, ?, ?)
            """,
                (discord_id, item_key, item_name, item_type, amount),
            )

        conn.commit()
        conn.close()

    def remove_item(self, discord_id: int, item_key: str, amount: int = 1) -> bool:
        """
        Removes items by item_key. Returns True if successful.
        """
        conn = self.db.connect()
        cur = conn.cursor()

        cur.execute(
            "SELECT count FROM inventory WHERE discord_id = ? AND item_key = ?",
            (discord_id, item_key),
        )
        row = cur.fetchone()

        if not row or row["count"] < amount:
            conn.close()
            return False  # Not enough items

        new_count = row["count"] - amount
        if new_count <= 0:
            cur.execute(
                "DELETE FROM inventory WHERE discord_id = ? AND item_key = ?",
                (discord_id, item_key),
            )
        else:
            cur.execute(
                "UPDATE inventory SET count = ? WHERE discord_id = ? AND item_key = ?",
                (new_count, discord_id, item_key),
            )

        conn.commit()
        conn.close()
        return True

    def get_inventory(self, discord_id: int):
        """
        Returns a list of dicts representing the player's bag.
        """
        conn = self.db.connect()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT item_key, item_name, item_type, count, equipped 
            FROM inventory 
            WHERE discord_id = ? 
            ORDER BY item_type, item_name
        """,
            (discord_id,),
        )

        items = [dict(row) for row in cur.fetchall()]
        conn.close()
        return items