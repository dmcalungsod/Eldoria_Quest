import sys
import unittest
from unittest.mock import MagicMock

# Mock pymongo BEFORE importing DatabaseManager
sys.modules["pymongo"] = MagicMock()

from game_systems.achievement_system import AchievementSystem  # noqa: E402


class TestMonsterAchievements(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.achievement_system = AchievementSystem(self.mock_db)
        self.discord_id = 12345

    def test_check_group_achievements_goblin_bane(self):
        """Test that killing 100 Goblins awards Goblin-Bane."""
        # Setup mock return for get_specific_monster_kills
        # 60 Grunts + 40 Scouts = 100 Goblins
        self.mock_db.get_specific_monster_kills.return_value = {
            "Goblin Grunt": 60,
            "Goblin Scout": 40,
            "Wolf": 10,
        }

        # Setup add_title to return True (title newly added)
        self.mock_db.add_title.return_value = True

        # Run the check
        result = self.achievement_system.check_group_achievements(self.discord_id, "Goblin Grunt")

        # Verify calls
        self.mock_db.add_title.assert_any_call(self.discord_id, "Goblin-Chaser")
        self.mock_db.add_title.assert_any_call(self.discord_id, "Goblin-Bane")

        self.assertIn("Goblin-Bane", result)
        self.assertIn("Goblin-Chaser", result)

    def test_check_group_achievements_no_milestone(self):
        """Test that low kills do not award titles."""
        self.mock_db.get_specific_monster_kills.return_value = {"Goblin Grunt": 10}

        result = self.achievement_system.check_group_achievements(self.discord_id, "Goblin Grunt")

        self.mock_db.add_title.assert_not_called()
        self.assertIsNone(result)

    def test_check_group_achievements_multiple_groups(self):
        """Test a monster belonging to multiple groups (e.g. Abyssal Wolf -> Void & Wolf)."""
        # "Abyssal Wolf" matches "Wolf" and "Abyssal" (Void)

        self.mock_db.get_specific_monster_kills.return_value = {"Abyssal Wolf": 50}
        self.mock_db.add_title.return_value = True

        result = self.achievement_system.check_group_achievements(self.discord_id, "Abyssal Wolf")

        # Should trigger Wolf-Hunter (50 Wolves) and Void-Walker (50 Void)
        self.mock_db.add_title.assert_any_call(self.discord_id, "Wolf-Hunter")
        self.mock_db.add_title.assert_any_call(self.discord_id, "Void-Walker")

        self.assertIn("Wolf-Hunter", result)
        self.assertIn("Void-Walker", result)


if __name__ == "__main__":
    unittest.main()
