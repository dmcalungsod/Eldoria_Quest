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


# Create a real DuplicateKeyError class for mocking
class DuplicateKeyError(Exception):
    pass


import database.database_manager as _dbm  # noqa: E402
from database.database_manager import DatabaseManager  # noqa: E402

_dbm.DuplicateKeyError = DuplicateKeyError


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

        # Initialize DatabaseManager (singleton reset)
        DatabaseManager._instance = None
        self.db = DatabaseManager()

    def tearDown(self):
        self.mongo_patcher.stop()
        DatabaseManager._instance = None

    def test_upgrade_skill_concurrent_failure_refunds_vestige(self):
        """
        Test that if the skill level changes concurrently (causing update failure),
        the deducted vestige is refunded.
        """
        discord_id = 12345
        skill_key = "fireball"
        cost = 10
        current_level = 1

        # 1. Mock existing skill row (level 1)
        # Mocking get_player_skill_row which calls find_one on player_skills
        self.mock_db.player_skills.find_one.return_value = {"skill_level": current_level}

        # 2. Mock player has enough vestige (find_one on players) - Not used in upgrade_skill if we use update_one directly?
        # Actually upgrade_skill calls find_one first. Let's mock it just in case logic changes,
        # but the critical part is update_one return value.
        self.mock_db.players.find_one.return_value = {"vestige_pool": 100}

        # 3. Mock update_one on players (deduction) to SUCCEED
        # First call is deduction
        deduct_result = MagicMock()
        deduct_result.modified_count = 1

        # 4. Mock update_one on player_skills (upgrade) to FAIL (modified_count=0)
        # This simulates that the query {"skill_level": 1} failed to match because level changed to 2 concurrently
        upgrade_result = MagicMock()
        upgrade_result.modified_count = 0

        # 5. Mock update_one on players (refund)
        refund_result = MagicMock()
        refund_result.modified_count = 1

        # Configure side effects for update_one
        # Calls:
        # 1. Deduct vestige (players)
        # 2. Upgrade skill (player_skills) -> FAILS
        # 3. Refund vestige (players)

        # Since update_one is called on different collections, we need to mock them separately.
        self.mock_db.players.update_one.side_effect = [deduct_result, refund_result]
        self.mock_db.player_skills.update_one.return_value = upgrade_result

        # EXECUTE
        success, msg, level = self.db.upgrade_skill(discord_id, skill_key, cost)

        # VERIFY
        self.assertFalse(success, "Upgrade should fail if concurrent modification occurred")
        self.assertIn("changed during transaction", msg)
        self.assertEqual(level, current_level)

        # Verify calls
        # 1. Deduction
        self.mock_db.players.update_one.assert_any_call(
            {"discord_id": discord_id, "vestige_pool": {"$gte": cost}},
            {"$inc": {"vestige_pool": -cost}}
        )

        # 2. Attempted Upgrade with specific level check
        self.mock_db.player_skills.update_one.assert_called_with(
            {"discord_id": discord_id, "skill_key": skill_key, "skill_level": current_level},
            {"$inc": {"skill_level": 1}}
        )

        # 3. Refund
        self.mock_db.players.update_one.assert_any_call(
            {"discord_id": discord_id},
            {"$inc": {"vestige_pool": cost}}
        )

    def test_learn_skill_concurrent_duplicate_refunds_vestige(self):
        """
        Test that if learning a skill fails (e.g., DuplicateKeyError),
        the deducted vestige is refunded.
        """
        discord_id = 12345
        skill_key = "ice_bolt"
        cost = 50

        # 1. Mock player_has_skill to return False (initially check passes)
        # This calls find_one on player_skills
        self.mock_db.player_skills.find_one.return_value = None

        # 2. Mock player has enough vestige
        self.mock_db.players.find_one.return_value = {"vestige_pool": 100}

        # 3. Mock deduction succeeds
        deduct_result = MagicMock()
        deduct_result.modified_count = 1

        # 4. Mock insertion fails with DuplicateKeyError
        self.mock_db.player_skills.insert_one.side_effect = DuplicateKeyError("Duplicate key")

        # 5. Mock refund
        refund_result = MagicMock()
        refund_result.modified_count = 1

        self.mock_db.players.update_one.side_effect = [deduct_result, refund_result]

        # EXECUTE
        success, msg = self.db.learn_skill(discord_id, skill_key, cost)

        # VERIFY
        self.assertFalse(success, "Learn should fail if duplicate key error")
        self.assertIn("refunded", msg)  # The duplicate key path returns "System error (refunded)."

        # Verify calls
        # 1. Deduction
        self.mock_db.players.update_one.assert_any_call(
            {"discord_id": discord_id, "vestige_pool": {"$gte": cost}},
            {"$inc": {"vestige_pool": -cost}}
        )

        # 2. Insertion Attempt
        self.mock_db.player_skills.insert_one.assert_called()

        # 3. Refund
        self.mock_db.players.update_one.assert_any_call(
            {"discord_id": discord_id},
            {"$inc": {"vestige_pool": cost}}
        )

if __name__ == "__main__":
    unittest.main()
