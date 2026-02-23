import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager


class TestDatabaseOptimization(unittest.TestCase):
    def setUp(self):
        # Mock the MongoClient
        self.mock_client = MagicMock()
        self.mock_db = MagicMock()
        self.mock_client.__getitem__.return_value = self.mock_db

        # Dynamic attribute access for collections
        def get_collection(name):
            # Return a new mock for each collection, or reuse if already accessed
            if not hasattr(self.mock_db, f"_{name}_col"):
                setattr(self.mock_db, f"_{name}_col", MagicMock())
            return getattr(self.mock_db, f"_{name}_col")

        self.mock_db.__getitem__.side_effect = get_collection

        # Patch MongoClient
        self.mongo_patcher = patch(
            "database.database_manager.MongoClient", return_value=self.mock_client
        )
        self.mongo_patcher.start()

        # Reset singleton
        DatabaseManager._instance = None
        DatabaseManager._initialized = False
        self.db = DatabaseManager()

    def tearDown(self):
        self.mongo_patcher.stop()
        DatabaseManager._instance = None

    def test_get_combat_context_bundle_optimization(self):
        discord_id = 12345

        # Mock aggregation result used in the new implementation
        mock_agg_result = [
            {
                "discord_id": discord_id,
                "name": "Test",
                "stats_docs": [{"stats_json": "{}"}],
                "buffs": [],
                "player_skills": [
                    {"skill_key": "skill_1", "skill_level": 1},
                    {"skill_key": "skill_2", "skill_level": 1},
                    {"skill_key": "skill_3", "skill_level": 1},
                ],
            }
        ]
        self.mock_db["players"].aggregate.return_value = mock_agg_result

        # Setup find return value (cursor) for optimized version
        mock_cursor = [
            {"key_id": "skill_1", "type": "Active", "name": "Skill 1"},
            {"key_id": "skill_2", "type": "Active", "name": "Skill 2"},
            {"key_id": "skill_3", "type": "Active", "name": "Skill 3"},
        ]
        self.mock_db["skills"].find.return_value = mock_cursor

        # Also mock find_one for the unoptimized version
        self.mock_db["skills"].find_one.side_effect = [
            {"key_id": "skill_1", "type": "Active", "name": "Skill 1"},
            {"key_id": "skill_2", "type": "Active", "name": "Skill 2"},
            {"key_id": "skill_3", "type": "Active", "name": "Skill 3"},
        ]

        # Execute
        self.db.get_combat_context_bundle(discord_id)

        # Verification
        find_calls = self.mock_db["skills"].find.call_count
        find_one_calls = self.mock_db["skills"].find_one.call_count

        # The optimization goal: 1 find call, 0 find_one calls
        # Currently, it should fail with find_calls=0 and find_one_calls=3
        self.assertEqual(find_calls, 1, f"Expected 1 find call, got {find_calls}")
        self.assertEqual(
            find_one_calls, 0, f"Expected 0 find_one calls, got {find_one_calls}"
        )

    def test_get_combat_skills_optimization(self):
        discord_id = 12345

        # Mock player skills (3 skills)
        self.mock_db["player_skills"].find.return_value = [
            {"skill_key": "skill_1", "skill_level": 1},
            {"skill_key": "skill_2", "skill_level": 1},
            {"skill_key": "skill_3", "skill_level": 1},
        ]

        # Setup find return value (cursor) for optimized version
        mock_cursor = [
            {"key_id": "skill_1", "type": "Active", "name": "Skill 1"},
            {"key_id": "skill_2", "type": "Active", "name": "Skill 2"},
            {"key_id": "skill_3", "type": "Active", "name": "Skill 3"},
        ]
        self.mock_db["skills"].find.return_value = mock_cursor

        # Execute
        self.db.get_combat_skills(discord_id)

        # Verification
        find_calls = self.mock_db["skills"].find.call_count
        find_one_calls = self.mock_db["skills"].find_one.call_count

        self.assertEqual(find_calls, 1, f"Expected 1 find call, got {find_calls}")
        self.assertEqual(
            find_one_calls, 0, f"Expected 0 find_one calls, got {find_one_calls}"
        )

    def test_get_player_skills_optimization(self):
        discord_id = 12345

        # Mock player skills (3 skills)
        self.mock_db["player_skills"].find.return_value = [
            {"skill_key": "skill_1", "skill_level": 1, "skill_exp": 10},
            {"skill_key": "skill_2", "skill_level": 1, "skill_exp": 20},
            {"skill_key": "skill_3", "skill_level": 1, "skill_exp": 30},
        ]

        # Setup find return value (cursor) for optimized version
        mock_cursor = [
            {"key_id": "skill_1", "type": "Active", "name": "Skill 1"},
            {"key_id": "skill_2", "type": "Passive", "name": "Skill 2"},
            {"key_id": "skill_3", "type": "Active", "name": "Skill 3"},
        ]
        self.mock_db["skills"].find.return_value = mock_cursor

        # Execute
        self.db.get_player_skills(discord_id)

        # Verification
        find_calls = self.mock_db["skills"].find.call_count
        find_one_calls = self.mock_db["skills"].find_one.call_count

        # get_combat_context_bundle might have been called in previous test but setUp resets db wrapper.
        # But mock_db is reused? No, setUp resets mocks.

        self.assertEqual(find_calls, 1, f"Expected 1 find call, got {find_calls}")
        self.assertEqual(
            find_one_calls, 0, f"Expected 0 find_one calls, got {find_one_calls}"
        )


if __name__ == "__main__":
    unittest.main()
