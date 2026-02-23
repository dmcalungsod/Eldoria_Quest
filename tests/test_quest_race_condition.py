import os
import sys
import unittest
from unittest.mock import MagicMock

# Mock pymongo before importing anything that uses it
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.guild_system.quest_system import QuestSystem  # noqa: E402


class TestQuestRaceCondition(unittest.TestCase):
    def setUp(self):
        # We need to patch DatabaseManager because QuestSystem instantiates it or uses it.
        # But QuestSystem takes db_manager in __init__.
        self.mock_db = MagicMock()

        # Patch the actual DatabaseManager class if needed, but we are passing a mock.
        self.quest_system = QuestSystem(self.mock_db)

        # Mock RewardSystem inside QuestSystem
        # QuestSystem.__init__ creates self.reward_system = RewardSystem(db_manager)
        # We need to mock that instance method.
        self.quest_system.reward_system = MagicMock()

    def test_complete_quest_race_condition(self):
        """
        Simulates a race condition where two processes attempt to complete the same quest.
        Process A (this test) reads the quest as 'in_progress'.
        Process B (simulated) updates the quest to 'completed' via DB update (modified_count=0 for A).
        Process A should NOT grant rewards if update fails.
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
        mock_player_quests_col.find_one.return_value = {
            "discord_id": user_id,
            "quest_id": quest_id,
            "status": "in_progress",
            "progress": '{"slay": {"Goblin": 1}}',
        }

        # 2. Mock Quest Data (Valid)
        mock_quests_col.find_one.return_value = {
            "id": quest_id,
            "tier": "F",
            "objectives": '{"slay": {"Goblin": 1}}',
            "rewards": '{"gold": 100}',
        }

        # 3. Simulate Race Condition: update_one returns modified_count=0
        # This means the document was NOT updated (e.g., status changed by another thread/process)
        mock_update_result = MagicMock()
        mock_update_result.modified_count = 0
        mock_player_quests_col.update_one.return_value = mock_update_result

        # EXECUTE
        success, message = self.quest_system.complete_quest(user_id, quest_id)

        # VERIFY
        print(f"\n[TEST] Success: {success}, Message: {message}")
        print(
            f"[TEST] Rewards Granted Call Count: {self.quest_system.reward_system.grant_rewards.call_count}"
        )

        if self.quest_system.reward_system.grant_rewards.call_count > 0:
            print(
                "[VULNERABLE] Rewards were granted despite update failure (Race Condition Exploit Successful)."
            )
        else:
            print("[SECURE] Rewards were NOT granted when update failed.")

        # For verification, we assert that the vulnerability is FIXED (so we expect 0 calls)
        self.assertEqual(
            self.quest_system.reward_system.grant_rewards.call_count,
            0,
            "Fix failed: Rewards granted despite update failure.",
        )


if __name__ == "__main__":
    unittest.main()
