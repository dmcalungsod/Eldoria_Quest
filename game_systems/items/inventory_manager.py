"""
inventory_manager.py

Manages player inventory: adding loot, removing items, and fetching the backpack.
"""

import sqlite3
from database.database_manager import DatabaseManager

class InventoryManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def add_item(self, discord_id: int, item_name: str, item_type: str, amount: int = 1):
        """
        Adds an item to the player's inventory. Stacks if it already exists.
        """
        conn = self.db.connect()
        cur = conn.cursor()

        # Check if item exists in inventory
        cur.execute("""
            SELECT count FROM inventory 
            WHERE discord_id = ? AND item_name = ? AND item_type = ?
        """, (discord_id, item_name, item_type))
        
        row = cur.fetchone()

        if row:
            # Stack it
            cur.execute("""
                UPDATE inventory SET count = count + ? 
                WHERE discord_id = ? AND item_name = ? AND item_type = ?
            """, (amount, discord_id, item_name, item_type))
        else:
            # Create new entry
            cur.execute("""
                INSERT INTO inventory (discord_id, item_name, item_type, count)
                VALUES (?, ?, ?, ?)
            """, (discord_id, item_name, item_type, amount))

        conn.commit()
        conn.close()

    def remove_item(self, discord_id: int, item_name: str, amount: int = 1) -> bool:
        """
        Removes items. Returns True if successful, False if not enough quantity.
        """
        conn = self.db.connect()
        cur = conn.cursor()

        cur.execute("SELECT count FROM inventory WHERE discord_id = ? AND item_name = ?", (discord_id, item_name))
        row = cur.fetchone()

        if not row or row['count'] < amount:
            conn.close()
            return False

        new_count = row['count'] - amount
        if new_count <= 0:
            cur.execute("DELETE FROM inventory WHERE discord_id = ? AND item_name = ?", (discord_id, item_name))
        else:
            cur.execute("UPDATE inventory SET count = ? WHERE discord_id = ? AND item_name = ?", (new_count, discord_id, item_name))

        conn.commit()
        conn.close()
        return True

    def get_inventory(self, discord_id: int):
        """
        Returns a list of dicts representing the player's bag.
        """
        conn = self.db.connect()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT item_name, item_type, count, equipped 
            FROM inventory 
            WHERE discord_id = ? 
            ORDER BY item_type, item_name
        """, (discord_id,))
        
        items = [dict(row) for row in cur.fetchall()]
        conn.close()
        return items