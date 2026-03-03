import unittest
from unittest.mock import MagicMock

from database.database_manager import DatabaseManager


class TestInfirmaryRace(unittest.TestCase):
    def setUp(self):
        self.mock_db_client = MagicMock()
        self.mock_db = MagicMock()
        self.mock_db_client.__getitem__.return_value = self.mock_db

        # Patch the client creation in DatabaseManager
        # We can't easily patch the class attribute _instance, so we'll mock the internals
        self.db = DatabaseManager()
        self.db._client = self.mock_db_client
        self.db.db = self.mock_db
        self.db._col = MagicMock()

    def test_execute_heal_uses_atomic_inc(self):
        """Test that execute_heal uses $inc for aurum to prevent lost updates."""

        # Mock finding the player
        # Initial state: 50 HP, 1000 Gold
        self.db._col("players").find_one.return_value = {
            "discord_id": 12345,
            "current_hp": 50,
            "current_mp": 10,
            "aurum": 1000,
        }

        # Mock update result to simulate success
        mock_result = MagicMock()
        mock_result.modified_count = 1
        self.db._col("players").update_one.return_value = mock_result

        # Call execute_heal
        # Target: 150 HP (Missing 100). Cost should be 200 (2.0 * 100)
        # Target: 50 MP (Missing 40). Cost should be 120 (3.0 * 40)
        # Total Cost: 320
        result, msg = self.db.execute_heal(12345, max_hp=150, max_mp=50)

        self.assertTrue(result)
        self.assertIn("Restored HP/MP", msg)

        # Check the update_one call
        args, kwargs = self.db._col("players").update_one.call_args
        filter_query = args[0]
        update_op = args[1]

        # 1. Verify Optimistic Locking: Filter should include current_hp
        self.assertEqual(
            filter_query["current_hp"],
            50,
            "Update should filter by previous HP (Optimistic Locking)",
        )

        # 2. Verify Atomic Increment: Update should use $inc for aurum
        self.assertIn("$inc", update_op, "Update should use $inc for atomic balance deduction")
        self.assertEqual(update_op["$inc"]["aurum"], -320, "Should deduct 320 aurum")

        # 3. Verify Vitals Set: Update should use $set for HP/MP
        self.assertIn("$set", update_op)
        self.assertEqual(update_op["$set"]["current_hp"], 150)

    def test_execute_heal_handles_race_condition(self):
        """Test that execute_heal fails if HP changes between fetch and update."""

        # Mock finding the player
        self.db._col("players").find_one.return_value = {
            "discord_id": 12345,
            "current_hp": 50,
            "current_mp": 10,
            "aurum": 1000,
        }

        # Mock update result to simulate FAILURE (modified_count = 0)
        # This happens if the filter (current_hp=50) doesn't match DB anymore
        mock_result = MagicMock()
        mock_result.modified_count = 0
        self.db._col("players").update_one.return_value = mock_result

        # Call execute_heal
        result, msg = self.db.execute_heal(12345, max_hp=150, max_mp=50)

        # Should return False because update failed
        self.assertFalse(result)
        self.assertEqual(msg, "Healing failed due to state change. Please try again.")


if __name__ == "__main__":
    unittest.main()
