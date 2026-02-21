import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo BEFORE import
mock_pymongo = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = MagicMock()

from database.database_manager import DatabaseManager  # noqa: E402


class TestWorldEventCaching(unittest.TestCase):
    def setUp(self):
        # Reset singleton state
        DatabaseManager._instance = None
        DatabaseManager._initialized = False

        # Patch MongoClient
        self.client_patcher = patch("database.database_manager.MongoClient")
        self.mock_client_cls = self.client_patcher.start()

        self.mock_client = MagicMock()
        self.mock_client_cls.return_value = self.mock_client

        self.mock_db = MagicMock()
        self.mock_client.__getitem__.return_value = self.mock_db

        # Bridge collection access
        def get_collection(name):
            return getattr(self.mock_db, name)
        self.mock_db.__getitem__.side_effect = get_collection

        self.db = DatabaseManager()

    def tearDown(self):
        self.client_patcher.stop()
        DatabaseManager._instance = None
        DatabaseManager._initialized = False

    def test_world_event_caching(self):
        # Setup mock return
        self.mock_db.world_events.find_one.return_value = {"type": "blood_moon", "active": 1}

        # 1. First Call - Should hit DB
        with patch("time.time", return_value=1000.0):
            event1 = self.db.get_active_world_event()

        self.assertEqual(event1["type"], "blood_moon")
        self.mock_db.world_events.find_one.assert_called_once()

        # 2. Second Call (Immediate) - Should NOT hit DB (if cached)
        self.mock_db.world_events.find_one.reset_mock()

        # We simulate time advancing only slightly (within 60s window)
        with patch("time.time", return_value=1030.0):
            event2 = self.db.get_active_world_event()

        self.assertEqual(event2["type"], "blood_moon")

        # Expectation: Not called
        self.mock_db.world_events.find_one.assert_not_called()

    def test_cache_expiration(self):
        self.mock_db.world_events.find_one.return_value = {"type": "blood_moon", "active": 1}

        # 1. Populate cache
        with patch("time.time", return_value=1000.0):
            self.db.get_active_world_event()

        self.mock_db.world_events.find_one.reset_mock()

        # 2. Call after expiration (61s later)
        with patch("time.time", return_value=1061.0):
            self.db.get_active_world_event()

        # Expectation: Called
        self.mock_db.world_events.find_one.assert_called_once()

    def test_invalidation_on_set(self):
        self.mock_db.world_events.find_one.return_value = {"type": "blood_moon", "active": 1}

        # Populate cache
        with patch("time.time", return_value=1000.0):
            self.db.get_active_world_event()

        # Set new event
        with patch("time.time", return_value=1010.0):
            self.db.set_active_world_event("void_incursion", "start", "end")

        # Check if invalidation happened
        self.mock_db.world_events.find_one.reset_mock()
        with patch("time.time", return_value=1020.0):
            self.db.get_active_world_event()

        # Expectation: Called
        self.mock_db.world_events.find_one.assert_called_once()

    def test_return_copy(self):
        """Test that the cache returns a copy to prevent mutation."""
        self.mock_db.world_events.find_one.return_value = {"type": "blood_moon", "active": 1, "data": {}}

        with patch("time.time", return_value=1000.0):
            event1 = self.db.get_active_world_event()

        # Mutate the returned object
        event1["mutated"] = True

        # Fetch again
        with patch("time.time", return_value=1010.0):
            event2 = self.db.get_active_world_event()

        # The second fetch should NOT have the mutation
        self.assertNotIn("mutated", event2)
        self.assertNotEqual(event1, event2)

if __name__ == "__main__":
    unittest.main()
