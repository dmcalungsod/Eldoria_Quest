import unittest
import os
import sys
from unittest.mock import MagicMock

# Ensure root dir is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.player.level_up import LevelUpSystem
from game_systems.player.player_stats import PlayerStats

class TestLevelUpSystem(unittest.TestCase):
    def setUp(self):
        self.stats = PlayerStats()
        self.system = LevelUpSystem(self.stats, level=1, exp=0, exp_to_next=100)

    def test_add_exp_no_level_up(self):
        # Add 50 XP (Level 1 requires 100)
        leveled_up = self.system.add_exp(50)
        
        self.assertFalse(leveled_up)
        self.assertEqual(self.system.level, 1)
        self.assertEqual(self.system.exp, 50)

    def test_add_exp_with_level_up(self):
        # Add 120 XP (Total 120, Level 1 requires 100)
        leveled_up = self.system.add_exp(120)
        
        self.assertTrue(leveled_up)
        self.assertEqual(self.system.level, 2)
        # exp_to_next should update: 200 * 2^2 + 800 * 2 = 800 + 1600 = 2400
        self.assertEqual(self.system.exp_to_next, 2400)
        self.assertEqual(self.system.exp, 20) # 120 - 100

    def test_to_dict_from_dict(self):
        self.system.add_exp(50)
        data = self.system.to_dict()
        
        new_system = LevelUpSystem.from_dict(data)
        self.assertEqual(new_system.level, 1)
        self.assertEqual(new_system.exp, 50)
        self.assertEqual(new_system.exp_to_next, 100)

if __name__ == "__main__":
    unittest.main()
