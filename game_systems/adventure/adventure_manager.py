"""
adventure_manager.py

Coordinates all active adventures across Eldoria.
Handles creation, progression, boss trials, and reward distribution.
Compatible with the improved MANUAL + AUTO hybrid AdventureSession system.
"""

import datetime
import json

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.data.materials import MATERIALS
from game_systems.guild_system.quest_system import QuestSystem
from game_systems.items.inventory_manager import InventoryManager
from game_systems.player.level_up import LevelUpSystem
from game_systems.player.player_stats import PlayerStats

from .adventure_session import AdventureSession


class AdventureManager:
    """
    Oversees all adventure sessions:
    • Normal expeditions
    • Timed adventures
    • Rank Promotion Trials
    • Reward and level-up handling
    """

    def __init__(self, db_manager: DatabaseManager, bot):
        self.db = db_manager
        self.bot = bot
        self.inventory_manager = InventoryManager(self.db)
        self.quest_system = QuestSystem(self.db)

    # --------------------------------------------------
    # Normal Adventure Start
    # --------------------------------------------------

    def start_adventure(self, discord_id: int, location_id: str, duration_minutes: int):
        """
        Starts a new adventure session.
        Duration -1 means “long expedition” (up to 90 days).
        """
        start_time = datetime.datetime.now()
        end_time = (
            start_time + datetime.timedelta(days=90)
            if duration_minutes == -1
            else start_time + datetime.timedelta(minutes=duration_minutes)
        )

        self._create_session(discord_id, location_id, start_time, end_time, duration_minutes)
        return True

    # --------------------------------------------------
    # Rank Promotion Trial
    # --------------------------------------------------

    def start_promotion_trial(self, discord_id: int, next_rank: str):
        """
        Initializes a special Promotion Trial.
        The player faces a scaling, boss-tier Examiner within the Guild Arena.
        """
        stats_json = self.db.get_player_stats_json(discord_id)
        p_stats = PlayerStats.from_dict(stats_json)

        # --- Examiner Scaling ---
        boss_hp = int(p_stats.max_hp * 2.5)
        boss_atk = int(p_stats.endurance * 1.5 + (p_stats.max_hp / 10))
        boss_def = int(p_stats.strength * 0.8)

        active_monster = {
            "name": f"Rank {next_rank} Examiner",
            "level": 99,  # Cosmetic
            "tier": "Boss",  # Forces manual combat
            "HP": boss_hp,
            "max_hp": boss_hp,
            "MP": 100,
            "ATK": boss_atk,
            "DEF": boss_def,
            "xp": 500,
            "drops": [],  # No material drops for trials
            "promotion_target": next_rank,
        }

        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(hours=1)

        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # Clean old inactive sessions
            cur.execute("DELETE FROM adventure_sessions WHERE discord_id = ? AND active = 0", (discord_id,))

            # Insert new arena session
            cur.execute(
                """
                INSERT OR REPLACE INTO adventure_sessions
                (discord_id, location_id, start_time, end_time, duration_minutes, active, logs, loot_collected, active_monster_json)
                VALUES (?, ?, ?, ?, ?, 1, ?, '{}', ?)
                """,
                (
                    discord_id,
                    "guild_arena",
                    start_time.isoformat(),
                    end_time.isoformat(),
                    -1,
                    json.dumps([f"{E.COMBAT} **PROMOTION TRIAL COMMENCED**\nThe Examiner steps forward."]),
                    json.dumps(active_monster),
                ),
            )

        return True

    # --------------------------------------------------
    # Helper — Session Creation
    # --------------------------------------------------

    def _create_session(self, discord_id, location_id, start_time, end_time, duration):
        """Internal method: Inserts a new adventure session."""
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
                    duration,
                ),
            )

    # --------------------------------------------------
    # Fetch / Simulate
    # --------------------------------------------------

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

    def simulate_adventure_step(self, discord_id: int) -> dict:
        """
        Runs a single step in AUTO adventure mode.
        Returns logs + state flags.
        """
        session_row = self.get_active_session(discord_id)
        if not session_row:
            return {"log": ["Error: No active session."], "dead": True}

        session = AdventureSession(
            self.db,
            self.quest_system,
            self.inventory_manager,
            discord_id,
            session_row,
        )

        result_dict = session.simulate_step()

        # If the player dies during AUTO mode, grant minimal rewards
        if result_dict.get("dead", False):
            stats_json = self.db.get_player_stats_json(discord_id)
            player_stats = PlayerStats.from_dict(stats_json)

            with self.db.get_connection() as conn:
                items_awarded = self._grant_rewards(
                    session=session,
                    total_exp=0,
                    conn=conn,
                    player_stats=player_stats,
                )

            for item in items_awarded:
                self.inventory_manager.add_item(
                    discord_id,
                    item["key"],
                    item["name"],
                    item["type"],
                    item["rarity"],
                    item["amount"],
                )

        return result_dict

    # --------------------------------------------------
    # Adventure End
    # --------------------------------------------------

    def end_adventure(self, discord_id: int):
        """
        Finalizes an adventure:
        • Grants EXP + Materials
        • Levels up player
        • Saves Vitals
        """
        stats_json = self.db.get_player_stats_json(discord_id)
        player_stats = PlayerStats.from_dict(stats_json)

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM adventure_sessions WHERE discord_id = ? AND active = 1",
                (discord_id,),
            )
            session_row = cur.fetchone()

            if not session_row:
                return

            session = AdventureSession(self.db, self.quest_system, self.inventory_manager, discord_id, session_row)
            total_exp = session.loot.pop("exp", 0)

            items_to_add = self._grant_rewards(session, total_exp, conn, player_stats)

            cur.execute(
                "UPDATE adventure_sessions SET active = 0 WHERE discord_id = ?",
                (discord_id,),
            )

        for item in items_to_add:
            self.inventory_manager.add_item(
                discord_id,
                item["key"],
                item["name"],
                item["type"],
                item["rarity"],
                item["amount"],
            )

    # --------------------------------------------------
    # Rewards / Level Up
    # --------------------------------------------------

    def _grant_rewards(self, session, total_exp, conn, player_stats) -> list:
        """
        Grants EXP, performs Level Ups, and converts collected materials
        into proper inventory items.
        """
        cur = conn.cursor()
        cur.execute("SELECT * FROM players WHERE discord_id = ?", (session.discord_id,))
        p_row = cur.fetchone()

        level_sys = LevelUpSystem(
            stats=player_stats,
            level=p_row["level"],
            exp=p_row["experience"],
            exp_to_next=p_row["exp_to_next"],
        )

        # Experience Gain
        if total_exp > 0:
            level_sys.add_exp(total_exp)

        # HP/MP Save Rules
        current_hp = p_row["current_hp"]
        saved_hp = 1 if current_hp <= 0 else current_hp
        saved_mp = level_sys.stats.max_mp

        cur.execute(
            """
            UPDATE players
            SET level = ?, experience = ?, exp_to_next = ?, vestige_pool = vestige_pool + ?, current_hp = ?, current_mp = ?
            WHERE discord_id = ?
            """,
            (
                level_sys.level,
                level_sys.exp,
                level_sys.exp_to_next,
                total_exp,
                saved_hp,
                saved_mp,
                session.discord_id,
            ),
        )

        # Convert session loot into final inventory items
        items_awarded = []
        for item_key, count in session.loot.items():
            mat = MATERIALS.get(item_key)
            name = mat["name"] if mat else item_key
            rarity = mat.get("rarity", "Common") if mat else "Common"

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
