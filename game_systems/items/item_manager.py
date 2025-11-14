"""
item_manager.py

Provides a unified interface for fetching items from the database:
- Equipment
- Class equipment
- Consumables
- Quest items
- Monster loot tables

Also handles:
- Random rarity rolls
- Random monster drops
- Item lookup by name, rarity, slot
"""

import sqlite3
import random
import json

DB_NAME = "EQ_Game.db"


class ItemManager:
    def __init__(self, db_path=DB_NAME):
        self.db_path = db_path

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # --------------------------------------------------------------------
    #     GENERIC ITEM LOOKUP
    # --------------------------------------------------------------------
    def get_equipment_by_id(self, equip_id: int):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM equipment WHERE id = ?", (equip_id,))
        item = cur.fetchone()
        conn.close()
        return item

    def get_equipment_by_name(self, name: str):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM equipment WHERE name LIKE ?", ('%' + name + '%',))
        item = cur.fetchone()
        conn.close()
        return item

    def get_consumable(self, name: str):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM consumables WHERE name LIKE ?", ('%' + name + '%',))
        item = cur.fetchone()
        conn.close()
        return item

    def get_quest_item(self, name: str):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM quest_items WHERE name LIKE ?", ('%' + name + '%',))
        item = cur.fetchone()
        conn.close()
        return item

    # --------------------------------------------------------------------
    #     CLASS EQUIPMENT (for class-specific gear)
    # --------------------------------------------------------------------
    def get_class_equipment_for_class(self, class_id: int, level: int = 1):
        """
        Fetch class equipment appropriate for player's class and level.
        """
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM class_equipment
            WHERE class_id = ?
              AND min_level <= ?
        """, (class_id, level))
        results = cur.fetchall()
        conn.close()
        return results

    # --------------------------------------------------------------------
    #     RANDOM RARITY ROLL
    # --------------------------------------------------------------------
    def roll_rarity(self):
        """
        Returns a rarity string based on weighted chances.
        """
        rolls = {
            "Common": 55,
            "Uncommon": 25,
            "Rare": 12,
            "Epic": 5,
            "Legendary": 2,
            "Mythical": 1,
        }

        total = sum(rolls.values())
        r = random.randint(1, total)
        current = 0

        for rarity, weight in rolls.items():
            current += weight
            if r <= current:
                return rarity

        return "Common"

    # --------------------------------------------------------------------
    #     MONSTER DROPS
    # --------------------------------------------------------------------
    def get_monster(self, monster_name: str):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM monsters WHERE name LIKE ?", ('%' + monster_name + '%',))
        monster = cur.fetchone()
        conn.close()
        return monster

    def generate_monster_loot(self, monster_row):
        """
        Returns 0–2 random items for defeating a monster.
        Loot pool = all items, filtered by rarity roll.
        """
        loot = []
        level = monster_row["level"]

        conn = self.connect()
        cur = conn.cursor()

        for _ in range(random.randint(0, 2)):  # Up to 2 items per monster
            rarity = self.roll_rarity()

            # Search ALL equipment tables
            cur.execute("""
                SELECT id, name, rarity, slot, min_level, 'equipment' AS source
                FROM equipment
                WHERE rarity = ? AND min_level <= ?
                UNION ALL
                SELECT id, name, rarity, slot, min_level, 'class_equipment' AS source
                FROM class_equipment
                WHERE rarity = ? AND min_level <= ?
                LIMIT 1;
            """, (rarity, level, rarity, level))

            row = cur.fetchone()
            if row:
                loot.append(dict(row))

        conn.close()
        return loot

    # --------------------------------------------------------------------
    #     SEARCH & UTILITY
    # --------------------------------------------------------------------
    def search_items(self, text: str):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, name, rarity, slot, 'equipment' AS table_name
            FROM equipment
            WHERE name LIKE ?
            UNION ALL
            SELECT id, name, rarity, slot, 'class_equipment'
            FROM class_equipment
            WHERE name LIKE ?
            UNION ALL
            SELECT id, name, rarity, NULL AS slot, 'consumables'
            FROM consumables
            WHERE name LIKE ?
            UNION ALL
            SELECT id, name, rarity, NULL AS slot, 'quest_items'
            FROM quest_items
            WHERE name LIKE ?;
        """, (f"%{text}%", f"%{text}%", f"%{text}%", f"%{text}%"))

        results = cur.fetchall()
        conn.close()
        return results

    def format_consumable_effect(self, effect_json):
        if not effect_json:
            return "No effect"
        try:
            parsed = json.loads(effect_json)
            return ", ".join(f"{k}: {v}" for k, v in parsed.items())
        except json.JSONDecodeError:
            return effect_json


# --------------------------------------------------------------------
#     Singleton Instance (for easy import everywhere)
# --------------------------------------------------------------------
item_manager = ItemManager()
