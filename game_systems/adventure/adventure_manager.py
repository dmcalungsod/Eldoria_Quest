"""
adventure_manager.py

Orchestrates all active adventures.
(Refactored for material-based economy)
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

        # Create instances of systems we need
        self.inventory_manager = InventoryManager(self.db)
        self.quest_system = QuestSystem(self.db)

        # Start the background loop
        self.update_loop.start()

    def start_adventure(self, discord_id: int, location_id: str, duration_minutes: int):
        """
        Begins a new adventure session in the DB.
        """
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(minutes=duration_minutes)

        conn = self.db.connect()
        cur = conn.cursor()

        # Clear old/finished sessions
        cur.execute(
            "DELETE FROM adventure_sessions WHERE discord_id = ? AND active = 0",
            (discord_id,),
        )

        cur.execute(
            """
            INSERT INTO adventure_sessions 
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

    @tasks.loop(minutes=5)
    async def update_loop(self):
        """
        Runs every 5 minutes.
        1. Checks all active sessions.
        2. Triggers a simulation step (fight).
        3. Checks if time is up.
        """
        await self.bot.wait_until_ready()

        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM adventure_sessions WHERE active = 1")
        active_rows = cur.fetchall()
        conn.close()

        for row_data in active_rows:
            # Pass the QuestSystem to the session
            session = AdventureSession(
                self.db, self.quest_system, row_data["discord_id"], row_data
            )

            # Check if time expired
            now = datetime.datetime.now()
            if now >= session.end_time:
                await self.complete_adventure(session)
                continue

            # Simulate one 5-minute step
            is_alive = await session.simulate_step()

            if not is_alive:
                # Player died in combat
                await self.fail_adventure(session)

    async def complete_adventure(self, session: AdventureSession):
        """
        Finalizes the adventure, grants rewards, and notifies the user.
        """
        # 1. Pop EXP, leaving only materials in the loot dict
        total_exp = session.loot.pop("exp", 0)

        # 2. Grant Rewards to DB
        conn = self.db.connect()
        cur = conn.cursor()

        # --- Apply EXP ---
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
        leveled_up = level_system.add_exp(total_exp)

        # Save updated player data
        self.db.update_player_level_data(
            session.discord_id,
            level_system.level,
            level_system.exp,
            level_system.exp_to_next,
        )
        self.db.update_player_stats(session.discord_id, level_system.stats.to_dict())

        # --- Add Items to Inventory ---
        loot_summary_list = []
        for item_key, count in session.loot.items():
            mat_data = MATERIALS.get(item_key)
            item_name = mat_data["name"] if mat_data else item_key

            # Use InventoryManager to add to DB
            self._add_item_key_to_inventory(
                session.discord_id, item_key, item_name, "material", count
            )

            loot_summary_list.append(f"{item_name} x{count}")

        # Mark session inactive
        cur.execute(
            "UPDATE adventure_sessions SET active = 0 WHERE discord_id = ?",
            (session.discord_id,),
        )
        conn.commit()
        conn.close()

        # 3. Notify User (DM)
        user = self.bot.get_user(session.discord_id)
        if user:
            loot_str = ", ".join(loot_summary_list) if loot_summary_list else "nothing"

            summary = (
                f"{E.VICTORY} **Adventure Complete!**\n"
                f"You have returned from the wilds, weary but successful.\n\n"
                f"{E.EXP} **EXP Gained:** `+{total_exp}`\n"
                f"{E.ITEM_BOX} **Materials Hauled:** {loot_str}\n\n"
                f"*(Take your materials to the Guild Exchange to sell them for Aurum!)*"
            )
            if leveled_up:
                summary += (
                    f"\n\n{E.LEVEL_UP} **You are now Level {level_system.level}!**"
                )

            try:
                await user.send(summary)
            except:
                pass  # Can't DM

    def _add_item_key_to_inventory(
        self, discord_id, item_key, item_name, item_type, amount
    ):
        """
        Private helper to add an item to inventory using its key,
        which is needed for the Guild Exchange to find its value.
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
        # Handle death (No EXP, No Loot)
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE adventure_sessions SET active = 0 WHERE discord_id = ?",
            (session.discord_id,),
        )
        conn.commit()
        conn.close()

        user = self.bot.get_user(session.discord_id)
        if user:
            try:
                await user.send(
                    f"{E.DEFEAT} **Adventure Failed**\n"
                    "You were defeated in the wilds. The Guild rescue team "
                    "retrieved your body, but your haul was lost..."
                )
            except:
                pass

    @update_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
