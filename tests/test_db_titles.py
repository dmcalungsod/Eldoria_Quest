import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock pymongo BEFORE import
sys.modules["pymongo"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager  # noqa: E402


class TestDatabaseTitles(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_db = MagicMock()
        self.mock_client.__getitem__.return_value = self.mock_db

        # Support db['collection'] syntax
        self.mock_db.__getitem__.side_effect = lambda name: getattr(self.mock_db, name)

        self.mongo_patcher = patch(
            "database.database_manager.MongoClient", return_value=self.mock_client
        )
        self.mongo_patcher.start()

        DatabaseManager._instance = None
        DatabaseManager._initialized = False
        self.db = DatabaseManager()

    def tearDown(self):
        self.mongo_patcher.stop()
        DatabaseManager._instance = None

    def test_add_title(self):
        discord_id = 123
        title = "Dragon Slayer"

        # Mock update_one result
        mock_result = MagicMock()
        mock_result.modified_count = 1
        self.mock_db.players.update_one.return_value = mock_result

        result = self.db.add_title(discord_id, title)

        self.assertTrue(result)
        self.mock_db.players.update_one.assert_called_with(
            {"discord_id": discord_id}, {"$addToSet": {"titles": title}}
        )

    def test_get_titles(self):
        discord_id = 123
        titles = ["Novice", "Expert"]

        self.mock_db.players.find_one.return_value = {"titles": titles}

        result = self.db.get_titles(discord_id)
        self.assertEqual(result, titles)

    def test_get_titles_none(self):
        discord_id = 123
        self.mock_db.players.find_one.return_value = None

        result = self.db.get_titles(discord_id)
        self.assertEqual(result, [])

    def test_set_active_title_success(self):
        discord_id = 123
        title = "Novice"

        # Mock get_titles to return list containing the title
        self.mock_db.players.find_one.side_effect = [{"titles": ["Novice"]}]

        # Mock update_one
        self.mock_db.players.update_one.return_value.modified_count = 1

        result = self.db.set_active_title(discord_id, title)

        self.assertTrue(result)
        self.mock_db.players.update_one.assert_called_with(
            {"discord_id": discord_id}, {"$set": {"active_title": title}}
        )

    def test_set_active_title_fail_ownership(self):
        discord_id = 123
        title = "God"

        # Mock get_titles to return list NOT containing the title
        self.mock_db.players.find_one.side_effect = [{"titles": ["Novice"]}]

        result = self.db.set_active_title(discord_id, title)

        self.assertFalse(result)
        # Verify update_one was NOT called to set title
        calls = self.mock_db.players.update_one.call_args_list
        set_calls = [
            c for c in calls if "$set" in c[0][1] and "active_title" in c[0][1]["$set"]
        ]
        self.assertEqual(len(set_calls), 0)

    def test_set_active_title_none(self):
        discord_id = 123
        result = self.db.set_active_title(discord_id, None)
        self.assertTrue(result)
        self.mock_db.players.update_one.assert_called_with(
            {"discord_id": discord_id}, {"$set": {"active_title": None}}
        )

    def test_get_active_title(self):
        discord_id = 123
        title = "Novice"
        self.mock_db.players.find_one.return_value = {"active_title": title}

        result = self.db.get_active_title(discord_id)
        self.assertEqual(result, title)


if __name__ == "__main__":
    unittest.main()
