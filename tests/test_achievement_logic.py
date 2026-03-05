import os
import sys
import unittest
from unittest.mock import MagicMock

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.player.achievement_system import AchievementSystem  # noqa: E402


class TestAchievementLogic(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.achievements = AchievementSystem(self.mock_db)

    def test_check_kill_achievements_normal_success(self):
        discord_id = 123
        kill_type = "Normal"

        # Mock guild stats: 50 kills (matches 50 milestone)
        self.mock_db.get_guild_member_data.return_value = {"normal_kills": 50}

        # Mock add_title to return True only for "Monster Hunter"
        def side_effect(did, title):
            return title == "Monster Hunter"

        self.mock_db.add_title.side_effect = side_effect

        msg = self.achievements.check_kill_achievements(discord_id, kill_type)

        self.mock_db.add_title.assert_any_call(discord_id, "Monster Hunter")
        self.assertIn("**Title Unlocked:** Monster Hunter", msg)

    def test_check_kill_achievements_already_have(self):
        discord_id = 123
        kill_type = "Normal"

        # Mock guild stats: 50 kills
        self.mock_db.get_guild_member_data.return_value = {"normal_kills": 50}

        # Mock add_title returns False (already have)
        self.mock_db.add_title.return_value = False

        msg = self.achievements.check_kill_achievements(discord_id, kill_type)

        self.assertIsNone(msg)

    def test_check_quest_achievements_success(self):
        discord_id = 123

        # Mock guild stats: 10 quests
        self.mock_db.get_guild_member_data.return_value = {"quests_completed": 10}

        # Mock add_title returns True
        self.mock_db.add_title.return_value = True

        msg = self.achievements.check_quest_achievements(discord_id)

        self.mock_db.add_title.assert_any_call(discord_id, "Adventurer")
        self.assertIn("**Title Unlocked:** Adventurer", msg)

    def test_check_combat_achievements_rogue_no_damage(self):
        discord_id = 123
        class_name = "Rogue"
        damage_taken = 0

        self.mock_db.add_title.return_value = True

        msg = self.achievements.check_combat_achievements(
            discord_id, class_name, damage_taken
        )

        self.mock_db.add_title.assert_any_call(discord_id, "Without a Trace")
        self.mock_db.add_title.assert_any_call(discord_id, "Untouchable")
        self.assertIn("Without a Trace", msg)
        self.assertIn("Untouchable", msg)

    def test_check_combat_achievements_wrong_class(self):
        discord_id = 123
        class_name = "Warrior"
        damage_taken = 0

        self.mock_db.add_title.return_value = True

        msg = self.achievements.check_combat_achievements(
            discord_id, class_name, damage_taken
        )

        self.mock_db.add_title.assert_called_once_with(discord_id, "Untouchable")
        self.assertIn("**Title Unlocked:** Untouchable", msg)
        self.assertNotIn("Without a Trace", msg)

    def test_check_combat_achievements_took_damage(self):
        discord_id = 123
        class_name = "Rogue"
        damage_taken = 5

        self.mock_db.add_title.return_value = True

        msg = self.achievements.check_combat_achievements(
            discord_id, class_name, damage_taken
        )

        self.mock_db.add_title.assert_not_called()
        self.assertIsNone(msg)

    def test_check_auto_adventure_achievements_success(self):
        discord_id = 123
        self.mock_db.get_exploration_stats.return_value = {"total_adventure_minutes": 5500}
        self.mock_db.add_title.return_value = True

        msg = self.achievements.check_auto_adventure_achievements(discord_id)

        self.mock_db.add_title.assert_any_call(discord_id, "Wanderer")
        self.mock_db.add_title.assert_any_call(discord_id, "Explorer")
        self.assertIn("Wanderer", msg)
        self.assertIn("Explorer", msg)
        self.assertNotIn("Vagabond", msg)


if __name__ == "__main__":
    unittest.main()
