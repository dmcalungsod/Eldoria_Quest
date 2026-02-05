"""
Database Manager for Eldoria Quest
----------------------------------
Fully optimized for SQLite with WAL mode, Foreign Key enforcement,
and atomic transaction handling via context managers.
"""

import datetime
import json
import logging
import sqlite3
from contextlib import contextmanager
from typing import Any

# Configure logging
logger = logging.getLogger("eldoria.db")

DATABASE_NAME = "EQ_Game.db"


class DatabaseManager:
    """
    Handles all database operations for Eldoria Quest.
    Enforces thread safety, connection cleanup, and data integrity.
    """

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_name: str = DATABASE_NAME):
        if self._initialized:
            return

        self.db_name = db_name
        self._class_cache = {}
        self._initialize_db_settings()
        self._initialized = True

    def _initialize_db_settings(self):
        """Applies performance and integrity settings on startup."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                # Write-Ahead Logging allows concurrent readers/writers
                conn.execute("PRAGMA journal_mode=WAL;")
        except sqlite3.Error as e:
            logger.critical(f"Failed to set database PRAGMAs: {e}")

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        - Ensures connections are always closed.
        - Automatically commits on success, rolls back on failure.
        - Enforces Foreign Keys on every connection.
        """
        conn = None
        try:
            # Timeout increased to handle busy locks
            conn = sqlite3.connect(self.db_name, timeout=20.0)
            conn.row_factory = sqlite3.Row
            # Crucial: Enforce relational integrity
            conn.execute("PRAGMA foreign_keys = ON;")
            # NORMAL sync is faster and safe enough for WAL - Must be set per connection
            conn.execute("PRAGMA synchronous=NORMAL;")
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database Transaction Error: {e}")
            raise e
        finally:
            if conn:
                conn.close()

    # ============================================================
    # PLAYER CORE
    # ============================================================

    def player_exists(self, discord_id: int) -> bool:
        """Checks if a player profile exists."""
        with self.get_connection() as conn:
            cur = conn.execute("SELECT 1 FROM players WHERE discord_id = ?", (discord_id,))
            return cur.fetchone() is not None

    def create_player(
        self,
        discord_id: int,
        name: str,
        class_id: int,
        stats_data: dict[str, Any],
        initial_hp: int,
        initial_mp: int,
        race: str | None = None,
        gender: str | None = None,
    ):
        """Creates a new player with stats."""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO players (
                    discord_id, name, class_id, race, gender,
                    level, experience, exp_to_next,
                    current_hp, current_mp, vestige_pool, aurum
                ) VALUES (?, ?, ?, ?, ?, 1, 0, 1000, ?, ?, 0, 0)
                """,
                (discord_id, name, class_id, race, gender, initial_hp, initial_mp),
            )
            conn.execute(
                "INSERT INTO stats (discord_id, stats_json) VALUES (?, ?)",
                (discord_id, json.dumps(stats_data)),
            )
            logger.info(f"Created new player: {name} ({discord_id})")

    def get_player(self, discord_id: int) -> sqlite3.Row | None:
        """Fetches the main player record."""
        with self.get_connection() as conn:
            return conn.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,)).fetchone()

    # ============================================================
    # STATS & VITALS
    # ============================================================

    def get_player_stats_json(self, discord_id: int) -> dict[str, Any]:
        """Fetches and parses the JSON stats block."""
        with self.get_connection() as conn:
            row = conn.execute("SELECT stats_json FROM stats WHERE discord_id = ?", (discord_id,)).fetchone()
            if not row or not row["stats_json"]:
                return {}
            try:
                return json.loads(row["stats_json"])
            except json.JSONDecodeError:
                logger.error(f"Corrupted stats_json for user {discord_id}")
                return {}

    def get_player_stats_row(self, discord_id: int) -> sqlite3.Row | None:
        """Fetches the raw stats row (including practice EXP columns)."""
        with self.get_connection() as conn:
            return conn.execute("SELECT * FROM stats WHERE discord_id = ?", (discord_id,)).fetchone()

    def update_player_stats(self, discord_id: int, stats_data: dict[str, Any]):
        """Updates the JSON stats block."""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE stats SET stats_json = ? WHERE discord_id = ?",
                (json.dumps(stats_data), discord_id),
            )

    def get_player_vitals(self, discord_id: int) -> sqlite3.Row | None:
        """Fetches current HP/MP."""
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT current_hp, current_mp FROM players WHERE discord_id = ?", (discord_id,)
            ).fetchone()

    def set_player_vitals(self, discord_id: int, hp: int, mp: int):
        """Updates current HP/MP."""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE players SET current_hp = ?, current_mp = ? WHERE discord_id = ?",
                (hp, mp, discord_id),
            )

    def update_player_level_data(self, discord_id: int, level: int, exp: int, exp_to_next: int):
        """Updates level and experience values."""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE players SET level = ?, experience = ?, exp_to_next = ? WHERE discord_id = ?",
                (level, exp, exp_to_next, discord_id),
            )

    # ============================================================
    # CLASS & SKILLS
    # ============================================================

    def get_class(self, class_id: int) -> dict[str, Any] | None:
        """Fetches class definition with caching."""
        if class_id in self._class_cache:
            return self._class_cache[class_id]

        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM classes WHERE id = ?", (class_id,)).fetchone()
            if row:
                data = dict(row)
                self._class_cache[class_id] = data
                return data
            return None

    def get_player_skills(self, discord_id: int) -> list[sqlite3.Row]:
        """Fetches all learned skills joined with skill definitions."""
        with self.get_connection() as conn:
            cur = conn.execute(
                """
                SELECT s.name, s.type, ps.skill_level, ps.skill_exp
                FROM player_skills ps
                JOIN skills s ON ps.skill_key = s.key_id
                WHERE ps.discord_id = ?
                ORDER BY s.type, s.name
                """,
                (discord_id,),
            )
            return cur.fetchall()

    def get_combat_skills(self, discord_id: int) -> list[dict[str, Any]]:
        """Fetches detailed skill info for combat (Active skills only)."""
        with self.get_connection() as conn:
            cur = conn.execute(
                """
                SELECT s.key_id, s.name, s.type, ps.skill_level, s.mp_cost,
                       s.power_multiplier, s.heal_power, s.buff_data
                FROM player_skills ps
                JOIN skills s ON ps.skill_key=s.key_id
                WHERE ps.discord_id=? AND s.type='Active'
                """,
                (discord_id,),
            )
            return [dict(row) for row in cur.fetchall()]

    # ============================================================
    # GUILD SYSTEM
    # ============================================================

    def get_guild_member_data(self, discord_id: int) -> sqlite3.Row | None:
        """Fetches guild membership details (Rank, Points)."""
        with self.get_connection() as conn:
            return conn.execute("SELECT * FROM guild_members WHERE discord_id = ?", (discord_id,)).fetchone()

    def get_guild_card_data(self, discord_id: int) -> sqlite3.Row | None:
        """Fetches data specifically for the Guild Card UI."""
        with self.get_connection() as conn:
            return conn.execute(
                """
                SELECT p.name, gm.rank, gm.join_date
                FROM players p
                JOIN guild_members gm ON p.discord_id = gm.discord_id
                WHERE p.discord_id = ?
                """,
                (discord_id,),
            ).fetchone()

    # ============================================================
    # GLOBAL SYSTEMS (Boosts)
    # ============================================================

    def get_active_boosts(self) -> list[dict[str, Any]]:
        """Fetches currently active global server boosts."""
        now = datetime.datetime.now().isoformat()
        try:
            with self.get_connection() as conn:
                cur = conn.execute(
                    "SELECT boost_key, multiplier, end_time FROM global_boosts WHERE end_time > ?", (now,)
                )
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching active boosts: {e}")
            return []

    def set_global_boost(self, key: str, multiplier: float, duration_hours: int):
        """
        Sets a global boost (e.g., exp_boost, loot_boost).
        Updates the record if it already exists.
        """
        end_time = (datetime.datetime.now() + datetime.timedelta(hours=duration_hours)).isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO global_boosts (boost_key, multiplier, end_time)
                VALUES (?, ?, ?)
                ON CONFLICT(boost_key) DO UPDATE SET
                    multiplier = excluded.multiplier,
                    end_time = excluded.end_time
                """,
                (key, multiplier, end_time),
            )
            logger.info(f"Global Boost Activated: {key} x{multiplier} for {duration_hours}h")

    def clear_global_boosts(self):
        """Removes all active global boosts."""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM global_boosts")
            logger.info("All Global Boosts cleared.")
