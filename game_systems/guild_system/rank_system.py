"""
rank_system.py

Handles adventurer rank promotions based on the detailed requirements
from the Guild Rank System documentation.
"""

from database.database_manager import DatabaseManager
from typing import Dict, Optional, Tuple

class RankSystem:
    """
    Manages the adventurer ranking system based on quests, kills, and other achievements.
    """
    
    RANKS = {
        "F": {
            "title": "Initiate",
            "next_rank": "E",
            "requirements": {"quests_completed": 5, "normal_kills": 10}
        },
        "E": {
            "title": "Novice",
            "next_rank": "D",
            "requirements": {"quests_completed": 20, "elite_kills": 1}
        },
        "D": {
            "title": "Apprentice",
            "next_rank": "C",
            "requirements": {"quests_completed": 40, "elite_kills": 3, "boss_kills": 0} # Boss survival is not tracked yet
        },
        "C": {
            "title": "Adept",
            "next_rank": "B",
            "requirements": {"quests_completed": 80, "boss_kills": 1}
        },
        "B": {
            "title": "Veteran",
            "next_rank": "A",
            "requirements": {"quests_completed": 150, "boss_kills": 5}
        },
        "A": {
            "title": "Master Adventurer",
            "next_rank": "S",
            "requirements": {"quests_completed": 300, "boss_kills": 10}
        },
        "S": {"title": "Elite", "next_rank": "SS", "requirements": {}}, # Further ranks require manual implementation
        "SS": {"title": "Paragon", "next_rank": "SSS", "requirements": {}},
        "SSS": {"title": "Mythic", "next_rank": None, "requirements": {}}
    }

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_rank_info(self, discord_id: int) -> Optional[Dict]:
        """
        Retrieves a player's full progression data from the guild_members table.
        """
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM guild_members WHERE discord_id = ?", (discord_id,))
        data = cur.fetchone()
        conn.close()
        
        if data:
            return dict(data)
        return None

    def check_promotion_eligibility(self, discord_id: int) -> bool:
        """
        Checks if a player has met the detailed requirements for the next rank.
        """
        player_data = self.get_rank_info(discord_id)
        if not player_data:
            return False

        current_rank = player_data['rank']
        next_rank_key = self.RANKS.get(current_rank, {}).get("next_rank")
        
        if not next_rank_key:
            return False  # Already at max rank or rank not in simple progression

        requirements = self.RANKS[current_rank].get("requirements", {})
        
        for req, value in requirements.items():
            if player_data.get(req, 0) < value:
                return False
        
        return True

    def promote_player(self, discord_id: int) -> Tuple[bool, str]:
        """
        Promotes a player to the next rank if they are eligible.
        Returns a tuple of (success, message).
        """
        if not self.check_promotion_eligibility(discord_id):
            return False, "You have not yet met the requirements for a promotion."

        player_data = self.get_rank_info(discord_id)
        current_rank = player_data['rank']
        next_rank_key = self.RANKS[current_rank]["next_rank"]

        if not next_rank_key:
            return False, "You have already reached the highest rank in the simple progression."

        try:
            conn = self.db.connect()
            cur = conn.cursor()
            cur.execute("UPDATE guild_members SET rank = ? WHERE discord_id = ?", (next_rank_key, discord_id))
            conn.commit()
            conn.close()
            
            next_rank_title = self.RANKS[next_rank_key]['title']
            return True, f"Congratulations! You have been promoted to Rank {next_rank_key} – {next_rank_title}."
        except Exception as e:
            print(f"Error during rank promotion: {e}")
            return False, "An error occurred while processing your promotion."
