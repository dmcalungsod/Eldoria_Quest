import sys
import unittest
from unittest.mock import MagicMock

# Mock pymongo before importing DatabaseManager
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from game_systems.guild_system.rank_system import RankSystem  # noqa: E402


class TestRankProgression(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.rank_system = RankSystem(self.mock_db)
        self.mock_db.get_exploration_stats.return_value = {"total_expeditions": 50}

    def test_s_rank_promotion_requirements(self):
        # Setup: Player is Rank S, wanting to go to SS.
        discord_id = 12345

        # 1. Test Ineligibility (Low Stats)
        self.mock_db.get_guild_member.return_value = {
            "rank": "S",
            "quests_completed": 10,
            "boss_kills": 0,
            "elite_kills": 0,
        }

        eligible = self.rank_system.check_promotion_eligibility(discord_id)
        self.assertFalse(eligible, "Rank S should NOT be eligible with low stats.")

        # 2. Test Eligibility (Met Requirements)
        # S -> SS Reqs: 60 Quests, 35 Boss, 120 Elite, 1000 normal kills
        self.mock_db.get_guild_member.return_value = {
            "rank": "S",
            "quests_completed": 60,
            "normal_kills": 1000,
            "boss_kills": 35,
            "elite_kills": 120,
        }
        eligible = self.rank_system.check_promotion_eligibility(discord_id)
        self.assertTrue(eligible, "Rank S SHOULD be eligible with sufficient stats.")

    def test_ss_rank_promotion_requirements(self):
        # Setup: Player is Rank SS, wanting to go to SSS.
        discord_id = 12345

        # 1. Test Ineligibility (Low Stats)
        self.mock_db.get_guild_member.return_value = {
            "rank": "SS",
            "quests_completed": 60,
            "boss_kills": 49,
            "elite_kills": 199,
        }

        eligible = self.rank_system.check_promotion_eligibility(discord_id)
        self.assertFalse(eligible, "Rank SS should NOT be eligible with low stats.")

        # 2. Test Eligibility (Met Requirements)
        # SS -> SSS Reqs: 65 Quests, 50 Boss, 200 Elite, 1500 normal kills
        self.mock_db.get_guild_member.return_value = {
            "rank": "SS",
            "quests_completed": 65,
            "normal_kills": 1500,
            "boss_kills": 50,
            "elite_kills": 200,
        }
        eligible = self.rank_system.check_promotion_eligibility(discord_id)
        self.assertTrue(eligible, "Rank SS SHOULD be eligible with sufficient stats.")


if __name__ == "__main__":
    unittest.main()
