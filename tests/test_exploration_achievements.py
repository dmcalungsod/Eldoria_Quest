import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock pymongo before importing modules that use it
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.collection"] = MagicMock()
sys.modules["pymongo.results"] = MagicMock()

from game_systems.adventure.adventure_manager import AdventureManager  # noqa: E402
from game_systems.achievement_system import AchievementSystem  # noqa: E402

class TestExplorationAchievements(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_bot = MagicMock()
        self.adventure_manager = AdventureManager(self.mock_db, self.mock_bot)

    def test_end_adventure_awards_achievement(self):
        # Setup
        discord_id = 123456
        location_id = "forest_outskirts"

        # Mock active adventure
        self.mock_db.get_active_adventure.return_value = {
            "discord_id": discord_id,
            "location_id": location_id,
            "start_time": "2023-10-26T12:00:00",
            "duration_minutes": 60,
            "active": 1,
            "version": 1,
            "loot_collected": "{}",
            "logs": "[]",
            "active_monster_json": None
        }

        # Mock player stats json
        self.mock_db.get_player_stats_json.return_value = {
            "STR": {"base": 10},
            "END": {"base": 10},
            "DEX": {"base": 10},
            "AGI": {"base": 10},
            "MAG": {"base": 10},
            "LCK": {"base": 10},
            "DEF": 0
        }
        self.mock_db.get_player.return_value = {
            "level": 1,
            "experience": 0,
            "exp_to_next": 100,
            "current_hp": 100,
            "current_mp": 50,
            "vestige_pool": 0,
            "aurum": 0
        }

        self.mock_db.get_player_field.return_value = 1

        # Mock AchievementSystem (internal to AdventureManager)
        # We patch where it is IMPORTED
        with patch('game_systems.adventure.adventure_manager.AchievementSystem') as MockAchievementSystem:
            mock_ach_system_instance = MockAchievementSystem.return_value
            mock_ach_system_instance.check_exploration_achievements.return_value = "🏆 Title Unlocked: Pathfinder"

            # Execute
            summary = self.adventure_manager.end_adventure(discord_id)

            # Verify
            self.mock_db.update_exploration_stats.assert_called_with(discord_id, location_id)
            mock_ach_system_instance.check_exploration_achievements.assert_called_with(discord_id)

            self.assertIsNotNone(summary)
            self.assertEqual(summary.get("new_titles"), "🏆 Title Unlocked: Pathfinder")

    def test_achievement_system_logic(self):
        # Test the logic inside AchievementSystem separately
        ach_sys = AchievementSystem(self.mock_db)
        discord_id = 123456

        # Case 1: 10 Expeditions (Pathfinder)
        self.mock_db.get_exploration_stats.return_value = {
            "unique_locations": ["loc1"],
            "total_expeditions": 10
        }
        # Simulate add_title returning True (new title)
        self.mock_db.add_title.return_value = True

        msg = ach_sys.check_exploration_achievements(discord_id)

        self.mock_db.add_title.assert_any_call(discord_id, "Pathfinder")
        self.assertIn("Pathfinder", msg)

        # Case 2: 5 Locations (Scout)
        self.mock_db.get_exploration_stats.return_value = {
            "unique_locations": ["1", "2", "3", "4", "5"],
            "total_expeditions": 5
        }
        self.mock_db.add_title.reset_mock()

        msg = ach_sys.check_exploration_achievements(discord_id)

        self.mock_db.add_title.assert_any_call(discord_id, "Scout")
        self.assertIn("Scout", msg)

if __name__ == '__main__':
    unittest.main()
