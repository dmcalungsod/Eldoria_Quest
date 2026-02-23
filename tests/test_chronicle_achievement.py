"""
test_chronicle_achievement.py

Tests for Crafting Achievements.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from game_systems.achievement_system import AchievementSystem  # noqa: E402
from game_systems.crafting.crafting_system import CraftingSystem  # noqa: E402
from database.database_manager import DatabaseManager  # noqa: E402

class TestCraftingAchievements(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock(spec=DatabaseManager)
        self.achievement_system = AchievementSystem(self.db)
        self.crafting = CraftingSystem(self.db)
        # Inject the real achievement system into the crafting system mock
        self.crafting.achievement_system = self.achievement_system
        self.discord_id = 12345

    def test_check_crafting_achievements_award(self):
        # Setup: Player reached level 5
        self.db.get_player.return_value = {"crafting_level": 5}
        self.db.add_title.return_value = True # Title successfully added

        msg = self.achievement_system.check_crafting_achievements(self.discord_id)

        self.assertIn("Apprentice Smith", msg)
        self.db.add_title.assert_called_with(self.discord_id, "Apprentice Smith")

    def test_check_crafting_achievements_already_owned(self):
        # Setup: Player reached level 5 but already has title
        self.db.get_player.return_value = {"crafting_level": 5}
        self.db.add_title.return_value = False # Title already owned

        msg = self.achievement_system.check_crafting_achievements(self.discord_id)

        self.assertIsNone(msg)
        self.db.add_title.assert_called_with(self.discord_id, "Apprentice Smith")

    def test_crafting_xp_awards_achievement(self):
        # Mock the achievement system specifically for this test to verify the hook
        self.crafting.achievement_system = MagicMock()
        self.crafting.achievement_system.check_crafting_achievements.return_value = "🏆 Title Unlocked: Apprentice Smith"

        # Mock DB returns
        self.db.get_player.return_value = {"crafting_level": 4, "crafting_xp": 100}

        msg = self.crafting._add_crafting_xp(self.discord_id, "Common")

        self.assertIn("Apprentice Smith", msg)
        self.crafting.achievement_system.check_crafting_achievements.assert_called()

if __name__ == "__main__":
    unittest.main()
