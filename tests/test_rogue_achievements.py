import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the project root to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game_systems.player.achievement_system import AchievementSystem, ROGUE_ASSASSIN_SKILLS, ROGUE_PHANTOM_SKILLS

class TestRogueAchievements(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.achievements = AchievementSystem(self.mock_db)
        self.discord_id = 123456789

    # --- Class Mastery Tests ---

    def test_check_class_mastery_assassin_success(self):
        """Test awarding the 'Assassin' title when all skills are present."""
        # Mock player skills to include all Assassin skills
        skills = [{"skill_key": s} for s in ROGUE_ASSASSIN_SKILLS]
        self.mock_db.get_all_player_skills.return_value = skills
        self.mock_db.add_title.return_value = True  # Title awarded

        msg = self.achievements.check_class_mastery_achievements(self.discord_id, 3)

        self.assertIsNotNone(msg)
        self.assertIn("Assassin", msg)
        self.mock_db.add_title.assert_called_with(self.discord_id, "Assassin")

    def test_check_class_mastery_phantom_success(self):
        """Test awarding the 'Phantom' title when all skills are present."""
        skills = [{"skill_key": s} for s in ROGUE_PHANTOM_SKILLS]
        self.mock_db.get_all_player_skills.return_value = skills
        self.mock_db.add_title.return_value = True

        msg = self.achievements.check_class_mastery_achievements(self.discord_id, 3)

        self.assertIsNotNone(msg)
        self.assertIn("Phantom", msg)
        self.mock_db.add_title.assert_called_with(self.discord_id, "Phantom")

    def test_check_class_mastery_incomplete(self):
        """Test no title awarded if skills are missing."""
        # Missing one skill
        if len(ROGUE_ASSASSIN_SKILLS) > 1:
            incomplete_skills = list(ROGUE_ASSASSIN_SKILLS)[:-1]
            skills = [{"skill_key": s} for s in incomplete_skills]
            self.mock_db.get_all_player_skills.return_value = skills

            msg = self.achievements.check_class_mastery_achievements(self.discord_id, 3)

            self.assertIsNone(msg)
            self.mock_db.add_title.assert_not_called()

    def test_check_class_mastery_wrong_class(self):
        """Test no title awarded if class ID is not Rogue (3)."""
        skills = [{"skill_key": s} for s in ROGUE_ASSASSIN_SKILLS]
        self.mock_db.get_all_player_skills.return_value = skills

        msg = self.achievements.check_class_mastery_achievements(self.discord_id, 1) # Warrior

        self.assertIsNone(msg)
        self.mock_db.add_title.assert_not_called()

    # --- Combat Feat Tests ---

    def test_check_combat_feats_unseen_death_success(self):
        """Test awarding 'Unseen Death' for 0 damage as Rogue."""
        combat_data = {"damage_taken": 0, "class_id": 3}
        self.mock_db.add_title.return_value = True

        msg = self.achievements.check_combat_feats(self.discord_id, combat_data)

        self.assertIsNotNone(msg)
        self.assertIn("Unseen Death", msg)
        self.mock_db.add_title.assert_called_with(self.discord_id, "Unseen Death")

    def test_check_combat_feats_damage_taken(self):
        """Test no award if damage taken > 0."""
        combat_data = {"damage_taken": 10, "class_id": 3}

        msg = self.achievements.check_combat_feats(self.discord_id, combat_data)

        self.assertIsNone(msg)
        self.mock_db.add_title.assert_not_called()

    def test_check_combat_feats_wrong_class(self):
        """Test no award if class is not Rogue (even with 0 damage)."""
        combat_data = {"damage_taken": 0, "class_id": 1} # Warrior

        msg = self.achievements.check_combat_feats(self.discord_id, combat_data)

        self.assertIsNone(msg)
        self.mock_db.add_title.assert_not_called()

if __name__ == "__main__":
    unittest.main()
