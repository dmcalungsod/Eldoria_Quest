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

EXPLORATION_MILESTONES = {
    10: ("Pathfinder", "Survived 10 Expeditions."),
    50: ("Trailblazer", "Survived 50 Expeditions."),
    100: ("Voyager", "Survived 100 Expeditions."),
}

LOCATION_MILESTONES = {
    5: ("Scout", "Discovered 5 unique locations."),
    10: ("Cartographer", "Discovered 10 unique locations."),
    12: ("World-Walker", "Discovered all known locations."),
}

SKILL_COUNT_MILESTONES = {
    2: ("Student", "Learned 2 skills."),
    4: ("Scholar", "Learned 4 skills."),
    6: ("Polymath", "Learned 6 skills."),
}

SKILL_LEVEL_MILESTONES = {
    5: ("Expert", "Reached skill level 5."),
    10: ("Virtuoso", "Reached skill level 10."),
    20: ("Paragon", "Reached skill level 20."),
}

DURATION_MILESTONES = {
    60: ("Day Tripper", "Completed an adventure lasting at least 1 hour."),
    240: ("Endurance Runner", "Completed an adventure lasting at least 4 hours."),
    480: ("Marathoner", "Completed an adventure lasting at least 8 hours."),
}

CRAFTING_MILESTONES = {
    5: ("Apprentice Smith", "Reached Crafting Level 5."),
    10: ("Journeyman Crafter", "Reached Crafting Level 10."),
    20: ("Master Artisan", "Reached Crafting Level 20."),
    50: ("Grandmaster of the Forge", "Reached Crafting Level 50."),
}

# --- Rogue Expansion Skill Sets ---
# Using existing Rogue skills from skills_data.py
# Assassin: DPS focused (Double Strike, Toxic Blade)
ROGUE_ASSASSIN_SKILLS = {"double_strike", "toxic_blade"}
# Phantom: Stealth focused (Stealth) - Limited existing skills, but fits the theme
ROGUE_PHANTOM_SKILLS = {"stealth"}


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

    def check_group_achievements(self, discord_id: int, monster_name: str) -> str | None:
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

    def check_exploration_achievements(self, discord_id: int) -> str | None:
        """
        Checks if the player has reached exploration or location milestones.
        Returns a success message if a new title is awarded, else None.
        """
        try:
            stats = self.db.get_exploration_stats(discord_id)
            unique_locations = stats.get("unique_locations", [])
            total_expeditions = stats.get("total_expeditions", 0)

            newly_awarded = []

            # Check Expedition Counts
            for count, (title, desc) in EXPLORATION_MILESTONES.items():
                if total_expeditions >= count:
                    if self.db.add_title(discord_id, title):
                        newly_awarded.append(title)
                        logger.info(f"Awarded title '{title}' to {discord_id}")

            # Check Unique Locations
            loc_count = len(unique_locations)
            for count, (title, desc) in LOCATION_MILESTONES.items():
                if loc_count >= count:
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
            logger.error(f"Error checking exploration achievements for {discord_id}: {e}")
            return None

    def check_skill_achievements(self, discord_id: int) -> str | None:
        """
        Checks if the player has reached skill milestones (count or max level).
        Returns a success message if a new title is awarded, else None.
        """
        try:
            skills = self.db.get_all_player_skills(discord_id)
            if not skills:
                return None

            skill_count = len(skills)
            max_skill_level = max(s["skill_level"] for s in skills) if skills else 0

            newly_awarded = []

            # Check Skill Count Milestones
            for count, (title, desc) in SKILL_COUNT_MILESTONES.items():
                if skill_count >= count:
                    if self.db.add_title(discord_id, title):
                        newly_awarded.append(title)
                        logger.info(f"Awarded title '{title}' to {discord_id}")

            # Check Skill Level Milestones
            for level, (title, desc) in SKILL_LEVEL_MILESTONES.items():
                if max_skill_level >= level:
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
            logger.error(f"Error checking skill achievements for {discord_id}: {e}")
            return None

    def check_duration_achievements(self, discord_id: int, duration_minutes: int) -> str | None:
        """
        Checks if the player has reached an adventure duration milestone.
        Returns a success message if a new title is awarded, else None.
        """
        try:
            newly_awarded = []

            for minutes, (title, desc) in DURATION_MILESTONES.items():
                if duration_minutes >= minutes:
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
            logger.error(f"Error checking duration achievements for {discord_id}: {e}")
            return None

    def check_crafting_achievements(self, discord_id: int) -> str | None:
        """
        Checks if the player has reached a crafting level milestone.
        Returns a success message if a new title is awarded, else None.
        """
        try:
            player = self.db.get_player(discord_id)
            if not player:
                return None

            crafting_level = player.get("crafting_level", 1)
            newly_awarded = []

            for level, (title, desc) in CRAFTING_MILESTONES.items():
                if crafting_level >= level:
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
            logger.error(f"Error checking crafting achievements for {discord_id}: {e}")
            return None

    def check_class_mastery_achievements(self, discord_id: int, class_id: int) -> str | None:
        """
        Checks for class-specific mastery titles (e.g. Rogue paths).
        Returns a success message if a new title is awarded, else None.
        """
        try:
            # Only check Rogue (Class ID 3) for now
            if class_id != 3:
                return None

            skills = self.db.get_all_player_skills(discord_id)
            if not skills:
                return None

            known_skill_keys = {s["skill_key"] for s in skills}
            newly_awarded = []

            # Check Assassin Path
            if ROGUE_ASSASSIN_SKILLS.issubset(known_skill_keys):
                if self.db.add_title(discord_id, "Assassin"):
                    newly_awarded.append("Assassin")
                    logger.info(f"Awarded title 'Assassin' to {discord_id}")

            # Check Phantom Path
            if ROGUE_PHANTOM_SKILLS.issubset(known_skill_keys):
                if self.db.add_title(discord_id, "Phantom"):
                    newly_awarded.append("Phantom")
                    logger.info(f"Awarded title 'Phantom' to {discord_id}")

            if newly_awarded:
                if len(newly_awarded) == 1:
                    return f"🏆 **Title Unlocked:** {newly_awarded[0]}"
                else:
                    return f"🏆 **Titles Unlocked:** {', '.join(newly_awarded)}"

            return None

        except Exception as e:
            logger.error(f"Error checking class mastery achievements for {discord_id}: {e}")
            return None

    def check_combat_feats(self, discord_id: int, combat_data: dict) -> str | None:
        """
        Checks for combat-specific feats (e.g. No Damage).
        combat_data: {"damage_taken": int, "class_id": int}
        """
        try:
            damage_taken = combat_data.get("damage_taken", -1)
            class_id = combat_data.get("class_id")

            newly_awarded = []

            # "Unseen Death" - Rogue wins without taking damage
            if class_id == 3 and damage_taken == 0:
                if self.db.add_title(discord_id, "Unseen Death"):
                    newly_awarded.append("Unseen Death")
                    logger.info(f"Awarded title 'Unseen Death' to {discord_id}")

            if newly_awarded:
                if len(newly_awarded) == 1:
                    return f"🏆 **Achievement Unlocked:** {newly_awarded[0]}"
                else:
                    return f"🏆 **Achievements Unlocked:** {', '.join(newly_awarded)}"

            return None

        except Exception as e:
            logger.error(f"Error checking combat feats for {discord_id}: {e}")
            return None
