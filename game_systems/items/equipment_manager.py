"""
equipment_manager.py

Handles all logic for equipping, unequipping, and recalculating stats
based on a player's gear.
"""

import math
from typing import Dict, Tuple

from database.database_manager import DatabaseManager
from game_systems.data.class_data import CLASSES
from game_systems.data.skills_data import SKILLS
from game_systems.player.player_stats import PlayerStats


class EquipmentManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.stat_bonus_keys = [
            "str_bonus",
            "end_bonus",
            "dex_bonus",
            "agi_bonus",
            "mag_bonus",
            "lck_bonus",
        ]
        self.stat_map = {
            "str_bonus": "STR",
            "end_bonus": "END",
            "dex_bonus": "DEX",
            "agi_bonus": "AGI",
            "mag_bonus": "MAG",
            "lck_bonus": "LCK",
        }
        self.valid_tables = ["equipment", "class_equipment"]

    def _get_player_allowed_slots(self, discord_id: int) -> list:
        """Fetches the player's class and returns their allowed slots."""
        player_row = self.db.get_player(discord_id)
        if not player_row:
            return []

        player_class_id = player_row["class_id"]

        # Find the class name from the ID
        class_name = None
        for name, data in CLASSES.items():
            if data["id"] == player_class_id:
                class_name = name
                break

        if class_name:
            return CLASSES[class_name].get("allowed_slots", [])

        return []

    def _get_item_bonuses(self, item_key: str, source_table: str) -> Dict:
        """
        Safely fetches the stat bonuses for a single item from its source table.
        """
        if source_table not in self.valid_tables:
            print(f"Error: Invalid source table '{source_table}'")
            return {}

        conn = self.db.connect()
        cur = conn.cursor()

        query_table = "equipment" if source_table == "equipment" else "class_equipment"
        cur.execute(f"SELECT * FROM {query_table} WHERE id = ?", (item_key,))
        item_row = cur.fetchone()
        conn.close()

        if not item_row:
            return {}

        bonuses = {}
        for key, stat in self.stat_map.items():
            if key in item_row.keys() and item_row[key] != 0:
                bonuses[stat] = item_row[key]
        return bonuses

    def recalculate_player_stats(self, discord_id: int) -> PlayerStats:
        """
        Recalculates a player's total stats based on equipped items AND passive skills.
        1. Fetches base stats.
        2. Creates a PlayerStats object.
        3. Fetches all equipped items and applies their bonuses.
        4. Fetches all learned passive skills and applies their bonuses.
        5. Saves the new stats_json back to the database.

        Returns the updated PlayerStats object.
        """
        base_stats_json = self.db.get_player_stats_json(discord_id)
        if not base_stats_json:
            print(f"Error: Could not find base stats for {discord_id}")
            return PlayerStats()

        # 1. Create PlayerStats object from BASE stats
        stats = PlayerStats.from_dict(base_stats_json)

        conn = self.db.connect()
        cur = conn.cursor()

        # 2. Fetch and apply equipped item bonuses
        cur.execute(
            """
            SELECT item_key, item_source_table FROM inventory
            WHERE discord_id = ? AND equipped = 1
        """,
            (discord_id,),
        )
        equipped_items = cur.fetchall()

        for item in equipped_items:
            bonuses = self._get_item_bonuses(item["item_key"], item["item_source_table"])
            for stat, value in bonuses.items():
                stats.add_bonus_stat(stat, value)

        # 3. Fetch and apply passive skill bonuses
        cur.execute(
            "SELECT skill_key, skill_level FROM player_skills WHERE discord_id = ?",
            (discord_id,),
        )
        player_skills = cur.fetchall()

        for p_skill in player_skills:
            skill_data = SKILLS.get(p_skill["skill_key"])

            # Check if it's a passive skill with bonuses
            if skill_data and skill_data.get("type") == "Passive" and "passive_bonus" in skill_data:
                skill_level = p_skill["skill_level"]

                for stat, bonus_percent in skill_data["passive_bonus"].items():
                    if stat.endswith("_percent"):
                        # Calculate percentage bonus (e.g., 0.1 for 10%)
                        # We apply this to the STATS (Base + Item Bonuses)
                        stat_name = stat.split("_")[0].upper()  # "AGI_percent" -> "AGI"

                        # Get the current total for that stat
                        current_stat_total = 0
                        if stat_name == "STR":
                            current_stat_total = stats.strength
                        elif stat_name == "END":
                            current_stat_total = stats.endurance
                        elif stat_name == "DEX":
                            current_stat_total = stats.dexterity
                        elif stat_name == "AGI":
                            current_stat_total = stats.agility
                        elif stat_name == "MAG":
                            current_stat_total = stats.magic
                        elif stat_name == "LCK":
                            current_stat_total = stats.luck

                        # Calculate the bonus
                        total_bonus_percent = bonus_percent * skill_level
                        bonus_amount = math.ceil(current_stat_total * total_bonus_percent)

                        stats.add_bonus_stat(stat_name, bonus_amount)

        # 4. Save the new stats (base + bonus) back to the DB
        self.db.update_player_stats(discord_id, stats.to_dict())

        conn.close()
        return stats

    def equip_item(self, discord_id: int, inventory_db_id: int) -> Tuple[bool, str]:
        """
        Equips an item from an inventory stack.
        """
        conn = self.db.connect()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM inventory WHERE id = ? AND discord_id = ?",
            (inventory_db_id, discord_id),
        )
        item_stack = cur.fetchone()

        if not item_stack:
            conn.close()
            return False, "Item not found in your inventory."
        if item_stack["item_type"] != "equipment":
            conn.close()
            return False, "This item cannot be equipped."
        if item_stack["equipped"] == 1:
            conn.close()
            return False, "This item is already equipped."

        slot_to_equip = item_stack["slot"]

        # --- CLASS RESTRICTION ---
        allowed_slots = self._get_player_allowed_slots(discord_id)
        if slot_to_equip not in allowed_slots:
            conn.close()
            return False, f"Your class cannot equip this item type ({slot_to_equip})."
        # --- END RESTRICTION ---

        cur.execute(
            """
            SELECT id FROM inventory
            WHERE discord_id = ? AND slot = ? AND equipped = 1
        """,
            (discord_id, slot_to_equip),
        )
        item_to_unequip = cur.fetchone()

        conn.close()

        if item_to_unequip:
            self.unequip_item(discord_id, item_to_unequip["id"])

        conn = self.db.connect()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM inventory WHERE id = ? AND discord_id = ?",
            (inventory_db_id, discord_id),
        )
        item_stack = cur.fetchone()

        if not item_stack or item_stack["equipped"] == 1:
            conn.close()
            return True, "Item equipped."

        if item_stack["count"] > 1:
            cur.execute(
                "UPDATE inventory SET count = count - 1 WHERE id = ?",
                (inventory_db_id,),
            )
            cur.execute(
                """
                INSERT INTO inventory (discord_id, item_key, item_name, item_type, rarity,
                                       slot, item_source_table, count, equipped)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1)
                """,
                (
                    discord_id,
                    item_stack["item_key"],
                    item_stack["item_name"],
                    item_stack["item_type"],
                    item_stack["rarity"],
                    item_stack["slot"],
                    item_stack["item_source_table"],
                ),
            )
        else:
            cur.execute("UPDATE inventory SET equipped = 1 WHERE id = ?", (inventory_db_id,))

        conn.commit()
        conn.close()

        # Recalculate stats, which will now include passives
        self.recalculate_player_stats(discord_id)
        return True, "Item equipped."

    def unequip_item(self, discord_id: int, inventory_db_id: int) -> Tuple[bool, str]:
        """
        Unequips an item, merging it with an existing unequipped stack if possible.
        """
        conn = self.db.connect()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM inventory WHERE id = ? AND discord_id = ?",
            (inventory_db_id, discord_id),
        )
        item_to_unequip = cur.fetchone()

        if not item_to_unequip:
            conn.close()
            return False, "Item not found in your inventory."
        if item_to_unequip["equipped"] == 0:
            conn.close()
            return False, "This item is not equipped."

        cur.execute(
            """
            SELECT id FROM inventory
            WHERE discord_id = ?
              AND item_key = ?
              AND rarity = ?
              AND slot = ?
              AND item_source_table = ?
              AND equipped = 0
            LIMIT 1
        """,
            (
                discord_id,
                item_to_unequip["item_key"],
                item_to_unequip["rarity"],
                item_to_unequip["slot"],
                item_to_unequip["item_source_table"],
            ),
        )
        stack_row = cur.fetchone()

        if stack_row:
            cur.execute(
                "UPDATE inventory SET count = count + 1 WHERE id = ?",
                (stack_row["id"],),
            )
            cur.execute("DELETE FROM inventory WHERE id = ?", (inventory_db_id,))
        else:
            cur.execute(
                "UPDATE inventory SET equipped = 0, count = 1 WHERE id = ?",
                (inventory_db_id,),
            )

        conn.commit()
        conn.close()

        # Recalculate stats, which will now include passives
        self.recalculate_player_stats(discord_id)
        return True, "Item unequipped."
