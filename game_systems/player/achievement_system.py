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

AUTO_ADVENTURE_MILESTONES = {
    1000: ("Wanderer", "Spent 1000 total minutes in auto-adventures."),
    5000: ("Explorer", "Spent 5000 total minutes in auto-adventures."),
    10000: ("Vagabond", "Spent 10000 total minutes in auto-adventures."),
}

CRAFTING_MILESTONES = {
    5: ("Apprentice Smith", "Reached Crafting Level 5."),
    10: ("Journeyman Crafter", "Reached Crafting Level 10."),
    20: ("Master Artisan", "Reached Crafting Level 20."),
    50: ("Grandmaster of the Forge", "Reached Crafting Level 50."),
}

CLASS_MASTERY_MILESTONES = {
    "Nightblade": {"double_strike", "toxic_blade", "venomous_strike", "death_blossom"},
    "Ghost-Walker": {"stealth", "shadow_step", "flash_powder"},
    "Assassin": {"double_strike", "toxic_blade", "venomous_strike", "death_blossom"},
    "Phantom": {"stealth", "shadow_step", "flash_powder"},
}


class AchievementSystem:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_title_message(newly_awarded: list) -> str | None:
        """Formats a 🏆 message for one or more newly awarded titles, or None."""
        if not newly_awarded:
            return None
        if len(newly_awarded) == 1:
            return f"🏆 **Title Unlocked:** {newly_awarded[0]}"
        return f"🏆 **Titles Unlocked:** {', '.join(newly_awarded)}"

    def _check_milestones(
        self, discord_id: int, milestones: dict, current_count: int
    ) -> list:
        """
        Awards any milestone titles that the player has reached but not yet earned.
        Returns a list of newly awarded title names.
        """
        newly_awarded = []
        # Safe fallback for mocked current_count during tests
        try:
            count_val = int(current_count)
        except (TypeError, ValueError):
            count_val = 0

        for threshold, (title, _desc) in milestones.items():
            if count_val >= threshold and self.db.add_title(discord_id, title):
                newly_awarded.append(title)
                logger.info(f"Awarded title '{title}' to {discord_id}")
        return newly_awarded

    # ------------------------------------------------------------------
    # Public check methods
    # ------------------------------------------------------------------

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
            newly_awarded = self._check_milestones(
                discord_id, milestones, current_count
            )
            return self._format_title_message(newly_awarded)

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
            newly_awarded = self._check_milestones(
                discord_id, QUEST_MILESTONES, current_count
            )
            return self._format_title_message(newly_awarded)

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
            relevant_groups = [
                group
                for group, keywords in MONSTER_GROUPS.items()
                if any(k in monster_name for k in keywords)
            ]
            if not relevant_groups:
                return None

            kill_data = self.db.get_specific_monster_kills(discord_id)
            if not kill_data:
                return None

            newly_awarded = []
            for group in relevant_groups:
                milestones = GROUP_MILESTONES.get(group)
                if not milestones:
                    continue

                keywords = MONSTER_GROUPS[group]
                total_kills = sum(
                    count
                    for m_name, count in kill_data.items()
                    if any(k in m_name for k in keywords)
                )
                newly_awarded.extend(
                    self._check_milestones(discord_id, milestones, total_kills)
                )

            return self._format_title_message(newly_awarded)

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
            total_expeditions = stats.get("total_expeditions", 0)
            loc_count = len(stats.get("unique_locations", []))

            newly_awarded = self._check_milestones(
                discord_id, EXPLORATION_MILESTONES, total_expeditions
            )
            newly_awarded += self._check_milestones(
                discord_id, LOCATION_MILESTONES, loc_count
            )
            return self._format_title_message(newly_awarded)

        except Exception as e:
            logger.error(
                f"Error checking exploration achievements for {discord_id}: {e}"
            )
            return None

    def check_skill_achievements(self, discord_id: int) -> str | None:
        """
        Checks if the player has reached skill milestones (count or max level) or class mastery.
        Returns a success message if a new title is awarded, else None.
        """
        try:
            skills = self.db.get_all_player_skills(discord_id)
            if not skills:
                return None

            skill_count = len(skills)
            max_skill_level = max(s["skill_level"] for s in skills)

            newly_awarded = self._check_milestones(
                discord_id, SKILL_COUNT_MILESTONES, skill_count
            )
            newly_awarded += self._check_milestones(
                discord_id, SKILL_LEVEL_MILESTONES, max_skill_level
            )

            player_skill_keys = {s.get("skill_key") for s in skills}
            for title, required_skills in CLASS_MASTERY_MILESTONES.items():
                if required_skills.issubset(player_skill_keys):
                    if self.db.add_title(discord_id, title):
                        newly_awarded.append(title)
                        logger.info(f"Awarded title '{title}' to {discord_id}")

            return self._format_title_message(newly_awarded)

        except Exception as e:
            logger.error(f"Error checking skill achievements for {discord_id}: {e}")
            return None

    def check_duration_achievements(
        self, discord_id: int, duration_minutes: int
    ) -> str | None:
        """
        Checks if the player has reached an adventure duration milestone.
        Returns a success message if a new title is awarded, else None.
        """
        try:
            newly_awarded = self._check_milestones(
                discord_id, DURATION_MILESTONES, duration_minutes
            )
            return self._format_title_message(newly_awarded)

        except Exception as e:
            logger.error(f"Error checking duration achievements for {discord_id}: {e}")
            return None

    def check_auto_adventure_achievements(self, discord_id: int) -> str | None:
        """
        Checks if the player has reached a total auto-adventure duration milestone.
        Returns a success message if a new title is awarded, else None.
        """
        try:
            stats = self.db.get_exploration_stats(discord_id)
            total_minutes = stats.get("total_adventure_minutes", 0)

            newly_awarded = self._check_milestones(
                discord_id, AUTO_ADVENTURE_MILESTONES, total_minutes
            )
            return self._format_title_message(newly_awarded)

        except Exception as e:
            logger.error(f"Error checking auto-adventure achievements for {discord_id}: {e}")
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
            newly_awarded = self._check_milestones(
                discord_id, CRAFTING_MILESTONES, crafting_level
            )
            return self._format_title_message(newly_awarded)

        except Exception as e:
            logger.error(f"Error checking crafting achievements for {discord_id}: {e}")
            return None

    def check_combat_achievements(
        self, discord_id: int, class_name: str, damage_taken: int
    ) -> str | None:
        """
        Checks for combat-specific achievements like 'Without a Trace' and 'Untouchable'.
        Returns a success message if a new title is awarded, else None.
        """
        try:
            newly_awarded = []

            # "Untouchable" - Win a battle without taking damage (any class)
            if damage_taken <= 0:
                if self.db.add_title(discord_id, "Untouchable"):
                    newly_awarded.append("Untouchable")
                    logger.info(f"Awarded title 'Untouchable' to {discord_id}")

            # "Without a Trace" - Win a battle without taking damage as a Rogue
            if class_name == "Rogue" and damage_taken <= 0:
                if self.db.add_title(discord_id, "Without a Trace"):
                    newly_awarded.append("Without a Trace")
                    logger.info(f"Awarded title 'Without a Trace' to {discord_id}")

            return self._format_title_message(newly_awarded)
        except Exception as e:
            logger.error(f"Error checking combat achievements for {discord_id}: {e}")
            return None
