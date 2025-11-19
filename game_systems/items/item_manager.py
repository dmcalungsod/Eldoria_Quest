"""
item_manager.py

Unified item lookup system.
Hardened with parameterized queries and safe table whitelisting.
"""

import json
import logging
import random
import sqlite3

logger = logging.getLogger("eldoria.items")
DB_NAME = "EQ_Game.db"

STAT_MAP = {
    "str_bonus": "STR",
    "end_bonus": "END",
    "dex_bonus": "DEX",
    "agi_bonus": "AGI",
    "mag_bonus": "MAG",
    "lck_bonus": "LCK",
}
VALID_EQUIP_TABLES = {"equipment", "class_equipment"}


class ItemManager:
    def __init__(self, db_path=DB_NAME):
        self.db_path = db_path

    def connect(self):
        """Creates a read-only connection for lookups."""
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn

    def get_equipment_stats(self, item_key: str, source_table: str) -> dict:
        """Fetches stats for a specific item safely."""
        if source_table not in VALID_EQUIP_TABLES:
            logger.warning(f"Invalid table access attempt: {source_table}")
            return {}

        try:
            with self.connect() as conn:
                # Safe f-string: source_table is whitelisted above
                row = conn.execute(f"SELECT * FROM {source_table} WHERE id = ?", (item_key,)).fetchone()

                if not row:
                    return {}

                return {stat: row[key] for key, stat in STAT_MAP.items() if key in row.keys() and row[key] != 0}
        except Exception as e:
            logger.error(f"Error fetching stats for {item_key}: {e}")
            return {}

    # --------------------------------------------------------------------
    # GENERIC ITEM LOOKUP
    # --------------------------------------------------------------------
    def _lookup(self, table: str, query: str, params: tuple) -> sqlite3.Row | None:
        """Internal helper for safe single-row lookups."""
        try:
            with self.connect() as conn:
                return conn.execute(f"SELECT * FROM {table} WHERE {query}", params).fetchone()
        except Exception as e:
            logger.error(f"Lookup error in {table}: {e}")
            return None

    def get_equipment_by_id(self, equip_id: int):
        return self._lookup("equipment", "id = ?", (equip_id,))

    def get_equipment_by_name(self, name: str):
        return self._lookup("equipment", "name LIKE ?", (f"%{name}%",))

    def get_consumable(self, name: str):
        return self._lookup("consumables", "name LIKE ?", (f"%{name}%",))

    def get_quest_item(self, name: str):
        return self._lookup("quest_items", "name LIKE ?", (f"%{name}%",))

    # --------------------------------------------------------------------
    # CLASS EQUIPMENT
    # --------------------------------------------------------------------
    def get_class_equipment_for_class(self, class_id: int, level: int = 1):
        try:
            with self.connect() as conn:
                return conn.execute(
                    "SELECT * FROM class_equipment WHERE class_id = ? AND min_level <= ?", (class_id, level)
                ).fetchall()
        except Exception as e:
            logger.error(f"Class equipment lookup error: {e}")
            return []

    # --------------------------------------------------------------------
    # DROPS & RNG
    # --------------------------------------------------------------------
    def roll_rarity(self):
        rolls = {"Common": 55, "Uncommon": 25, "Rare": 12, "Epic": 5, "Legendary": 2, "Mythical": 1}
        r = random.randint(1, sum(rolls.values()))
        current = 0
        for rarity, weight in rolls.items():
            current += weight
            if r <= current:
                return rarity
        return "Common"

    def generate_monster_loot(self, monster_row: dict) -> list[dict]:
        """Generates random equipment drops."""
        loot = []
        if random.randint(1, 100) > 20:  # 80% chance of no equipment
            return loot

        try:
            rarity = self.roll_rarity()
            level = monster_row.get("level", 1)

            with self.connect() as conn:
                # Get one random item matching criteria
                row = conn.execute(
                    """
                    SELECT id, name, rarity, slot, 'equipment' AS source
                    FROM equipment
                    WHERE rarity = ? AND min_level <= ?
                    ORDER BY RANDOM() LIMIT 1
                    """,
                    (rarity, level),
                ).fetchone()

                if row:
                    loot.append(dict(row))
        except Exception as e:
            logger.error(f"Loot generation error: {e}")

        return loot

    # --------------------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------------------
    def search_items(self, text: str):
        """Searches all item tables safely."""
        search_term = f"%{text}%"
        try:
            with self.connect() as conn:
                # UNION ALL query to search everything at once
                return conn.execute(
                    """
                    SELECT id, name, rarity, slot, 'equipment' AS table_name FROM equipment WHERE name LIKE ?
                    UNION ALL
                    SELECT id, name, rarity, slot, 'class_equipment' FROM class_equipment WHERE name LIKE ?
                    UNION ALL
                    SELECT id, name, rarity, NULL, 'consumables' FROM consumables WHERE name LIKE ?
                    UNION ALL
                    SELECT id, name, rarity, NULL, 'quest_items' FROM quest_items WHERE name LIKE ?
                    """,
                    (search_term, search_term, search_term, search_term),
                ).fetchall()
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def format_consumable_effect(self, effect_json):
        if not effect_json:
            return "No effect"
        try:
            parsed = json.loads(effect_json)
            return ", ".join(f"{k}: {v}" for k, v in parsed.items())
        except json.JSONDecodeError:
            return str(effect_json)


# Singleton
item_manager = ItemManager()
