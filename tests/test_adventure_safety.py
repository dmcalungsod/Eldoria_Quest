import os
import sys
import unittest
from unittest.mock import MagicMock

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.MongoClient"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.adventure.adventure_manager import AdventureManager  # noqa: E402


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
        active_session = {
            "location_id": "test_loc",
            "active": 1,
            "logs": "[]",
            "loot_collected": '{"iron_ore": 5}',
            "active_monster_json": None,
        }
        self.mock_db.get_active_adventure.return_value = active_session
        self.mock_db.mark_adventure_claiming.return_value = active_session

        # Mock player stats
        self.mock_db.get_player_stats_json.return_value = {}
        self.mock_db.get_player.return_value = {
            "level": 1,
            "experience": 0,
            "current_hp": 10,
            "current_mp": 10,
            "exp_to_next": 1000,
        }

        # Mock level values
        self.mock_db.get_player_field.return_value = 1

        # Mock database methods to track call order
        manager_mock = MagicMock()
        self.mock_db.end_adventure_session.side_effect = manager_mock.end_adventure_session

        # Configure add_inventory_items_bulk to return empty list (no failures)
        # We use side_effect to track the call on manager_mock, but also return []
        def add_items_side_effect(*args, **kwargs):
            manager_mock.add_inventory_items_bulk(*args, **kwargs)
            return []

        self.mock_db.add_inventory_items_bulk.side_effect = add_items_side_effect

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

    def test_failure_stops_process(self):
        """
        Verifies that if add_items_bulk fails, end_adventure_session is NOT called.
        """
        discord_id = 12345

        active_session = {
            "location_id": "test_loc",
            "active": 1,
            "logs": "[]",
            "loot_collected": '{"iron_ore": 5}',
            "active_monster_json": None,
        }
        self.mock_db.get_active_adventure.return_value = active_session
        self.mock_db.mark_adventure_claiming.return_value = active_session
        self.mock_db.get_player_stats_json.return_value = {}
        self.mock_db.get_player.return_value = {
            "level": 1,
            "experience": 0,
            "current_hp": 10,
            "current_mp": 10,
            "exp_to_next": 1000,
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

    def test_invalid_start_adventure(self):
        """
        Verifies that start_adventure returns False for invalid inputs.
        """
        discord_id = 12345

        # 1. Invalid Location
        result = self.manager.start_adventure(discord_id, "invalid_zone", -1)
        self.assertFalse(result, "Should fail with invalid location_id")
        self.mock_db.insert_adventure_session.assert_not_called()

        # 2. Invalid Duration (Too high)
        # Using a valid location for this test
        # We need to ensure "forest_outskirts" (or similar) is recognized as valid
        # Since LOCATIONS is imported in adventure_manager, we rely on it being present.
        # Assuming "forest_outskirts" exists in LOCATIONS as per previous read.

        result = self.manager.start_adventure(discord_id, "forest_outskirts", 9999999)
        self.assertFalse(result, "Should fail with excessive duration")
        self.mock_db.insert_adventure_session.assert_not_called()

        # 3. Invalid Duration (Negative but not -1)
        result = self.manager.start_adventure(discord_id, "forest_outskirts", -5)
        self.assertFalse(result, "Should fail with negative duration != -1")
        self.mock_db.insert_adventure_session.assert_not_called()

        # 4. Valid Case
        result = self.manager.start_adventure(discord_id, "forest_outskirts", 60)
        self.assertTrue(result, "Should succeed with valid inputs")
        self.mock_db.insert_adventure_session.assert_called_once()
        print("SUCCESS: Input validation passed.")


if __name__ == "__main__":
    unittest.main()
