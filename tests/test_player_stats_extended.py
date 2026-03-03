import unittest
import os
import sys
from unittest.mock import MagicMock

# Ensure root dir is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.player.player_stats import PlayerStats, calculate_practice_threshold, calculate_tiered_bonus

class TestPlayerStats(unittest.TestCase):
    def setUp(self):
        self.stats = PlayerStats(str_base=10, end_base=10, dex_base=10)

    def test_initial_stats(self):
        self.assertEqual(self.stats.strength, 10)
        self.assertEqual(self.stats.endurance, 10)
        self.assertEqual(self.stats.dexterity, 10)

    def test_derived_stats(self):
        # Base HP is 50 + bonus from 10 END (10 * 10 = 100) = 150
        self.assertEqual(self.stats.max_hp, 150)
        # Base MP is 20 + bonus from 1 MAG (5 * 1 = 5) = 25
        self.assertEqual(self.stats.max_mp, 25)
        # Inventory: 10 + floor(10*0.5) + floor(10*0.25) = 10 + 5 + 2 = 17
        self.assertEqual(self.stats.max_inventory_slots, 17)

    def test_stat_modification(self):
        self.stats.add_base_stat("STR", 5)
        self.assertEqual(self.stats.strength, 15)
        self.stats.set_base_stat("STR", 20)
        self.assertEqual(self.stats.strength, 20)

    def test_bonus_stats(self):
        self.stats.add_bonus_stat("STR", 5)
        self.assertEqual(self.stats.strength, 15) # 10 base + 5 bonus
        
        # Test recalculate_bonuses
        items = [{"stats_bonus": {"STR": 10, "END": 5}}]
        self.stats.recalculate_bonuses(items)
        self.assertEqual(self.stats.strength, 20) # 10 base + 10 bonus
        self.assertEqual(self.stats.endurance, 15) # 10 base + 5 bonus

    def test_serialization(self):
        self.stats.add_bonus_stat("STR", 5)
        data = self.stats.to_dict()
        new_stats = PlayerStats.from_dict(data)
        self.assertEqual(new_stats.strength, 15)

    def test_helper_functions(self):
        # calculate_practice_threshold: 100 + (base * 5)
        self.assertEqual(calculate_practice_threshold(10), 150)
        # calculate_tiered_bonus: Tier 1 (1-100) is 1.0x
        self.assertEqual(calculate_tiered_bonus(50, 10.0), 500)

if __name__ == "__main__":
    unittest.main()
