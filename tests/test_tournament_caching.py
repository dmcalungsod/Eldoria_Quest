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


class TestTournamentCaching(unittest.TestCase):
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

        # Mock counters collection
        self.mock_db.counters.find_one_and_update.return_value = {"seq": 100}

        self.db = DatabaseManager()

    def tearDown(self):
        self.client_patcher.stop()
        DatabaseManager._instance = None
        DatabaseManager._initialized = False

    def test_tournament_caching(self):
        # Setup mock return
        self.mock_db.tournaments.find_one.return_value = {
            "type": "spectral_tide",
            "active": 1,
        }

        # 1. First Call - Should hit DB
        with patch("time.time", return_value=1000.0):
            tourney1 = self.db.get_active_tournament()

        self.assertEqual(tourney1["type"], "spectral_tide")
        self.mock_db.tournaments.find_one.assert_called()
        call_count_after_first = self.mock_db.tournaments.find_one.call_count

        # 2. Second Call (Immediate) - Should NOT hit DB (if cached)
        # We simulate time advancing only slightly (within 60s window)
        with patch("time.time", return_value=1030.0):
            tourney2 = self.db.get_active_tournament()

        self.assertEqual(tourney2["type"], "spectral_tide")

        # Expectation: Call count should remain the same (cached)
        self.assertEqual(
            self.mock_db.tournaments.find_one.call_count,
            call_count_after_first,
            "DB should not be hit again if cached",
        )

    def test_cache_expiration(self):
        self.mock_db.tournaments.find_one.return_value = {
            "type": "spectral_tide",
            "active": 1,
        }

        # 1. Populate cache
        with patch("time.time", return_value=1000.0):
            self.db.get_active_tournament()

        self.mock_db.tournaments.find_one.reset_mock()

        # 2. Call after expiration (61s later)
        with patch("time.time", return_value=1061.0):
            self.db.get_active_tournament()

        # Expectation: Called
        self.mock_db.tournaments.find_one.assert_called_once()

    def test_invalidation_create(self):
        self.mock_db.tournaments.find_one.return_value = {
            "type": "spectral_tide",
            "active": 1,
        }

        # 1. Populate cache
        with patch("time.time", return_value=1000.0):
            self.db.get_active_tournament()

        self.mock_db.tournaments.find_one.reset_mock()

        # 2. Create new tournament (should invalidate cache)
        with patch("time.time", return_value=1010.0):
            self.db.create_tournament("void_hunt", "start", "end")

        # 3. Fetch again - Should hit DB
        with patch("time.time", return_value=1020.0):
            self.db.get_active_tournament()

        # Expectation: Called
        self.mock_db.tournaments.find_one.assert_called_once()

    def test_invalidation_end(self):
        self.mock_db.tournaments.find_one.return_value = {
            "type": "spectral_tide",
            "active": 1,
        }

        # 1. Populate cache
        with patch("time.time", return_value=1000.0):
            self.db.get_active_tournament()

        self.mock_db.tournaments.find_one.reset_mock()

        # 2. End tournament (should invalidate cache)
        with patch("time.time", return_value=1010.0):
            self.db.end_active_tournament()

        # 3. Fetch again - Should hit DB
        with patch("time.time", return_value=1020.0):
            self.db.get_active_tournament()

        # Expectation: Called
        self.mock_db.tournaments.find_one.assert_called_once()

    def test_return_copy(self):
        """Test that the cache returns a copy to prevent mutation."""
        self.mock_db.tournaments.find_one.return_value = {
            "type": "spectral_tide",
            "active": 1,
            "data": {},
        }

        with patch("time.time", return_value=1000.0):
            tourney1 = self.db.get_active_tournament()

        # Mutate the returned object
        tourney1["mutated"] = True

        # Fetch again
        with patch("time.time", return_value=1010.0):
            tourney2 = self.db.get_active_tournament()

        # The second fetch should NOT have the mutation
        self.assertNotIn("mutated", tourney2)
        self.assertNotEqual(tourney1, tourney2)


if __name__ == "__main__":
    unittest.main()
