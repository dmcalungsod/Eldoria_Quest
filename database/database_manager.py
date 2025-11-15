"""
Database Manager for Eldoria Quest
----------------------------------
Optimized with context managers for better performance and resource management.
"""

import sqlite3
import json
from typing import Optional, Dict, Any, List
from contextlib import contextmanager


DATABASE_NAME = "EQ_Game.db"


class DatabaseManager:
    """Handles all database operations for Eldoria Quest with optimized connection handling."""

    def __init__(self):
        self.db_name = DATABASE_NAME

    # ------------------------------------------------------------
    # INTERNAL CONNECTION HANDLER (OPTIMIZED)
    # ------------------------------------------------------------
    @contextmanager
    def get_connection(self):
        """Context manager for database connections - ensures proper cleanup."""
        conn = sqlite3.connect(self.db_name, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def connect(self):
        """Legacy method for backward compatibility."""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------
    # PLAYER EXISTENCE
    # ------------------------------------------------------------
    def player_exists(self, discord_id: int) -> bool:
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM players WHERE discord_id = ?", (discord_id,))
        exists = cur.fetchone() is not None

        conn.close()
        return exists

    # ------------------------------------------------------------
    # CREATE NEW PLAYER
    # ------------------------------------------------------------
    def create_player(
        self,
        discord_id: int,
        name: str,
        class_id: int,
        stats_data: Dict[str, Any],
        initial_hp: int,
        initial_mp: int,
        race: Optional[str] = None,
        gender: Optional[str] = None,
    ):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO players (discord_id, name, class_id, race, gender, 
                                 level, experience, exp_to_next, 
                                 current_hp, current_mp)
            VALUES (?, ?, ?, ?, ?, 1, 0, 100, ?, ?)
        """,
            (discord_id, name, class_id, race, gender, initial_hp, initial_mp),
        )

        cur.execute(
            """
            INSERT INTO stats (discord_id, stats_json)
            VALUES (?, ?)
        """,
            (discord_id, json.dumps(stats_data)),
        )

        conn.commit()
        conn.close()

    # ------------------------------------------------------------
    # GET PLAYER BASE DATA
    # ------------------------------------------------------------
    def get_player(self, discord_id: int) -> Optional[sqlite3.Row]:
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,))
        row = cur.fetchone()

        conn.close()
        return row

    # ------------------------------------------------------------
    # CLASS DATA
    # ------------------------------------------------------------
    def get_class(self, class_id: int) -> Optional[sqlite3.Row]:
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
        row = cur.fetchone()

        conn.close()
        return row

    # ------------------------------------------------------------
    # STATS JSON LOADING
    # ------------------------------------------------------------
    def get_player_stats_json(self, discord_id: int) -> Dict[str, Any]:
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("SELECT stats_json FROM stats WHERE discord_id = ?", (discord_id,))
        row = cur.fetchone()

        conn.close()

        if not row:
            return {}

        return json.loads(row["stats_json"])

    # --- NEW FUNCTION ---
    # ------------------------------------------------------------
    # PLAYER VITALS (HP/MP)
    # ------------------------------------------------------------
    def get_player_vitals(self, discord_id: int) -> Optional[sqlite3.Row]:
        """
        Fetches the player's current HP and MP.
        """
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT current_hp, current_mp FROM players WHERE discord_id = ?",
            (discord_id,),
        )
        row = cur.fetchone()
        conn.close()
        return row

    # --- NEW FUNCTION ---
    def set_player_vitals(self, discord_id: int, hp: int, mp: int):
        """
        Updates the player's current HP and MP.
        """
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE players SET current_hp = ?, current_mp = ? WHERE discord_id = ?",
            (hp, mp, discord_id),
        )
        conn.commit()
        conn.close()

    # ------------------------------------------------------------
    # PLAYER SKILLS
    # ------------------------------------------------------------
    def get_player_skills(self, discord_id: int) -> List[sqlite3.Row]:
        """
        Fetches all skills a player has learned, joining with the skills table.
        """
        conn = self.connect()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT s.name, s.type, ps.skill_level
            FROM player_skills ps
            JOIN skills s ON ps.skill_key = s.key_id
            WHERE ps.discord_id = ?
            ORDER BY s.type, s.name
        """,
            (discord_id,),
        )

        rows = cur.fetchall()
        conn.close()
        return rows

    # ------------------------------------------------------------
    # UPDATE STORED STATS
    # ------------------------------------------------------------
    def update_player_stats(self, discord_id: int, stats_data: Dict[str, Any]):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE stats
            SET stats_json = ?
            WHERE discord_id = ?
        """,
            (json.dumps(stats_data), discord_id),
        )

        conn.commit()
        conn.close()

    # ------------------------------------------------------------
    # UPDATE LEVEL+EXP
    # ------------------------------------------------------------
    def update_player_level_data(
        self, discord_id: int, level: int, exp: int, exp_to_next: int
    ):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE players
            SET level = ?, experience = ?, exp_to_next = ?
            WHERE discord_id = ?
        """,
            (level, exp, exp_to_next, discord_id),
        )

        conn.commit()
        conn.close()
