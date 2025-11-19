"""
rank_system.py

Manages Guild Rank progression.
"""

from typing import Dict, Optional, Tuple
from database.database_manager import DatabaseManager

class RankSystem:
    # Static Configuration
    RANKS = {
        "F": {"title": "Initiate", "next_rank": "E", "requirements": {"quests_completed": 5, "normal_kills": 10}},
        "E": {"title": "Novice", "next_rank": "D", "requirements": {"quests_completed": 20, "elite_kills": 1}},
        "D": {"title": "Apprentice", "next_rank": "C", "requirements": {"quests_completed": 40, "elite_kills": 3, "boss_kills": 0}},
        "C": {"title": "Adept", "next_rank": "B", "requirements": {"quests_completed": 80, "boss_kills": 1}},
        "B": {"title": "Veteran", "next_rank": "A", "requirements": {"quests_completed": 150, "boss_kills": 5}},
        "A": {"title": "Master", "next_rank": "S", "requirements": {"quests_completed": 300, "boss_kills": 10}},
        "S": {"title": "Elite", "next_rank": "SS", "requirements": {}},
        "SS": {"title": "Paragon", "next_rank": "SSS", "requirements": {}},
        "SSS": {"title": "Mythic", "next_rank": None, "requirements": {}},
    }

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_rank_info(self, discord_id: int) -> Optional[Dict]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM guild_members WHERE discord_id = ?", (discord_id,)).fetchone()
            return dict(row) if row else None

    def check_promotion_eligibility(self, discord_id: int) -> bool:
        player_data = self.get_rank_info(discord_id)
        if not player_data: return False

        current_rank = player_data["rank"]
        rank_data = self.RANKS.get(current_rank)
        
        if not rank_data or not rank_data["next_rank"]:
            return False 

        reqs = rank_data["requirements"]
        for col, target in reqs.items():
            if player_data.get(col, 0) < target:
                return False
        
        return True

    def get_next_rank(self, current_rank: str) -> Optional[str]:
        return self.RANKS.get(current_rank, {}).get("next_rank")

    def finalize_promotion(self, discord_id: int, new_rank: str) -> Tuple[bool, str]:
        """
        Applies rank up.
        """
        try:
            with self.db.get_connection() as conn:
                conn.execute("UPDATE guild_members SET rank = ? WHERE discord_id = ?", (new_rank, discord_id))
            
            title = self.RANKS.get(new_rank, {}).get("title", "Adventurer")
            return True, f"Promoted to Rank {new_rank} — {title}."
        except Exception as e:
            return False, "Promotion update failed."