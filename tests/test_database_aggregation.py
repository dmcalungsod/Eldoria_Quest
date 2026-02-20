
import json
import unittest
from unittest.mock import MagicMock, patch

from database.database_manager import DatabaseManager


class TestDatabaseAggregation(unittest.TestCase):
    def setUp(self):
        # Mock the MongoClient
        self.mock_client = MagicMock()
        self.mock_db = MagicMock()
        self.mock_client.__getitem__.return_value = self.mock_db

        # Collections map
        self.collections = {}

        def get_collection(name):
            if name not in self.collections:
                self.collections[name] = MagicMock()
            return self.collections[name]

        self.mock_db.__getitem__.side_effect = get_collection

        # Patch MongoClient
        self.mongo_patcher = patch("database.database_manager.MongoClient", return_value=self.mock_client)
        self.mongo_patcher.start()

        # Reset singleton
        DatabaseManager._instance = None
        DatabaseManager._initialized = False
        self.db = DatabaseManager()

    def tearDown(self):
        self.mongo_patcher.stop()
        DatabaseManager._instance = None

    def test_get_combat_context_bundle_query_count(self):
        discord_id = 12345

        # Access collections via mock_db to trigger the side effect and populate self.collections
        # We don't need to setup find/find_one returns because they shouldn't be called,
        # but mocking them prevents errors if they ARE called.
        self.mock_db["players"].find_one.return_value = None
        self.mock_db["stats"].find_one.return_value = None
        self.mock_db["active_buffs"].find.return_value = []
        self.mock_db["player_skills"].find.return_value = []

        # Setup aggregate return
        # Structure: [{ ...player_fields..., stats_docs: [...], buffs: [...], player_skills: [...] }]
        mock_agg_result = [{
            "discord_id": discord_id,
            "name": "Hero",
            "current_hp": 100,
            "current_mp": 50,
            "stats_docs": [{"stats_json": json.dumps({"STR": 10})}],
            "buffs": [{"name": "Might", "amount": 5}],
            "player_skills": [{"skill_key": "fireball", "skill_level": 2}],
            "active_session": [{"location_id": "forest"}]
        }]

        # aggregate returns a cursor, which is iterable.
        self.mock_db["players"].aggregate.return_value = mock_agg_result

        # Ensure skill cache is populated so we can resolve the skill
        self.db._skill_cache = {
            "fireball": {
                "key_id": "fireball",
                "name": "Fireball",
                "type": "Active",
                "mp_cost": 10
            }
        }

        # Execute
        result = self.db.get_combat_context_bundle(discord_id)

        # Check call counts
        # Expected:
        # players.aggregate -> 1
        # others -> 0

        print(f"players.aggregate: {self.collections['players'].aggregate.call_count}")
        print(f"players.find_one: {self.collections['players'].find_one.call_count}")
        print(f"stats.find_one: {self.collections['stats'].find_one.call_count}")
        print(f"active_buffs.find: {self.collections['active_buffs'].find.call_count}")
        print(f"player_skills.find: {self.collections['player_skills'].find.call_count}")

        self.assertEqual(self.collections['players'].aggregate.call_count, 1, "Should use aggregation")
        self.assertEqual(self.collections['players'].find_one.call_count, 0, "Should not use find_one on players")
        self.assertEqual(self.collections['stats'].find_one.call_count, 0, "Should not use find_one on stats")
        self.assertEqual(self.collections['active_buffs'].find.call_count, 0, "Should not use find on active_buffs")
        self.assertEqual(self.collections['player_skills'].find.call_count, 0, "Should not use find on player_skills")

        # Check Result correctness
        self.assertIsNotNone(result)
        self.assertEqual(result["player"]["name"], "Hero")
        self.assertEqual(result["player"]["current_hp"], 100)
        # Check that joined fields are cleaned up from player row
        self.assertNotIn("stats_docs", result["player"])
        self.assertNotIn("buffs", result["player"])
        self.assertNotIn("player_skills", result["player"])
        self.assertNotIn("active_session", result["player"])

        # Check Stats
        self.assertEqual(result["stats"]["STR"], 10)

        # Check Buffs
        self.assertEqual(len(result["buffs"]), 1)
        self.assertEqual(result["buffs"][0]["name"], "Might")

        # Check Skills
        self.assertEqual(len(result["skills"]), 1)
        self.assertEqual(result["skills"][0]["name"], "Fireball")
        self.assertEqual(result["skills"][0]["skill_level"], 2)

        # Check Active Session
        self.assertIsNotNone(result.get("active_session"))
        self.assertEqual(result["active_session"]["location_id"], "forest")

        # Verify Pipeline Structure (ensure _id projection prevents data leak)
        call_args = self.mock_db["players"].aggregate.call_args
        pipeline = call_args[0][0] # first arg is pipeline list

        # Check for stats lookup projection
        stats_lookup = next(stage["$lookup"] for stage in pipeline if stage.get("$lookup", {}).get("as") == "stats_docs")
        self.assertIn("pipeline", stats_lookup)
        stats_pipeline = stats_lookup["pipeline"]
        self.assertTrue(any("$project" in stage and stage["$project"] == {"_id": 0} for stage in stats_pipeline), "Stats lookup should project out _id")

        # Check for buffs lookup projection
        buffs_lookup = next(stage["$lookup"] for stage in pipeline if stage.get("$lookup", {}).get("as") == "buffs")
        buffs_pipeline = buffs_lookup["pipeline"]
        self.assertTrue(any("$project" in stage and stage["$project"] == {"_id": 0} for stage in buffs_pipeline), "Buffs lookup should project out _id")

        # Check for player_skills lookup projection
        skills_lookup = next(stage["$lookup"] for stage in pipeline if stage.get("$lookup", {}).get("as") == "player_skills")
        skills_pipeline = skills_lookup["pipeline"]
        self.assertTrue(any("$project" in stage and stage["$project"] == {"_id": 0} for stage in skills_pipeline), "Skills lookup should project out _id")

        # Check for active_session lookup projection
        session_lookup = next(stage["$lookup"] for stage in pipeline if stage.get("$lookup", {}).get("as") == "active_session")
        session_pipeline = session_lookup["pipeline"]
        self.assertTrue(any("$project" in stage and stage["$project"] == {"_id": 0} for stage in session_pipeline), "Session lookup should project out _id")

if __name__ == "__main__":
    unittest.main()
