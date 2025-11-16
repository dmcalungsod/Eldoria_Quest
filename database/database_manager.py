"""
Database Manager for Eldoria Quest
----------------------------------
Optimized with context managers for better performance and resource management.
"""

import sqlite3
import json
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import datetime


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
            
            -- --- THIS IS THE CHANGE ---
            VALUES (?, ?, ?, ?, ?, 1, 0, 1000, ?, ?)
            -- --- END OF CHANGE ---
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
    def get_player_stats_row(self, discord_id: int) -> Optional[sqlite3.Row]:
        """
        Fetches the entire row from the 'stats' table, including
        stats_json and all stat_exp columns.
        """
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("SELECT * FROM stats WHERE discord_id = ?", (discord_id,))
        row = cur.fetchone()

        conn.close()
        return row
    # --- END NEW FUNCTION ---

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

    # --- THIS FUNCTION IS MODIFIED ---
    def get_active_boosts(self) -> List[Dict[str, Any]]:
        """
        Fetches all active (non-expired) global boosts.
        Returns a list of dictionaries, 
        e.g., [{"boost_key": "exp_boost", "multiplier": 2.0, "end_time": "..."}]
        """
        boosts = []
        now = datetime.datetime.now().isoformat()
        
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT boost_key, multiplier, end_time FROM global_boosts WHERE end_time > ?",
                    (now,)
                )
                for row in cur.fetchall():
                    boosts.append(dict(row))
        except Exception as e:
            print(f"Error fetching active boosts: {e}")
            
        return boosts
    # --- END OF MODIFICATION ---

    # --- NEW HELPER FUNCTIONS FOR ASYNC ---

    def get_guild_member_data(self, discord_id: int) -> Optional[sqlite3.Row]:
        """Fetches guild member rank."""
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT rank FROM guild_members WHERE discord_id = ?", (discord_id,)
        )
        row = cur.fetchone()
        conn.close()
        return row

    def get_guild_card_data(self, discord_id: int) -> Optional[sqlite3.Row]:
        """Fetches data needed for the guild card."""
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT p.name, gm.rank, gm.join_date FROM players p "
            "JOIN guild_members gm ON p.discord_id = gm.discord_id "
            "WHERE p.discord_id = ?",
            (discord_id,),
        )
        row = cur.fetchone()
        conn.close()
        return row