import os
import sys
import unittest
from unittest.mock import MagicMock

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.crafting.crafting_system import CraftingSystem  # noqa: E402
from game_systems.player.achievement_system import AchievementSystem  # noqa: E402


class TestCraftingAchievements(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.achievement_system = AchievementSystem(self.mock_db)
        self.crafting_system = CraftingSystem(self.mock_db)

    def test_check_crafting_achievements_level_5(self):
        discord_id = 123

        # Mock player data with level 5 crafting
        self.mock_db.get_player.return_value = {"crafting_level": 5}

        # Mock add_title to return True for new title
        self.mock_db.add_title.return_value = True

        msg = self.achievement_system.check_crafting_achievements(discord_id)

        self.mock_db.add_title.assert_any_call(discord_id, "Apprentice Smith")
        # Updated assertion to match exact format: 🏆 **Title Unlocked:** Apprentice Smith
        self.assertIn("**Title Unlocked:** Apprentice Smith", msg)

    def test_check_crafting_achievements_level_10(self):
        discord_id = 123

        self.mock_db.get_player.return_value = {"crafting_level": 10}
        self.mock_db.add_title.return_value = True

        msg = self.achievement_system.check_crafting_achievements(discord_id)

        self.mock_db.add_title.assert_any_call(discord_id, "Journeyman Crafter")
        # Updated assertion to allow for multiple titles if both unlock at once
        # Or specifically check for the title presence in the string
        self.assertIn("Journeyman Crafter", msg)

    def test_crafting_level_up_triggers_achievement(self):
        discord_id = 123

        # Mock get_player to return level 4 initially, then level 5
        self.mock_db.get_player.side_effect = [
            {"crafting_level": 4, "crafting_xp": 300}, # For _add_crafting_xp calculation
            {"crafting_level": 5}  # For achievement check
        ]

        self.mock_db.add_title.return_value = True

        # Since we can't easily trigger _add_crafting_xp from public methods without crafting,
        # and mocking craft_item is complex, we'll access the private method directly for testing.
        # This is acceptable for unit testing internal logic.
        msg = self.crafting_system._add_crafting_xp(discord_id, "Common")

        # Check if the message contains the achievement notification
        self.assertIn("Title Unlocked", msg)
        self.assertIn("Apprentice Smith", msg)

if __name__ == "__main__":
    unittest.main()
