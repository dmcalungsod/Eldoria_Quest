import importlib
import os
import sys

sys.path.append(os.getcwd())

import unittest  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: E402


class TestQuestOptimization(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules to mock dependencies before import
        self.modules_patcher = patch.dict(
            sys.modules, {"pymongo": MagicMock(), "pymongo.errors": MagicMock(), "discord": MagicMock()}
        )
        self.modules_patcher.start()

        # Import AdventureRewards inside setUp to use mocked modules
        import game_systems.adventure.adventure_rewards

        importlib.reload(game_systems.adventure.adventure_rewards)
        self.AdventureRewards = game_systems.adventure.adventure_rewards.AdventureRewards

        # Patch dependencies
        self.patcher1 = patch("game_systems.adventure.adventure_rewards.RankSystem")
        self.patcher2 = patch("game_systems.adventure.adventure_rewards.AchievementSystem")
        self.patcher3 = patch("game_systems.adventure.adventure_rewards.FactionSystem")

        self.mock_rank = self.patcher1.start()
        self.mock_ach = self.patcher2.start()
        self.mock_faction = self.patcher3.start()

        self.mock_db = MagicMock()
        self.rewards = self.AdventureRewards(self.mock_db, 12345)
        self.mock_quest_system = MagicMock()

    def tearDown(self):
        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()
        self.modules_patcher.stop()

    def test_update_quests_aggregates_drops(self):
        # Setup
        self.mock_quest_system.get_player_quests.return_value = [
            {"id": 1, "title": "Gather Herbs", "objectives": {"collect": ["herb"]}, "flavor_text": {}}
        ]

        actual_drops = ["herb", "herb", "herb", "stone"]
        logs = []

        # Execute
        self.rewards._update_quests(self.mock_quest_system, "Goblin", actual_drops, logs)

        # Verify
        # Currently, it calls update_progress 3 times for "herb"

        # Let's count calls
        # Signature: update_progress(discord_id, quest_id, obj_type, target, amount=1)
        # args are (12345, 1, "collect", "herb")

        herb_calls = [c for c in self.mock_quest_system.update_progress.call_args_list if c.args[3] == "herb"]

        print(f"Update calls for 'herb': {len(herb_calls)}")

        # Verify optimization: Should be called ONCE
        self.assertEqual(len(herb_calls), 1)

        # Verify correct amount
        call_args = herb_calls[0]
        # Check kwargs for amount
        self.assertEqual(call_args.kwargs.get("amount"), 3)


if __name__ == "__main__":
    unittest.main()
