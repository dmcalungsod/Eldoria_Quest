import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add repo root to path
sys.path.append(os.getcwd())

from game_systems.guild_system.quest_system import QuestSystem

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
            "objectives": '{"slay": {"Dragon": 1}}'
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

if __name__ == '__main__':
    unittest.main()
