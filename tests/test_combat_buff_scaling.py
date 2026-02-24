import sys
import unittest
from unittest.mock import MagicMock

# Mock external dependencies
sys.modules["pymongo"] = MagicMock()
sys.modules["discord"] = MagicMock()

from game_systems.combat.combat_engine import CombatEngine


class TestCombatBuffScaling(unittest.TestCase):
    def setUp(self):
        # Create a mock player with stats
        self.mock_player = MagicMock()
        self.mock_player.hp_current = 100
        self.mock_player.stats = MagicMock()
        self.mock_player.stats.max_hp = 100

        # Define distinct base and total stats to test scaling logic
        # Base stats = 100 (original stats)
        # Total stats = 200 (e.g. from gear or existing buffs)
        self.base_stats = {
            "STR": 100,
            "END": 100,
            "DEX": 100,
            "AGI": 100,
            "MAG": 100,
            "LCK": 100,
            "HP": 100,
            "MP": 100
        }

        self.total_stats = {
            "STR": 200,
            "END": 200,
            "DEX": 200,
            "AGI": 200,
            "MAG": 200,
            "LCK": 200,
            "HP": 200,
            "MP": 200
        }

        # Initialize CombatEngine with explicit stats dicts
        self.engine = CombatEngine(
            player=self.mock_player,
            monster={"HP": 100, "name": "Dummy"},
            player_skills=[],
            player_mp=100,
            player_class_id=1,
            stats_dict=self.total_stats,
            base_stats_dict=self.base_stats
        )

    def test_percentage_buff_uses_base_stats(self):
        """
        Verify that percentage buffs (e.g. STR_percent) calculate based on BASE stats,
        not total stats. This prevents exponential compounding.
        """
        # Skill that grants +50% STR
        skill = {
            "name": "Rage",
            "buff_data": {
                "STR_percent": 0.5,
                "duration": 3
            }
        }

        # Apply the buff logic (directly calling the internal method for unit testing)
        self.engine._apply_skill_buffs(skill)

        # Check the generated buffs
        # Expect: 50% of BASE (100) = 50
        # NOT: 50% of TOTAL (200) = 100
        buffs = self.engine.new_buffs
        self.assertEqual(len(buffs), 1)

        str_buff = buffs[0]
        self.assertEqual(str_buff["stat"], "STR")
        self.assertEqual(str_buff["amount"], 50,
            f"Expected buff amount to be 50 (0.5 * base 100), but got {str_buff['amount']}")

    def test_all_stats_buff_uses_base_stats(self):
        """
        Verify that 'all_stats_percent' buffs calculate based on BASE stats.
        """
        # Skill that grants +10% to all stats
        skill = {
            "name": "Limit Break",
            "buff_data": {
                "all_stats_percent": 0.1,
                "duration": 3
            }
        }

        self.engine._apply_skill_buffs(skill)

        buffs = self.engine.new_buffs
        # Expect 6 buffs (STR, END, DEX, AGI, MAG, LCK)
        self.assertEqual(len(buffs), 6)

        for buff in buffs:
            expected_amount = 10  # 10% of base 100
            self.assertEqual(buff["amount"], expected_amount,
                f"Expected {buff['stat']} buff amount to be 10, but got {buff['amount']}")

    def test_buff_duration_parsing(self):
        """Verify duration is parsed correctly from skill data."""
        skill = {
            "name": "Short Burst",
            "buff_data": {
                "STR_percent": 0.1,
                "duration": 5
            }
        }

        self.engine._apply_skill_buffs(skill)

        buff = self.engine.new_buffs[0]
        self.assertEqual(buff["duration"], 5)

if __name__ == "__main__":
    unittest.main()
