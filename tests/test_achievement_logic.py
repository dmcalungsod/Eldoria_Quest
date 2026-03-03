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


if __name__ == "__main__":
    unittest.main()
