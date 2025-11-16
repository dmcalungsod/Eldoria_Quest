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
        """
        start_time = datetime.datetime.now()

        if duration_minutes == -1:
            end_time = start_time + datetime.timedelta(days=90)
        else:
            end_time = start_time + datetime.timedelta(minutes=duration_minutes)

        # Use the context manager for a safe transaction
        with self.db.get_connection() as conn:
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

        # session.save_state() is called inside simulate_step, which is good

        if result_dict.get("dead", False):
            # Player is dead, grant 0 EXP but process loot
            stats_json = self.db.get_player_stats_json(discord_id)
            player_stats = PlayerStats.from_dict(stats_json)
            items_to_add = []
            with self.db.get_connection() as conn:
                items_to_add = self._grant_rewards(session, 0, conn, player_stats)
            
            for item in items_to_add:
                self.inventory_manager.add_item(
                    discord_id=discord_id,
                    item_key=item["key"],
                    item_name=item["name"],
                    item_type=item["type"],
                    rarity=item["rarity"],
                    amount=item["amount"],
                )

        return result_dict

    def end_adventure(self, discord_id: int):
        """
        Manually ends an adventure (e.g., "Return to City").
        Grants all collected EXP and loot.
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
                    session, total_exp, conn, player_stats
                )

                cur.execute(
                    "UPDATE adventure_sessions SET active = 0 WHERE discord_id = ?",
                    (discord_id,),
                )
        
        for item in items_to_add:
            self.inventory_manager.add_item(
                discord_id=discord_id,
                item_key=item["key"],
                item_name=item["name"],
                item_type=item["type"],
                rarity=item["rarity"],
                amount=item["amount"],
            )


    def _grant_rewards(
        self,
        session: AdventureSession,
        total_exp: int,
        conn: sqlite3.Connection,
        player_stats: PlayerStats, 
    ) -> list: 
        """
        (Internal) Grants EXP and Items to the player's main profile.
        Uses the connection passed in from end_adventure to prevent db locks.
        Returns a list of items to be added to inventory.
        
        --- THIS VERSION ONLY HEALS MP, NOT HP ---
        """
        cur = conn.cursor()
        cur.execute("SELECT * FROM players WHERE discord_id = ?", (session.discord_id,))
        player_row = cur.fetchone()

        level_system = LevelUpSystem(
            stats=player_stats,
            level=player_row["level"],
            exp=player_row["experience"],
            exp_to_next=player_row["exp_to_next"],
        )

        if total_exp > 0:
            level_system.add_exp(total_exp)

            cur.execute(
                """
                UPDATE players
                SET level = ?, experience = ?, exp_to_next = ?
                WHERE discord_id = ?
            """,
                (
                    level_system.level,
                    level_system.exp,
                    level_system.exp_to_next,
                    session.discord_id,
                ),
            )

            cur.execute(
                "UPDATE players SET vestige_pool = vestige_pool + ? WHERE discord_id = ?",
                (total_exp, session.discord_id),
            )

        # --- Restore Vitals (THE FIX IS HERE) ---
        new_max_mp = level_system.stats.max_mp # We only care about MP
        
        # Get the HP the player ended the adventure with
        current_hp_from_db = player_row['current_hp']
        
        # If they died, set HP to 1. Otherwise, it stays as-is.
        hp_to_save = 1 if current_hp_from_db <= 0 else current_hp_from_db
        
        # Always restore MP
        mp_to_save = new_max_mp  

        cur.execute(
            "UPDATE players SET current_hp = ?, current_mp = ? WHERE discord_id = ?",
            (hp_to_save, mp_to_save, session.discord_id),
        )
        # --- END OF FIX ---

        # Add Materials to Inventory
        items_to_add = []
        for item_key, count in session.loot.items():
            mat_data = MATERIALS.get(item_key)

            if mat_data:
                item_name = mat_data["name"]
                item_rarity = mat_data.get("rarity", "Common")
            else:
                item_name = item_key
                item_rarity = "Common"

            items_to_add.append(
                {
                    "key": item_key,
                    "name": item_name,
                    "type": "material",
                    "rarity": item_rarity,
                    "amount": count,
                }
            )
            
        return items_to_add

    async def fail_adventure(self, session: AdventureSession):
        """
        Note: This function is not currently called, but is good to have.
        """
        user = self.bot.get_user(session.discord_id)
        if user:
            try:
                await user.send(
                    f"{E.DEFEAT} **You have been defeated!**\n"
                    "You collapsed in the wilds. A Guild rescue team retrieved your body, "
                    "but any unbanked Vestige was lost. Your recovered materials are in your inventory."
                )
            except:
                pass