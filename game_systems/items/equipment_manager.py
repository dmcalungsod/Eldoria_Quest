"""
game_systems/items/equipment_manager.py

Handles equipping/unequipping and stat recalculation.
Hardened: Atomic equipment swaps and safe dynamic SQL.
"""

import math
import logging
from typing import Tuple, Dict
from database.database_manager import DatabaseManager
from game_systems.data.class_data import CLASSES
from game_systems.data.skills_data import SKILLS
from game_systems.player.player_stats import PlayerStats

logger = logging.getLogger("eldoria.equipment")

class EquipmentManager:
    # Whitelist valid tables to prevent injection
    VALID_TABLES = {"equipment", "class_equipment"}
    
    STAT_MAP = {
        "str_bonus": "STR", "end_bonus": "END", "dex_bonus": "DEX",
        "agi_bonus": "AGI", "mag_bonus": "MAG", "lck_bonus": "LCK",
    }

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def _get_player_allowed_slots(self, conn, discord_id: int) -> list:
        """Internal helper using an existing connection."""
        row = conn.execute("SELECT class_id FROM players WHERE discord_id = ?", (discord_id,)).fetchone()
        if not row:
            return []
        
        for name, data in CLASSES.items():
            if data["id"] == row["class_id"]:
                return data.get("allowed_slots", [])
        return []

    def recalculate_player_stats(self, discord_id: int) -> PlayerStats:
        """
        Recalculates a player's total stats based on equipped items AND passive skills.
        Transactional to ensure data consistency.
        """
        try:
            with self.db.get_connection() as conn:
                # 1. Get Base Stats
                row = conn.execute("SELECT stats_json FROM stats WHERE discord_id = ?", (discord_id,)).fetchone()
                if not row:
                    return PlayerStats()
                
                try:
                    stats = PlayerStats.from_dict(self.db.get_player_stats_json(discord_id))
                except Exception:
                    stats = PlayerStats()

                # 2. Apply Equipped Item Bonuses
                equipped_items = conn.execute(
                    "SELECT item_key, item_source_table FROM inventory WHERE discord_id = ? AND equipped = 1",
                    (discord_id,)
                ).fetchall()

                for item in equipped_items:
                    table = item["item_source_table"]
                    if table not in self.VALID_TABLES:
                        continue
                    
                    # Safe F-string because table is whitelisted
                    item_data = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (item["item_key"],)).fetchone()
                    if item_data:
                        for col, stat_name in self.STAT_MAP.items():
                            if col in item_data.keys() and item_data[col]:
                                stats.add_bonus_stat(stat_name, item_data[col])

                # 3. Apply Passive Skill Bonuses
                player_skills = conn.execute(
                    "SELECT skill_key, skill_level FROM player_skills WHERE discord_id = ?",
                    (discord_id,)
                ).fetchall()

                for p_skill in player_skills:
                    skill_data = SKILLS.get(p_skill["skill_key"])
                    if skill_data and skill_data.get("type") == "Passive" and "passive_bonus" in skill_data:
                        level = p_skill["skill_level"]
                        
                        for stat_key, percent in skill_data["passive_bonus"].items():
                            if stat_key.endswith("_percent"):
                                stat_name = stat_key.split("_")[0].upper()
                                # Get current total for percentage calc
                                current_total = getattr(stats, stat_name.lower(), 0)
                                if current_total == 0: 
                                    # Fallback mapping if needed
                                    mapping = {"STR": stats.strength, "END": stats.endurance, "DEX": stats.dexterity,
                                               "AGI": stats.agility, "MAG": stats.magic, "LCK": stats.luck}
                                    current_total = mapping.get(stat_name, 0)

                                bonus = math.ceil(current_total * (percent * level))
                                stats.add_bonus_stat(stat_name, bonus)

                # 4. Save Updates
                self.db.update_player_stats(discord_id, stats.to_dict())
                return stats

        except Exception as e:
            logger.error(f"Stat calc failed for {discord_id}: {e}", exc_info=True)
            return PlayerStats()

    def equip_item(self, discord_id: int, inventory_db_id: int) -> Tuple[bool, str]:
        """
        Equips an item. Handles slot conflicts and stack splitting atomically.
        """
        try:
            with self.db.get_connection() as conn:
                # Fetch target item
                item = conn.execute(
                    "SELECT * FROM inventory WHERE id = ? AND discord_id = ?", 
                    (inventory_db_id, discord_id)
                ).fetchone()
                
                if not item: return False, "Item not found."
                if item["item_type"] != "equipment": return False, "Not equippable."
                if item["equipped"] == 1: return False, "Already equipped."

                # Validate Class Permissions
                allowed = self._get_player_allowed_slots(conn, discord_id)
                if item["slot"] not in allowed:
                    return False, f"Your class cannot equip {item['slot']} items."

                # Check for existing equipped item in that slot
                existing = conn.execute(
                    "SELECT id FROM inventory WHERE discord_id = ? AND slot = ? AND equipped = 1",
                    (discord_id, item["slot"])
                ).fetchone()
                
                if existing:
                    # Unequip the old item first
                    self._unequip_logic(conn, discord_id, existing["id"])

                # Equip the new item
                if item["count"] > 1:
                    # Split stack: Decrement old stack, insert new equipped single
                    conn.execute("UPDATE inventory SET count = count - 1 WHERE id = ?", (inventory_db_id,))
                    conn.execute(
                        """
                        INSERT INTO inventory (discord_id, item_key, item_name, item_type, rarity, slot, item_source_table, count, equipped)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1)
                        """,
                        (discord_id, item["item_key"], item["item_name"], item["item_type"], item["rarity"], item["slot"], item["item_source_table"])
                    )
                else:
                    # Mark existing single as equipped
                    conn.execute("UPDATE inventory SET equipped = 1 WHERE id = ?", (inventory_db_id,))
            
            # Recalculate stats after successful commit
            self.recalculate_player_stats(discord_id)
            return True, "Item equipped."

        except Exception as e:
            logger.error(f"Equip error: {e}", exc_info=True)
            return False, "An error occurred."

    def unequip_item(self, discord_id: int, inventory_db_id: int) -> Tuple[bool, str]:
        """
        Unequips an item safely.
        """
        try:
            with self.db.get_connection() as conn:
                self._unequip_logic(conn, discord_id, inventory_db_id)
            
            self.recalculate_player_stats(discord_id)
            return True, "Item unequipped."
        except ValueError as ve:
            return False, str(ve)
        except Exception as e:
            logger.error(f"Unequip error: {e}", exc_info=True)
            return False, "An error occurred."

    def _unequip_logic(self, conn, discord_id, inv_id):
        """Internal logic to unequip and merge stacks."""
        item = conn.execute("SELECT * FROM inventory WHERE id = ? AND discord_id = ?", (inv_id, discord_id)).fetchone()
        if not item or not item["equipped"]:
            raise ValueError("Item not equipped or not found.")

        # Look for an existing unequipped stack to merge into
        stack = conn.execute(
            """
            SELECT id FROM inventory 
            WHERE discord_id = ? AND item_key = ? AND rarity = ? AND slot = ? AND item_source_table = ? AND equipped = 0
            LIMIT 1
            """,
            (discord_id, item["item_key"], item["rarity"], item["slot"], item["item_source_table"])
        ).fetchone()

        if stack:
            conn.execute("UPDATE inventory SET count = count + 1 WHERE id = ?", (stack["id"],))
            conn.execute("DELETE FROM inventory WHERE id = ?", (inv_id,))
        else:
            conn.execute("UPDATE inventory SET equipped = 0 WHERE id = ?", (inv_id,))