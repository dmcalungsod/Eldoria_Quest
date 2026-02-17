
import unittest
from unittest.mock import MagicMock, ANY
import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.adventure.adventure_manager import AdventureManager
from database.database_manager import DatabaseManager

class TestAdventureDataLoss(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock(spec=DatabaseManager)
        self.mock_bot = MagicMock()
        self.manager = AdventureManager(self.mock_db, self.mock_bot)

    def test_safe_reward_order(self):
        """
        Verifies that items are added BEFORE end_adventure_session is called.
        """
        discord_id = 12345

        # Mock active session
        self.mock_db.get_active_adventure.return_value = {
            "location_id": "test_loc",
            "active": 1,
            "logs": "[]",
            "loot_collected": '{"iron_ore": 5}',
            "active_monster_json": None
        }

        # Mock player stats
        self.mock_db.get_player_stats_json.return_value = {}
        self.mock_db.get_player.return_value = {
            "level": 1, "experience": 0, "exp_to_next": 100, "current_hp": 10, "exp_to_next": 1000
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
            end_idx = method_names.index('end_adventure_session')
            add_idx = method_names.index('add_inventory_items_bulk')

            if add_idx < end_idx:
                print("SUCCESS: Items added before session ended.")
            else:
                self.fail("BUG: Session ended before items added.")

        except ValueError:
            self.fail("One of the methods was not called.")

    def test_failure_stops_process(self):
        """
        Verifies that if add_items_bulk fails, end_adventure_session is NOT called.
        """
        discord_id = 12345

        self.mock_db.get_active_adventure.return_value = {
            "location_id": "test_loc",
            "active": 1,
            "logs": "[]",
            "loot_collected": '{"iron_ore": 5}',
            "active_monster_json": None
        }
        self.mock_db.get_player_stats_json.return_value = {}
        self.mock_db.get_player.return_value = {
            "level": 1, "experience": 0, "exp_to_next": 100, "current_hp": 10, "exp_to_next": 1000
        }
        self.mock_db.get_player_field.return_value = 1

        # Make add_items_bulk raise an exception
        self.mock_db.add_inventory_items_bulk.side_effect = Exception("DB Error")

        # Run end_adventure
        result = self.manager.end_adventure(discord_id)

        # Should return None due to exception
        self.assertIsNone(result)

        # Verify end_adventure_session was NOT called
        self.mock_db.end_adventure_session.assert_not_called()
        print("SUCCESS: Session not ended after item add failure.")

if __name__ == '__main__':
    unittest.main()
