import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class TestSkillAchievements(unittest.TestCase):
    def setUp(self):
        # 1. Patch sys.modules dynamically
        self.patcher = patch.dict(sys.modules)
        self.patcher.start()

        # Mock dependencies
        self.mock_pymongo = MagicMock()
        sys.modules["pymongo"] = self.mock_pymongo
        sys.modules["pymongo.errors"] = MagicMock()
        sys.modules["discord"] = MagicMock()

        # Mock DatabaseManager
        self.mock_db_module = MagicMock()
        sys.modules["database.database_manager"] = self.mock_db_module
        self.mock_db_module.DatabaseManager = MagicMock()

        # Import System Under Test inside setUp to use patched modules
        import game_systems.achievement_system
        from game_systems.achievement_system import AchievementSystem

        self.AchievementSystem = AchievementSystem
        self.mock_db = MagicMock()
        self.ach_system = self.AchievementSystem(self.mock_db)

    def tearDown(self):
        self.patcher.stop()

    def test_skill_count_achievement_student(self):
        """Test awarding 'Student' for 2 skills."""
        # Setup: 2 skills
        self.mock_db.get_all_player_skills.return_value = [
            {"skill_key": "s1", "skill_level": 1},
            {"skill_key": "s2", "skill_level": 1}
        ]
        # Simulate add_title returning True (newly added)
        self.mock_db.add_title.side_effect = lambda uid, title: True

        msg = self.ach_system.check_skill_achievements(123)

        self.assertIsNotNone(msg)
        self.assertIn("Student", msg)
        self.mock_db.add_title.assert_any_call(123, "Student")

    def test_skill_count_achievement_scholar(self):
        """Test awarding 'Scholar' for 4 skills."""
        self.mock_db.get_all_player_skills.return_value = [
            {"skill_key": f"s{i}", "skill_level": 1} for i in range(4)
        ]
        self.mock_db.add_title.side_effect = lambda uid, title: True

        msg = self.ach_system.check_skill_achievements(123)

        self.assertIsNotNone(msg)
        self.assertIn("Scholar", msg)
        self.mock_db.add_title.assert_any_call(123, "Scholar")

    def test_skill_level_achievement_virtuoso(self):
        """Test awarding 'Virtuoso' for level 10 skill."""
        self.mock_db.get_all_player_skills.return_value = [
            {"skill_key": "s1", "skill_level": 10}
        ]
        self.mock_db.add_title.side_effect = lambda uid, title: True

        msg = self.ach_system.check_skill_achievements(123)

        self.assertIsNotNone(msg)
        self.assertIn("Expert", msg)   # Level 5 passed
        self.assertIn("Virtuoso", msg) # Level 10 passed
        self.mock_db.add_title.assert_any_call(123, "Expert")
        self.mock_db.add_title.assert_any_call(123, "Virtuoso")

    def test_no_new_achievement(self):
        """Test no message if titles already owned."""
        self.mock_db.get_all_player_skills.return_value = [
            {"skill_key": "s1", "skill_level": 1},
            {"skill_key": "s2", "skill_level": 1}
        ]
        # Simulate add_title returning False (already owned)
        self.mock_db.add_title.return_value = False

        msg = self.ach_system.check_skill_achievements(123)
        self.assertIsNone(msg)

    def test_mixed_achievements(self):
        """Test getting both count and level achievements at once."""
        # 4 skills, one of them level 5
        skills = [
            {"skill_key": "s1", "skill_level": 5},
            {"skill_key": "s2", "skill_level": 1},
            {"skill_key": "s3", "skill_level": 1},
            {"skill_key": "s4", "skill_level": 1},
        ]
        self.mock_db.get_all_player_skills.return_value = skills
        self.mock_db.add_title.side_effect = lambda uid, title: True

        msg = self.ach_system.check_skill_achievements(123)

        self.assertIsNotNone(msg)
        self.assertIn("Student", msg)
        self.assertIn("Scholar", msg)
        self.assertIn("Expert", msg)

if __name__ == "__main__":
    unittest.main()
