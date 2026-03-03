import unittest

from game_systems.rewards.aurum_calculator import AurumCalculator
from game_systems.rewards.exp_calculator import ExpCalculator
from game_systems.rewards.loot_calculator import LootCalculator


class TestRewardCalculators(unittest.TestCase):
    def test_exp_calculation(self):
        calc = ExpCalculator()
        monster = {"level": 10, "xp": 50, "tier": "Normal"}
        player_level = 10
        exp = calc.calculate_exp(player_level, monster)
        self.assertEqual(exp, 50)

    def test_aurum_calculation(self):
        calc = AurumCalculator()
        # monster_level, tier, luck
        aurum = calc.calculate_drop(10, "Normal", 0)
        self.assertGreaterEqual(aurum, 10)

    def test_loot_calculation(self):
        calc = LootCalculator()
        # base_chance, rarity, luck, loot_boost
        chance = calc.calculate_drop_chance(10.0, "Common", 0, 1.0)
        self.assertEqual(chance, 10.0)


if __name__ == "__main__":
    unittest.main()
