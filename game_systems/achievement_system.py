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

MONSTER_GROUPS = {
    "Goblin": ["Goblin"],
    "Slime": ["Slime"],
    "Wolf": ["Wolf", "Hound"],
    "Spider": ["Spider"],
    "Treant": ["Treant", "Ent", "Sapling"],
    "Undead": ["Wisp", "Shade", "Duskling", "Revenant", "Wight", "Skeleton", "Zombie"],
    "Beast": ["Boar", "Stag", "Hare", "Tortoise", "Bear"],
    "Dragon": ["Drake", "Dragon"],
    "Construct": ["Golem", "Construct", "Gargoyle"],
    "Void": ["Void", "Abyssal", "Null", "Entropy"],
    "Aquatic": ["Coral", "Eel", "Siren", "Crawler", "Leviathan"],
}

GROUP_MILESTONES = {
    "Goblin": {
        50: ("Goblin-Chaser", "Slain 50 Goblins."),
        100: ("Goblin-Bane", "Slain 100 Goblins."),
    },
    "Slime": {
        50: ("Slime-Splatterer", "Slain 50 Slimes."),
    },
    "Wolf": {
        50: ("Wolf-Hunter", "Slain 50 Wolves."),
    },
    "Spider": {
        50: ("Arachnid-Slayer", "Slain 50 Spiders."),
    },
    "Treant": {
        50: ("Lumberjack", "Slain 50 Treants."),
    },
    "Undead": {
        50: ("Spirit-Walker", "Laid to rest 50 Undead."),
        100: ("Exorcist", "Laid to rest 100 Undead."),
    },
    "Beast": {
        50: ("Wild-Tamer", "Hunted 50 Beasts."),
    },
    "Dragon": {
        10: ("Scale-Breaker", "Slain 10 Dragons."),
        50: ("Dragon-Slayer", "Slain 50 Dragons."),
    },
    "Construct": {
        50: ("Stone-Breaker", "Destroyed 50 Constructs."),
    },
    "Void": {
        50: ("Void-Walker", "Banished 50 Void creatures."),
    },
    "Aquatic": {
        50: ("Tide-Turner", "Slain 50 Aquatic creatures."),
    },
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
                "Boss": ("boss_kills", BOSS_MILESTONES),
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

    def check_group_achievements(
        self, discord_id: int, monster_name: str
    ) -> str | None:
        """
        Checks if the player has reached a milestone for a monster group.
        Returns a success message if a new title is awarded, else None.
        """
        try:
            # 1. Identify groups
            relevant_groups = []
            for group, keywords in MONSTER_GROUPS.items():
                if any(k in monster_name for k in keywords):
                    relevant_groups.append(group)

            if not relevant_groups:
                return None

            # 2. Fetch kill data
            # get_specific_monster_kills returns a dict: {"Goblin Grunt": 5, "Wolf": 2, ...}
            kill_data = self.db.get_specific_monster_kills(discord_id)
            if not kill_data:
                return None

            newly_awarded = []

            for group in relevant_groups:
                milestones = GROUP_MILESTONES.get(group)
                if not milestones:
                    continue

                # Sum kills for this group
                keywords = MONSTER_GROUPS[group]
                total_kills = 0
                for m_name, count in kill_data.items():
                    # Check if this specific monster belongs to the group
                    if any(k in m_name for k in keywords):
                        total_kills += count

                # Check milestones
                for count, (title, desc) in milestones.items():
                    if total_kills >= count:
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
            logger.error(f"Error checking group achievements for {discord_id}: {e}")
            return None
