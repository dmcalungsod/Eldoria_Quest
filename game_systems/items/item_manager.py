"""
item_manager.py

Unified item lookup system.
Hardened with safe collection lookups for MongoDB.
"""

import json
import logging
import random

from database.database_manager import DatabaseManager

logger = logging.getLogger("eldoria.items")

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
    def __init__(self):
        self.db = DatabaseManager()

    def get_equipment_stats(self, item_key: str, source_table: str) -> dict:
        """Fetches stats for a specific item safely."""
        if source_table not in VALID_EQUIP_TABLES:
            logger.warning(f"Invalid table access attempt: {source_table}")
            return {}

        try:
            try:
                item_id = int(item_key)
            except ValueError:
                logger.warning(f"Invalid equipment key format: {item_key}")
                return {}

            row = self.db._col(source_table).find_one({"id": item_id}, {"_id": 0})
            if not row:
                return {}
            return {
                stat: row[key]
                for key, stat in STAT_MAP.items()
                if key in row and row[key] != 0
            }
        except Exception as e:
            logger.error(f"Error fetching stats for {item_key}: {e}")
            return {}

    # --------------------------------------------------------------------
    # GENERIC ITEM LOOKUP
    # --------------------------------------------------------------------
    def _lookup(self, collection_name: str, query: dict) -> dict | None:
        """Internal helper for safe single-row lookups."""
        try:
            return self.db._col(collection_name).find_one(query, {"_id": 0})
        except Exception as e:
            logger.error(f"Lookup error in {collection_name}: {e}")
            return None

    def get_equipment_by_id(self, equip_id: int):
        return self._lookup("equipment", {"id": equip_id})

    def get_equipment_by_name(self, name: str):
        return self._lookup("equipment", {"name": {"$regex": name, "$options": "i"}})

    def get_consumable(self, name: str):
        return self._lookup("consumables", {"name": {"$regex": name, "$options": "i"}})

    def get_quest_item(self, name: str):
        return self._lookup("quest_items", {"name": {"$regex": name, "$options": "i"}})

    # --------------------------------------------------------------------
    # CLASS EQUIPMENT
    # --------------------------------------------------------------------
    def get_class_equipment_for_class(self, class_id: int, level: int = 1):
        try:
            return list(
                self.db._col("class_equipment").find(
                    {"class_id": class_id, "min_level": {"$lte": level}},
                    {"_id": 0},
                )
            )
        except Exception as e:
            logger.error(f"Class equipment lookup error: {e}")
            return []

    # --------------------------------------------------------------------
    # DROPS & RNG
    # --------------------------------------------------------------------
    def roll_rarity(self):
        rolls = {
            "Common": 55,
            "Uncommon": 25,
            "Rare": 12,
            "Epic": 5,
            "Legendary": 2,
            "Mythical": 1,
        }
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

            # Use MongoDB aggregation for random sampling
            pipeline = [
                {"$match": {"rarity": rarity, "min_level": {"$lte": level}}},
                {"$sample": {"size": 1}},
                {"$project": {"_id": 0}},
            ]
            results = list(self.db._col("equipment").aggregate(pipeline))

            if results:
                row = results[0]
                loot.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "rarity": row["rarity"],
                        "slot": row.get("slot"),
                        "source": "equipment",
                    }
                )
        except Exception as e:
            logger.error(f"Loot generation error: {e}")

        return loot

    # --------------------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------------------
    def search_items(self, text: str):
        """Searches all item collections."""
        try:
            regex_filter = {"$regex": text, "$options": "i"}
            results = []

            # Equipment
            for row in self.db._col("equipment").find(
                {"name": regex_filter}, {"_id": 0}
            ):
                results.append({**row, "table_name": "equipment"})

            # Class Equipment
            for row in self.db._col("class_equipment").find(
                {"name": regex_filter}, {"_id": 0}
            ):
                results.append({**row, "table_name": "class_equipment"})

            # Consumables
            for row in self.db._col("consumables").find(
                {"name": regex_filter}, {"_id": 0}
            ):
                results.append({**row, "table_name": "consumables"})

            # Quest Items
            for row in self.db._col("quest_items").find(
                {"name": regex_filter}, {"_id": 0}
            ):
                results.append({**row, "table_name": "quest_items"})

            return results
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
