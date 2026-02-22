import os
import sys
import unittest
from unittest.mock import MagicMock

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo before importing anything that uses it
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from game_systems.guild_system.quest_system import QuestSystem
from game_systems.data.emojis import ERROR


class TestQuestSecurity(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.quest_system = QuestSystem(self.mock_db)

    def test_accept_quest_bypass_prevention(self):
        # Setup: Player is Rank 'F'
        user_id = 12345
        s_rank_quest_id = 999

        # Mock get_guild_member_field to return 'F'
        self.mock_db.get_guild_member_field.return_value = "F"

        # Mock database collections
        mock_quests_col = MagicMock()
        mock_player_quests_col = MagicMock()

        def mock_col(name):
            if name == "quests":
                return mock_quests_col
            elif name == "player_quests":
                return mock_player_quests_col
            return MagicMock()

        self.mock_db._col.side_effect = mock_col

        # Mock Quest Data (S-Rank Quest)
        mock_quests_col.find_one.return_value = {
            "id": s_rank_quest_id,
            "tier": "S",
            "objectives": '{"slay": {"Dragon": 1}}',
        }

        # Mock Player Quests (Player has no quests)
        mock_player_quests_col.find_one.return_value = None

        # EXECUTE: Try to accept S-Rank quest as F-Rank player
        result = self.quest_system.accept_quest(user_id, s_rank_quest_id)

        # VERIFY
        if not result:
            print("\n[SECURE] Access Denied: Rank mismatch correctly caught.")
        else:
            print("\n[CRITICAL] VULNERABILITY STILL EXISTS: F-Rank player accepted S-Rank quest!")

        self.assertFalse(result, "The security check should block this action.")

    def test_complete_quest_malformed_rewards(self):
        """
        Regression Test: Ensure quests with malformed 'rewards' JSON strings
        cannot be completed, preventing crashes or data corruption.
        """
        user_id = 12345
        quest_id = 101

        # Mock database collections
        mock_quests_col = MagicMock()
        mock_player_quests_col = MagicMock()

        def mock_col(name):
            if name == "quests":
                return mock_quests_col
            elif name == "player_quests":
                return mock_player_quests_col
            return MagicMock()

        self.mock_db._col.side_effect = mock_col

        # 1. Mock Player Quest (In Progress, ready to complete)
        # Objectives met: Slay 1 Goblin
        mock_player_quests_col.find_one.return_value = {
            "discord_id": user_id,
            "quest_id": quest_id,
            "status": "in_progress",
            "progress": '{"slay": {"Goblin": 1}}' # Valid JSON progress
        }

        # 2. Mock Quest Data (BROKEN REWARDS JSON)
        mock_quests_col.find_one.return_value = {
            "id": quest_id,
            "tier": "F",
            "objectives": '{"slay": {"Goblin": 1}}',
            "rewards": '{ "gold": 100, "xp": 50 ' # <-- MISSING CLOSING BRACE
        }

        # EXECUTE
        success, message = self.quest_system.complete_quest(user_id, quest_id)

        # VERIFY
        self.assertFalse(success, "Should fail due to malformed rewards JSON")
        self.assertIn("System error: Reward data corrupted", message)
        self.assertIn(ERROR, message)


if __name__ == "__main__":
    unittest.main()
