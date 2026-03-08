"""
rank_system.py

Manages Guild Rank progression.
"""

from database.database_manager import DatabaseManager


class RankSystem:
    # Static Configuration
    RANKS = {
        "F": {
            "title": "Initiate",
            "next_rank": "E",
            "requirements": {
                "quests_completed": 3,
                "normal_kills": 50,
                "total_expeditions": 2,
                "total_adventure_minutes": 60,
            },
        },
        "E": {
            "title": "Novice",
            "next_rank": "D",
            "requirements": {
                "quests_completed": 10,
                "normal_kills": 150,
                "elite_kills": 5,
                "total_expeditions": 5,
                "total_adventure_minutes": 300,
            },
        },
        "D": {
            "title": "Apprentice",
            "next_rank": "C",
            "requirements": {
                "quests_completed": 20,
                "normal_kills": 300,
                "elite_kills": 20,
                "boss_kills": 1,
                "total_expeditions": 10,
                "total_adventure_minutes": 600,
            },
        },
        "C": {
            "title": "Adept",
            "next_rank": "B",
            "requirements": {
                "quests_completed": 30,
                "normal_kills": 450,
                "elite_kills": 40,
                "boss_kills": 2,
                "total_expeditions": 15,
                "total_adventure_minutes": 1200,
            },
        },
        "B": {
            "title": "Veteran",
            "next_rank": "A",
            "requirements": {
                "quests_completed": 40,
                "normal_kills": 600,
                "boss_kills": 4,
                "elite_kills": 65,
                "total_expeditions": 20,
                "total_adventure_minutes": 2400,
            },
        },
        "A": {
            "title": "Master",
            "next_rank": "S",
            "requirements": {
                "quests_completed": 50,
                "normal_kills": 800,
                "boss_kills": 6,
                "elite_kills": 95,
                "total_expeditions": 30,
                "total_adventure_minutes": 4800,
            },
        },
        "S": {
            "title": "Elite",
            "next_rank": "SS",
            "requirements": {
                "quests_completed": 60,
                "normal_kills": 1000,
                "boss_kills": 10,
                "elite_kills": 135,
                "total_expeditions": 40,
                "total_adventure_minutes": 9600,
            },
        },
        "SS": {
            "title": "Paragon",
            "next_rank": "SSS",
            "requirements": {
                "quests_completed": 65,
                "normal_kills": 1500,
                "boss_kills": 20,
                "elite_kills": 185,
                "total_expeditions": 50,
                "total_adventure_minutes": 19200,
            },
        },
        "SSS": {"title": "Mythic", "next_rank": None, "requirements": {}},
    }

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_rank_info(self, discord_id: int) -> dict | None:
        row = self.db.get_guild_member(discord_id)
        if not row:
            return None

        player_data = dict(row)
        exploration = self.db.get_exploration_stats(discord_id) or {}
        player_data["total_expeditions"] = exploration.get("total_expeditions", 0)
        player_data["total_adventure_minutes"] = exploration.get(
            "total_adventure_minutes", 0
        )

        return player_data

    def check_promotion_eligibility(self, discord_id: int) -> bool:
        player_data = self.get_rank_info(discord_id)
        if not player_data:
            return False

        current_rank = player_data["rank"]
        rank_data = self.RANKS.get(current_rank)

        if not rank_data or not rank_data["next_rank"]:
            return False

        reqs = rank_data["requirements"]
        for col, target in reqs.items():
            if player_data.get(col, 0) < target:
                return False

        return True

    def get_next_rank(self, current_rank: str) -> str | None:
        return self.RANKS.get(current_rank, {}).get("next_rank")

    def finalize_promotion(self, discord_id: int, new_rank: str) -> tuple[bool, str]:
        """Applies rank up."""
        try:
            self.db.update_guild_member_rank(discord_id, new_rank)
            title = self.RANKS.get(new_rank, {}).get("title", "Adventurer")
            return True, f"Promoted to Rank {new_rank} — {title}."
        except Exception:
            return False, "Promotion update failed."
