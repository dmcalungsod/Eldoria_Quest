import json
import unittest
import sys
import os
from unittest.mock import MagicMock

# Add root to path
sys.path.append(os.getcwd())

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from pathlib import Path  # noqa: E402
from game_systems.guild_system.rank_system import RankSystem  # noqa: E402


class TestRankBalance(unittest.TestCase):
    def test_quest_counts_are_achievable(self):
        # Load quests.json directly
        data_path = Path("game_systems/data/quests.json")
        with open(data_path, "r", encoding="utf-8") as f:
            quests = json.load(f)

        total_quests_available = len(quests)
        print(f"Total Quests Available: {total_quests_available}")

        # Check each rank
        for rank, data in RankSystem.RANKS.items():
            reqs = data.get("requirements", {})
            quest_req = reqs.get("quests_completed", 0)

            if quest_req > 0:
                print(f"Rank {rank} requires {quest_req} quests.")
                self.assertLessEqual(
                    quest_req,
                    total_quests_available,
                    f"Rank {rank} requires {quest_req} quests, but only {total_quests_available} exist!",
                )


if __name__ == "__main__":
    unittest.main()
