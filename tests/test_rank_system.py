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
        self.mock_db.get_exploration_stats.return_value = {"total_expeditions": 2}

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
        self.mock_db.get_exploration_stats.return_value = {"total_expeditions": 5}

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
        # Rank D -> C requires 20 quests, 300 normal kills, 20 elite kills, 1 boss kill
        self.mock_db.get_exploration_stats.return_value = {"total_expeditions": 10}

        # Case 1: Not enough kills (Testing 299 < 300)
        self.mock_db.get_guild_member.return_value = {
            "rank": "D",
            "quests_completed": 20,
            "normal_kills": 299,
            "elite_kills": 20,
            "boss_kills": 1,
        }
        self.assertFalse(self.rank_system.check_promotion_eligibility(123))

        # Case 2: Meets requirements (300)
        self.mock_db.get_guild_member.return_value = {
            "rank": "D",
            "quests_completed": 20,
            "normal_kills": 300,
            "elite_kills": 20,
            "boss_kills": 1,
        }
        self.assertTrue(self.rank_system.check_promotion_eligibility(123))

    def test_rank_c_requirements(self):
        # Rank C -> B requires 30 quests, 450 normal kills, 40 elite kills, 2 boss kills
        self.mock_db.get_exploration_stats.return_value = {"total_expeditions": 15}

        # Case 1: Not enough kills (Testing 449 < 450)
        self.mock_db.get_guild_member.return_value = {
            "rank": "C",
            "quests_completed": 30,
            "normal_kills": 449,
            "elite_kills": 40,
            "boss_kills": 2,
        }
        self.assertFalse(self.rank_system.check_promotion_eligibility(123))

        # Case 2: Meets requirements (450 normal kills, 40 elite kills)
        self.mock_db.get_guild_member.return_value = {
            "rank": "C",
            "quests_completed": 30,
            "normal_kills": 450,
            "elite_kills": 40,
            "boss_kills": 2,
        }
        self.assertTrue(self.rank_system.check_promotion_eligibility(123))

    def test_rank_b_requirements(self):
        # Rank B -> A requires 40 quests, 600 normal kills, 65 elite kills, 4 boss kills
        self.mock_db.get_exploration_stats.return_value = {"total_expeditions": 20}

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

    def test_rank_a_requirements(self):
        # Rank A -> S requires 50 quests, 800 normal kills, 80 elite kills, 6 boss kills
        self.mock_db.get_exploration_stats.return_value = {"total_expeditions": 30}

        # Case 1: Not enough boss kills (5 < 6)
        self.mock_db.get_guild_member.return_value = {
            "rank": "A",
            "quests_completed": 50,
            "normal_kills": 800,
            "elite_kills": 80,
            "boss_kills": 5,
        }
        self.assertFalse(self.rank_system.check_promotion_eligibility(123))

        # Case 2: Meets requirements (6 boss kills)
        self.mock_db.get_guild_member.return_value = {
            "rank": "A",
            "quests_completed": 50,
            "normal_kills": 800,
            "elite_kills": 80,
            "boss_kills": 6,
        }
        self.assertTrue(self.rank_system.check_promotion_eligibility(123))

    def test_rank_s_requirements(self):
        # Rank S -> SS requires 60 quests, 1000 normal kills, 120 elite kills, 10 boss kills
        self.mock_db.get_exploration_stats.return_value = {"total_expeditions": 40}

        # Case 1: Not enough boss kills (9 < 10)
        self.mock_db.get_guild_member.return_value = {
            "rank": "S",
            "quests_completed": 60,
            "normal_kills": 1000,
            "elite_kills": 120,
            "boss_kills": 9,
        }
        self.assertFalse(self.rank_system.check_promotion_eligibility(123))

        # Case 2: Meets requirements (10 boss kills)
        self.mock_db.get_guild_member.return_value = {
            "rank": "S",
            "quests_completed": 60,
            "normal_kills": 1000,
            "elite_kills": 120,
            "boss_kills": 10,
        }
        self.assertTrue(self.rank_system.check_promotion_eligibility(123))

    def test_rank_ss_requirements(self):
        # Rank SS -> SSS requires 65 quests, 1500 normal kills, 200 elite kills, 20 boss kills
        self.mock_db.get_exploration_stats.return_value = {"total_expeditions": 50}

        # Case 1: Not enough boss kills (19 < 20)
        self.mock_db.get_guild_member.return_value = {
            "rank": "SS",
            "quests_completed": 65,
            "normal_kills": 1500,
            "elite_kills": 200,
            "boss_kills": 19,
        }
        self.assertFalse(self.rank_system.check_promotion_eligibility(123))

        # Case 2: Meets requirements (20 boss kills)
        self.mock_db.get_guild_member.return_value = {
            "rank": "SS",
            "quests_completed": 65,
            "normal_kills": 1500,
            "elite_kills": 200,
            "boss_kills": 20,
        }
        self.assertTrue(self.rank_system.check_promotion_eligibility(123))


if __name__ == "__main__":
    unittest.main()
