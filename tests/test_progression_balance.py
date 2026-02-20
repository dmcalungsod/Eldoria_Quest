import sys
import unittest
from unittest.mock import MagicMock

# Mock pymongo before importing DatabaseManager
sys.modules["pymongo"] = MagicMock()

from game_systems.guild_system.rank_system import RankSystem  # noqa: E402


class TestProgressionBalance(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.rank_system = RankSystem(self.mock_db)

    def test_rank_d_progression_softlock(self):
        """
        Verify that a player with reasonable progression (25 quests)
        can promote from D to C.

        Current Requirement: 40 Quests.
        Total Available Quests (F+E+D): 10+10+10 = 30.

        This test expects SUCCESS (True), meaning the system is BALANCED.
        It will FAIL currently because the requirement is 40.
        """
        # Player Data: Rank D, 25 Quests (Max possible is 30)
        # 150 Normal Kills (New Req), 20 Elite Kills (New Req), 1 Boss Kill (New Req)
        player_data = {"rank": "D", "quests_completed": 25, "normal_kills": 200, "elite_kills": 25, "boss_kills": 2}

        # Mock get_guild_member to return this player
        self.mock_db.get_guild_member.return_value = player_data

        # Check eligibility
        is_eligible = self.rank_system.check_promotion_eligibility(12345)

        # We expect this to be True after rebalancing.
        # Currently, it is False because 25 < 40.
        self.assertTrue(is_eligible, "Player with 25 quests should be eligible for Rank C promotion (Current Req: 40)")


if __name__ == "__main__":
    unittest.main()
