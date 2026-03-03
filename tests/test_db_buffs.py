import sys
import unittest
from unittest.mock import MagicMock

# Mock pymongo modules BEFORE importing database_manager
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Ensure we can import game modules
sys.path.append(".")

from database.database_manager import DatabaseManager  # noqa: E402


class TestDBBuffs(unittest.TestCase):
    def setUp(self):
        # Reset singleton to ensure fresh mock
        DatabaseManager._instance = None
        DatabaseManager._initialized = False

    def tearDown(self):
        DatabaseManager._instance = None

    def test_add_active_buff_replaces_existing(self):
        # Mock DatabaseManager
        # Since pymongo is mocked, we don't need real URI
        db = DatabaseManager(mongo_uri="mongodb://mock")

        # Mock collection
        mock_col = MagicMock()
        # Mock _col method directly to avoid internal structure assumptions
        db._col = MagicMock(return_value=mock_col)

        # Call add_active_buff
        db.add_active_buff(discord_id=123, buff_id="buff1", name="Rage", stat="STR", amount=50, duration_s=60)

        # Verify delete_many was called
        # Note: In database_manager.py:
        # self._col("active_buffs").delete_many({"discord_id": discord_id, "name": name})

        # Check call args of _col first
        db._col.assert_any_call("active_buffs")

        # Check calls on the mock_col returned by _col
        mock_col.delete_many.assert_called_with({"discord_id": 123, "name": "Rage"})

        # Verify insert_one was called
        mock_col.insert_one.assert_called()


if __name__ == "__main__":
    unittest.main()
