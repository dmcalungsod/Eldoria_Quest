"""
game_systems/items/inventory_manager.py

Manages player inventory with DatabaseManager methods.
Hardened against duplication bugs and concurrency issues.
"""

import logging
from typing import Any

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
        Uses DatabaseManager methods for stack merging or insertion.
        """
        if amount <= 0:
            logger.warning(f"Attempted to add invalid amount {amount} of {item_key} for {discord_id}")
            return False

        try:
            self.db.add_inventory_item(
                discord_id, item_key, item_name, item_type, rarity, amount, slot, item_source_table
            )
            logger.info(f"Added {amount}x {item_key} for user {discord_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add item {item_key} for {discord_id}: {e}", exc_info=True)
            return False

    def add_items_bulk(self, discord_id: int, items: list[dict]) -> bool:
        """
        Adds multiple items to inventory efficiently.
        Delegates to DatabaseManager.add_inventory_items_bulk.
        """
        if not items:
            return True

        self.db.add_inventory_items_bulk(discord_id, items)
        return True

    def remove_item(self, discord_id: int, item_key: str, amount: int = 1) -> bool:
        """
        Removes items safely. Returns True if successful, False if insufficient quantity.
        Prioritizes unequipped stacks.
        """
        if amount <= 0:
            return False

        try:
            return self.db.remove_inventory_item(discord_id, item_key, amount)
        except Exception as e:
            logger.error(f"Failed to remove item {item_key} for {discord_id}: {e}", exc_info=True)
            return False

    def get_inventory(self, discord_id: int) -> list[dict[str, Any]]:
        """Fetches the player's full inventory."""
        try:
            return self.db.get_inventory_items(discord_id)
        except Exception as e:
            logger.error(f"Failed to fetch inventory for {discord_id}: {e}", exc_info=True)
            return []
