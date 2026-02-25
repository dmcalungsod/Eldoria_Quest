import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from game_systems.adventure.adventure_manager import AdventureManager  # noqa: E402


class TestSupplyAchievements(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_bot = MagicMock()
        self.adventure_manager = AdventureManager(self.mock_db, self.mock_bot)
        self.discord_id = 12345

    def test_start_adventure_increments_stats(self):
        # Setup
        supplies = {"torch": 2, "ration": 3}
        self.mock_db.get_inventory_item_count.return_value = 10
        self.mock_db.remove_inventory_item.return_value = True

        # Execute
        # We need to mock LOCATIONS to pass validation
        with patch("game_systems.adventure.adventure_manager.LOCATIONS", {"forest": {}}):
            success = self.adventure_manager.start_adventure(self.discord_id, "forest", 60, supplies=supplies)

        # Verify
        self.assertTrue(success)
        self.mock_db.increment_supply_stats.assert_called_with(self.discord_id, 5)

    def test_end_adventure_checks_supply_achievements(self):
        # Setup
        # Mock active adventure
        self.mock_db.get_active_adventure.return_value = {
            "discord_id": self.discord_id,
            "location_id": "forest",
            "start_time": "2023-10-26T12:00:00",
            "duration_minutes": 60,
            "active": 1,
            "version": 1,
            "loot_collected": "{}",
            "logs": "[]",
            "active_monster_json": None,
        }

        # Mock player stats
        self.mock_db.get_player_stats_json.return_value = {}
        self.mock_db.get_player.return_value = {
            "level": 1,
            "experience": 0,
            "exp_to_next": 100,
            "current_hp": 100,
            "current_mp": 100,
        }
        self.mock_db.get_player_field.return_value = 1

        # Patch AchievementSystem
        with patch("game_systems.adventure.adventure_manager.AchievementSystem") as MockAchievementSystem:
            mock_ach_system = MockAchievementSystem.return_value
            mock_ach_system.check_exploration_achievements.return_value = None
            mock_ach_system.check_duration_achievements.return_value = None
            mock_ach_system.check_supply_achievements.return_value = "🏆 Title Unlocked: Provisioner"

            # Execute
            summary = self.adventure_manager.end_adventure(self.discord_id)

            # Verify
            self.assertIsNotNone(summary)
            self.assertIn("Provisioner", summary["new_titles"])
            mock_ach_system.check_supply_achievements.assert_called_with(self.discord_id)


if __name__ == "__main__":
    unittest.main()
