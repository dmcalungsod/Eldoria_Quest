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

    def test_s_rank_promotion_requirements(self):
        # Setup: Player is Rank S, wanting to go to SS.
        discord_id = 12345

        # 1. Test Ineligibility (Low Stats)
        self.mock_db.get_guild_member.return_value = {
            "rank": "S",
            "quests_completed": 100,  # Requirement: 500
            "boss_kills": 0,  # Requirement: 20
            "elite_kills": 0,  # Requirement: 50
        }

        eligible = self.rank_system.check_promotion_eligibility(discord_id)
        self.assertFalse(eligible, "Rank S should NOT be eligible with low stats.")

        # 2. Test Eligibility (Met Requirements)
        self.mock_db.get_guild_member.return_value = {
            "rank": "S",
            "quests_completed": 501,
            "boss_kills": 21,
            "elite_kills": 51,
        }
        eligible = self.rank_system.check_promotion_eligibility(discord_id)
        self.assertTrue(eligible, "Rank S SHOULD be eligible with sufficient stats.")

    def test_ss_rank_promotion_requirements(self):
        # Setup: Player is Rank SS, wanting to go to SSS.
        discord_id = 12345

        # 1. Test Ineligibility (Low Stats)
        self.mock_db.get_guild_member.return_value = {
            "rank": "SS",
            "quests_completed": 999,  # Requirement: 1000
            "boss_kills": 49,  # Requirement: 50
            "elite_kills": 99,  # Requirement: 100
        }

        eligible = self.rank_system.check_promotion_eligibility(discord_id)
        self.assertFalse(eligible, "Rank SS should NOT be eligible with low stats.")

        # 2. Test Eligibility (Met Requirements)
        self.mock_db.get_guild_member.return_value = {
            "rank": "SS",
            "quests_completed": 1001,
            "boss_kills": 51,
            "elite_kills": 101,
        }
        eligible = self.rank_system.check_promotion_eligibility(discord_id)
        self.assertTrue(eligible, "Rank SS SHOULD be eligible with sufficient stats.")


if __name__ == "__main__":
    unittest.main()
