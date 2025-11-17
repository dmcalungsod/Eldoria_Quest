"""
adventure_manager.py

Orchestrates all active adventures.
Compatible with the improved MANUAL + AUTO hybrid AdventureSession.
"""

import sqlite3
import json
import datetime
from discord.ext import tasks
from database.database_manager import DatabaseManager
from game_systems.items.inventory_manager import InventoryManager
from game_systems.guild_system.quest_system import QuestSystem
from game_systems.player.player_stats import PlayerStats
from game_systems.player.level_up import LevelUpSystem
from .adventure_session import AdventureSession
from game_systems.data.materials import MATERIALS
import game_systems.data.emojis as E


# =====================================================================
# ADVENTURE MANAGER
# =====================================================================

class AdventureManager:
    def __init__(self, db_manager: DatabaseManager, bot):
        self.db = db_manager
        self.bot = bot

        self.inventory_manager = InventoryManager(self.db)
        self.quest_system = QuestSystem(self.db)

    # =================================================================
    # START ADVENTURE
    # =================================================================

    def start_adventure(self, discord_id: int, location_id: str, duration_minutes: int):
        """
        Begins a new adventure session in the DB.
        """

        start_time = datetime.datetime.now()

        if duration_minutes == -1:
            # Effectively infinite until manually ended
            end_time = start_time + datetime.timedelta(days=90)
        else:
            end_time = start_time + datetime.timedelta(minutes=duration_minutes)

        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # Cleanup inactive sessions
            cur.execute(
                "DELETE FROM adventure_sessions WHERE discord_id = ? AND active = 0",
                (discord_id,),
            )

            # Create new session
            cur.execute(
                """
                INSERT OR REPLACE INTO adventure_sessions 
                (discord_id, location_id, start_time, end_time, duration_minutes, active, logs, loot_collected)
                VALUES (?, ?, ?, ?, ?, 1, '[]', '{}')
                """,
                (
                    discord_id,
                    location_id,
                    start_time.isoformat(),
                    end_time.isoformat(),
                    duration_minutes,
                ),
            )

        return True

    # =================================================================
    # LOAD AN ACTIVE SESSION
    # =================================================================

    def get_active_session(self, discord_id):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM adventure_sessions WHERE discord_id = ? AND active = 1",
            (discord_id,),
        )
        row = cur.fetchone()
        conn.close()
        return row

    # =================================================================
    # SIMULATE A SINGLE STEP
    # =================================================================

    def simulate_adventure_step(self, discord_id: int) -> dict:
        """
        Loads the session, simulates one step, updates DB, and returns result.
        """

        session_row = self.get_active_session(discord_id)
        if not session_row:
            return {
                "log": ["Error: Could not find your active adventure session."],
                "dead": True,
            }

        session = AdventureSession(
            self.db,
            self.quest_system,
            self.inventory_manager,
            discord_id,
            session_row,
        )

        result_dict = session.simulate_step()

        # If the player died in this step:
        if result_dict.get("dead", False):
            stats_json = self.db.get_player_stats_json(discord_id)
            player_stats = PlayerStats.from_dict(stats_json)

            # Even if dead, loot is preserved. EXP = 0.
            with self.db.get_connection() as conn:
                items_awarded = self._grant_rewards(
                    session=session,
                    total_exp=0,
                    conn=conn,
                    player_stats=player_stats,
                )

            # Add materials to inventory
            for item in items_awarded:
                self.inventory_manager.add_item(
                    discord_id=discord_id,
                    item_key=item["key"],
                    item_name=item["name"],
                    item_type=item["type"],
                    rarity=item["rarity"],
                    amount=item["amount"],
                )

        return result_dict

    # =================================================================
    # MANUAL END (Return to city)
    # =================================================================

    def end_adventure(self, discord_id: int):
        """
        Manually ends an adventure.
        Grants collected EXP + items.
        DOES NOT HEAL HP — except MP restore at end.
        """

        stats_json = self.db.get_player_stats_json(discord_id)
        player_stats = PlayerStats.from_dict(stats_json)

        items_to_add = []

        with self.db.get_connection() as conn:
            cur = conn.cursor()

            cur.execute(
                "SELECT * FROM adventure_sessions WHERE discord_id = ? AND active = 1",
                (discord_id,),
            )
            session_row = cur.fetchone()

            if session_row:
                session = AdventureSession(
                    self.db,
                    self.quest_system,
                    self.inventory_manager,
                    discord_id,
                    session_row,
                )

                total_exp = session.loot.pop("exp", 0)

                items_to_add = self._grant_rewards(
                    session=session,
                    total_exp=total_exp,
                    conn=conn,
                    player_stats=player_stats,
                )

                # End session
                cur.execute(
                    "UPDATE adventure_sessions SET active = 0 WHERE discord_id = ?",
                    (discord_id,),
                )

        # Add material rewards
        for item in items_to_add:
            self.inventory_manager.add_item(
                discord_id=discord_id,
                item_key=item["key"],
                item_name=item["name"],
                item_type=item["type"],
                rarity=item["rarity"],
                amount=item["amount"],
            )

    # =================================================================
    # INTERNAL: REWARD GRANTING
    # =================================================================

    def _grant_rewards(
        self,
        session: AdventureSession,
        total_exp: int,
        conn: sqlite3.Connection,
        player_stats: PlayerStats,
    ) -> list:
        """
        Unified EXP + loot reward handler.
        HP does NOT heal.
        MP is always restored.
        """

        cur = conn.cursor()

        # Load player core stats
        cur.execute("SELECT * FROM players WHERE discord_id = ?", (session.discord_id,))
        p_row = cur.fetchone()

        # Level handler
        level_sys = LevelUpSystem(
            stats=player_stats,
            level=p_row["level"],
            exp=p_row["experience"],
            exp_to_next=p_row["exp_to_next"],
        )

        # -------- EXP + LEVEL --------
        if total_exp > 0:
            level_sys.add_exp(total_exp)

        # -------- VITALS --------

        # Current HP from database (after last combat)
        current_hp = p_row["current_hp"]

        # If they died, revive with 1 HP.
        hp_save = 1 if current_hp <= 0 else current_hp

        # MP always restored on return to city
        mp_save = level_sys.stats.max_mp

        cur.execute(
            """
            UPDATE players
            SET 
                level = ?, 
                experience = ?, 
                exp_to_next = ?,
                vestige_pool = vestige_pool + ?,
                current_hp = ?,
                current_mp = ?
            WHERE discord_id = ?
            """,
            (
                level_sys.level,
                level_sys.exp,
                level_sys.exp_to_next,
                total_exp,
                hp_save,
                mp_save,
                session.discord_id,
            ),
        )

        # -------- MATERIAL LOOT --------

        items_awarded = []
        for item_key, count in session.loot.items():
            mat = MATERIALS.get(item_key, None)

            if mat:
                name = mat["name"]
                rarity = mat.get("rarity", "Common")
            else:
                name = item_key
                rarity = "Common"

            items_awarded.append(
                {
                    "key": item_key,
                    "name": name,
                    "type": "material",
                    "rarity": rarity,
                    "amount": count,
                }
            )

        return items_awarded

    # =================================================================
    # NOT CURRENTLY USED (Future death handling)
    # =================================================================

    async def fail_adventure(self, session: AdventureSession):
        """
        Optional future feature — handles death notifications.
        """
        user = self.bot.get_user(session.discord_id)
        if user:
            try:
                await user.send(
                    f"{E.DEFEAT} **You have been defeated!**\n"
                    "A Guild rescue team recovered you, but your Vestige was lost.\n"
                    "Materials gathered remain in your inventory."
                )
            except:
                pass
