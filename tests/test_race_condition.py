"""
Tests for Race Condition Handling in DatabaseManager
----------------------------------------------------
Specifically targets learn_skill and upgrade_skill methods to ensure atomic-like behavior
and refund logic in case of concurrent modifications or failures.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager

# Local exception to ensure consistent mocking regardless of pymongo installation
class MockDuplicateKeyError(Exception):
    pass

class TestRaceCondition(unittest.TestCase):
    def setUp(self):
        # Mock the MongoClient to prevent actual DB connection
        self.mock_client = MagicMock()
        self.mock_db = MagicMock()
        self.mock_client.__getitem__.return_value = self.mock_db

        def get_collection(name):
            return getattr(self.mock_db, name)

        self.mock_db.__getitem__.side_effect = get_collection

        self.mongo_patcher = patch("database.database_manager.MongoClient", return_value=self.mock_client)
        self.mongo_patcher.start()

        # Patch DuplicateKeyError in database_manager to use our local mock
        self.dup_error_patcher = patch("database.database_manager.DuplicateKeyError", MockDuplicateKeyError)
        self.dup_error_patcher.start()

        # Initialize DatabaseManager (singleton reset)
        DatabaseManager._instance = None
        self.db = DatabaseManager()

    def tearDown(self):
        self.mongo_patcher.stop()
        self.dup_error_patcher.stop()
        DatabaseManager._instance = None

    def test_upgrade_skill_concurrent_failure_refunds_vestige(self):
        discord_id = 12345
        skill_key = "fireball"
        cost = 10
        current_level = 1

        self.mock_db.player_skills.find_one.return_value = {"skill_level": current_level}
        self.mock_db.players.find_one.return_value = {"vestige_pool": 100}

        deduct_result = MagicMock()
        deduct_result.modified_count = 1

        upgrade_result = MagicMock()
        upgrade_result.modified_count = 0

        refund_result = MagicMock()
        refund_result.modified_count = 1

        self.mock_db.players.update_one.side_effect = [deduct_result, refund_result]
        self.mock_db.player_skills.update_one.return_value = upgrade_result

        success, msg, level = self.db.upgrade_skill(discord_id, skill_key, cost)

        self.assertFalse(success)
        self.assertIn("changed during transaction", msg)
        self.assertEqual(level, current_level)

    def test_learn_skill_concurrent_duplicate_refunds_vestige(self):
        discord_id = 12345
        skill_key = "ice_bolt"
        cost = 50

        self.mock_db.player_skills.find_one.return_value = None
        self.mock_db.players.find_one.return_value = {"vestige_pool": 100}

        deduct_result = MagicMock()
        deduct_result.modified_count = 1

        # Raise our MOCKED DuplicateKeyError
        self.mock_db.player_skills.insert_one.side_effect = MockDuplicateKeyError("Duplicate key")

        refund_result = MagicMock()
        refund_result.modified_count = 1

        self.mock_db.players.update_one.side_effect = [deduct_result, refund_result]

        success, msg = self.db.learn_skill(discord_id, skill_key, cost)

        self.assertFalse(success, f"Should have failed due to duplicate key. Msg: {msg}")
        self.assertIn("refunded", msg)

if __name__ == "__main__":
    unittest.main()
