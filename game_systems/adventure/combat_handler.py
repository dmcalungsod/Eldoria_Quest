"""
combat_handler.py

Handles the heavy lifting for combat:
- Spawning monsters (Initiate)
- Setting up the CombatEngine (loading stats, skills, boosts)
- Running a turn
- Aggregating battle reports
"""

import json
import logging
import random
from typing import Any, Dict, Tuple

from database.database_manager import DatabaseManager
from game_systems.combat.combat_engine import CombatEngine
from game_systems.combat.combat_phrases import CombatPhrases
from game_systems.data.monsters import MONSTERS
from game_systems.player.level_up import LevelUpSystem
from game_systems.player.player_stats import PlayerStats

logger = logging.getLogger("discord")

class CombatHandler:
    def __init__(self, db: DatabaseManager, discord_id: int):
        self.db = db
        self.discord_id = discord_id

    def initiate_combat(self, location: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """
        Selects a monster and returns (monster_dict, opening_phrase).
        Now supports conditional spawns based on player level.
        """
        try:
            # 1. Start with the base pool
            monster_pool = list(location.get("monsters", []))

            # 2. Check for Conditional Monsters (Level-based spawns)
            conditionals = location.get("conditional_monsters", [])

            if conditionals:
                # Fetch player level to determine eligibility
                with self.db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT level FROM players WHERE discord_id = ?", (self.discord_id,))
                    row = cur.fetchone()
                    player_level = row["level"] if row else 1

                # Inject stronger monsters if the player qualifies
                for cond in conditionals:
                    if player_level >= cond.get("min_level", 1):
                        monster_pool.append((cond["monster_key"], cond["weight"]))

            # 3. Handle empty pool case
            if not monster_pool:
                return None, "The area is eerily silent. No further threats present themselves."

            # 4. Select Monster
            choices, weights = zip(*monster_pool)
            monster_key = random.choices(choices, weights=weights, k=1)[0]

            template = MONSTERS.get(monster_key)
            if not template:
                return None, "Error: Monster data missing."

            active_monster = {
                "name": template["name"], "level": template["level"], "tier": template["tier"],
                "HP": template["hp"], "max_hp": template["hp"], "MP": 10,
                "ATK": template["atk"], "DEF": template["def"], "xp": template["xp"],
                "drops": template.get("drops", [])
            }

            phrase = CombatPhrases.opening(active_monster)
            return active_monster, phrase

        except Exception as e:
            logger.error(f"Error spawning monster: {e}")
            return None, "Error: Failed to initiate combat."

    def resolve_turn(self, active_monster: Dict[str, Any], battle_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepares player data, runs CombatEngine, updates DB, and returns result.
        """
        # 1. Load Data
        stats_json = self.db.get_player_stats_json(self.discord_id)
        player_stats = PlayerStats.from_dict(stats_json)
        vitals = self.db.get_player_vitals(self.discord_id)

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            # Get Class & Level
            cur.execute("SELECT level, experience, exp_to_next, class_id FROM players WHERE discord_id=?", (self.discord_id,))
            p_row = cur.fetchone()

            # Get Skills
            cur.execute(
                """SELECT s.key_id, s.name, s.type, ps.skill_level, s.mp_cost,
                          s.power_multiplier, s.heal_power, s.buff_data
                   FROM player_skills ps
                   JOIN skills s ON ps.skill_key=s.key_id
                   WHERE ps.discord_id=? AND s.type='Active'""",
                (self.discord_id,)
            )
            skills = [dict(row) for row in cur.fetchall()]

        # 2. Parse Buffs
        for s in skills:
            if s.get("buff_data"):
                try:
                    s["buff_data"] = json.loads(s["buff_data"])
                except Exception:
                    s["buff_data"] = {}

        # 3. Setup Wrappers
        player_wrapper = LevelUpSystem(
            player_stats, p_row["level"], p_row["experience"], p_row["exp_to_next"]
        )
        player_wrapper.hp_current = vitals["current_hp"]

        boosts = self._fetch_active_boosts()

        # 4. Run Engine
        engine = CombatEngine(
            player_wrapper, active_monster, skills, vitals["current_mp"],
            p_row["class_id"], boosts
        )
        result = engine.run_combat_turn()

        # 5. Update State (DB + Monster Object)
        self.db.set_player_vitals(self.discord_id, result["hp_current"], result["mp_current"])
        active_monster["HP"] = result["monster_hp"]

        # 6. Update Report
        self._aggregate_battle_report(battle_report, result.get("turn_report", {}))

        return result

    def _fetch_active_boosts(self):
        try:
            return {b["boost_key"]: b["multiplier"] for b in self.db.get_active_boosts()}
        except Exception:
            return {}

    @staticmethod
    def create_empty_battle_report():
        return {
            "str_hits": 0, "dex_hits": 0, "mag_hits": 0,
            "player_crit": 0, "player_dodge": 0, "damage_taken": 0,
            "skills_used": 0, "skill_key_used": None
        }

    @staticmethod
    def _aggregate_battle_report(base, turn):
        for k in base:
            if k != "skill_key_used":
                base[k] += turn.get(k, 0)
        base["skill_key_used"] = turn.get("skill_key_used")
