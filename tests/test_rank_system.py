"""
Rank System Tests
-----------------
Tests guild rank progression requirements.
"""

import sys
import unittest
from unittest.mock import MagicMock

# Mock pymongo and its errors
mock_pymongo = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = MagicMock()

from game_systems.guild_system.rank_system import RankSystem  # noqa: E402

class TestRankSystem(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.rank_system = RankSystem(self.mock_db)

    def test_rank_f_requirements(self):
        # Rank F -> E requires 3 quests and 25 normal kills

        # Case 1: Not enough quests
        self.mock_db.get_guild_member.return_value = {
            "rank": "F", "quests_completed": 2, "normal_kills": 30, "elite_kills": 0, "boss_kills": 0
        }
        self.assertFalse(self.rank_system.check_promotion_eligibility(123))

        # Case 2: Not enough kills (Overlap scenario check)
        self.mock_db.get_guild_member.return_value = {
            "rank": "F", "quests_completed": 3, "normal_kills": 18, "elite_kills": 0, "boss_kills": 0
        }
        self.assertFalse(self.rank_system.check_promotion_eligibility(123))

        # Case 3: Meets requirements
        self.mock_db.get_guild_member.return_value = {
            "rank": "F", "quests_completed": 3, "normal_kills": 25, "elite_kills": 0, "boss_kills": 0
        }
        self.assertTrue(self.rank_system.check_promotion_eligibility(123))

    def test_rank_e_requirements(self):
        # Rank E -> D requires 10 quests, 80 normal kills, 5 elite kills

        # Case 1: Not enough kills
        self.mock_db.get_guild_member.return_value = {
            "rank": "E", "quests_completed": 10, "normal_kills": 60, "elite_kills": 5, "boss_kills": 0
        }
        self.assertFalse(self.rank_system.check_promotion_eligibility(123))

        # Case 2: Not enough elite kills
        self.mock_db.get_guild_member.return_value = {
            "rank": "E", "quests_completed": 10, "normal_kills": 80, "elite_kills": 4, "boss_kills": 0
        }
        self.assertFalse(self.rank_system.check_promotion_eligibility(123))

        # Case 3: Meets requirements
        self.mock_db.get_guild_member.return_value = {
            "rank": "E", "quests_completed": 10, "normal_kills": 80, "elite_kills": 5, "boss_kills": 0
        }
        self.assertTrue(self.rank_system.check_promotion_eligibility(123))

    def test_rank_d_requirements(self):
        # Rank D -> C requires 20 quests, 250 normal kills, 20 elite kills, 1 boss kill

        # Case 1: Not enough kills
        self.mock_db.get_guild_member.return_value = {
            "rank": "D", "quests_completed": 20, "normal_kills": 200, "elite_kills": 20, "boss_kills": 1
        }
        self.assertFalse(self.rank_system.check_promotion_eligibility(123))

        # Case 2: Meets requirements
        self.mock_db.get_guild_member.return_value = {
            "rank": "D", "quests_completed": 20, "normal_kills": 250, "elite_kills": 20, "boss_kills": 1
        }
        self.assertTrue(self.rank_system.check_promotion_eligibility(123))

if __name__ == '__main__':
    unittest.main()
