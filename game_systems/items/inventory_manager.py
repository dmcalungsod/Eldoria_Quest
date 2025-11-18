"""
inventory_manager.py

Manages player inventory: adding loot, removing items, and fetching the backpack.
Now uses 'item_key' as the primary identifier.
"""

from database.database_manager import DatabaseManager


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
    ):
        """
        Adds an item to the player's inventory using its item_key.
        Stacks if it already exists (and is not equipped).
        """
        conn = self.db.connect()
        cur = conn.cursor()

        # --- THIS IS THE FIX ---
        # We must find a stack that matches ALL properties, not just the key.
        cur.execute(
            """
            SELECT id, count FROM inventory 
            WHERE discord_id = ? 
              AND item_key = ? 
              AND rarity = ?
              AND slot = ? 
              AND item_source_table = ?
              AND equipped = 0
            LIMIT 1
            """,
            (discord_id, item_key, rarity, slot, item_source_table),
        )
        row = cur.fetchone()
        # --- END OF FIX ---

        if row:
            # Stack it on the existing unequipped row
            cur.execute(
                """
                UPDATE inventory SET count = count + ? 
                WHERE id = ?
            """,
                (amount, row["id"]),
            )
        else:
            # Create new entry (it will default to equipped=0)
            cur.execute(
                """
                INSERT INTO inventory (discord_id, item_key, item_name, item_type, 
                                       rarity, slot, item_source_table, count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    discord_id,
                    item_key,
                    item_name,
                    item_type,
                    rarity,
                    slot,
                    item_source_table,
                    amount,
                ),
            )

        conn.commit()
        conn.close()

    def remove_item(self, discord_id: int, item_key: str, amount: int = 1) -> bool:
        """
        Removes items by item_key. Returns True if successful.
        This primarily targets unequipped stacks.
        """
        conn = self.db.connect()
        cur = conn.cursor()

        # Find an unequipped stack of the item
        # Note: This is simplified and just finds *any* unequipped stack
        # of the item. For selling, this is fine.
        cur.execute(
            "SELECT id, count FROM inventory WHERE discord_id = ? AND item_key = ? AND equipped = 0 LIMIT 1",
            (discord_id, item_key),
        )
        row = cur.fetchone()

        if not row or row["count"] < amount:
            conn.close()
            return False  # Not enough items

        new_count = row["count"] - amount
        if new_count <= 0:
            cur.execute(
                "DELETE FROM inventory WHERE id = ?",
                (row["id"],),
            )
        else:
            cur.execute(
                "UPDATE inventory SET count = ? WHERE id = ?",
                (new_count, row["id"]),
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
            SELECT id, item_key, item_name, item_type, slot, 
                   rarity, item_source_table, count, equipped 
            FROM inventory 
            WHERE discord_id = ? 
            ORDER BY item_type, item_name
        """,
            (discord_id,),
        )

        items = [dict(row) for row in cur.fetchall()]
        conn.close()
        return items
