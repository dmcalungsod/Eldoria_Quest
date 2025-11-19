"""
game_systems/adventure/adventure_manager.py

Coordinates adventure lifecycles.
Hardened: Safe state transitions and secure reward handling.
"""

import json
import logging
import datetime
from database.database_manager import DatabaseManager
from game_systems.data.materials import MATERIALS
from game_systems.data.emojis import COMBAT
from game_systems.items.inventory_manager import InventoryManager
from game_systems.guild_system.quest_system import QuestSystem
from game_systems.player.player_stats import PlayerStats
from game_systems.player.level_up import LevelUpSystem
from .adventure_session import AdventureSession

logger = logging.getLogger("eldoria.adventure_mgr")

class AdventureManager:
    def __init__(self, db_manager: DatabaseManager, bot):
        self.db = db_manager
        self.bot = bot
        self.inventory_manager = InventoryManager(self.db)
        self.quest_system = QuestSystem(self.db)

    def start_adventure(self, discord_id: int, location_id: str, duration_minutes: int) -> bool:
        start_time = datetime.datetime.now()
        end_time = (
            start_time + datetime.timedelta(days=90) 
            if duration_minutes == -1 
            else start_time + datetime.timedelta(minutes=duration_minutes)
        )

        try:
            with self.db.get_connection() as conn:
                # Cleanup old sessions
                conn.execute("DELETE FROM adventure_sessions WHERE discord_id = ? AND active = 0", (discord_id,))
                
                # Create new session
                conn.execute(
                    """
                    INSERT OR REPLACE INTO adventure_sessions 
                    (discord_id, location_id, start_time, end_time, duration_minutes, active, logs, loot_collected)
                    VALUES (?, ?, ?, ?, ?, 1, '[]', '{}')
                    """,
                    (discord_id, location_id, start_time.isoformat(), end_time.isoformat(), duration_minutes)
                )
            return True
        except Exception as e:
            logger.error(f"Failed to start adventure for {discord_id}: {e}")
            return False

    def get_active_session(self, discord_id: int):
        try:
            with self.db.get_connection() as conn:
                return conn.execute(
                    "SELECT * FROM adventure_sessions WHERE discord_id = ? AND active = 1", (discord_id,)
                ).fetchone()
        except Exception as e:
            logger.error(f"Error fetching session for {discord_id}: {e}")
            return None

    def simulate_adventure_step(self, discord_id: int) -> dict:
        session_row = self.get_active_session(discord_id)
        if not session_row:
            return {"sequence": [["Error: No active session found."]], "dead": True}

        session = AdventureSession(
            self.db, self.quest_system, self.inventory_manager, discord_id, session_row
        )
        
        result = session.simulate_step()

        if result.get("dead", False):
            self._handle_death_rewards(discord_id, session)
        
        return result

    def _handle_death_rewards(self, discord_id, session):
        """Extracts partial rewards on death."""
        try:
            stats_json = self.db.get_player_stats_json(discord_id)
            p_stats = PlayerStats.from_dict(stats_json)

            with self.db.get_connection() as conn:
                items = self._grant_rewards_internal(session, 0, conn, p_stats)
            
            for item in items:
                self.inventory_manager.add_item(discord_id, item["key"], item["name"], item["type"], item["rarity"], item["amount"])
                
            with self.db.get_connection() as conn:
                 conn.execute("UPDATE adventure_sessions SET active = 0 WHERE discord_id = ?", (discord_id,))
                 
        except Exception as e:
            logger.error(f"Error handling death for {discord_id}: {e}")

    def end_adventure(self, discord_id: int):
        try:
            stats_json = self.db.get_player_stats_json(discord_id)
            p_stats = PlayerStats.from_dict(stats_json)
            items_to_add = []

            with self.db.get_connection() as conn:
                row = conn.execute("SELECT * FROM adventure_sessions WHERE discord_id = ? AND active = 1", (discord_id,)).fetchone()
                if not row: return

                session = AdventureSession(self.db, self.quest_system, self.inventory_manager, discord_id, row)
                total_exp = session.loot.pop("exp", 0)

                items_to_add = self._grant_rewards_internal(session, total_exp, conn, p_stats)
                
                conn.execute("UPDATE adventure_sessions SET active = 0 WHERE discord_id = ?", (discord_id,))

            for item in items_to_add:
                self.inventory_manager.add_item(discord_id, item["key"], item["name"], item["type"], item["rarity"], item["amount"])

        except Exception as e:
            logger.error(f"Error ending adventure for {discord_id}: {e}", exc_info=True)

    def _grant_rewards_internal(self, session, total_exp, conn, player_stats):
        """Helper to calculate rewards inside an existing DB transaction."""
        p_row = conn.execute("SELECT * FROM players WHERE discord_id = ?", (session.discord_id,)).fetchone()
        
        level_sys = LevelUpSystem(
            stats=player_stats, 
            level=p_row["level"], 
            exp=p_row["experience"], 
            exp_to_next=p_row["exp_to_next"]
        )

        if total_exp > 0:
            level_sys.add_exp(total_exp)

        # Save Vitals & Level
        current_hp = p_row["current_hp"]
        saved_hp = 1 if current_hp <= 0 else current_hp
        
        conn.execute(
            """
            UPDATE players 
            SET level = ?, experience = ?, exp_to_next = ?, vestige_pool = vestige_pool + ?, current_hp = ?, current_mp = ?
            WHERE discord_id = ?
            """,
            (level_sys.level, level_sys.exp, level_sys.exp_to_next, total_exp, saved_hp, level_sys.stats.max_mp, session.discord_id)
        )

        items_awarded = []
        for item_key, count in session.loot.items():
            mat = MATERIALS.get(item_key)
            name = mat["name"] if mat else item_key
            rarity = mat.get("rarity", "Common") if mat else "Common"
            items_awarded.append({"key": item_key, "name": name, "type": "material", "rarity": rarity, "amount": count})
            
        return items_awarded

    def start_promotion_trial(self, discord_id: int, next_rank: str):
        try:
            stats_json = self.db.get_player_stats_json(discord_id)
            p_stats = PlayerStats.from_dict(stats_json)
            
            boss_hp = int(p_stats.max_hp * 2.5)
            active_monster = {
                "name": f"Rank {next_rank} Examiner", "tier": "Boss", 
                "HP": boss_hp, "max_hp": boss_hp, "MP": 100, 
                "ATK": int(p_stats.endurance * 1.5 + 20), "DEF": int(p_stats.strength * 0.8), 
                "xp": 500, "drops": [], "promotion_target": next_rank
            }

            start = datetime.datetime.now()
            end = start + datetime.timedelta(hours=1)

            with self.db.get_connection() as conn:
                conn.execute("DELETE FROM adventure_sessions WHERE discord_id = ? AND active = 0", (discord_id,))
                conn.execute(
                    """
                    INSERT OR REPLACE INTO adventure_sessions
                    (discord_id, location_id, start_time, end_time, duration_minutes, active, logs, loot_collected, active_monster_json)
                    VALUES (?, 'guild_arena', ?, ?, -1, 1, ?, '{}', ?)
                    """,
                    (discord_id, start.isoformat(), end.isoformat(), 
                     json.dumps([f"{COMBAT} **PROMOTION TRIAL**\nThe Examiner awaits."]), 
                     json.dumps(active_monster))
                )
            return True
        except Exception as e:
            logger.error(f"Failed to start trial for {discord_id}: {e}")
            return False