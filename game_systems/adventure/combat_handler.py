"""
combat_handler.py

Manages combat initialization and turn resolution.
Hardened: Syncs session XP to prevent duplicate level-up messages.
"""

import json
import logging
import random
from typing import Any

from database.database_manager import DatabaseManager
from game_systems.combat.combat_engine import CombatEngine
from game_systems.combat.combat_phrases import CombatPhrases
from game_systems.data.monsters import MONSTERS
from game_systems.player.level_up import LevelUpSystem
from game_systems.player.player_stats import PlayerStats

logger = logging.getLogger("eldoria.combat")


class CombatHandler:
    def __init__(self, db: DatabaseManager, discord_id: int):
        self.db = db
        self.discord_id = discord_id

    def initiate_combat(self, location: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
        """
        Selects a monster and prepares the combat session.
        """
        try:
            # 1. Base Pool
            monster_pool = list(location.get("monsters", []))

            # 2. Conditional Spawns (Level Check)
            conditionals = location.get("conditional_monsters", [])
            if conditionals:
                with self.db.get_connection() as conn:
                    row = conn.execute("SELECT level FROM players WHERE discord_id = ?", (self.discord_id,)).fetchone()
                    player_level = row["level"] if row else 1

                for cond in conditionals:
                    if player_level >= cond.get("min_level", 1):
                        monster_pool.append((cond["monster_key"], cond["weight"]))

            if not monster_pool:
                return None, "The area is silent. No threats detected."

            # 3. Select Monster
            choices, weights = zip(*monster_pool)
            monster_key = random.choices(choices, weights=weights, k=1)[0]

            template = MONSTERS.get(monster_key)
            if not template:
                logger.error(f"Monster key {monster_key} not found in database.")
                return None, "You sense a presence, but it fades."

            # 4. Instantiate Monster
            active_monster = {
                "name": template["name"],
                "level": template["level"],
                "tier": template["tier"],
                "HP": template["hp"],
                "max_hp": template["hp"],
                "MP": 10 + (template["level"] * 3),
                "ATK": template["atk"],
                "DEF": template["def"],
                "xp": template["xp"],
                "drops": template.get("drops", []),
                "skills": list(template.get("skills", [])),
            }

            phrase = CombatPhrases.opening(active_monster)
            return active_monster, phrase

        except Exception as e:
            logger.error(f"Combat init failed for {self.discord_id}: {e}", exc_info=True)
            return None, "An error occurred while tracking the enemy."

    def resolve_turn(
        self,
        active_monster: dict[str, Any],
        battle_report: dict[str, Any],
        accumulated_exp: int = 0,
        context: dict[str, Any] | None = None,
        persist_vitals: bool = True,
    ) -> dict[str, Any]:
        """
        Executes a full combat round (Player vs Monster).
        Args:
            accumulated_exp: XP earned in this session but not yet saved to DB.
            context: Optional pre-fetched data to avoid DB calls.
            persist_vitals: Whether to write HP/MP to DB immediately.
        """
        try:
            # 1. Load Data
            if context:
                player_stats = context["player_stats"]
                stats_dict = context.get("stats_dict")
                vitals = context["vitals"]
                p_row = context["player_row"]
                skills = context["skills"]
                boosts = context.get("active_boosts", {})
            else:
                stats_json = self.db.get_player_stats_json(self.discord_id)
                player_stats = PlayerStats.from_dict(stats_json)

                # Apply Active Buffs (Manual Mode)
                self.db.clear_expired_buffs(self.discord_id)
                active_buffs = self.db.get_active_buffs(self.discord_id)
                for buff in active_buffs:
                    player_stats.add_bonus_stat(buff["stat"], buff["amount"])

                # Generate cached stats dict
                stats_dict = player_stats.get_total_stats_dict()

                vitals = self.db.get_player_vitals(self.discord_id)

                if not vitals:
                    raise ValueError("Player vitals not found.")

                with self.db.get_connection() as conn:
                    # Fetch Class & Level
                    p_row = conn.execute(
                        "SELECT level, experience, exp_to_next, class_id FROM players WHERE discord_id=?",
                        (self.discord_id,),
                    ).fetchone()

                    # Fetch Active Skills
                    skills_cursor = conn.execute(
                        """
                        SELECT s.key_id, s.name, s.type, ps.skill_level, s.mp_cost,
                               s.power_multiplier, s.heal_power, s.buff_data
                        FROM player_skills ps
                        JOIN skills s ON ps.skill_key=s.key_id
                        WHERE ps.discord_id=? AND s.type='Active'
                        """,
                        (self.discord_id,),
                    )
                    skills = [dict(row) for row in skills_cursor.fetchall()]

                active_boosts_list = self.db.get_active_boosts()
                boosts = {b["boost_key"]: b["multiplier"] for b in active_boosts_list}

            # 2. Parse Skill Buffs safely
            for s in skills:
                if s.get("buff_data") and isinstance(s["buff_data"], str):
                    try:
                        s["buff_data"] = json.loads(s["buff_data"])
                    except (json.JSONDecodeError, TypeError):
                        s["buff_data"] = {}

            # 3. Setup Wrappers & Fast-Forward State
            player_wrapper = LevelUpSystem(player_stats, p_row["level"], p_row["experience"], p_row["exp_to_next"])

            # Apply session XP so leveling logic is up to date
            if accumulated_exp > 0:
                player_wrapper.add_exp(accumulated_exp)

            player_wrapper.hp_current = vitals["current_hp"]

            # 4. Run Engine
            engine = CombatEngine(
                player=player_wrapper,
                monster=active_monster,
                player_skills=skills,
                player_mp=vitals["current_mp"],
                player_class_id=p_row["class_id"],
                active_boosts=boosts,
                stats_dict=stats_dict,
            )

            result = engine.run_combat_turn()

            # 5. Persist State (Vitals & Monster HP)
            # We update vitals immediately so if bot crashes, HP loss is saved
            if persist_vitals:
                self.db.set_player_vitals(self.discord_id, result["hp_current"], result["mp_current"])
            active_monster["HP"] = result["monster_hp"]

            # 6. Update Report
            self._aggregate_battle_report(battle_report, result.get("turn_report", {}))

            return result

        except Exception as e:
            logger.error(f"Combat turn error for {self.discord_id}: {e}", exc_info=True)
            # Return a safe "neutral" result to prevent crash loops
            return {
                "winner": None,
                "phrases": ["*Something disrupts the flow of battle...*"],
                "hp_current": vitals["current_hp"] if vitals else 1,
                "mp_current": vitals["current_mp"] if vitals else 1,
                "monster_hp": active_monster.get("HP", 0),
                "turn_report": {},
                "active_boosts": {},
            }

    @staticmethod
    def create_empty_battle_report():
        return {
            "str_hits": 0,
            "dex_hits": 0,
            "mag_hits": 0,
            "player_crit": 0,
            "player_dodge": 0,
            "damage_taken": 0,
            "skills_used": 0,
            "skill_key_used": None,
        }

    @staticmethod
    def _aggregate_battle_report(base, turn):
        for k in base:
            if k != "skill_key_used" and k in turn:
                base[k] += turn[k]
        base["skill_key_used"] = turn.get("skill_key_used")
