import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock pymongo globally
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.collection"] = MagicMock()
sys.modules["pymongo.results"] = MagicMock()

# Adjust path to include the root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.guild_system.quest_system import QuestSystem  # noqa: E402


class TestQuestSystemCoverage(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.quest_system = QuestSystem(self.mock_db)
        self.user_id = 12345

        # Ensure reward system is mocked
        self.quest_system.reward_system = MagicMock()

    def test_get_available_quests_rank_filtering(self):
        """Test that quests are filtered by rank correctly."""
        # Setup: Player is Rank D
        self.mock_db.get_guild_member_field.return_value = "D"
        self.mock_db.get_player_quest_ids.return_value = []

        # Mock quests
        # We need to ensure the query works as expected
        quests = [
            {"id": 1, "tier": "F", "exclusive_group": None, "prerequisites": []},
            {"id": 2, "tier": "D", "exclusive_group": None, "prerequisites": []},
            {"id": 3, "tier": "C", "exclusive_group": None, "prerequisites": []},
        ]

        # When finding quests, we return based on tier filter
        def mock_find(query, projection=None):
            if "tier" in query and "$in" in query["tier"]:
                allowed = query["tier"]["$in"]
                return [q for q in quests if q["tier"] in allowed]
            # For player quests query
            if "discord_id" in query:
                return []
            return []

        self.mock_db._col.return_value.find.side_effect = mock_find

        available = self.quest_system.get_available_quests(self.user_id)
        available_ids = [q["id"] for q in available]

        self.assertIn(1, available_ids)
        self.assertIn(2, available_ids)
        self.assertNotIn(3, available_ids)

    def test_get_available_quests_prerequisites(self):
        """Test prerequisite filtering."""
        self.mock_db.get_guild_member_field.return_value = "F"
        self.mock_db.get_player_quest_ids.return_value = []

        q2 = {"id": 2, "tier": "F", "prerequisites": [1], "exclusive_group": None}
        quests = [q2]

        # Case 1: Prereq not met
        def mock_find_1(query, projection=None):
            if "tier" in query:
                return quests
            if "discord_id" in query:
                return []  # No completed quests
            return []

        self.mock_db._col.return_value.find.side_effect = mock_find_1

        available = self.quest_system.get_available_quests(self.user_id)
        self.assertEqual(len(available), 0)

        # Case 2: Prereq met
        def mock_find_2(query, projection=None):
            if "tier" in query:
                return quests
            if "discord_id" in query:
                return [{"quest_id": 1, "status": "completed"}]
            return []

        self.mock_db._col.return_value.find.side_effect = mock_find_2

        available = self.quest_system.get_available_quests(self.user_id)
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0]["id"], 2)

    def test_get_quest_details_json_error(self):
        """Test handling of malformed JSON in quest details."""
        self.mock_db._col.return_value.find_one.return_value = {
            "id": 1,
            "objectives": "{invalid_json",
            "rewards": "{invalid_json",
        }

        details = self.quest_system.get_quest_details(1)
        self.assertEqual(details["objectives"], {})
        self.assertEqual(details["rewards"], {})

    def test_get_player_quests_json_error(self):
        """Test handling of malformed JSON in player quests."""
        # find returns the player quest row
        self.mock_db._col.return_value.find.return_value = [
            {"quest_id": 1, "status": "in_progress", "progress": "{bad"}
        ]
        # find_one returns the quest definition
        self.mock_db._col.return_value.find_one.return_value = {
            "id": 1,
            "title": "Test",
            "objectives": "{bad",
        }

        quests = self.quest_system.get_player_quests(self.user_id)
        self.assertEqual(len(quests), 1)
        self.assertEqual(quests[0]["progress"], {})
        self.assertEqual(quests[0]["objectives"], {})

    def test_accept_quest_security_check(self):
        """Test rank security check preventing acceptance."""
        self.mock_db.get_guild_member_field.return_value = "F"

        # Quest is Rank A
        quest = {"id": 1, "tier": "A", "objectives": "{}", "exclusive_group": None}

        def mock_find_one(query, projection=None):
            # Check for existing
            if "discord_id" in query:
                return None
            # Check for quest definition
            if "id" in query:
                return quest
            return None

        self.mock_db._col.return_value.find_one.side_effect = mock_find_one

        result = self.quest_system.accept_quest(self.user_id, 1)
        self.assertFalse(result)

    def test_accept_quest_json_error(self):
        """Test handling of invalid objectives JSON during accept."""
        self.mock_db.get_guild_member_field.return_value = "F"
        quest = {"id": 1, "tier": "F", "objectives": "{bad", "exclusive_group": None}

        def mock_find_one(query, projection=None):
            if "discord_id" in query:
                return None
            if "id" in query:
                return quest
            return None

        self.mock_db._col.return_value.find_one.side_effect = mock_find_one

        result = self.quest_system.accept_quest(self.user_id, 1)
        self.assertFalse(result)

    def test_update_progress_invalid_db_json(self):
        """Test update_progress when DB has invalid JSON."""
        self.mock_db._col.return_value.find_one.return_value = {"progress": "{bad"}

        result = self.quest_system.update_progress(self.user_id, 1, "kill", "slime")
        self.assertFalse(result)

    @patch("game_systems.guild_system.quest_system.TournamentSystem")
    def test_complete_quest_success(self, MockTournament):
        """Test successful quest completion."""
        # 1. find_one player quest
        # 2. find_one quest definition
        self.mock_db._col.return_value.find_one.side_effect = [
            {"progress": '{"kill": {"slime": 5}}', "status": "in_progress"},  # pq
            {"objectives": '{"kill": {"slime": 5}}', "rewards": '{"gold": 100}'},  # quest
        ]

        # Mock update result
        mock_result = MagicMock()
        mock_result.modified_count = 1
        self.mock_db._col.return_value.update_one.return_value = mock_result

        self.quest_system.reward_system.grant_rewards.return_value = "Rewards granted"

        success, msg = self.quest_system.complete_quest(self.user_id, 1)

        self.assertTrue(success)
        self.assertEqual(msg, "Rewards granted")
        MockTournament.return_value.record_action.assert_called()

    def test_complete_quest_race_condition(self):
        """Test race condition handling during completion."""
        self.mock_db._col.return_value.find_one.side_effect = [
            {"progress": '{"kill": {"slime": 5}}', "status": "in_progress"},
            {"objectives": '{"kill": {"slime": 5}}', "rewards": "{}"},
        ]

        # Simulate update affecting 0 rows (another process changed it)
        mock_result = MagicMock()
        mock_result.modified_count = 0
        self.mock_db._col.return_value.update_one.return_value = mock_result

        success, msg = self.quest_system.complete_quest(self.user_id, 1)

        self.assertFalse(success)
        self.assertIn("already completed", msg)

    def test_complete_quest_invalid_rewards(self):
        """Test completion with invalid reward JSON."""
        self.mock_db._col.return_value.find_one.side_effect = [
            {"progress": "{}", "status": "in_progress"},
            {"objectives": "{}", "rewards": "{bad"},
        ]

        success, msg = self.quest_system.complete_quest(self.user_id, 1)

        self.assertFalse(success)
        self.assertIn("System error", msg)


if __name__ == "__main__":
    unittest.main()
