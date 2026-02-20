import os
import sys
import unittest
from unittest.mock import MagicMock

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager


class TestAdventureDataLoss(unittest.TestCase):
    def setUp(self):
        # Mock DB
        self.mock_db = MagicMock(spec=DatabaseManager)
        self.bot = MagicMock()
        self.manager = AdventureManager(self.mock_db, self.bot)

    def test_safe_reward_order(self):
        """
        Verify that items are added BEFORE the session is marked inactive.
        This prevents a race condition where a crash leaves the player with no rewards but an inactive session.
        """
        discord_id = 12345

        # Mock active session
        self.mock_db.get_active_adventure.return_value = {
            "discord_id": discord_id,
            "location_id": "forest_outskirts",
            "start_time": "2023-01-01T00:00:00",
            "end_time": "2023-01-01T01:00:00",
            "duration_minutes": 60,
            "active": 1,
            "logs": "[]",
            "loot_collected": '{"exp": 100, "iron_ore": 2}',
            "active_monster_json": None,
        }

        # Mock player stats
        self.mock_db.get_player_stats_json.return_value = {}
        self.mock_db.get_player.return_value = {
            "level": 1, "experience": 0, "current_hp": 10, "current_mp": 10, "exp_to_next": 1000
        }

        # Mock level values
        self.mock_db.get_player_field.return_value = 1

        # Mock database methods to track call order
        manager_mock = MagicMock()
        self.mock_db.end_adventure_session.side_effect = manager_mock.end_adventure_session
        self.mock_db.add_inventory_items_bulk.side_effect = manager_mock.add_inventory_items_bulk

        # Run end_adventure
        self.manager.end_adventure(discord_id)

        # Check call order
        calls = manager_mock.mock_calls
        method_names = [c[0] for c in calls]

        try:
            end_idx = method_names.index("end_adventure_session")
            add_idx = method_names.index("add_inventory_items_bulk")

            if add_idx < end_idx:
                print("SUCCESS: Items added before session ended.")
            else:
                self.fail("BUG: Session ended before items added.")

        except ValueError:
            self.fail("One of the methods was not called.")

    def test_invalid_start_adventure(self):
        """Verifies that start_adventure returns False for invalid inputs."""
        discord_id = 12345

        # 1. Invalid Location
        result = self.manager.start_adventure(discord_id, "invalid_zone", -1)
        self.assertFalse(result, "Should fail for invalid location.")

        # 2. Invalid Duration (Too long)
        result = self.manager.start_adventure(discord_id, "forest_outskirts", 9999999)
        self.assertFalse(result, "Should fail for excessive duration.")

        # 3. Invalid Duration (Negative but not -1)
        result = self.manager.start_adventure(discord_id, "forest_outskirts", -5)
        self.assertFalse(result, "Should fail for negative duration.")

        # 4. Valid inputs
        result = self.manager.start_adventure(discord_id, "forest_outskirts", 60)
        self.assertTrue(result, "Should succeed for valid inputs.")


if __name__ == "__main__":
    unittest.main()
