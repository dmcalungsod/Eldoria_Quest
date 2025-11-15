"""
adventure_manager.py

Orchestrates all active adventures.
(Refactored for a MANUAL, step-by-step exploration system)
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


class AdventureManager:
    def __init__(self, db_manager: DatabaseManager, bot):
        self.db = db_manager
        self.bot = bot

        self.inventory_manager = InventoryManager(self.db)
        self.quest_system = QuestSystem(self.db)

    def start_adventure(self, discord_id: int, location_id: str, duration_minutes: int):
        """
        Begins a new adventure session in the DB.
        If duration_minutes is -1, it's an 'active' session, not a timed one.
        """
        start_time = datetime.datetime.now()

        if duration_minutes == -1:
            end_time = start_time + datetime.timedelta(days=90)
        else:
            end_time = start_time + datetime.timedelta(minutes=duration_minutes)

        conn = self.db.connect()
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM adventure_sessions WHERE discord_id = ? AND active = 0",
            (discord_id,),
        )

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

        conn.commit()
        conn.close()
        return True

    def get_active_session(self, discord_id):
        """Checks for a currently active session for a player."""
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM adventure_sessions WHERE discord_id = ? AND active = 1",
            (discord_id,),
        )
        row = cur.fetchone()
        conn.close()
        return row

    def simulate_adventure_step(self, discord_id: int) -> dict:
        """
        Loads the session, simulates one step, saves, and returns the result.
        This is the new main entry point for the 'Explore' button.
        """
        session_row = self.get_active_session(discord_id)
        if not session_row:
            return {
                "log": ["Error: Could not find your active adventure session."],
                "dead": True,
            }

        session = AdventureSession(self.db, self.quest_system, discord_id, session_row)

        # Simulate one step and get the results
        result_dict = session.simulate_step()

        # Save the updated state (logs, loot, active status) to the DB
        session.save_state()

        # If the player died, grant rewards (which is just items, no EXP)
        if result_dict.get("dead", False):
            # We call _grant_rewards with 0 EXP
            self._grant_rewards(session, 0)

        return result_dict

    def end_adventure(self, discord_id: int):
        """
        Manually ends an adventure (e.g., "Return to Guild").
        Grants all collected EXP and loot.
        """
        conn = self.db.connect()
        cur = conn.cursor()

        session_row = self.get_active_session(discord_id)
        if session_row:
            session = AdventureSession(
                self.db, self.quest_system, discord_id, session_row
            )

            total_exp = session.loot.pop("exp", 0)
            self._grant_rewards(session, total_exp)

            cur.execute(
                "UPDATE adventure_sessions SET active = 0 WHERE discord_id = ?",
                (discord_id,),
            )

        conn.commit()
        conn.close()

    def _grant_rewards(self, session: AdventureSession, total_exp: int):
        """
        (Internal) Grants EXP and Items to the player's main profile.
        """
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM players WHERE discord_id = ?", (session.discord_id,))
        player_row = cur.fetchone()
        stats_json = self.db.get_player_stats_json(session.discord_id)
        player_stats = PlayerStats.from_dict(stats_json)

        level_system = LevelUpSystem(
            stats=player_stats,
            level=player_row["level"],
            exp=player_row["experience"],
            exp_to_next=player_row["exp_to_next"],
        )

        # Only add EXP if it's greater than 0 (i.e., not dead)
        if total_exp > 0:
            level_system.add_exp(total_exp)

            self.db.update_player_level_data(
                session.discord_id,
                level_system.level,
                level_system.exp,
                level_system.exp_to_next,
            )
            self.db.update_player_stats(
                session.discord_id, level_system.stats.to_dict()
            )

        # Add Items to Inventory (even if dead)
        for item_key, count in session.loot.items():
            mat_data = MATERIALS.get(item_key)
            item_name = mat_data["name"] if mat_data else item_key

            self._add_item_key_to_inventory(
                session.discord_id, item_key, item_name, "material", count
            )

        conn.close()

    def _add_item_key_to_inventory(
        self, discord_id, item_key, item_name, item_type, amount
    ):
        """
        Private helper to add an item to inventory using its key.
        """
        conn = self.db.connect()
        cur = conn.cursor()

        cur.execute(
            "SELECT count FROM inventory WHERE discord_id = ? AND item_key = ? AND item_type = ?",
            (discord_id, item_key, item_type),
        )
        row = cur.fetchone()

        if row:
            cur.execute(
                "UPDATE inventory SET count = count + ? WHERE discord_id = ? AND item_key = ?",
                (amount, discord_id, item_key),
            )
        else:
            cur.execute(
                "INSERT INTO inventory (discord_id, item_key, item_name, item_type, count) VALUES (?, ?, ?, ?, ?)",
                (discord_id, item_key, item_name, item_type, amount),
            )
        conn.commit()
        conn.close()

    async def fail_adventure(self, session: AdventureSession):
        """
        Called when a player dies. This is now handled by _grant_rewards,
        but we still need to send the DM.
        """
        user = self.bot.get_user(session.discord_id)
        if user:
            try:
                await user.send(
                    f"{E.DEFEAT} **You have been defeated!**\n"
                    "You collapsed in the wilds. A Guild rescue team retrieved your body, "
                    "but any unbanked EXP was lost. Your recovered materials are in your inventory."
                )
            except:
                pass
