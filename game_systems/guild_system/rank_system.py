"""
rank_system.py

Handles adventurer rank progression and promotions based on the formal
Guild Rank System requirements.
"""

from database.database_manager import DatabaseManager
from typing import Dict, Optional, Tuple


class RankSystem:
    """
    Manages the guild's adventurer ranking system, including requirement
    checks, eligibility validation, and promotion processing.
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
            "requirements": {"quests_completed": 40, "elite_kills": 3, "boss_kills": 0}
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
        "S":  {"title": "Elite",   "next_rank": "SS",  "requirements": {}},
        "SS": {"title": "Paragon", "next_rank": "SSS", "requirements": {}},
        "SSS": {"title": "Mythic", "next_rank": None,  "requirements": {}}
    }

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    # -----------------------------------------------------
    # Data Retrieval
    # -----------------------------------------------------

    def get_rank_info(self, discord_id: int) -> Optional[Dict]:
        """Fetches a player's rank and progression statistics."""
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM guild_members WHERE discord_id = ?", (discord_id,))
        data = cur.fetchone()
        conn.close()

        return dict(data) if data else None

    # -----------------------------------------------------
    # Rank Eligibility Logic
    # -----------------------------------------------------

    def check_promotion_eligibility(self, discord_id: int) -> bool:
        """Returns True if the player meets the requirements for their next rank."""
        player_data = self.get_rank_info(discord_id)
        if not player_data:
            return False

        current_rank = player_data["rank"]
        next_rank_key = self.RANKS.get(current_rank, {}).get("next_rank")
        if not next_rank_key:
            return False  # Already at max rank

        required_stats = self.RANKS[current_rank].get("requirements", {})

        for req_name, req_value in required_stats.items():
            if player_data.get(req_name, 0) < req_value:
                return False

        return True

    def get_next_rank(self, current_rank: str) -> Optional[str]:
        """Returns the key for the next rank, if any."""
        return self.RANKS.get(current_rank, {}).get("next_rank")

    # -----------------------------------------------------
    # Promotion Handling
    # -----------------------------------------------------

    def promote_player(self, discord_id: int) -> Tuple[bool, str]:
        """
        Legacy/utility function.
        Standard rank-ups are now done via Guild Trial boss battles.
        """
        if not self.check_promotion_eligibility(discord_id):
            return False, "You have not yet met the requirements for a promotion."

        return (
            False,
            "Promotion requires completing a Guild Trial. Open 'Check Rank' to begin the trial."
        )

    def finalize_promotion(self, discord_id: int, new_rank: str) -> Tuple[bool, str]:
        """
        Applies a new rank after the player successfully completes their Promotion Trial.
        Called exclusively by the reward system after a Promotion Boss is defeated.
        """
        try:
            conn = self.db.connect()
            cur = conn.cursor()
            cur.execute(
                "UPDATE guild_members SET rank = ? WHERE discord_id = ?",
                (new_rank, discord_id),
            )
            conn.commit()
            conn.close()

            rank_title = self.RANKS.get(new_rank, {}).get("title", "Unknown")
            return True, f"Congratulations! You have been promoted to Rank {new_rank} — {rank_title}."

        except Exception as e:
            print(f"[RankSystem] Error during rank promotion: {e}")
            return False, "An unexpected error occurred while processing your promotion."
