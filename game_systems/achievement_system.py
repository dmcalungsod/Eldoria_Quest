"""
Achievement System
------------------
Tracks player milestones and awards titles.
"""

import logging

from database.database_manager import DatabaseManager

logger = logging.getLogger("eldoria.achievements")

# Milestones: {Count: (Title, Description)}
KILL_MILESTONES = {
    50: ("Monster Hunter", "Slain 50 monsters."),
    200: ("Slayer", "Slain 200 monsters."),
    500: ("Exterminator", "Slain 500 monsters."),
}
ELITE_MILESTONES = {
    10: ("Elite Vanquisher", "Defeated 10 Elite monsters."),
    50: ("Elite Executioner", "Defeated 50 Elite monsters."),
}
BOSS_MILESTONES = {
    1: ("Boss Breaker", "Defeated a Boss."),
    5: ("Titan Toppler", "Defeated 5 Bosses."),
}
QUEST_MILESTONES = {
    10: ("Adventurer", "Completed 10 Quests."),
    50: ("Hero", "Completed 50 Quests."),
    100: ("Legend", "Completed 100 Quests."),
}

class AchievementSystem:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def check_kill_achievements(self, discord_id: int, kill_type: str) -> str | None:
        """
        Checks if the player has reached a kill milestone.
        Returns a success message if a new title is awarded, else None.
        """
        try:
            member_data = self.db.get_guild_member_data(discord_id)
            if not member_data:
                return None

            field_map = {
                "Normal": ("normal_kills", KILL_MILESTONES),
                "Elite": ("elite_kills", ELITE_MILESTONES),
                "Boss": ("boss_kills", BOSS_MILESTONES)
            }

            if kill_type not in field_map:
                return None

            field, milestones = field_map[kill_type]
            current_count = member_data.get(field, 0)

            # Check for milestones met exactly or passed (in case of jumps, though usually incremental)
            # But we only award if they don't have it.
            # However, "check all milestones <= current_count" is safer.

            newly_awarded = []

            for count, (title, desc) in milestones.items():
                if current_count >= count:
                    if self.db.add_title(discord_id, title):
                        newly_awarded.append(title)
                        logger.info(f"Awarded title '{title}' to {discord_id}")

            if newly_awarded:
                if len(newly_awarded) == 1:
                    return f"🏆 **Title Unlocked:** {newly_awarded[0]}"
                else:
                    return f"🏆 **Titles Unlocked:** {', '.join(newly_awarded)}"

            return None

        except Exception as e:
            logger.error(f"Error checking kill achievements for {discord_id}: {e}")
            return None

    def check_quest_achievements(self, discord_id: int) -> str | None:
        """
        Checks if the player has reached a quest milestone.
        Returns a success message if a new title is awarded, else None.
        """
        try:
            member_data = self.db.get_guild_member_data(discord_id)
            if not member_data:
                return None

            current_count = member_data.get("quests_completed", 0)

            newly_awarded = []

            for count, (title, desc) in QUEST_MILESTONES.items():
                if current_count >= count:
                    if self.db.add_title(discord_id, title):
                        newly_awarded.append(title)
                        logger.info(f"Awarded title '{title}' to {discord_id}")

            if newly_awarded:
                if len(newly_awarded) == 1:
                    return f"🏆 **Title Unlocked:** {newly_awarded[0]}"
                else:
                    return f"🏆 **Titles Unlocked:** {', '.join(newly_awarded)}"

            return None

        except Exception as e:
            logger.error(f"Error checking quest achievements for {discord_id}: {e}")
            return None
