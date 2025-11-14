"""
Database Manager for Eldoria Quest
----------------------------------

Responsible for all interaction with EQ_Game.db.

Handles:
- Player creation
- Checking player existence
- Loading / saving stats (JSON)
- Updating levels, EXP, and class info
- Fetching class definitions

This file contains:
- DatabaseManager class
"""

import sqlite3
import json
from typing import Optional, Dict, Any


DATABASE_NAME = "EQ_Game.db"


class DatabaseManager:
    """Handles all database operations for Eldoria Quest."""

    def __init__(self):
        self.db_name = DATABASE_NAME

    # ------------------------------------------------------------
    # INTERNAL CONNECTION HANDLER
    # ------------------------------------------------------------
    def connect(self):
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
    def create_player(self, discord_id: int, name: str, class_id: int, stats_data: Dict[str, Any]):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO players (discord_id, name, class_id, level, experience, exp_to_next)
            VALUES (?, ?, ?, 1, 0, 100)
        """, (discord_id, name, class_id))

        cur.execute("""
            INSERT INTO stats (discord_id, stats_json)
            VALUES (?, ?)
        """, (discord_id, json.dumps(stats_data)))

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

    # ------------------------------------------------------------
    # UPDATE STORED STATS
    # ------------------------------------------------------------
    def update_player_stats(self, discord_id: int, stats_data: Dict[str, Any]):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            UPDATE stats
            SET stats_json = ?
            WHERE discord_id = ?
        """, (json.dumps(stats_data), discord_id))

        conn.commit()
        conn.close()

    # ------------------------------------------------------------
    # UPDATE LEVEL+EXP
    # ------------------------------------------------------------
    def update_player_level_data(self, discord_id: int, level: int, exp: int, exp_to_next: int):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            UPDATE players
            SET level = ?, experience = ?, exp_to_next = ?
            WHERE discord_id = ?
        """, (level, exp, exp_to_next, discord_id))

        conn.commit()
        conn.close()
