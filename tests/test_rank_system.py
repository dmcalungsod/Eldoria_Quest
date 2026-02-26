"""
Rank System Tests
-----------------
Tests guild rank progression requirements.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

# Mock pymongo and its errors
mock_pymongo = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = MagicMock()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from game_systems.guild_system.rank_system import RankSystem  # noqa: E402


class TestRankSystem(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.rank_system = RankSystem(self.mock_db)

    def test_rank_f_requirements(self):
        # Rank F -> E requires 3 quests and 50 normal kills

        # Case 1: Not enough quests
        self.mock_db.get_guild_member.return_value = {
            "rank": "F",
            "quests_completed": 2,
            "normal_kills": 60,
            "elite_kills": 0,
            "boss_kills": 0,
        }
        self.assertFalse(self.rank_system.check_promotion_eligibility(123))

        # Case 2: Not enough kills (Overlap scenario check)
        self.mock_db.get_guild_member.return_value = {
            "rank": "F",
            "quests_completed": 3,
            "normal_kills": 49,
            "elite_kills": 0,
            "boss_kills": 0,
        }
        self.assertFalse(self.rank_system.check_promotion_eligibility(123))

        # Case 3: Meets requirements
        self.mock_db.get_guild_member.return_value = {
            "rank": "F",
            "quests_completed": 3,
            "normal_kills": 50,
            "elite_kills": 0,
            "boss_kills": 0,
        }
        self.assertTrue(self.rank_system.check_promotion_eligibility(123))

    def test_rank_e_requirements(self):
        # Rank E -> D requires 10 quests, 150 normal kills, 5 elite kills

        # Case 1: Not enough kills
        self.mock_db.get_guild_member.return_value = {
            "rank": "E",
            "quests_completed": 10,
            "normal_kills": 149,
            "elite_kills": 5,
            "boss_kills": 0,
        }
        self.assertFalse(self.rank_system.check_promotion_eligibility(123))

        # Case 2: Not enough elite kills
        self.mock_db.get_guild_member.return_value = {
            "rank": "E",
            "quests_completed": 10,
            "normal_kills": 150,
            "elite_kills": 4,
            "boss_kills": 0,
        }
        self.assertFalse(self.rank_system.check_promotion_eligibility(123))

        # Case 3: Meets requirements
        self.mock_db.get_guild_member.return_value = {
            "rank": "E",
            "quests_completed": 10,
            "normal_kills": 150,
            "elite_kills": 5,
            "boss_kills": 0,
        }
        self.assertTrue(self.rank_system.check_promotion_eligibility(123))

    def test_rank_d_requirements(self):
        # Rank D -> C requires 20 quests, 250 normal kills, 20 elite kills, 1 boss kill

        # Case 1: Not enough kills
        self.mock_db.get_guild_member.return_value = {
            "rank": "D",
            "quests_completed": 20,
            "normal_kills": 240,
            "elite_kills": 20,
            "boss_kills": 1,
        }
        self.assertFalse(self.rank_system.check_promotion_eligibility(123))

        # Case 2: Meets requirements
        self.mock_db.get_guild_member.return_value = {
            "rank": "D",
            "quests_completed": 20,
            "normal_kills": 250,
            "elite_kills": 20,
            "boss_kills": 1,
        }
        self.assertTrue(self.rank_system.check_promotion_eligibility(123))

    def test_rank_b_requirements(self):
        # Rank B -> A requires 40 quests, 600 normal kills, 65 elite kills, 4 boss kills

        # Case 1: Not enough quests
        self.mock_db.get_guild_member.return_value = {
            "rank": "B",
            "quests_completed": 39,
            "normal_kills": 600,
            "elite_kills": 70,
            "boss_kills": 4,
        }
        self.assertFalse(self.rank_system.check_promotion_eligibility(123))

        # Case 2: Not enough normal kills
        self.mock_db.get_guild_member.return_value = {
            "rank": "B",
            "quests_completed": 40,
            "normal_kills": 599,
            "elite_kills": 65,
            "boss_kills": 4,
        }
        self.assertFalse(self.rank_system.check_promotion_eligibility(123))

        # Case 3: Meets requirements
        self.mock_db.get_guild_member.return_value = {
            "rank": "B",
            "quests_completed": 40,
            "normal_kills": 600,
            "elite_kills": 65,
            "boss_kills": 4,
        }
        self.assertTrue(self.rank_system.check_promotion_eligibility(123))


if __name__ == "__main__":
    unittest.main()
