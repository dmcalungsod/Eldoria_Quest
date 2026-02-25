import os
import sys
import unittest
from unittest.mock import MagicMock

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.crafting.crafting_system import CraftingSystem  # noqa: E402


class TestCraftingAchievements(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock(spec=DatabaseManager)
        self.crafting = CraftingSystem(self.mock_db)
        self.discord_id = 12345

    def test_craft_awards_achievement(self):
        # Setup common mocks
        self.mock_db.get_player.return_value = {"aurum": 1000, "crafting_level": 1}
        self.mock_db.get_inventory_item_count.return_value = 100
        self.mock_db.remove_inventory_item.return_value = True
        self.mock_db.get_equipment_id_by_name.return_value = "1"

        # Mock AchievementSystem check
        # Since CraftingSystem instantiates it in __init__, we need to mock it on the instance
        # or patch it before instantiation if we want to catch __init__.
        # But we already instantiated it in setUp.
        # So we can replace the attribute.

        mock_ach_system = MagicMock()
        self.crafting.achievement_system = mock_ach_system
        mock_ach_system.check_crafting_achievements.return_value = "🏆 Title Unlocked: Apprentice Smith"

        # Execute
        success, msg, item = self.crafting.craft_item(self.discord_id, "hp_potion_1")

        # Verify
        self.assertTrue(success)
        self.mock_db.increment_crafting_stats.assert_called_with(self.discord_id, 1)
        mock_ach_system.check_crafting_achievements.assert_called_with(self.discord_id)
        self.assertIn("Apprentice Smith", msg)

    def test_craft_no_achievement(self):
        # Setup common mocks
        self.mock_db.get_player.return_value = {"aurum": 1000, "crafting_level": 1}
        self.mock_db.get_inventory_item_count.return_value = 100
        self.mock_db.remove_inventory_item.return_value = True

        mock_ach_system = MagicMock()
        self.crafting.achievement_system = mock_ach_system
        mock_ach_system.check_crafting_achievements.return_value = None

        # Execute
        success, msg, item = self.crafting.craft_item(self.discord_id, "hp_potion_1")

        # Verify
        self.assertTrue(success)
        self.mock_db.increment_crafting_stats.assert_called_with(self.discord_id, 1)
        mock_ach_system.check_crafting_achievements.assert_called_with(self.discord_id)
        self.assertNotIn("Title Unlocked", msg)


if __name__ == "__main__":
    unittest.main()
