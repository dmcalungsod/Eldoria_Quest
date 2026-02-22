import unittest
from unittest.mock import MagicMock, ANY
import sys
import os

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.MongoClient"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.adventure.adventure_manager import AdventureManager  # noqa: E402
from game_systems.data.adventure_locations import LOCATIONS  # noqa: E402

class TestAdventureSchemaUpdate(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock(spec=DatabaseManager)
        self.mock_bot = MagicMock()
        self.manager = AdventureManager(self.mock_db, self.mock_bot)

    def test_start_adventure_passes_new_args(self):
        """
        Verifies that AdventureManager.start_adventure calls insert_adventure_session
        with 'supplies' and 'status' arguments.
        """
        discord_id = 12345
        location_id = "forest_outskirts" # Assuming this is valid based on previous files
        duration = 60

        # Ensure location is valid in the imported LOCATIONS
        # If LOCATIONS is a dict, we can mock it or assume it has keys.
        # But here we imported the real LOCATIONS. If "forest_outskirts" isn't there,
        # start_adventure returns False. Let's check LOCATIONS keys or mock it.
        # Since we imported it, we can't easily mock it unless we patch it.
        # Let's use a key that likely exists or patch LOCATIONS.

        with unittest.mock.patch("game_systems.adventure.adventure_manager.LOCATIONS", {"test_loc": {}}):
             self.manager.start_adventure(discord_id, "test_loc", duration)

        # Verify insert_adventure_session was called
        self.mock_db.insert_adventure_session.assert_called_once()

        # Check arguments
        args, kwargs = self.mock_db.insert_adventure_session.call_args

        # Signature: (discord_id, location_id, start_time, end_time, duration_minutes, supplies={}, status="in_progress")
        # args[0] -> discord_id
        # args[1] -> location_id
        # args[2] -> start_time
        # args[3] -> end_time
        # args[4] -> duration_minutes
        # args[5] -> supplies (or via kwargs)
        # args[6] -> status (or via kwargs)

        self.assertEqual(args[0], discord_id)
        self.assertEqual(args[1], "test_loc")
        self.assertEqual(args[4], duration)

        # Check supplies and status
        # They were passed as keyword args in my update:
        # supplies={}, status="in_progress"
        # Wait, in the code I used:
        # self.db.insert_adventure_session(..., supplies={}, status="in_progress")
        # So they should be in kwargs

        self.assertIn("supplies", kwargs)
        self.assertEqual(kwargs["supplies"], {})

        self.assertIn("status", kwargs)
        self.assertEqual(kwargs["status"], "in_progress")

        print("SUCCESS: AdventureManager calls insert_adventure_session with new schema args.")

    def test_database_manager_methods_exist(self):
        """
        Verifies that the new methods exist on the DatabaseManager class.
        """
        # Since we are mocking DatabaseManager in setUp, we need to inspect the real class
        # or just rely on the fact that if they didn't exist, other tests might fail if they called them.
        # But here I want to verify they are defined.

        real_db = DatabaseManager.__new__(DatabaseManager)

        self.assertTrue(hasattr(real_db, "get_adventures_ending_before"))
        self.assertTrue(hasattr(real_db, "update_adventure_status"))

        print("SUCCESS: New DatabaseManager methods found.")

if __name__ == "__main__":
    unittest.main()
