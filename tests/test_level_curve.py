import os
import sys
import unittest
from unittest.mock import MagicMock

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dependencies
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["discord"] = MagicMock()

from game_systems.player.level_up import LevelUpSystem  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestLevelCurve(unittest.TestCase):
    def test_xp_curve_values(self):
        """
        Verify the XP curve values for specific levels using the NEW formula:
        200 * L^2 + 800 * L
        """
        expected_values = {
            1: 1000,  # 200*1 + 800*1 = 1000
            2: 2400,  # 200*4 + 800*2 = 800 + 1600 = 2400
            5: 9000,  # 200*25 + 800*5 = 5000 + 4000 = 9000
            10: 28000,  # 200*100 + 800*10 = 20000 + 8000 = 28000
            20: 96000,  # 200*400 + 800*20 = 80000 + 16000 = 96000
        }

        stats = PlayerStats()

        for level, expected_xp in expected_values.items():
            if level == 1:
                # Level 1 is the starting state, check default
                system = LevelUpSystem(stats, level=1, exp=0, exp_to_next=1000)
                self.assertEqual(system.exp_to_next, expected_xp, f"Level {level} XP Requirement mismatch")
            else:
                # Create system just before target level
                system = LevelUpSystem(stats, level=level - 1, exp=0, exp_to_next=1000)

                # Trigger level up to reach `level` and calculate next XP requirement
                system.level_up()

                # Now at `level`. Check `exp_to_next`
                current_xp_req = system.exp_to_next
                self.assertEqual(
                    current_xp_req,
                    expected_xp,
                    f"Level {level} XP Requirement mismatch: Expected {expected_xp}, Got {current_xp_req}",
                )


if __name__ == "__main__":
    unittest.main()
