import os
import sys
import unittest
from unittest.mock import MagicMock

# Add root dir to sys.path
sys.path.append(os.getcwd())

# Mock modules before importing
if "pymongo" not in sys.modules:
    sys.modules["pymongo"] = MagicMock()
    sys.modules["pymongo.errors"] = MagicMock()
if "discord" not in sys.modules:
    sys.modules["discord"] = MagicMock()

from database.database_manager import DatabaseManager  # noqa: E402


class TestCodexUnlocks(unittest.TestCase):
    def setUp(self):
        # We test DatabaseManager's codex functions here for edge cases
        self.mock_client = MagicMock()
        self.mock_db = MagicMock()
        self.mock_client.__getitem__.return_value = self.mock_db

        def get_collection(name, *args, **kwargs):
            return getattr(self.mock_db, str(name))

        self.mock_db.__getitem__.side_effect = get_collection

        DatabaseManager._instance = None

        import unittest.mock as mock

        with mock.patch("database.database_manager.MongoClient", return_value=self.mock_client):
            self.db = DatabaseManager()

        self.user_id = 12345

    def test_update_codex_duplicate_entry(self):
        """Test that updating an existing entry overwrites the value correctly instead of creating duplicates."""
        # Initial data in the mock DB
        self.mock_db["player_codex"].find_one.return_value = {
            "user_id": self.user_id,
            "bestiary": {"1": {"kills": 10, "seen": True}},
        }

        # Call update_codex
        self.db.update_codex(self.user_id, "bestiary", "1", {"kills": 15, "seen": True})

        # Verify it uses $set properly to update the specific path
        # Mock logic creates a mock object for the col, let's verify on it.
        col_mock = self.mock_db._col.return_value if hasattr(self.mock_db, "_col") else self.mock_db["player_codex"]

        # update_codex uses self._col("player_codex").update_one
        # The mock logic in setup maps __getitem__ but database_manager uses _col typically.
        # Let's check what it uses.
        # It calls: self._col("player_codex").update_one( ... )
        # Since _col returns self.db[collection_name] and we patched __getitem__, it hits self.mock_db["player_codex"]

        # assert_called_with works on the mock
        col = self.db._col("player_codex")
        col.update_one.assert_called_with(
            {"user_id": self.user_id},
            {"$set": {"bestiary.1": {"kills": 15, "seen": True}}},
            upsert=True,
        )

    def test_update_codex_nested_edge_case(self):
        """Test updating a deeply nested key to ensure path formatting works."""
        self.db.update_codex(self.user_id, "atlas", "forest_outskirts", {"visits": 5})

        col = self.db._col("player_codex")
        col.update_one.assert_called_with(
            {"user_id": self.user_id},
            {"$set": {"atlas.forest_outskirts": {"visits": 5}}},
            upsert=True,
        )

    def test_get_codex_duplicate_merge(self):
        """Test fetching a document merges it properly even if the original structure has duplicates or unexpected fields."""

        # database_manager get_codex uses find_one on _col
        col = self.db._col("player_codex")
        col.find_one.return_value = {
            "user_id": self.user_id,
            "bestiary": {"106": {"kills": 5, "seen": True}},
            "extra_unneeded_field": True,  # Edge case: unknown field
        }

        codex = self.db.get_codex(self.user_id)

        # Verify defaults are present
        self.assertIn("atlas", codex)
        self.assertIn("armory", codex)

        # Verify specific fields
        self.assertEqual(codex["bestiary"]["106"]["kills"], 5)
        self.assertEqual(codex["user_id"], self.user_id)

        # Original field should still exist
        self.assertTrue(codex["extra_unneeded_field"])


if __name__ == "__main__":
    unittest.main()

# Trigger CI to bypass Codacy 503 error

# Trigger CI to bypass Codacy 503 error 2

# Trigger CI to bypass Codacy 503 error 3
