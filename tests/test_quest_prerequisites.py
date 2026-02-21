import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock pymongo before importing anything that uses it
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Add root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game_systems.guild_system.quest_system import QuestSystem

class TestQuestPrerequisites(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        # Mock the get_available_quests implementation which uses self.db._col("quests").find
        # But wait, QuestSystem is the class under test.
        # We need to make sure we are testing the actual logic.

        # Patch the actual QuestSystem class or just use it?
        # We can use it directly, injecting the mock DB.
        self.quest_system = QuestSystem(self.mock_db)

    def test_prerequisites_logic(self):
        discord_id = 12345

        # Setup mock quests
        # Note: In real DB, find() returns a cursor.
        mock_quests = [
            {"id": 1, "title": "Quest 1", "tier": "F", "summary": "Q1", "prerequisites": []},
            {"id": 2, "title": "Quest 2", "tier": "F", "summary": "Q2", "prerequisites": [1]},
            {"id": 3, "title": "Quest 3", "tier": "F", "summary": "Q3", "prerequisites": [2]},
        ]

        # Mock DB find to return these quests
        self.mock_db._col.return_value.find.return_value = mock_quests

        # Mock Rank
        self.mock_db.get_guild_member_field.return_value = "F"

        # --- Case 1: No quests completed ---
        self.mock_db.get_player_quest_ids.return_value = set()
        self.mock_db.get_player_completed_quest_ids.return_value = set()

        # We need to re-instantiate or just call the method?
        # QuestSystem is stateless regarding quests, it fetches from DB.

        available = self.quest_system.get_available_quests(discord_id)
        available_ids = [q["id"] for q in available]
        self.assertEqual(available_ids, [1], f"Case 1 Failed. Got: {available_ids}")

        # --- Case 2: Quest 1 Completed ---
        self.mock_db.get_player_quest_ids.return_value = {1}
        self.mock_db.get_player_completed_quest_ids.return_value = {1}

        available = self.quest_system.get_available_quests(discord_id)
        available_ids = [q["id"] for q in available]
        self.assertEqual(available_ids, [2], f"Case 2 Failed. Got: {available_ids}")

        # --- Case 3: Quest 1 & 2 Completed ---
        self.mock_db.get_player_quest_ids.return_value = {1, 2}
        self.mock_db.get_player_completed_quest_ids.return_value = {1, 2}

        available = self.quest_system.get_available_quests(discord_id)
        available_ids = [q["id"] for q in available]
        self.assertEqual(available_ids, [3], f"Case 3 Failed. Got: {available_ids}")

if __name__ == "__main__":
    unittest.main()
