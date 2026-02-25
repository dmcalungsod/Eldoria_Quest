import os
import sys
import unittest
from unittest.mock import MagicMock

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.guild_system.quest_system import QuestSystem  # noqa: E402


class TestQuestBranching(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.quest_system = QuestSystem(self.mock_db)
        self.user_id = 12345

        # Define Quests
        self.quest_base = {
            "id": 67,
            "title": "The Clockwork Heart: Anomaly",
            "tier": "B",
            "objectives": '{"locate": "Unit 734"}',
            "prerequisites": [],
        }
        self.quest_choice_a = {
            "id": 68,
            "title": "The Clockwork Heart: Dismantle",
            "tier": "B",
            "objectives": '{"defeat": "Unit 734"}',
            "prerequisites": [67],
            "exclusive_group": "clockwork_heart_choice",
        }
        self.quest_choice_b = {
            "id": 69,
            "title": "The Clockwork Heart: Stabilize",
            "tier": "B",
            "objectives": '{"defend": "Unit 734"}',
            "prerequisites": [67],
            "exclusive_group": "clockwork_heart_choice",
        }

        self.all_quests = [self.quest_base, self.quest_choice_a, self.quest_choice_b]

    def test_branching_logic_availability(self):
        # Setup: Player is Rank B
        self.mock_db.get_guild_member_field.return_value = "B"

        # Mock DB queries
        def mock_find(query, projection=None):
            # Simple filter simulation
            results = []
            if "tier" in query:
                # Returns all quests as we are filtering in the system usually
                results = self.all_quests
            return results

        mock_col = MagicMock()
        mock_col.find.side_effect = mock_find
        self.mock_db._col.return_value = mock_col

        # Case 1: Base quest completed. Both choices should be available.
        # Mock player quests: Base quest completed
        self.mock_db.get_player_quest_ids.return_value = [67]

        # Mock completed quests query
        mock_col.find.side_effect = None

        def mock_find_dynamic(query, projection=None):
            # Query for getting all player quests
            if "discord_id" in query and "quest_id" not in query:
                return [{"quest_id": 67, "status": "completed"}]
            if "tier" in query:
                return self.all_quests
            # Query for getting locked groups (IDs in ...)
            if "id" in query and "$in" in query["id"]:
                return [self.quest_base]  # No exclusive group
            return []

        mock_col.find.side_effect = mock_find_dynamic
        self.mock_db.get_player_quest_ids.return_value = [67]

        available = self.quest_system.get_available_quests(self.user_id)
        available_ids = [q["id"] for q in available]

        # Both 68 and 69 should be available
        self.assertIn(68, available_ids)
        self.assertIn(69, available_ids)

        # Case 2: Player has accepted Quest 68 (Choice A). Quest 69 should NOT be available.
        # Update mock to simulate Quest 68 being in progress
        self.mock_db.get_player_quest_ids.return_value = [67, 68]

        def mock_find_dynamic_2(query, projection=None):
            if "discord_id" in query and "quest_id" not in query:
                return [{"quest_id": 67, "status": "completed"}, {"quest_id": 68, "status": "in_progress"}]
            if "tier" in query:
                return self.all_quests
            if "id" in query and "$in" in query["id"]:
                # The system queries for definitions of player quests to find locked groups
                return [self.quest_base, self.quest_choice_a]
            return []

        mock_col.find.side_effect = mock_find_dynamic_2

        available = self.quest_system.get_available_quests(self.user_id)
        available_ids = [q["id"] for q in available]

        # 68 is taken, so it should not be available
        self.assertNotIn(68, available_ids)

        # 69 should be filtered out because of exclusive group conflict
        self.assertNotIn(69, available_ids)

    def test_accept_quest_exclusivity(self):
        # Setup: Player is Rank B
        self.mock_db.get_guild_member_field.return_value = "B"

        # Mock finding the quest to accept
        def mock_find_one(query, projection=None):
            q_id = query.get("id")
            if q_id == 68:
                return self.quest_choice_a
            if q_id == 69:
                return self.quest_choice_b
            if q_id == 67:
                return self.quest_base

            # Check for existing accepted quest (first check in accept_quest)
            if "discord_id" in query and "quest_id" in query and isinstance(query["quest_id"], int):
                return None

            # Check for exclusive group conflict (second check)
            if "discord_id" in query and "quest_id" in query and isinstance(query["quest_id"], dict):
                # This is the query: {"quest_id": {"$in": group_ids}}
                ids = query["quest_id"].get("$in", [])
                # If we are testing Case A, player has 68.
                if 68 in ids:
                    return {"_id": 1}  # Found conflict
                return None

            return None

        # We need to control the outcome based on the test case.
        # Let's use a side_effect that checks an external flag or just specific logic.

        self.mock_db._col.return_value.find_one.side_effect = mock_find_one

        # Mock finding quests by exclusive_group
        def mock_find(query, projection=None):
            if "exclusive_group" in query:
                return [{"id": 68}, {"id": 69}]
            return []

        self.mock_db._col.return_value.find.side_effect = mock_find

        # We need to simulate the state where user has Quest 68.
        # The mock_find_one above handles the conflict check if 68 is in the list.
        # So checking if "68 in ids" simulates "User has 68".
        # When accepting 69, the group IDs will be [68, 69].
        # So 68 is in ids. So it returns conflict.

        result = self.quest_system.accept_quest(self.user_id, 69)
        self.assertFalse(result, "Should prevent accepting mutually exclusive quest when conflict exists")

        # Case B: Player has no quests in group.
        # We need to change the mock behavior.

        def mock_find_one_clean(query, projection=None):
            q_id = query.get("id")
            if q_id == 69:
                return self.quest_choice_b

            # No existing quests found
            return None

        self.mock_db._col.return_value.find_one.side_effect = mock_find_one_clean

        # We also need to ensure insert_one is called (success)
        self.mock_db._col.return_value.insert_one = MagicMock()

        result = self.quest_system.accept_quest(self.user_id, 69)
        self.assertTrue(result, "Should allow accepting quest if no conflict")


if __name__ == "__main__":
    unittest.main()
